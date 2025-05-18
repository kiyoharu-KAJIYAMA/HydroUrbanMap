import os
import math
import pickle
import numpy as np
#import matplotlib.pyplot as plt

def explore_citymask(index, err_count):

    #-----------------------------------------------
    # Initialization
    #-----------------------------------------------

    # pop data
    POP='gpw4'

    # map data
    MAP='CAMA'

    # h08 directory
    workdir = '/your/directory/path'
    wup_path = f'{workdir}/WUP2018_300k_2010.txt'
    area_path = f'{workdir}/grdara.gl5'
    pop_path = f'{workdir}/GPW4ag__20100000.gl5'
    center_path = f'{workdir}/cty_cnt_/{POP}/city_{index:08d}.gl5'
    modified_center_path = f'{workdir}/cty_cnt_/{POP}/modified/city_{index:08d}.gl5'
    new_center_path = f'{workdir}/cty_cnt_/{POP}/modified/city_{index:08d}.gl5'
    dict_path = f'{workdir}/clusterd/city_{index:08d}.pickle'

    #-----------------------------------------------
    # Input Constants
    #-----------------------------------------------

    # city center modification
    modify_flag = True

    # search radius (1grid in 0.5degree)
    circle = 1

    # EN.1: lower limitation of population density
    lowlim = 100

    # EN.2: initial grid threshold
    threshold = 300

    # EN.3: downtown rate
    downtown_rate = 10

    # EN.3: grid sum
    grdlim = 3

    # EN.4: low ratio
    lowrat = 0.0

    # shape
    lat_shape = 2160
    lon_shape = 4320

    # date type
    dtype= 'float32'

    #-----------------------------------------------
    # Initialization
    #-----------------------------------------------

    # initialize variables
    best_coverage = float('inf')
    best_mask = None
    best_masked_pop = None

    #-----------------------------------------------
    # load true data (UN city list) unit=[1000person]
    #-----------------------------------------------

    # true population and city name
    un_pop_list = []
    name_list = []

    # load data
    for l in open(wup_path).readlines():
        data = l[:].split('\t')
        data = [item.strip() for item in data]
        un_pop_list.append(float(data[3]))
        name_list.append(data[4])

    # get true UN city population
    un_pop = un_pop_list[index-1]*1000

    # get city name
    city_name = name_list[index-1]

    #-----------------------------------------------
    #  Get area(m2)
    #-----------------------------------------------

    area = np.fromfile(area_path, dtype=dtype).reshape(lat_shape, lon_shape)

    #-----------------------------------------------
    # load gwp population data
    #-----------------------------------------------

    # population data(GWP4 2010)
    gwp_pop = np.fromfile(pop_path, dtype=dtype).reshape(lat_shape, lon_shape)

    # population density (person/km2)
    gwp_pop_density = (gwp_pop / (area / 10**6))

    #-----------------------------------------------
    # load city_center coordinate
    #-----------------------------------------------

    if modify_flag is True:
        location = np.fromfile(center_path, dtype=dtype).reshape(lat_shape,lon_shape)
    else:
        location = np.fromfile(modified_center_path, dtype=dtype).reshape(lat_shape,lon_shape)
    org_y = np.where(location==1)[0]
    org_x = np.where(location==1)[1]
    org_y = org_y[0]
    org_x = org_x[0]

    #-----------------------------------------------
    # check city center
    #-----------------------------------------------

    # original city center
    # Don't use gwp_pop. there is bug due to ocean land ara data
    org_cnt = gwp_pop_density[org_y, org_x]

    if modify_flag is True:
        # number of replacement
        replaced_num = 0
        print(f"cityindex {index}")
        print(f'original center [y, x] = [{org_y, org_x}]')
        print(f"org_cnt: {org_cnt}")

        # if there is larger grid, center grid is replaced
        for a_cnt in range(org_y-circle, org_y+circle+1):
            for b_cnt in range(org_x-circle, org_x+circle+1):
                # Don't use gwp_pop. there is bug due to ocean land ara data
                candidate = gwp_pop_density[a_cnt, b_cnt]
                if candidate >= org_cnt:
                    org_cnt = candidate
                    rpl_y = a_cnt
                    rpl_x = b_cnt
                    replaced_num += 1
        print(f'replaced center [y, x] = [{rpl_y, rpl_x}]')
        print(f"rpl_cnt: {gwp_pop_density[rpl_y, rpl_x]}")

    #-----------------------------------------------
    #  Initialization of mask array
    #-----------------------------------------------

    # mask array for saving
    mask = np.zeros((lat_shape,lon_shape), dtype=dtype)
    mask[rpl_y, rpl_x] = 1

    #-----------------------------------------------
    # overwrite city center file if changed
    #-----------------------------------------------

    if modify_flag is True:
        mask.astype(np.float32).tofile(new_center_path)

    #-----------------------------------------------
    #  Trace variable
    #-----------------------------------------------

    save_dict = {'mask': None,
                 'un_population': None,
                 'population_density': None,
                 'masked_population': [],
                 'added_density': [],
                 'next_density': [],
                 'cover_rate': [],
                 'next_coords': []
                 }

    #-----------------------------------------------
    #  Initialize loop
    #-----------------------------------------------

    # stop flag
    new_mask_added = True
    coverage_flag = True

    # city center
    best_mask = mask
    grid_num = np.sum(best_mask)
    best_masked_pop = np.sum(gwp_pop*mask)
    best_coverage = float(best_masked_pop / un_pop)

    # momnitor density ratio
    init_density = np.sum(gwp_pop_density[rpl_y, rpl_x])
    previous_density = np.sum(gwp_pop_density[rpl_y, rpl_x])

    # initial grid threshold
    err_flag = 0
    if gwp_pop_density[rpl_y, rpl_x] <= threshold:
        print("/// 111 ///")
        print(f"initial density {gwp_pop_density[rpl_y, rpl_x]} less than threshold {threshold}")
        print("/// 111 ///")
        new_mask_added = False
        coverage_flag = False
        density_ratio = (previous_density/init_density)*100
        err_flag = 1

    #-----------------------------------------------
    #  Explore start
    #-----------------------------------------------

    # loop start
    while new_mask_added:

        ### make search list
        search_lst = []
        new_mask_added = False
        indices = np.where(mask == 1)

        for ind in range(len(indices[0])):
            y_index = indices[0][ind]
            x_index = indices[1][ind]
            # rook neighbors
            for dx, dy in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                i = y_index + dy
                j = x_index + dx
                # not explored yet
                if mask[i, j] == 0:
                    # within grid range
                    if 0 <= i < lat_shape and 0<= j < lon_shape:
                        # Don't use gwp_pop. there is bug due to ocean land ara data
                        search_lst.append([gwp_pop_density[i, j], i, j])

        ### obtain largest searched grid
        # empty check
        if not search_lst:

            new_mask_added = False
            coverage_flag = False
            print('search_lst is empty')

        # get largest grid
        else:

            # largest density
            sorted_search = sorted(search_lst, key=lambda x: x[0], reverse=True)
            largest = sorted_search[0]

            # next density
            next_density = gwp_pop_density[largest[1], largest[2]]
            density_ratio = (next_density/init_density)*100

            # if largest grid in searched grid is too small, stop exploring
            if next_density <= lowlim:
                print("/// 222 ///")
                print(f"next density {next_density} smaller than lowlim {lowlim}")
                print("/// 222 ///")
                new_mask_added = False
                coverage_flag = False
                err_flag = 2

            elif next_density > previous_density and best_coverage > downtown_rate and grid_num >= grdlim:
                print("/// 333 ///")
                print(f"next density {next_density} bigger than previous density {previous_density}")
                print("/// 333 ///")
                new_mask_added = False
                coverage_flag = False
                err_flag = 3

            elif density_ratio < lowrat:
                print("/// 444 ///")
                print(f"next density {next_density} less than one-tenth of initial density {init_density}")
                print("/// 444 ///")
                new_mask_added = False
                coverage_flag = False
                err_flag = 4


        ### add new mask
        # stop flag
        if coverage_flag is True:

                # while loop continues
                new_mask_added = True

                # evaluate coverage
                gwp_masked_pop = np.sum(mask * gwp_pop)
                coverage = float(gwp_masked_pop / un_pop)

                # stop exploring
                if coverage >= 1.0:
                    new_mask_added = False
                    coverage_flag = False

                # judge
                judge_value = abs(1 - coverage)
                best_value = abs(1 - best_coverage)

                # update trace variables
                save_dict['masked_population'].append(gwp_masked_pop)
                save_dict['added_density'].append(previous_density)
                save_dict['next_density'].append(next_density)
                save_dict['cover_rate'].append(coverage)
                save_dict['next_coords'].append(largest)
                if np.sum(mask) == 1:
                    save_dict['mask'] = mask
                else:
                    save_dict['mask'] = np.dstack((save_dict['mask'], mask))

                # update
                if judge_value < best_value or np.sum(mask) == 1:
                    best_coverage = coverage
                    best_mask = mask
                    best_masked_pop = gwp_masked_pop
                    grid_num = np.sum(best_mask)
                    previous_density = gwp_pop_density[largest[1], largest[2]]

        # new mask added
        mask[largest[1], largest[2]] = 1

    #-----------------------------------------------
    # Output result
    #-----------------------------------------------

    print(
          f"explored_pop {best_masked_pop}\n" \
          f"true_pop {un_pop}\n" \
          f"coverage {best_coverage}\n" \
          f"city_mask {grid_num}\n" \
          f"density_ratio {density_ratio}\n" \
          f"{city_name}\n"
          )
    print('#########################################\n')

    #------------------------------------------------
    # SAVE FILE
    #------------------------------------------------

    # update error
    err_count[f'{err_flag}'] += 1
    print(err_count)


    """
    # result path save
    resultpath = f'{workdir}/result_downtown.txt'

    if index == 1:
        with open(resultpath, 'w') as file:
            file.write(f"{index}| {city_name}| {best_masked_pop}| {un_pop}| {best_coverage}| {grid_num}| {err_flag}\n")
    else:
        with open(resultpath, 'a') as file:
            file.write(f"{index}| {city_name}| {best_masked_pop}| {un_pop}| {best_coverage}| {grid_num}| {err_flag}\n")

    # binary file saved (latest version)
    maskpath_bin = f'{workdir}/cty_msk_/city_{index:08}.gl5'
    best_mask.astype(np.float32).tofile(maskpath_bin)

    # dict save
    with open(dict_path, 'wb') as handle:
        pickle.dump(save_dict, handle)
    """


    return err_count


