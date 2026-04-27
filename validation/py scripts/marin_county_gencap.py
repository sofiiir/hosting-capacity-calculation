import os
os.environ['PROJ_LIB'] = '/Users/sarak/.conda/envs/electrigrid-env/share/proj'

import logging
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from shapely.geometry import MultiLineString
import matplotlib.pyplot as plt



# set up logging
os.makedirs("outputs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("outputs/host_cap_run.log"),
        logging.StreamHandler()  # also prints to terminal
    ]
)
log = logging.getLogger(__name__)

log.info("Reading input data...")
pge_circuits = gpd.read_file("../../../../../capstone/electrigrid/data/utilities/pge_shapefiles/LineDetail/LineDetail.shp").to_crs("EPSG:4326")
utility_ter = gpd.read_file("../../../../../capstone/electrigrid/data/utilities/IOU_shapefiles.geojson")

pge_circuits = pge_circuits[pge_circuits['FeederName'] == "ALTO 1122"]
pge_circuits['GenCapacit'] = pge_circuits['GenCapacit'] / 1000
pge_circuits['GenCapac_1'] = pge_circuits['GenCapac_1'] / 1000
pge_circuits = pge_circuits.rename(columns={'FeederId': 'circuit_id', 'CSV_LineSe': 'segment_id'})

# crop buildings only to marin
from shapely.geometry import box
marin_bbox = box(-123.0328, 37.8324, -122.3482, 38.3541)

buildings = gpd.read_parquet(
    "../../../../../../capstone/electrigrid/data/building_zillow_merges/marin.parquet").set_crs("EPSG:4326")

buildings = gpd.clip(buildings, marin_bbox)

census_tracts = gpd.read_file("../../../../../capstone/electrigrid/data/census/tl_2025_06_tract/tl_2025_06_tract.shp").to_crs("EPSG:4326")

census_tracts = gpd.clip(census_tracts, marin_bbox)

log.info(f"Loaded {len(pge_circuits)} circuit segments, {len(buildings)} buildings, {len(census_tracts)} tracts")

pge_circuits = pge_circuits.to_crs("EPSG:3310")
buildings = buildings.to_crs("EPSG:3310")
pge_circuits['length_m'] = pge_circuits.length
pge_circuits.sindex
buildings.sindex





log.info("Running nearest join (buildings -> circuits)...")
linked = gpd.sjoin_nearest(buildings, pge_circuits, how="left", lsuffix='_left', rsuffix='_right', distance_col='dist_to_line_m')
linked = linked[linked['dist_to_line_m'] <= 1000]
log.info(f"{len(linked)} buildings within distance threshold")

linked = linked.to_crs("EPSG:4326")
assert linked.crs == census_tracts.crs

log.info("Joining to census tracts...")
linked = linked.sjoin(census_tracts, how="left", predicate="intersects")

log.info("Computing aggregations...")
by_tract = linked.groupby('GEOID_right').sum('unit')
units_by_tract = by_tract['unit'].rename('units_by_tract')
linked = linked.merge(units_by_tract, on="GEOID_right")

max_gen = linked.groupby('circuit_id').max('GenCapacit')
max_gen_feeder = max_gen['GenCapacit'].rename('max_gen')
linked = linked.merge(max_gen_feeder, on='circuit_id')

total_length = linked.groupby('circuit_id').sum('length_m')
total_length = total_length['length_m'].rename('total_feeder_length')
linked = linked.merge(total_length, on='circuit_id')
linked['perc_length'] = (linked['length_m'] / linked['total_feeder_length']) * 100

home_count_seg = linked.groupby('segment_id').sum('unit')['unit'].rename('home_count_seg')
linked = linked.merge(home_count_seg, on="segment_id")

home_count_circuit = linked.groupby('circuit_id').sum('unit')['unit'].rename('home_count_circuit')
linked = linked.merge(home_count_circuit, on="circuit_id")
linked['perc_homes'] = (linked['home_count_seg'] / linked['home_count_circuit']) * 100

circ_poly = linked.groupby(['GEOID_right', 'circuit_id']).sum('unit')
circ_poly_units = circ_poly['unit'].rename('tothh_Cpoly')
linked = linked.merge(circ_poly_units, on=['GEOID_right', 'circuit_id'])

circ_poly_gen = linked.groupby(['GEOID_right', 'circuit_id']).max('GenCapacit')
circ_poly_gen_max = circ_poly['GenCapacit'].rename('DER_max_Cpoly')
linked = linked.merge(circ_poly_gen_max, on=['GEOID_right', 'circuit_id'])

log.info("Computing DER capacity allocation...")
linked['_hhWt'] = linked['DER_max_Cpoly'] * (linked['tothh_Cpoly'] / linked['home_count_circuit'])
summ_hhWt = linked.groupby('circuit_id').sum('_hhWt')['_hhWt'].rename('summ_hhWt')
linked = linked.merge(summ_hhWt, on=['circuit_id'])

linked['_hhWt_n'] = linked['_hhWt'] * (linked['max_gen'] / linked['summ_hhWt'])
linked['_hhWt_n'] = np.where(linked['_hhWt_n'] > linked['DER_max_Cpoly'], linked['DER_max_Cpoly'], linked['_hhWt_n'])
linked['DER_remain'] = linked['_hhWt_n'] / linked['tothh_Cpoly'] * 1000

linked_clean = linked[['ID', 'unit', 'geometry',
                        'circuit_id', 'segment_id', 'GenCapacit',
                        'dist_to_line_m', 'GEOID_right',
                        'length_m', 'units_by_tract', 'max_gen', 'total_feeder_length', 'perc_length',
                        'home_count_seg', 'home_count_circuit', 'perc_homes',
                        'tothh_Cpoly', 'DER_max_Cpoly', '_hhWt', '_hhWt_n', 'DER_remain']]

log.info("Saving outputs...")
linked.to_parquet("../../../../../../capstone/electrigrid/data/linked_clean.parquet")
linked_clean.to_parquet("../../../../../../capstone/electrigrid/data/linked.parquet")
log.info("Done.")