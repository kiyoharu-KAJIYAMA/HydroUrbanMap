"""
Author Kajiyama @ 20240402
edited by Kajiyama @ 20240430
edited by Kajiyama @ 20241120
+ if grid_num = 0, no PRF
+ if grid_num = 1, PRF=SWG
+ if grid_num = 2  PRF=higher elevation, SWG=lower elevation
+ No main river, PRF=highest elevation in same basin, SWG=lowest elevation in same basin
+ No main river & no same basin, PRF=highest elevation in MASK, SWG=lowest elevation MASK
edited by Kajiyama @ 20241127
+ No main river, largest rivout is prf, lowest elevatoin is swg
edited by Kajiyama @ 20241215
+ If swg is located in upstream of prf, swg location is replaced to the same grid of prf
"""

import os
import copy
import numpy as np

#---------------------------------------------------------------------------------------------------------------
#   Main Function
#---------------------------------------------------------------------------------------------------------------

def explore(target_index, remove_grid, innercity_grid, width, save_flag=False):
    """
    A: After over remove_grid process
    B: After over remove_grid process & over innercity_grid process
    """
    latgrd = 2160 # sum of latitude grids (y)
    longrd = 4320 # sum of longitude grids (x)

#---------------------------------------------------------------------------------------------------------------
#   PATH
#---------------------------------------------------------------------------------------------------------------

    # root directory
    workdir         = "/your/directory/path"
    # lonlat data
    city_path        = f"{workdir}/table_first.txt"
    # city mask data
    cmsk_dir         = f"{workdir}/cty_msk_"
    # elevation data
    elvmin_path      = f"{workdir}/elevtn.CAMA.gl5"
    # riv data
    rivnum_path      = f"{workdir}/rivnum.CAMA.gl5"
    rivara_path      = f"{workdir}/rivara.CAMA.gl5"
    rivnxl_path      = f"{workdir}/rivnxl.CAMA.gl5"
    rivout_path      = f"{workdir}/W5E5LR__20190000.gl5"
    # facility data
    prf_save_dir     = f"{workdir}/cty_prf_"
    swg_save_dir     = f"{workdir}/cty_swg_"
    # auxiliary data
    nonprf_path      = f"{workdir}/nonprf_flag.txt"
    updown_path      = f"{workdir}/prf_updw/city_{target_index:08}.gl5"

#---------------------------------------------------------------------------------------------------------------
#   City Lon Lat Information
#---------------------------------------------------------------------------------------------------------------

    """
    first line of lines
    1|VALD|DOWN|36859.626|36855016.0|31821846.0|Japan|93.0|eastern asia| 35.6895|139.6917|Tokyo|East Asia
    """
    
    # Open city_list.txt and read all lines
    with open(city_path, "r") as input_file:
        lines = input_file.readlines()

    # Select the line corresponding to the target city
    line       = lines[target_index-1]
    parts      = line.split('|')  # Split each line by the pipe symbol
    parts      = [item.strip() for item in parts]
    city_num   = int(parts[0])  # City ID number
    cnt_lat    = float(parts[9])  # Latitude of the city center
    cnt_lon    = float(parts[10])  # Longitude of the city center
    city_name  = parts[11].replace("\"", "").replace("?", "").replace("/", "")  # Cleaned city name
    ovlp_state = parts[1]  # Overlap status
    clst_state = parts[2]  # Clustering status

    # Compute the bounding box using the specified width
    lonmin = float(cnt_lon - width)
    lonmax = float(cnt_lon + width)
    latmin = float(cnt_lat - width)
    latmax = float(cnt_lat + width)

    print(f"city_num {city_num}")
    print(city_name)