def summarize():

    # colored
    color_flag = True

    # pop data
    POP = 'gpw4'

    # paths
    workdir = '/your/directory/path'
    wup_path = f'{workdir}/WUP2018_300k_2010.txt'
    color_path = f"{workdir}/cty_msk_/city_clrd0000.gl5"
    monochrome_path = f"{workdir}cty_msk_/city_00000000.gl5"
    ovlp_color_path = f"{workdir}/cty_msk_/city_clrdovlp.gl5"
    ovlp_monochrome_path = f"{workdir}/cty_msk_/city_0000ovlp.gl5"
    textpath = h08dir + f'{workdir}/citymask_overlap.txt'

    # city_name
    name_list =  []
    pop_list = []
    for l in open(wup_path).readlines():
        data = l[:].split('\t')
        data = [item.strip() for item in data]
        pop_list.append(float(data[3]))
        name_list.append(data[4])

    # overlap text
    with open(textpath, 'w') as file:
        file.write(f"index | pop | grid_num | name|\n")

    # shape
    lat_shape = 2160
    lon_shape = 4320

    # date type
    dtype= 'float32'

    # make save array
    summary = np.empty((lat_shape, lon_shape)) # exclude overlap citymask
    overlap = np.empty((lat_shape, lon_shape)) # only overlap citymask

    # city index loop
    for index in range(1, 1861):
        city_name = name_list[index-1]
        city_pop = pop_list[index-1]

        # load city mask
        mask_path = f"{workdir}/cty_msk_/city_{index:08}.gl5"

        # mask existance
        if not os.path.exists(mask_path):
            print(f'{index} is invalid mask')
            save_path = None
            ovlp_save_path = None
        else:
            tmp = np.fromfile(mask_path, dtype=dtype).reshape(lat_shape, lon_shape)
            # overlap check
            if np.sum(summary[tmp==1]) < 1:
                # color or monotchrome
                if color_flag is True:
                    summary[tmp == 1] = index
                    save_path = color_path
                else:
                    summary[tmp == 1] = 1
                    save_path = monochrome_path
                print(f'{index} is valid mask')
            else:
                if color_flag is True:
                    overlap[tmp == 1] = index
                    ovlp_save_path = ovlp_color_path
                    save_path = ovlp_color_path
                else:
                    overlap[tmp == 1] = 1
                    ovlp_save_path = ovlp_monochrome_path

                with open(textpath, 'a') as file:
                    file.write(f"{index}| {city_pop}| {np.sum(tmp)}| {city_name}\n")

                print(f'{index} is overlaped')

    summary.astype(np.float32).tofile(save_path)
    overlap.astype(np.float32).tofile(ovlp_save_path)
    print(f'{save_path} is saved')

    return summary

def main(round_flag):

    if round_flag == 'First':
        ########################################################
        # err_flag = 1  #initial grid threshold
        # if gwp_pop_density[rpl_y, rpl_x] <= threshold(100)-> cluster(300):
        # err_flag = 2  # if largest grid in searched grid is too small, stop exploring
        # if next_density <= lowlim(100):
        ########################################################
        # err_flag = 3  # not activated
        # elif next_density > previous_density and best_coverage > downtown_rate and grid_num >= grdlim:
        # err_flag = 4  # not activated
        # elif density_ratio < lowrat:
        ########################################################

        err_count = {'0': 0, '1': 0, '2': 0, '3':0, '4':0}
        # python make_downtown.py > make_downtown.log
        for index in range(1, 1861):
            err_count = explore_citymask(index, err_count)

    elif round_flag == 'Second':
        summary = summarize()

        #plt.imshow(summary, cmap='rainbow')
        #plt.show()

    else:
        print(f"round flag is wrong {round_flag}")


if __name__ == '__main__':
    round_flag = 'First'
    main(round_flag)
