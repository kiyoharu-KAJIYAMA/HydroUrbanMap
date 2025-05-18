# HydroUrbanMap

This repository contains scripts for constructing the **HydroUrbanMap**, a global dataset that links urban water intake and sewage discharge points to river networks based on hydrological and topographical data.

## Overview

HydroUrbanMap is designed to spatially associate **city mask (urban area)**  with their corresponding **inlet (intake)** , **outlet (discharge)**, and **aqueduct origin (remote water source)** points on river networks, considering elevation, basin, and hydrological connectivity. The generated data is intended for hydrological modeling, water resource assessment, and infrastructure planning in urban water systems.

## Execution Order

The scripts in this repository are named using a **prefix number** that indicates the **recommended execution order**:

- `00` : Preprocessing of downloaded datasets (GPW, WUP)
- `01-03` : City mask exploration
- `04-09` : Postprocessing of city mask exploration
- `10-13` : Creation of core products (city mask, city water inlet, city water outlet, aqueduct origin)
- `14-15` : Postprocessing of core products

Please run the scripts in number order to ensure consistent output.

---

## Script Descriptions

### `00_load_gpwv4-2p5min.ipynb`

**Description**:  
This script loads a population raster file from the **Gridded Population of the World, Version 4 (GPWv4)** dataset. The data corresponds to the year 2010 and is provided at a 2.5 arc-minute spatial resolution. The population values are adjusted to match **UN World Population Prospects (UN WPP)** 2015 country totals.

The original dataset was downloaded from the official NASA SEDAC website:

> https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp

---

- **Input**:
  - `gpw_v4_population_count_adjusted_to_2015_unwpp_country_totals_rev11_2010_2pt5_min.tif`: Global population grid for the year 2010, adjusted to UN WPP estimates. Downloaded from NASA SEDAC GPWv4 dataset (https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11). Format: GeoTIFF. Resolution: 2.5 arc-minutes (~5 km). CRS: WGS84.

- **Output**:
  - `GPW4ag__20100000.gl5`: A vertically flipped binary population grid file (float32, 2160×4320) converted from the input GeoTIFF. Used as a base dataset to detect urban boundaries in the HydroUrbanMap workflow.

---

### `00_load_wup2018v11.ipynb`

**Description**:  
This script processes the city-level data from the **World Urbanization Prospects 2018 Revision (WUP2018v11)** dataset provided by the United Nations. It extracts urban agglomerations with populations over 300,000 as of 2010, along with city names, coordinates, population values, and regional classification. The cleaned and reformatted data are used as the master city list for the HydroUrbanMap workflow.

The original dataset was downloaded from the United Nations Population Division:

> https://population.un.org/wup/

---

- **Input**:
  - `WUP2018-F12-Cities_Over_300K.xls`: Raw city population estimates from the UN WUP2018 database. Includes latitude/longitude, population by year, and classification metadata.

- **Output**:
  - `WUP2018_300k_2010.txt`: Reformatted tab-delimited text file. Contains city IDs, coordinates, city names, country, population (year 2010), and continent/region labels. Used as input for subsequent masking and ID-based operations.

---

### `00_load_grid_area.py`

**Description**:  
This script calculates the surface area (in m²) of each grid cell on a global 5-arc-minute resolution grid using an ellipsoidal approximation of Earth’s shape. The computed grid-cell areas are used in later scripts for mass-conserving aggregation and area-weighted statistics.

The method is based on Oki and Kanae (1997), Japan Society of Hydrology and Water Resources.

---

- **Input**:
  - None (the script generates a 5-arc-minute global grid from predefined constants).

- **Output**:
  - `grdara.gl5`: A binary file (`float32`, 2160×4320) containing the surface area (m²) of each grid cell on a global 5-arc-minute grid.

---

### `01_make_citycenter.py`

**Description**:  
This script converts a city list with latitude/longitude coordinates into a raster map (`city_center.gl5`) where each grid cell is marked with its corresponding city index. This raster serves as a quick lookup map of city centers across the globe on a 5-arc-minute resolution grid.

