import numpy as np

def write_text(index, class_path, flag, city_name, country, region):
    if index == 0:
        with open(class_path, 'w') as file:
            file.write(f"{index+1}|{flag}|{region}|{country}|{city_name}\n")
    else:
        with open(class_path, 'a') as file:
            file.write(f"{index+1}|{flag}|{region}|{country}|{city_name}\n")

workdir    = '/your/directory/path'
nonprf_path = f"{workdir}/nonprf_flag.txt"
wup_path    = f"{wordir}/WUP2018_300k_2010.txt"
class_path  = f"{workdir}/classification.txt"

with open(nonprf_path, 'r') as input_file:
    nonprf = input_file.readlines()

with open(wup_path, 'r') as files:
    wup = files.readlines()

right_count = 0
no_prf_count = 0
invalid_mask_count = 0

for ind in range(1860):
    line  = nonprf[ind]
    parts = line.split('|')
    parts = [item.strip() for item in parts]
    flag  = parts[1]

    line2  = wup[ind]
    parts2 = line2.split('\t')
    parts2 = [item.strip() for item in parts2]
    city_name = parts2[3].replace("\"", "").replace("?", "").replace("/", "")
    country = parts2[4]
    region = parts2[5]

    if flag == 'False':
        write_text(ind, class_path, flag, city_name, country, region)
        right_count += 1

    elif flag == 'True':
        write_text(ind, class_path, flag, city_name, country, region)
        no_prf_count += 1

    elif flag == 'NoMASK':
        write_text(ind, class_path, flag, city_name, country, region)
        invalid_mask_count += 1

print(f"right: {right_count}, noprf: {no_prf_count}, nomask: {invalid_mask_count}")
with open(class_path, 'a') as file:
    file.write(f"right: {right_count}, noprf: {no_prf_count}, nomask: {invalid_mask_count}")