#---------------------------------------------------------------------------------------------------------------
#   Get Lon Lat
#---------------------------------------------------------------------------------------------------------------

    """Calculate the indices corresponding to the desired latitudes and longitudes"""
    # Western longitudes from the UK are negative: 0 >= lon >= -180
    # Eastern longitudes from the UK are positive: 0 <= lon <= 180
    # Ranges go from smaller to larger values (e.g., lat 34–36, lon 138–140)
    lat_length = np.linspace(-90, 90, latgrd+1)
    lon_length = np.linspace(-180, 180, longrd+1)
    lat_start, lat_end = np.searchsorted(lat_length, [latmin, latmax])
    lon_start, lon_end = np.searchsorted(lon_length, [lonmin, lonmax])

    # Adjust the starting grid index to align with a 0.25-degree resolution
    # Latitude index adjustment
    if lat_start % 3 == 0:
        lat_start = lat_start
    elif lat_start % 3 == 1:
        lat_start -= 1
    elif lat_start % 3 == 2:
        lat_start += 1
    # Longitude index adjustment
    if lon_start % 3 == 0:
        lon_start = lon_start
    elif lon_start % 3 == 1:
        lon_start -= 1
    elif lon_start % 3 == 2:
        lon_start += 1

    # Number of grids per side of the square computation window (1 degree = 12x12 grids)
    width_grid = width * 12 * 2

    # Update end indices based on adjusted start and window size
    lat_end = lat_start + width_grid
    lon_end = lon_start + width_grid

#---------------------------------------------------------------------------------------------------------------
#   Load city mask data (g_mask_cropped)
#---------------------------------------------------------------------------------------------------------------

    if clst_state == 'NoMK' or ovlp_state == 'RMVD':
        if city_num == 1:
            with open(nonprf_path, 'w') as file:
                file.write(f"{city_num}|NoMASK\n")
        else:
            with open(nonprf_path, 'a') as file:
                file.write(f"{city_num}|NoMASK\n")
        josui_for_save = np.zeros((2160, 4320))
        gesui_for_save = np.zeros((2160, 4320))
        return josui_for_save, gesui_for_save

    g_mask_original = np.fromfile(f'{cmsk_dir}/city_clrd0000.gl5', 'float32').reshape(latgrd, longrd)
    g_mask = np.flipud(g_mask_original)
    g_mask = np.ma.masked_where(g_mask != city_num, g_mask)
    g_mask_cropped = g_mask[lat_start:lat_end, lon_start:lon_end]
    g_mask_cropped = np.flipud(g_mask_cropped)

#---------------------------------------------------------------------------------------------------------------
#   external operation
#---------------------------------------------------------------------------------------------------------------

    grid_count = int(float(parts[7]))
    if grid_count == 1:
        if city_num == 1:
            with open(nonprf_path, 'w') as file:
                file.write(f"{city_num}|True\n")
        else:
            with open(nonprf_path, 'a') as file:
                file.write(f"{city_num}|True\n")

        josui_for_save = np.zeros((2160, 4320))
        gesui_for_save = np.zeros((2160, 4320))

        coordinates = np.where(g_mask_original==city_num)
        josui_for_save[coordinates] = city_num
        gesui_for_save[coordinates] = city_num

        return josui_for_save, gesui_for_save

#---------------------------------------------------------------------------------------------------------------
#   Load elevation data (g_elv_cropped)
#---------------------------------------------------------------------------------------------------------------

    g_elv = np.fromfile(elvmin_path, 'float32').reshape(latgrd, longrd)
    g_elv = np.flipud(g_elv)
    g_elv = np.ma.masked_where(g_elv >= 1E20, g_elv)
    g_elv_cropped = g_elv[lat_start:lat_end, lon_start:lon_end]
    g_elv_cropped = np.flipud(g_elv_cropped)

#---------------------------------------------------------------------------------------------------------------
#   Load basin data (g_rivnum_cropped)
#---------------------------------------------------------------------------------------------------------------

    g_rivnum = np.fromfile(rivnum_path, 'float32').reshape(latgrd, longrd)
    g_rivnum = np.flipud(g_rivnum)
    g_rivnum = np.ma.masked_where(g_rivnum >= 1E20, g_rivnum)
    g_rivnum_cropped = g_rivnum[lat_start:lat_end, lon_start:lon_end]
    g_rivnum_cropped = np.flipud(g_rivnum_cropped)
    g_rivnum_cropped = np.ma.masked_where(~np.isfinite(g_rivnum_cropped) | (g_rivnum_cropped == 0), g_rivnum_cropped)

