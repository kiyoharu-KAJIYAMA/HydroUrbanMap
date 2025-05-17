import os
import numpy as np

### to be changed ###
workdir = '/your/directory/path'
cmct_name = f'{workdir}/table_first.txt'

vlddir = f'{workdir}/vld_cty_'
moddir = f'{workdir}/dwn_msk_'
lowdir = f'{workdir}/low_msk_'
savetext_path = f'{workdir}/removed_overlap.txt'
canvas_path = f'{workdir}/cty_msk_/city_clrd0000.gl5'

canvas = np.zeros((2160, 4320))

for cty_ind in range(1, 1861):
    
    vld_path = f'{vlddir}/city_{cty_ind:08}.gl5'
    dwn_path = f'{moddir}/city_kj_{cty_ind:08}.gl5'
    if not os.path.exists(vld_path):
        
        low_path = f'{lowdir}/city_kj_{cty_ind:08}.gl5'
        if not os.path.exists(low_path):
            print(f"{cty_ind} is NoMASK")
            continue
        else:
            msk_path =  low_path
            
    elif os.path.exists(dwn_path):
        msk_path = dwn_path

    else:
        msk_path = vld_path

    ###################################################################
    # JOB
    ###################################################################
    # get mask value
    mask = np.fromfile(msk_path, dtype='float32').reshape(2160, 4320)
        
    # get mask index of non zero (tuple)
    non_zero_coords = np.where(mask != 0)
    
    # get value at mask
    settled_values = canvas[non_zero_coords]
    
    # is unique?
    unq = np.unique(settled_values)
    unq_non_zero = unq[unq > 0]

    # overlap judge
    if np.sum(settled_values) > 0:
        # remove overlap
        for j in range(len(mask)):
            for k in range(len(mask[0])):
                if mask[j,k] != 0:
                    if canvas[j,k] != 0:
                        mask[j,k] = 0
        non_zero_update = np.where(mask != 0)
        grid_num = np.sum(mask)

        # update canvas
        canvas[non_zero_update] = cty_ind

        # save text
        if not os.path.exists(savetext_path):
            with open(savetext_path, 'w') as file:
                file.write(f"{cty_ind}|{unq_non_zero}|{grid_num}\n")
        else:
            with open(savetext_path, 'a') as file:
                file.write(f"{cty_ind}|{unq_non_zero}|{grid_num}\n")

        # remove or modify
        if grid_num == 0:
            print(f'{cty_ind} is removed')
        else:
            print(f'{cty_ind} is modified')

        # save mask
        save_path = f'{root_dir}/camacity/dat/ovlpmsk_/city_kj_{cty_ind:08}.gl5'
        #mask.astype(np.float32).tofile(save_path)
        print(f"{save_path} saved")
        
    else:
        # update canvas
        canvas[non_zero_coords] = cty_ind