Each city in the WUP dataset is assigned a unique integer ID (starting from 1), and its corresponding grid cell is populated with this ID.

---

- **Input**:
  - `WUP2018_300k_2010.txt`: A tab-delimited text file containing a list of global cities. Columns include city ID, latitude, longitude, and name. (Used columns: [0]=ID, [1]=Lat, [2]=Lon)

- **Output**:
  - `city_center.gl5`: A binary raster file (`float32`, 2160×4320) where each cell contains the city ID if the cell corresponds to a city center, or 0 otherwise. Used as an index reference in subsequent mapping steps.

---

### `02_make_timestep.py`

**Description**:  
This script generates a raster grid (`city_time.gl5`) representing the order of cities based on a defined loop index. Each city is assigned a unique timestep value (1-based index) in the order they are processed. This raster is used to visualize or control the temporal processing sequence of cities in the HydroUrbanMap workflow.

---

- **Input**:
  - `WUP2018_300k_2010.txt`: A list of global cities including ID, latitude, and longitude. Each city is sequentially indexed based on its row number in the file (starting from 1).

- **Output**:
  - `city_time.gl5`: A binary raster (`float32`, 2160×4320) where each grid cell corresponding to a city center contains a timestep value representing the order in which it was processed. Cells not corresponding to a city center remain 0.

---

### `03_make_cluster.py`

**Description**:  
This script assigns cluster IDs to cities based on their adjacency or spatial proximity in the population raster. Each city is labeled with a cluster ID in the `city_clst.gl5` output. The clustering helps differentiate overlapping or neighboring urban areas and is used in later masking and filtering steps in the HydroUrbanMap workflow.

---

- **Input**:
  - `WUP2018_300k_2010.txt`: A tab-separated list of cities including ID, latitude, longitude, and population.
  - `city_center.gl5`: A raster (`float32`, 2160×4320) indicating the center location of each city, where grid cell values correspond to the city index.
  - `GPW4ag__20100000.gl5`: Population raster used for neighborhood-based adjacency calculations (converted from GPWv4 dataset).

- **Output**:
  - `city_clst.gl5`: A binary raster (`float32`, 2160×4320) where each city center grid is assigned a cluster ID. Multiple cities within the same spatial group (e.g., overlapping or very close) share the same cluster number.

---

### `04_add_cluster_log.py`

**Description**:  
This script parses the output log generated from cluster validation procedures and extracts useful metrics for each city, including gradient availability, number of city mask grids, and coverage ratio. The parsed information is then saved in a summary file (`cluster_result.txt`) for quality control and post-analysis.

---

- **Input**:
  - `cluster.log`: A plain text log file containing diagnostic output from prior steps (e.g., gradient analysis). Each city block is separated by dashed lines and includes information such as city index, mask grid count, and coverage.

- **Output**:
  - `cluster_result.txt`: A tab-separated summary text file containing four values per city:
    - `city_index`: ID of the city
    - `has_valid_gradient`: Boolean indicating whether a valid terrain gradient was detected
    - `city_mask`: Number of grid cells identified in the city mask
    - `mask_cover`: Coverage ratio of the city mask over the population center

---

### `05_add_invalid.py`

**Description**:  
This script identifies invalid or missing city datasets by comparing a master city list with the results of previous analyses (e.g., clustering, purification intake/outlet detection). Cities that are missing masks, have no river networks, or fail key spatial checks are labeled accordingly. This helps ensure downstream analyses only include reliable urban water datasets.

---

- **Input**:
  - `WUP2018_300k_2010.txt`: Master list of global cities used throughout the HydroUrbanMap workflow, including city index, coordinates, and population.
  - `nonprf_flag.txt`: List of cities without purification intakes (`PRF`). Entries include city index and flag (`NoMASK` or `True`).
  - `cluster_result.txt`: City-wise evaluation file including gradient flags, city mask grid count, and coverage ratio.