#---------------------------------------------------------------------------------------------------------------
#   Load upper river catchment area (g_rivara_cropped)
#---------------------------------------------------------------------------------------------------------------

    g_rivara = np.fromfile(rivara_path, 'float32').reshape(latgrd, longrd)
    g_rivara = np.flipud(g_rivara)
    g_rivara = np.ma.masked_where(g_rivara >= 1E20, g_rivara)
    g_rivara_cropped = g_rivara[lat_start:lat_end, lon_start:lon_end]
    g_rivara_cropped = np.flipud(g_rivara_cropped)
    g_rivara_cropped = np.ma.masked_where(~np.isfinite(g_rivara_cropped) | (g_rivara_cropped == 0), g_rivara_cropped)

#---------------------------------------------------------------------------------------------------------------
#   Load annual steamflow 2010-2019 mean (g_rivout_cropped)
#---------------------------------------------------------------------------------------------------------------

    g_rivout = np.fromfile(rivout_path, 'float32').reshape(latgrd, longrd)
    g_rivout = np.flipud(g_rivout)
    g_rivout = np.ma.masked_where(g_rivout >= 1E20, g_rivout)
    g_rivout_cropped = g_rivout[lat_start:lat_end, lon_start:lon_end]
    g_rivout_cropped = np.flipud(g_rivout_cropped)
    g_rivout_cropped = np.ma.masked_where(~np.isfinite(g_rivout_cropped) | (g_rivout_cropped == 0), g_rivout_cropped)


#---------------------------------------------------------------------------------------------------------------
#   Load river's next l coordinate data (g_rivnxl_cropped)
#---------------------------------------------------------------------------------------------------------------

    g_rivnxl = np.fromfile(rivnxl_path, 'float32').reshape(latgrd, longrd)
    g_rivnxl = np.flipud(g_rivnxl)
    g_rivnxl = np.ma.masked_where(g_rivnxl >= 1E20, g_rivnxl)
    g_rivnxl_cropped = g_rivnxl[lat_start:lat_end, lon_start:lon_end]
    g_rivnxl_cropped = np.flipud(g_rivnxl_cropped)
    g_rivnxl_cropped = np.ma.masked_where(~np.isfinite(g_rivnxl_cropped) | (g_rivnxl_cropped == 0), g_rivnxl_cropped)

#---------------------------------------------------------------------------------------------------------------
#   Basin data only where city mask exists (g_rivnum_cropped_city)
#---------------------------------------------------------------------------------------------------------------

    g_rivnum_cropped_city = np.where(g_mask_cropped == city_num, g_rivnum_cropped, np.nan)
    g_rivnum_cropped_city = np.ma.masked_where(~np.isfinite(g_rivnum_cropped_city) | (g_rivnum_cropped_city == 0), g_rivnum_cropped_city)

#---------------------------------------------------------------------------------------------------------------
#   3D array consists of g_rivara_cropped + g_rivnum_cropped (g_ara_num_cropped)
#---------------------------------------------------------------------------------------------------------------

    # g_ara_num_croppedを構造化配列として作成
    dtype = [('rivara', 'float32'), ('rivnum', 'float32')]
    g_ara_num_cropped = np.empty(g_rivara_cropped.shape, dtype=dtype)

    # rivaraとrivnumのデータをg_ara_num_croppedに追加
    g_ara_num_cropped['rivara'] = g_rivara_cropped
    g_ara_num_cropped['rivnum'] = g_rivnum_cropped

