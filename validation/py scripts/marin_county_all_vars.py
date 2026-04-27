import os
os.environ['PROJ_LIB'] = '/Users/sarak/.conda/envs/electrigrid-env/share/proj'

import logging
import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box, MultiLineString
import matplotlib.pyplot as plt

os.makedirs("outputs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler("outputs/host_cap_run_all.log"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

CAP_VARS = ['GenCapacit', 'GenericPVC', 'GenCapac_1', 'GenericCap', 'LoadCapaci']

log.info("Reading input data...")
pge_circuits = gpd.read_file("../../../../../capstone/electrigrid/data/utilities/pge_shapefiles/LineDetail/LineDetail.shp").to_crs("EPSG:4326")
utility_ter = gpd.read_file("../../../../../capstone/electrigrid/data/utilities/IOU_shapefiles.geojson")

pge_circuits = pge_circuits[pge_circuits['FeederName'] == "ALTO 1122"]

# Divide all capacity columns by 1000
for col in CAP_VARS:
    pge_circuits[col] = pge_circuits[col] / 1000

pge_circuits = pge_circuits.rename(columns={'FeederId': 'circuit_id', 'CSV_LineSe': 'segment_id'})

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

total_length = linked.groupby('circuit_id').sum('length_m')
total_length = total_length['length_m'].rename('total_feeder_length')
linked = linked.merge(total_length, on='circuit_id')
linked['perc_length'] = (linked['length_m'] / linked['total_feeder_length']) * 100

home_count_seg = linked.groupby('segment_id').sum('unit')['unit'].rename('home_count_seg')
linked = linked.merge(home_count_seg, on="segment_id")

home_count_circuit = linked.groupby('circuit_id').sum('unit')['unit'].rename('home_count_circuit')
linked = linked.merge(home_count_circuit, on="circuit_id")
linked['perc_homes'] = (linked['home_count_seg'] / linked['home_count_circuit']) * 100

# Run DER allocation for each capacity variable
log.info("Computing DER capacity allocation for all capacity variables...")
result_cols = {}

for cap_var in CAP_VARS:
    log.info(f"  Processing {cap_var}...")

    max_gen = linked.groupby('circuit_id')[cap_var].max().rename(f'max_gen_{cap_var}')
    linked = linked.merge(max_gen, on='circuit_id')

    circ_poly_units = linked.groupby(['GEOID_right', 'circuit_id'])['unit'].sum().rename('tothh_Cpoly')
    linked = linked.merge(circ_poly_units, on=['GEOID_right', 'circuit_id'])

    circ_poly_gen = linked.groupby(['GEOID_right', 'circuit_id'])[cap_var].max().rename(f'DER_max_Cpoly_{cap_var}')
    linked = linked.merge(circ_poly_gen, on=['GEOID_right', 'circuit_id'])

    hhWt_col = f'_hhWt_{cap_var}'
    linked[hhWt_col] = linked[f'DER_max_Cpoly_{cap_var}'] * (linked['tothh_Cpoly'] / linked['home_count_circuit'])

    summ_hhWt = linked.groupby('circuit_id')[hhWt_col].sum().rename(f'summ_hhWt_{cap_var}')
    linked = linked.merge(summ_hhWt, on='circuit_id')

    hhWt_n_col = f'_hhWt_n_{cap_var}'
    linked[hhWt_n_col] = linked[hhWt_col] * (linked[f'max_gen_{cap_var}'] / linked[f'summ_hhWt_{cap_var}'])
    linked[hhWt_n_col] = np.where(
        linked[hhWt_n_col] > linked[f'DER_max_Cpoly_{cap_var}'],
        linked[f'DER_max_Cpoly_{cap_var}'],
        linked[hhWt_n_col]
    )

    result_col = f'{cap_var}_kWphh'
    linked[result_col] = linked[hhWt_n_col] / linked['tothh_Cpoly'] * 1000
    result_cols[cap_var] = result_col

    # Drop intermediate columns to keep linked clean between iterations
    linked = linked.drop(columns=[
        f'max_gen_{cap_var}', f'DER_max_Cpoly_{cap_var}',
        hhWt_col, f'summ_hhWt_{cap_var}', hhWt_n_col,
        'tothh_Cpoly'  # re-merged each iteration
    ])

log.info("Saving outputs...")
result_cols_list = list(result_cols.values())

linked_clean = linked[['ID', 'unit', 'geometry',
                        'circuit_id', 'segment_id',
                        'dist_to_line_m', 'GEOID_right',
                        'length_m', 'units_by_tract', 'total_feeder_length', 'perc_length',
                        'home_count_seg', 'home_count_circuit', 'perc_homes']
                       + result_cols_list]

linked.to_parquet("../../../../../../capstone/electrigrid/data/linked_all.parquet")
linked_clean.to_parquet("../../../../../../capstone/electrigrid/data/linked_clean_all.parquet")
log.info(f"Done. Result columns: {result_cols_list}")