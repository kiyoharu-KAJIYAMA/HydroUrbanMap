import numpy as np
import pickle

def open_text(path):
    with open(path, 'r') as files:
        data = files.readlines()
    return data

def nomsk_check():
    workdir = '/your/directory/path'
    cama_txt = f"{workdir}/table_first.txt"

    cama = open_text(cama_txt)

    nomsk_cities = []

    for ind in range(1860):
        line_cama = cama[ind]
        parts_cama = line_cama.split('|')
        parts_cama = [item.strip() for item in parts_cama]
        msk_flg = parts_cama[1]

        if msk_flg == 'NoMASK':
            nomsk_cities.append(int(ind+1))

    return nomsk_cities

def cluster_judge(nomsk_cities):
    # conditions
    # 1. if initial grid cell has less population than 300 -> NoMASK
    # 2. Classify city masks with 1 or 2 grid cells into low_msk_ directory
    # 3. Save city masks with more than 3 grid cells to cty_msk_ direcotry
    textpath = '/mnt/c/Users/tsimk/Downloads/dotfiles/h08/camacity/dat/cty_lst_/cluster_rejudge.txt'
    save_dir = '/mnt/c/Users/tsimk/Downloads/dotfiles/h08/camacity/dat'

    threshold = 100
    mininit = 300
    mingrid = 3

    for index in nomsk_cities:
        load_path = f'{workdir}dwn_twn_/city_{index:08}.pickle'
        with open(load_path, 'rb') as file:
            load_dict = pickle.load(file)

        density_track = load_dict['added_density']

        if not density_track:
            print(index, 'NoMASK')
            flag = 'NoMASK'

        else:
            valid_track = [x for x in density_track if x > threshold]

            if density_track[0] < mininit:
                print(index, 'LowINIT')
                flag = 'LOWINI'

            if density_track[0] >= mininit and len(valid_track) < mingrid:
                if len(valid_track) == 1:
                    print(index, 'SMALL')
                    flag = 'SMALL'
                    bestmask = load_dict['mask']
                    save_path = f'{workdir}/low_msk_/city_kj_{index:08}.gl5'
                    bestmask.astype(np.float32).tofile(save_path)
                else:
                    print(index, 'SMALL')
                    flag = 'SMALL'
                    target_index = len(valid_track) - 1
                    bestmask = load_dict['mask'][:, :, target_index]
                    save_path = f'{save_dir}/low_msk_/city_kj_{index:08}.gl5'
                    bestmask.astype(np.float32).tofile(save_path)

            if density_track[0] >= mininit and len(valid_track) >= mingrid:
                print(index, 'VALID')
                flag = 'VALID'
                target_index = len(valid_track) - 1
                bestmask = load_dict['mask'][:, :, target_index]
                save_path = f'{workdir}/cty_msk_/city_kj_{index:08}.gl5'
                bestmask.astype(np.float32).tofile(save_path)

        if index == nomsk_cities[0]:
            with open(textpath, 'w') as file:
                file.write(f"{index} | {flag}\n")
        else:
            with open(textpath, 'a') as file:
                file.write(f"{index} | {flag}\n")


if __name__ == '__main__':
    nomsk_cities = nomsk_check()
    cluster_judge(nomsk_cities)