#---------------------------------------------------------------------------------------------------------------
#  　Basin over remove_grid (Rivnum_A_array)
#---------------------------------------------------------------------------------------------------------------

    # Create a masked array from g_rivnum_cropped, masking NaN values
    g_rivnum_cropped_masked = np.ma.masked_array(g_rivnum_cropped, np.isnan(g_rivnum_cropped))

    # Get unique values (non-NaN river basin IDs) and their occurrence counts
    unique_values_org, counts_org = np.unique(g_rivnum_cropped_masked.compressed(), return_counts=True)
    value_counts_dict = dict(zip(unique_values_org, counts_org))

    # Sort the river basin IDs in descending order of occurrence count
    # These are expected to be sorted by frequency within the city mask
    sorted_dict_by_value_descending = dict(sorted(value_counts_dict.items(), key=lambda item: item[1], reverse=True))

    # Create a new dictionary with only river basins that exceed the remove_grid threshold
    # This step filters out small basins
    filtered_dict_A = {key: value for key, value in sorted_dict_by_value_descending.items() if value >= remove_grid}

    # Create an empty masked array (e.g., 24x24) to store valid river basin IDs
    Rivnum_A_array = np.ma.masked_all(g_rivnum_cropped_masked.shape, dtype='float32')

    # For each river basin ID that passed the threshold, find matching positions
    # and assign the basin ID to the new array
    for rivnum_id in filtered_dict_A.keys():
        matching_positions = np.where(g_rivnum_cropped_masked.data == rivnum_id)
        Rivnum_A_array[matching_positions] = rivnum_id

    # Apply mask to remove any invalid or zero values
    Rivnum_A_array = np.ma.masked_where(~np.isfinite(Rivnum_A_array) | (Rivnum_A_array == 0), Rivnum_A_array)

#---------------------------------------------------------------------------------------------------------------
#   Basin over remove_grid within city mask (Rivnum_A_array_citymasked)
#---------------------------------------------------------------------------------------------------------------

    # Create a mask where Rivnum_A_array is either NaN or equal to 0
    invalid_mask = np.isnan(Rivnum_A_array) | (Rivnum_A_array == 0)

    # Apply masking to all locations where:
    # - g_mask_cropped does not equal the current city ID (i.e., outside the city), or
    # - the river basin value is invalid (NaN or 0)
    Rivnum_A_array_citymasked = np.ma.masked_where((g_mask_cropped != city_num) | invalid_mask, Rivnum_A_array)


#---------------------------------------------------------------------------------------------------------------
#   Identify unique river basin IDs and their frequency within the city-masked area(unique_values_A)
#---------------------------------------------------------------------------------------------------------------

    unique_values_A, counts_A = np.unique(Rivnum_A_array_citymasked.compressed(), return_counts=True)
    value_counts_dict_A = dict(zip(unique_values_A, counts_A))

#---------------------------------------------------------------------------------------------------------------
#   Identify river mouth grid cells using rivara (rivara_max_array_A)
#---------------------------------------------------------------------------------------------------------------

    # Create a new masked array with the same shape and dtype as g_ara_num_cropped
    rivara_max_array_A = np.ma.masked_all(g_ara_num_cropped.shape, dtype='float32')

    for rivnum_id in value_counts_dict_A.keys():
        # Find positions corresponding to the same river basin ID
        matching_positions = np.where(Rivnum_A_array_citymasked == rivnum_id)
        
        # Get the index of the maximum rivara value within these positions
        max_rivara_position = np.argmax(g_rivara_cropped[matching_positions])
        
        # Assign the basin ID to the location of the maximum rivara value
        # This location is considered the river mouth grid
        rivara_max_array_A[matching_positions[0][max_rivara_position], matching_positions[1][max_rivara_position]] = rivnum_id

#---------------------------------------------------------------------------------------------------------------
#   riv nxtl -> lonlat coordinate array 24x24x2 (riv_nxlonlat_cropped)
#---------------------------------------------------------------------------------------------------------------

    # l coordiate to lonlat coordinate
    vfunc = np.vectorize(l_coordinate_to_tuple, otypes=[tuple])
    riv_nxlonlat = np.empty(g_rivnxl_cropped.shape, dtype=tuple)
    mask = ~np.isnan(g_rivnxl_cropped)
    riv_nxlonlat[mask] = vfunc(g_rivnxl_cropped[mask])
    riv_nxlonlat_shape = (riv_nxlonlat.shape[0], riv_nxlonlat.shape[1], 2)

    riv_nxlonlat_lst = []
    for row in riv_nxlonlat:
        for x, y in row:
            # width_grid = cropped scale(24x24)
            modified_x = width_grid - (x - lat_start)
            modified_y = y - lon_start
            riv_nxlonlat_lst.append((modified_x, modified_y))

    riv_nxlonlat_cropped = np.array(riv_nxlonlat_lst).reshape(riv_nxlonlat_shape)
    riv_nxlonlat_cropped = riv_nxlonlat_cropped.astype(int)

