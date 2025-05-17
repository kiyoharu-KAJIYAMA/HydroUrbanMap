import numpy as np

def write_text(save_path, index, flag, wup_pop, estimated_pop, city_name, country, region):
    if index == 0:
        with open(save_path, 'w') as file:
            file.write(f"{index+1}|{flag}|{wup_pop}|{estimated_pop}|{region}|{country}|{city_name}\n")
    else:
        with open(save_path, 'a') as file:
            file.write(f"{index+1}|{flag}|{wup_pop}|{estimated_pop}|{region}|{country}|{city_name}\n")

workdir    = '/your/directory/path'
wup_path    = f"{workdir}/WUP2018_300k_2010.txt"
class_path  = f"{workdir}/classification.txt"
pop_path    = f"{workdir}GPW4ag__20100000.gl5"
msk_dir     = f"{workdir}/vld_cty_"
save_path   = f"{workdir}/wup_vs_vldcty.txt"

with open(wup_path, 'r') as files:
    wup = files.readlines()

with open(class_path, 'r') as input_file:
    cla = input_file.readlines()

for ind in range(1860):
    line  = cla[ind]
    parts = line.split('|')
    parts = [item.strip() for item in parts]
    flag  = parts[1]

    line2  = wup[ind]
    parts2 = line2.split('\t')
    parts2 = [item.strip() for item in parts2]
    wup_pop = float(parts2[2])
    city_name = parts2[3].replace("\"", "").replace("?", "").replace("/", "")
    country = parts2[4]
    region = parts2[5]

    city_num = ind + 1
    msk_path = f'{msk_dir}/city_{city_num:08}.gl5'
    if flag != "NoMASK":
        msk = np.fromfile(msk_path, dtype='float32').reshape(2160, 4320)
        pop = np.fromfile(pop_path, dtype='float32').reshape(2160, 4320)
        pop_msk = np.ma.masked_where(msk != 1, pop)
        pop_sum = np.sum(pop_msk)
    else:
        pop_sum = 'NA'

    write_text(save_path, ind, flag, wup_pop, pop_sum, city_name, country, region)

