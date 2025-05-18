import os
import numpy as np

camadir = '/your/directory/path'
city_path = f"{workdir}/table_first.txt"
savedir = f"{workdir}/100km_elevation"
layers = [np.zeros((2160, 4320), dtype=np.float32)]
overlaplist = []

with open(city_path, "r") as input_file:
    lines = input_file.readlines()
    
for i in range(1860):
    line = lines[i]
    parts = line.split('|')
    parts = [item.strip() for item in parts]
    ovlp_state = parts[1]
    clst_state = parts[2]
    if clst_state == 'NoMK' or ovlp_state == 'RMVD':
        continue
        
    city_num = i+1
    loadpath = f"{savedir}/city_{city_num:08}.gl5"
    try:
        aqd = np.fromfile(loadpath, dtype='float32').reshape(2160, 4320)
    except FileNotFoundError:
        print(f"city file not found: {loadpath}")
        continue
        
    non_zero_coords = np.where(aqd != 0)
    assigned = False

    for layer in layers:
        settled_values = layer[non_zero_coords]
        if not np.any(settled_values > 0):
            layer[non_zero_coords] = city_num
            assigned = True
            break

    if not assigned:
        new_layer = np.zeros((2160, 4320), dtype=np.float32)
        new_layer[non_zero_coords] = city_num
        layers.append(new_layer)
        overlaplist.append(city_num)

#---------------------------------------------------------------------------
# save different layers
#---------------------------------------------------------------------------
for idx, layer in enumerate(layers, start=1):
    savepath = f"{workdir}/aqd_layer{idx:03}.gl5"
    layer.tofile(savepath)
    print(f"Layer {idx} saved to {savepath}")

print(overlaplist)