#---------------------------------------------------------------------------------------------------------------
#   Trace flow paths for each basin (path_dict)
#   Each path is recorded by basin ID and stored in a single file (riv_path_array_A)
#---------------------------------------------------------------------------------------------------------------

    # Initialize storage variables
    path_dict = {}
    riv_path_array_A = np.ma.masked_all(rivara_max_array_A.shape, dtype='float32')
    visited_coords = set()

    # Loop through each unique river basin ID
    for uid in unique_values_A:
        # Find the river mouth grid (maximum rivara) for this basin
        coords_a = np.argwhere(rivara_max_array_A == uid)
        riv_path_array_A[coords_a[0][0], coords_a[0][1]] = uid
        if coords_a.size > 0:
            target_coord = tuple(coords_a[0]) 
            path_coords = [target_coord]
            for _ in range(len(g_mask_cropped)):
                if target_coord in visited_coords:
                    break
                visited_coords.add(target_coord)

                # Convert rivnxl L-coordinates to 2D lat-lon indices and match to the target
                matched_coords = np.argwhere(np.all(target_coord == riv_nxlonlat_cropped, axis=2))
                if len(matched_coords) == 0:
                    break

                # Filter out already visited cells
                unvisited_matched = [tuple(coord) for coord in matched_coords if tuple(coord) not in visited_coords]
                if not unvisited_matched:
                    break

                # Among candidate next cells, choose the one with the highest rivara (most upstream)
                rivara_values = [g_rivara_cropped[coord[0], coord[1]] for coord in unvisited_matched]
                max_index = np.argmax(rivara_values)
                best_coord = unvisited_matched[max_index]

                # Mark the selected cell in the river path array
                riv_path_array_A[best_coord[0], best_coord[1]] = uid
                target_coord = best_coord
                path_coords.append(target_coord)

            # Save the full traced path for this basin ID
            path_dict[uid] = path_coords

#---------------------------------------------------------------------------------------------------------------
#   Filter rivpath inside city mask using innercity_grid threshold (riv_path_city_B)
#---------------------------------------------------------------------------------------------------------------

    # Define a placeholder value for masked cells
    fill_value = 1e20

    # Fill masked values and extract only paths within the city mask
    riv_path_array_filled = riv_path_array_A.filled(fill_value)
    riv_path_city_A = np.where(g_mask_cropped == city_num, riv_path_array_filled, fill_value)

    # Copy for further filtering
    riv_path_city_B = copy.deepcopy(riv_path_city_A)

    for uid in unique_values_A:
        # Count how many river path cells exist for this basin within the city mask
        mask = (riv_path_city_A == uid)
        count = np.sum(mask)

        # If the number of cells is below threshold, remove the path
        if count < innercity_grid:
            riv_path_city_B[riv_path_city_B == uid] = fill_value

    # Mask out placeholder values
    riv_path_city_B = np.ma.masked_where(riv_path_city_B >= fill_value, riv_path_city_B)

#---------------------------------------------------------------------------------------------------------------
#   Update list of valid basin IDs after two-stage filtering (unique_values_B)
#---------------------------------------------------------------------------------------------------------------

    # Use .compressed() to avoid including masked values in the unique count
    unique_values_B, _ = np.unique(riv_path_city_B.compressed(), return_counts=True)

