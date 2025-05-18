import os
import math
import numpy as np

def l_coordinate_to_tuple(lcoordinate, a=2160, b=4320):
    lat_l = ((lcoordinate - 1) // b)
    lon_l = (lcoordinate) % b - 1
    return (lat_l, lon_l)

def nxtl2nxtxy(rgnfile, upperindex, leftindex):
    vfunc = np.vectorize(l_coordinate_to_tuple, otypes=[tuple])
    riv_nxtxy = np.empty(rgnfile.shape, dtype=tuple)
    mask = ~np.isnan(rgnfile)
    riv_nxtxy[mask] = vfunc(rgnfile[mask])
    riv_nxtxy_shape = (riv_nxtxy.shape[0], riv_nxtxy.shape[1], 2)
    
    riv_nxtxy_lst = []
    for row in riv_nxtxy:
        for y, x in row:
            modified_y = y - upperindex
            modified_x = x - leftindex
            riv_nxtxy_lst.append((modified_y, modified_x))

    riv_nxtxy_cropped = np.array(riv_nxtxy_lst).reshape(riv_nxtxy_shape)
    riv_nxtxy_cropped = riv_nxtxy_cropped.astype(int)
    return riv_nxtxy_cropped

def exeption_rivergrid(city_num, riv_nxlonlat_cropped):
    # coord of purficication
    workdir = '/your/directory/path'
    prf_path = f"{workdir}/cty_prf_/vld_cty_/city_{city_num:08}.gl5"
        
    prf = np.fromfile(prf_path, dtype='float32').reshape(2160, 4320)
    prf_coords = np.where(prf == 1)
    print(f'citynum: {city_num}, coord of prfs: {prf_coords}')
    
    # save variable
    riv_path_array = np.zeros((2160, 4320))
    
    # initial grid
    for pid in range(len(prf_coords[0])):
        print(f'pid == {pid}, len(prf_coords) == {len(prf_coords[0])}')
        
        # down stream exploration
        target_coord = (prf_coords[0][pid], prf_coords[1][pid])
        visited_coords = set()
        while True:
            if target_coord in visited_coords:
                break
            visited_coords.add(target_coord)
            target_row, target_col = target_coord
            next_coord = riv_nxlonlat_cropped[target_row, target_col]
            if next_coord.size == 0 or next_coord.shape != (2,):
                break
            target_coord = (next_coord[0], next_coord[1])

        # update riv_path_array
        for row, col in visited_coords:
            riv_path_array[row, col] = city_num
    
        # up stream exploration
        def explore_upstream(target_coord, visited_coords, riv_nxlonlat_cropped, city_num):
            while True:
                if target_coord in visited_coords:
                    break
                visited_coords.add(target_coord)
                matched_coords = np.argwhere(np.all(target_coord == riv_nxlonlat_cropped, axis=2))
                if len(matched_coords) == 0:
                    break
                unvisited_matched = [tuple(coord) for coord in matched_coords if tuple(coord) not in visited_coords]
                for up_coord in unvisited_matched:
                    print(f'len(visited_coords): {len(visited_coords)}, len(unvisited_matched): {len(unvisited_matched)}')
                    explore_upstream(up_coord, visited_coords, riv_nxlonlat_cropped, city_num)

        # execute function
        target_coord = (prf_coords[0][pid], prf_coords[1][pid])
        visited_coords = set()
        explore_upstream(target_coord, visited_coords, riv_nxlonlat_cropped, city_num)
        
        # update riv_path_array
        for row, col in visited_coords:
            riv_path_array[row, col] = city_num
    
    return riv_path_array
  
# rivnxl in xy coord
workdir = '/your/directory/path'
rivnxl_path = f"{workdir}/rivnxl.CAMA.gl5"
rivnxl_gl5 = np.fromfile(rivnxl_path, 'float32').reshape(2160, 4320)
riv_nxlonlat_cropped = nxtl2nxtxy(rivnxl_gl5, 0, 0)

# this loop will take hours
for city_num in range(1, 1861):
    savepath = f"{workdir}/prf_updw/city_{city_num:08}.gl5"
    prf_path = f"{workdir}cty_prf_/city_{city_num:08}.gl5"
    if not os.path.exists(prf_path):
        print(f'{city_num} is invalid prf')
        continue 
    
    riv_path_array =  exeption_rivergrid(city_num, riv_nxlonlat_cropped)
    
    riv_path_array.astype(np.float32).tofile(savepath)
    print(f"{savepath} saved")