- **Output**:
  - `invalid_city.txt`: A text summary listing invalid cities. Each line contains the city index and the reason for invalidation (e.g., `NoMASK`, `NoRiver`, `NoCluster`), serving as an exclusion reference for later steps in HydroUrbanMap.

---

### `06_add_nomask_flag.py`

**Description**:  
This script classifies cities into three categories based on water infrastructure validity flags:  
- Cities with valid purification infrastructure (`False`)  
- Cities without purification infrastructure but with valid masks (`True`)  
- Cities with no valid city mask (`NoMASK`)  

The classification is output as a summary text file listing each city’s metadata and category. A total count for each classification is appended at the end of the file.

---

- **Input**:
  - `nonprf_flag.txt`: Text file containing one line per city, in the format: `city_index|flag`, where `flag` is one of `False`, `True`, or `NoMASK`.
  - `WUP2018_300k_2010.txt`: Master city list containing metadata such as city name, country, and region (tab-separated).

- **Output**:
  - `classification.txt`: Each line includes the city index, classification flag, region, country, and city name. The final three lines summarize counts of cities in each category:
    - `right`: Cities with valid purification (`False`)
    - `noprf`: Cities lacking purification intake (`True`)
    - `nomask`: Cities without valid masks (`NoMASK`)

---

### `07_add_clustered_population.py`

**Description**:  
This script appends estimated clustered population values to each city entry. It loads population data (e.g., sum of grid cells within clustered masks) from a precomputed `.npy` file and merges this information with existing classification results. The final output is a text file listing the city ID, classification flag, region, country, city name, and the estimated population within clustered urban areas.

---

- **Input**:
  - `classification.txt`: A classification result file where each line contains:
    - `city_index|flag|region|country|city_name`
  - `pop_cluster.npy`: A NumPy binary file storing an array of shape `(1860,)`, where each element corresponds to the clustered population estimate of a city (as a float or integer).

- **Output**:
  - `classification_clustered.txt`: A tab-separated text file with one line per city, containing:
    - `city_index`, `flag`, `region`, `country`, `city_name`, `clustered_population`

---

### `08_add_table.py`

**Description**:  
This script generates a final formatted table of urban water infrastructure classification results. It reads the output of prior steps—especially the classification file with clustered population estimates—and combines them with the original WUP2018 city data. The result is a comprehensive table that includes geographic attributes, classification flags, and clustered population statistics, which can be used in publications or GIS applications.

---

- **Input**:
  - `classification_clustered.txt`: Text file from `07_add_clustered_population.py`, including fields:
    - `city_index|flag|region|country|city_name|clustered_population`
  - `WUP2018_300k_2010.txt`: Original city information from UN WUP 2018, including:
    - `city_index`, `lat`, `lon`, `est_pop`, `country`, `region`, `city_name`

- **Output**:
  - `city_table.txt`: Final tabular text file including:
    - `city_index`, `flag`, `region`, `country`, `city_name`, `lat`, `lon`, `est_pop`, `clustered_population`

---

### `09_add_citymask_status.py`

**Description**:  
This script adds city mask status information to the final output table by checking the presence and validity of binary mask files (`city_XXXXXXXX.gl5`). Cities without a corresponding mask file are flagged accordingly. The status is appended as a new column to the urban classification table, allowing downstream processes or quality control to filter based on data completeness.

---

- **Input**:
  - `city_table.txt`: Table generated by `08_add_table.py`, listing urban water classification metadata.
  - `cty_msk_*/city_XXXXXXXX.gl5`: Binary grid mask files for each city, expected to be present for valid entries.
  - `nonprf_flag.txt`: Flags indicating whether a city lacks a mask (`NoMASK`) or lacks a main river (`True`).

- **Output**:
  - `city_table_with_maskstatus.txt`: Updated table including a new column `mask_status` that takes values:
    - `Valid`: Mask file exists and is valid
    - `NoMASK`: No valid mask file
    - `True`: Valid mask but no detectable purification river

---

### `10_make_citymask.py`

