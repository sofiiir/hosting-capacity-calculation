# Hosting capacity calculations

Recreating the hosting capacity calculations based on [Brockway et. al's (2021)](https://doi.org/10.1038/s41560-021-00887-6) methodology, which was found in [Supplementary Table 4](https://static-content.springer.com/esm/art%3A10.1038%2Fs41560-021-00887-6/MediaObjects/41560_2021_887_MOESM1_ESM.pdf). 

A comprehensive list of this project's data sources can be found on the [GitHub organization's README](https://github.com/ElectriGrid).

## Repository Structure

```
├── README.md
├── final
│   ├── pge.ipynb
│   ├── sce.ipynb
│   └── sdge.ipynb
├── initial_attempts
│   ├── pge_explore.ipynb
│   ├── pge_hosting_capacity.ipynb
│   └── sdge_hosting_capacity.ipynb
└── validation
    ├── host_cap_investigation.ipynb
    ├── images
    │   └── pg&e_pv.png
    ├── marin_check.ipynb
    ├── outputs
    │   ├── host_cap_run.log
    │   ├── host_cap_run_all.log
    │   └── host_cap_run_all_fresno.log
    ├── pge_brockway_check.ipynb
    └── py scripts
        ├── fresno_county_all_vars.py
        ├── marin_county_all_vars.py
        └── marin_county_gencap.py
```
### Folder description

**final**: Final hosting capacity calculation performed on each IOU. Notebooks differ in the application of customer use data onto generation values (because each IOU stores the data differently). For example, PG&E's customer breakdown had to be coverted from counts to percentages first.

**initial_attempts:** Contains different versions of hosting capacity calculations, one based on PG&E and the other on SDGE IOUs.

**validation:** Notebooks with different attempt at calculation validation (graphing, comparison with Brockway's results).
- **images:** Contains example plot from Brockway et al., which `pge_brockway_check.ipynb` attempts to replicate.
- **outputs:** Log outputs from running .py scripts in tmux.
- **py scripts:** .py scripts used to run hosting capacity calculations on different areas of California. This was completed as part of the validation step.


## Contributors
- [Sofia Sarak](https://github.com/sofiasarak)
- [Sofia Rodas](https://github.com/sofiiir)
- [Zach Loo](https://github.com/zachyyy700)

The analysis is part of a larger capstone project for the [Master of Environmental Data Science program](https://bren.ucsb.edu/masters-programs/master-environmental-data-science) at the Bren School of Environmental Science & Management. More information on the project can be found on the [Bren website](https://bren.ucsb.edu/projects/power-lines-and-people-mapping-how-distribution-grid-constraints-shape-resilient-and).