#---------------------------------------------------------------------------------------------------------------
#   Extract full river basin regions corresponding to valid IDs (Rivnum_B_array)
#---------------------------------------------------------------------------------------------------------------

    # Initialize a new masked array
    Rivnum_B_array = np.ma.masked_all(g_rivnum_cropped_masked.shape, dtype='float32')

    # Populate it only with grid cells from basins that survived both filtering stages
    for uid in unique_values_B:
        row_indices, col_indices = np.where(Rivnum_A_array == uid)
        Rivnum_B_array[row_indices, col_indices] = uid

#---------------------------------------------------------------------------------------------------------------
#   Identify updated river mouth grids based on remaining basins (rivara_max_array_B)
#---------------------------------------------------------------------------------------------------------------

    # Create a new array to store river mouth locations (maximum rivara per basin)
    rivara_max_array_B = np.ma.masked_all(g_ara_num_cropped.shape, dtype='float32')

    for rivnum_id in unique_values_B:
        # Get all grid cells belonging to the same basin within the city mask
        matching_positions = np.where(Rivnum_A_array_citymasked == rivnum_id)

        # Find the position with the maximum rivara value (i.e., river mouth)
        max_rivara_position = np.argmax(g_rivara_cropped[matching_positions])

        # Store this location as the river mouth for the current basin
        rivara_max_array_B[matching_positions[0][max_rivara_position], matching_positions[1][max_rivara_position]] = rivnum_id

#---------------------------------------------------------------------------------------------------------------
#   Update riv_path_array with full length out of city mask (riv_path_array_B)
#---------------------------------------------------------------------------------------------------------------

    # Initialize variables for storing path data
    path_dict = {}
    riv_path_array_B = np.ma.masked_all(rivara_max_array_B.shape, dtype='float32')
    visited_coords = set()

    # Iterate over each valid river basin ID
    for uid in unique_values_B:
        # Get the grid index of the river mouth for this basin
        coords_a = np.argwhere(rivara_max_array_B == uid)
        riv_path_array_B[coords_a[0][0], coords_a[0][1]] = uid

        if coords_a.size > 0:
            target_coord = tuple(coords_a[0])
            path_coords = [target_coord]

            for _ in range(len(g_mask_cropped)):
                if target_coord in visited_coords:
                    break
                visited_coords.add(target_coord)

                # Convert rivnxl index to (lat, lon) coordinate and find the next cell
                matched_coords = np.argwhere(np.all(target_coord == riv_nxlonlat_cropped, axis=2))
                if len(matched_coords) == 0:
                    break

                # Skip already visited coordinates and find candidates
                unvisited_matched = [tuple(coord) for coord in matched_coords if tuple(coord) not in visited_coords]
                if not unvisited_matched:
                    break

                # From the candidate next cells, choose the one with the highest upstream area (rivara)
                rivara_values = [g_rivara_cropped[coord[0], coord[1]] for coord in unvisited_matched]
                max_index = np.argmax(rivara_values)
                best_coord = unvisited_matched[max_index]

                # Mark the path grid for this basin
                riv_path_array_B[best_coord[0], best_coord[1]] = uid
                target_coord = best_coord
                path_coords.append(target_coord)

            # Save the full path for the basin
            path_dict[uid] = path_coords

#---------------------------------------------------------------------------------------------------------------
#   Explore josui grids (josui_lst)
#---------------------------------------------------------------------------------------------------------------

    # determine josui place
    josui_lst = []

    # loop uid
    for key_num in unique_values_B:
        # get river path
        indices = np.argwhere(riv_path_city_B == key_num)
        # get minmum river area
        rivara_values = [g_rivara_cropped[coord[0], coord[1]] for coord in indices]
        min_arg = np.argmin(rivara_values)
        josui = indices[min_arg]
        # add to list
        josui_lst.append(josui)

#---------------------------------------------------------------------------------------------------------------
#   Josui map 24 x 24 (josui_array)
#---------------------------------------------------------------------------------------------------------------

    # Create a 24x24 masked array to store water intake (purification plant) information
    josui_array = np.ma.masked_all(rivara_max_array_B.shape, dtype='float32')

    # Assign each intake grid (from josui_lst) with the corresponding river basin ID
    for matching_position, uid in zip(josui_lst, unique_values_B):
        josui_array[matching_position[0], matching_position[1]] = uid


