# Hosting capacity calculations

Recreating the hosting capacity calculations adapted from [Brockway et. al's (2021)](https://doi.org/10.1038/s41560-021-00887-6) methodology, which was found in [Supplementary Table 4](https://static-content.springer.com/esm/art%3A10.1038%2Fs41560-021-00887-6/MediaObjects/41560_2021_887_MOESM1_ESM.pdf). 

A comprehensive list of this project's data sources can be found on the [GitHub organization's README](https://github.com/ElectriGrid).

## Repository Structure

```
├── README.md
├── pge.ipynb
├── sce.ipynb
└── sdge.ipynb
```
## File descriptons

Each notebook, named after its respective utility, contains household-level hosting capacily calculations for generation capacity with and without operational flex, solar photovolatic with and without operational flex, and load capacity. 

To run this code, building point geometries (with information on the number of residential units) and ICA utility data is necessary.

## Contributors
- [Sofia Sarak](https://github.com/sofiasarak)
- [Sofia Rodas](https://github.com/sofiiir)
- [Zach Loo](https://github.com/zachyyy700)

The analysis is part of a larger capstone project for the [Master of Environmental Data Science program](https://bren.ucsb.edu/masters-programs/master-environmental-data-science) at the Bren School of Environmental Science & Management. More information on the project can be found on the [Bren website](https://bren.ucsb.edu/projects/power-lines-and-people-mapping-how-distribution-grid-constraints-shape-resilient-and).