**Description**:  
This script generates a global raster file showing all valid urban masks used in HydroUrbanMap. It reads individual binary mask files for each city (`city_XXXXXXXX.gl5`) and combines them into a single 2D global grid (2160×4320). Each pixel in the output indicates the ID of the corresponding city, or zero where no city mask is present.

---

- **Input**:
  - `cty_msk_*/city_XXXXXXXX.gl5`: Binary mask files for each valid city (format: `float32`, shape: 2160×4320). A value of `1` denotes inclusion in the city mask, and `0` otherwise.

- **Output**:
  - `city_clrd0000.gl5`: A global binary mask grid (float32, 2160×4320) where each pixel value corresponds to a unique city ID. Used in subsequent processing to analyze city boundaries collectively.

---

### `11_make_city_water_inlet_outlet.py`

**Description**:  
This script detects the major **intake (inlet)** and **outlet (sewage)** points of urban water infrastructure for each city. It analyzes hydrological variables such as elevation, river catchment area, and flow direction. 

This script handles the loading and preprocessing of CAMA-Flood river network data at 5 arc-minute resolution. These data include river flow direction, catchment area, and next-cell coordinates, all required for hydrological network analysis.
The dataset referred to as "CAMA" (Catchment-based Macro-scale Floodplain model) can be obtained by accessing the following website and contacting the developer, **Dr. Dai Yamazaki**, for download permission:

> https://hydro.iis.u-tokyo.ac.jp/~yamadai/cama-flood/

Please choose the **5 min resolution** dataset.

Cities without valid masks or main rivers are flagged in the output log.

The resulting binary files mark key urban water infrastructure locations, which are critical for assessing water vulnerability and aqueduct dependencies in HydroUrbanMap.

---

- **Input**:
  - `cty_lst_*.txt`: List of cities with IDs, names, and geographic coordinates.
  - `cty_msk_*/city_XXXXXXXX.gl5`: Binary mask files for each city.
  - `rivnum.CAMA.gl5`: River basin (catchment) ID map.
  - `rivara.CAMA.gl5`: Upstream catchment area (m²) per grid.
  - `rivnxl.CAMA.gl5`: River downstream link (next cell) in l-coordinate.
  - `elevtn.CAMA.gl5`: Elevation data (m).
  - `WUP2018_300k_2010.txt`: Metadata including population and city information.

- **Output**:
  - `cty_prf_*/city_XXXXXXXX.gl5`: Binary raster file (2160×4320, float32) marking the main **intake (inlet)** location for the given city (value = city ID).
  - `cty_swg_*/city_XXXXXXXX.gl5`: Binary raster file (2160×4320, float32) marking the **outlet (sewage)** location for the given city (value = city ID).
  - `nonprf_flag.txt`: Text log listing cities with:
    - `NoMASK` – missing or invalid city mask.
    - `True` – mask exists but no valid intake could be detected.
    - `False` – valid intake and outlet detected.

---

### `12_make_updown.py`

**Description**:  
This script determines whether the outlet (sewage) point is **downstream** of the intake (inlet) point for each city. It uses a pre-generated set of city-level intake (`cty_prf_*`) and outlet (`cty_swg_*`) raster files, and performs a **topographic and routing-based check** using river network data. The result is saved as a raster (`prf_updw/`) indicating the **upstream/downstream relationship**.

This information is important for identifying cities with potentially problematic water flows (e.g., outlet placed upstream of intake, which may indicate data or infrastructure anomalies).

---

- **Input**:
  - `cty_prf_*/city_XXXXXXXX.gl5`: City-specific intake raster.
  - `cty_swg_*/city_XXXXXXXX.gl5`: City-specific outlet raster.
  - `rivnxl.CAMA.gl5`: Downstream routing index (next l-coordinate per cell).
  - `rivnum.CAMA.gl5`: River basin (catchment ID) map.

- **Output**:
  - `prf_updw/city_XXXXXXXX.gl5`: Binary raster (2160×4320, float32) where cells belonging to cities with outlets **upstream** of intake are marked as `1`, otherwise `0`. Used to **enforce intake-outlet consistency** in later analysis steps.

---

### `13_make_aqueduct_origin.py`