#---------------------------------------------------------------------------------------------------------------
#   Gesui map 24 x 24 (josui_array)
#---------------------------------------------------------------------------------------------------------------

    gesui_array = copy.deepcopy(rivara_max_array_B)

#---------------------------------------------------------------------------------------------------------------
#   Check whehter no prf
#---------------------------------------------------------------------------------------------------------------

    # Flag to determine whether to search for an alternative basin when remote aqueduct is needed
    no_prf_flag = False

    # Check whether any purification (intake) points exist in josui_array
    josui_array = np.ma.filled(josui_array, fill_value=0)
    prf_coords = np.where(josui_array > 0)

    if len(prf_coords[0]) == 0:
        print(f"no purification")

        # Enable fallback search for same-basin intake (used in explore_prf)
        no_prf_flag = True

        josui_array, gesui_array = explore_prf(g_mask_cropped, 
                                               city_num,
                                               g_rivnum_cropped_city, 
                                               g_elv_cropped, 
                                               g_rivara_cropped,
                                               g_rivout_cropped,
                                               )

        # Check the flow direction relationship between intake (prf) and outlet (swg)
        swg_coord = np.where(gesui_array == 1)
        print(f'swg_coord: {swg_coord}')
        updown = np.fromfile(updown_path, dtype='float32').reshape(2160, 4320)
        g_updwon = np.flipud(updown)
        g_updown_cropped = g_updwon[lat_start:lat_end, lon_start:lon_end]
        g_updown_cropped = np.flipud(g_updown_cropped)

        # If the outlet is located upstream of the intake, treat both as the same point
        if g_updown_cropped[swg_coord] != 0:
            gesui_array = josui_array
            print(f"swg = prf due to updown relationship")

#---------------------------------------------------------------------------------------------------------------
#   Check whehter no prf
#---------------------------------------------------------------------------------------------------------------

    # text save
    if save_flag is True:
        if target_index == 1:
            with open(nonprf_path, 'w') as file:
                file.write(f"{target_index}|{no_prf_flag}\n")
        else:
            with open(nonprf_path, 'a') as file:
                file.write(f"{target_index}|{no_prf_flag}\n")
    else:
        print('nonprf save_flag is false')

#---------------------------------------------------------------------------------------------------------------
#   Save file (josui_array)
#---------------------------------------------------------------------------------------------------------------

    """
    Always flip the cropped array vertically during processing,
    then flip it back when saving or visualizing to match global map orientation.
    """

    # Initialize an empty array for saving the intake grid (same shape as global rivara)
    josui_for_save = np.ma.masked_all(g_rivara.shape, dtype='float32')

    # Assign the flipped cropped intake array to the correct region in the global array
    # (Global maps are typically stored upside-down)
    josui_for_save[lat_start:lat_end, lon_start:lon_end] = np.flipud(josui_array)

    # Convert to binary format: assign city ID where intake exists, 0 elsewhere
    josui_for_save = np.ma.filled(josui_for_save, fill_value=0)
    josui_for_save = np.where(josui_for_save > 0, city_num, josui_for_save)

    # Flip back before saving to match the correct global orientation
    josui_for_save = np.flipud(josui_for_save)

#---------------------------------------------------------------------------------------------------------------
#   Save file (gesui_array=rivara_max_array_B)
#---------------------------------------------------------------------------------------------------------------

    """
    Always flip vertically when cropping,
    and flip back to the correct orientation when saving or visualizing.
    """

    # Create an empty array for saving the drainage (outlet) grid, with the same shape as global data
    gesui_for_save = np.ma.masked_all(g_rivara.shape, dtype='float32')

    # Insert the flipped cropped drainage array into the correct location of the global array
    # (Global maps are typically stored upside down)
    gesui_for_save[lat_start:lat_end, lon_start:lon_end] = np.flipud(gesui_array)

    # Convert to binary format: assign city ID where outlet exists, 0 elsewhere
    gesui_for_save = np.ma.filled(gesui_for_save, fill_value=0)
    gesui_for_save = np.where(gesui_for_save > 0, city_num, gesui_for_save)

    # Flip again before saving to restore proper global orientation
    gesui_for_save = np.flipud(gesui_for_save)

    return josui_for_save, gesui_for_save

