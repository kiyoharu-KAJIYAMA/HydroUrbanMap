# HydroUrbanMap

This repository contains scripts for constructing the **HydroUrbanMap**, a global dataset that links urban water intake and sewage discharge points to river networks based on hydrological and topographical data.

## Overview

HydroUrbanMap is designed to spatially associate **city mask (urban area)**  with their corresponding **inlet (intake)** , **outlet (discharge)**, and **aqueduct origin** points on river networks, considering elevation, basin, and hydrological connectivity. The generated data is intended for hydrological modeling, water resource assessment, and infrastructure planning in urban water systems.

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

### `A_explore_citymask.py`

**Description**:  
Extracts and verifies the binary city mask for each urban area. Filters out invalid or missing masks.

- **Input**:
  - `cty_lst_*.txt`: List of cities with location and ID
  - `city_XXXXXXXX.gl5`: Binary mask files for each city
- **Output**:
  - `nonprf_flag.txt`: Flags cities with missing masks

---

### `B_detect_mainstream.py`

**Description**:  
Identifies the main stream segments within each urban area by combining elevation and catchment area information. Constructs main river paths for each basin.

- **Input**:
  - `elevtn.CAMA.gl5`: Elevation data
  - `rivnum.CAMA.gl5`: Basin ID map
  - `rivnxl.CAMA.gl5`: River direction (next downstream cell)
  - `rivara.CAMA.gl5`: Upstream catchment area
- **Output**:
  - Masked arrays of valid basins and river paths

---

### `C_define_inlet_outlet.py`

**Description**:  
Detects urban inlet and outlet points based on flow direction, elevation, and location within main river paths. Inlets are typically upstream cells with small area; outlets are downstream with large area.

- **Input**:
  - Processed river path data (from script B)
  - `WUP2018_300k_2010.txt`: City population and location info
- **Output**:
  - `cty_prf_/*.gl5`: Inlet points (purification plants)
  - `cty_swg_/*.gl5`: Outlet points (sewage plants)

---

### `D_generate_aqueduct_layers.py`

**Description**:  
Constructs aqueduct connections for cities with remote intakes. Creates multiple aqueduct layers representing potential transfer paths from intake to city.

- **Input**:
  - Inlet and outlet grids
  - River network
- **Output**:
  - `aqd_layer*.gl5`: Binary aqueduct layers

---

### `E_convert_to_geotiff.py`

**Description**:  
Converts `.gl5` binary format to `.tif` (GeoTIFF) format for visualization and use in GIS software like QGIS.

- **Input**:
  - Any `.gl5` file from prior steps (e.g., `inlet_clrd0000.gl5`)
- **Output**:
  - Corresponding `.tif` file with georeferencing (e.g., `inlet_0000.tif`)

---

## License

This project is released under the MIT License.

## Contact

For questions or contributions, please contact [Kiyoharu Kajiyama](https://github.com/kiyoharu-KAJIYAMA).