**Description**:  
This script identifies the **origin grid cells of aqueducts** supplying water to each city. It assumes that water is transferred from high-discharge or geographically suitable river grids **outside** the urban mask and **within the same basin** when possible. The script uses `rivout` (river discharge), `rivnum` (basin ID), and `city_mask` data to locate candidate source grids. If no appropriate source is found within the same basin, it looks for the highest discharge grid **in the surrounding region**.

This operation supports the construction of **virtual aqueduct networks**, which are used to trace water intake origins in cities lacking sufficient local river flow.

---

- **Input**:
  - `rivout.CAMA.gl5`: River discharge (e.g., 2010–2019 mean annual discharge).
  - `rivnum.CAMA.gl5`: River basin IDs (to restrict candidate source grids).
  - `cty_msk_*/city_XXXXXXXX.gl5`: City binary mask (used to exclude in-city grids).
  - `nonprf_flag.txt`: Flags for cities lacking intake points (`True` or `NoMASK`).
  - `cty_prf_*/city_XXXXXXXX.gl5`: City intake map (to ensure only `nonprf` cities are processed).

- **Output**:
  - `cty_prf_*/city_XXXXXXXX.gl5`: Updated intake maps where new **virtual source grids** are assigned as intake cells.
  - `cty_aqd_/aqd_layer001.gl5`: Aggregated binary raster of aqueduct origin points (layered format). Multiple layers may be created to represent overlapping or distant source points.

---

### `14_make_layered_aqueduct.py`

**Description**:  
This script organizes aqueduct origin points into **multiple global layers**, where each layer contains **non-overlapping aqueduct source cells**. Since some cities may share the same intake cells, layering ensures that all unique intake sources are preserved without overwriting. This is especially useful for visualizing or analyzing water transfers in a **spatially disaggregated but complete** manner.

The layering process continues until **all aqueduct origin cells are uniquely assigned** to a layer, avoiding conflicts in overlapping regions.

---

- **Input**:
  - `cty_prf_*/city_XXXXXXXX.gl5`: City-specific intake grid files (created in previous steps).
  - `nonprf_flag.txt`: List of cities flagged with `True`, indicating lack of intake and need for virtual aqueducts.

- **Output**:
  - `cty_aqd_/aqd_layerXXX.gl5`: Stacked binary layers (e.g., `aqd_layer001.gl5`, `aqd_layer002.gl5`, ...) where each file contains **non-overlapping** aqueduct source grids (float32 format, 2160×4320). These layers together represent the complete global aqueduct origin map.

---

### `15_binary2tiff.py`

**Description**:  
This script converts binary `.gl5` files (float32 format, 2160×4320) into **GeoTIFF** format for use in **GIS software** like QGIS. The conversion uses a WGS84 coordinate reference system with a spatial resolution of **5 arc-minutes (~10 km)**. Multiple `.gl5` files can be converted in one script run by changing the input/output paths.

This script is useful for visualizing water infrastructure layers—such as **city masks**, **intake points**, **sewage points**, and **aqueduct sources**—in map-based applications.

---

- **Input**:
  - `city_clrd0000.gl5`: Global binary city mask (0 = background, city_id elsewhere).
  - `inlet_clrd0000.gl5`: Global intake point binary map.
  - `outlet_clrd0000.gl5`: Global outlet point binary map.
  - `aqd_layer001.gl5` – `aqd_layer004.gl5`: Aqueduct source layers (non-overlapping grids per layer).

- **Output**:
  - `mask_0000.tif`: Converted city mask GeoTIFF.
  - `inlet_0000.tif`: Converted inlet map GeoTIFF.
  - `outlet_0000.tif`: Converted outlet map GeoTIFF.
  - `aqueduct_layer001.tif` – `aqueduct_layer004.tif`: GeoTIFF versions of the aqueduct origin layers.

---

## License

This project is released under the MIT License.

## Contact

For questions or contributions, please contact [Kiyoharu Kajiyama](https://github.com/kiyoharu-KAJIYAMA).