#---------------------------------------------------------------------------------------------------------------
# MODULES
#---------------------------------------------------------------------------------------------------------------

def l_coordinate_to_tuple(lcoordinate, a=2160, b=4320):
    lat_l = a - ((lcoordinate - 1) // b)
    lon_l = (lcoordinate) % b - 1
    return (lat_l, lon_l)


def explore_prf(citymask, city_num, rivnum, elevation, rivara, rivout):
    """
    citymask:  g_mask_cropped,             city_mask
    rivnum:    g_rivnum_cropped_city,      city_mask内のrivnumデータ
    elevation: g_elv_cropped,              elevationデータ
    rivara:    g_rivara_cropped,           rivaraデータ
    rivout:    g_rivout_cropped,           rivoutデータ
    """
    mask_indices = np.argwhere(citymask != 0)
    dis_values = [rivout[coord[0], coord[1]] for coord in mask_indices]
    dis_maxarg = np.argmax(dis_values)
    josui_coord = mask_indices[dis_maxarg]
    josui_array = np.zeros(rivnum.shape, dtype='float32')
    josui_array[josui_coord[0], josui_coord[1]] = 1

    elv_indices = np.argwhere((citymask != 0) & (josui_array != 1))
    elv_values = [elevation[coord[0], coord[1]] for coord in elv_indices]
    elv_minarg = np.argmin(elv_values)
    gesui_coord = elv_indices[elv_minarg]
    gesui_array = np.zeros(rivnum.shape, dtype='float32')
    gesui_array[gesui_coord[0], gesui_coord[1]] = 1

    return josui_array, gesui_array

#---------------------------------------------------------------------------------------------------------------
# Main loop
#---------------------------------------------------------------------------------------------------------------

def main():

#---------------------------------------------------------------------------------------------------------------
#   Initialization
#---------------------------------------------------------------------------------------------------------------

    save_flag = True
    remove_grid = 5 # minimum number of grids in one basin
    innercity_grid = 2 # minimum number of main river grid within city mask
    width = 2 # lonlat delta degree from city center

#---------------------------------------------------------------------------------------------------------------
#   save file
#---------------------------------------------------------------------------------------------------------------
    canvas_prf = np.zeros((2160, 4320))
    canvas_swg = np.zeros((2160, 4320))

#---------------------------------------------------------------------------------------------------------------
#   loop start
#---------------------------------------------------------------------------------------------------------------

    # number of the city (1-1860)
    for target_index in range(1, 1861):
        josui_for_save, gesui_for_save = explore(target_index, remove_grid, innercity_grid, width, save_flag=save_flag)

        non_zero_prf = np.where(josui_for_save != 0)
        non_zero_swg = np.where(gesui_for_save != 0)
        canvas_prf[non_zero_prf] = target_index
        canvas_swg[non_zero_swg] = target_index

#---------------------------------------------------------------------------------------------------------------
#   save file
#---------------------------------------------------------------------------------------------------------------

    workdir         = "/your/directory/path"
    prf_save_dir     = f"{root_dir}/cty_prf_"
    swg_save_dir     = f"{root_dir}/cty_swg_"

    prf_save_path = f'{prf_save_dir}/inlet_clrd0000.gl5'
    swg_save_path = f'{swg_save_dir}/outlet_clrd0000.gl5'

    if save_flag is True:
        canvas_prf.astype(np.float32).tofile(prf_save_path)
        canvas_swg.astype(np.float32).tofile(swg_save_path)
        print(f"{prf_save_path}, {swg_save_path} saved")
    else:
        print('save_flag is false')

if __name__ == '__main__':
    main()
