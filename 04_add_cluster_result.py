import re

def parse_log_file(log_file_content):
    log_file_content = "".join(log_file_content)
    city_blocks = log_file_content.strip().split('--------------------------------------------------------------')
    result = []
    for block in city_blocks:
        if not block.strip():
            continue
        city_index_match = re.search(r'city_index:\s*(\d+)', block)
        valid_gradient_match = re.search(r'len of valid_gradient:\s*(\d+)', block)
        city_mask_match = re.search(r'city_mask:\s*([\d\.]+)', block)
        mask_cover_match = re.search(r'mask_cover:\s*([\d\.]+)', block)
        if city_index_match:
            city_index = int(city_index_match.group(1))
            has_valid_gradient = bool(valid_gradient_match)
            city_mask = float(city_mask_match.group(1)) if city_mask_match else None
            mask_cover = float(mask_cover_match.group(1)) if mask_cover_match else None
            # adding the dictionary to the results
            result.append({
                'city_index': city_index,
                'has_valid_gradient': has_valid_gradient,
                'city_mask': city_mask,
                'mask_cover': mask_cover
            })
    return result

def write_text(save_path, city_index, grad_flag, grid_num, cover_rate):
    if city_index == 1:
        with open(save_path, 'w') as file:
            file.write(f"{city_index}|{grad_flag}|{grid_num}|{cover_rate}\n")
    else:
        with open(save_path, 'a') as file:
            file.write(f"{city_index}|{grad_flag}|{grid_num}|{cover_rate}\n")

def main():
    workdir = "/your/directory/path"
    log_path = f"{workdir}/cluster.log"
    save_path = f"{workdir}/cluster_result.txt"

    with open(log_path, 'r') as f:
        log_file_content = f.readlines()

    parsed_data = parse_log_file(log_file_content)
    for entry in parsed_data:
        city_index = entry['city_index']
        grad_flag = entry['has_valid_gradient']
        grid_num = entry['city_mask']
        cover_rate = entry['mask_cover']
        # mask flag
        # cityname
        # wup pop
        # 100% est_pop
        # vld_pop
        write_text(save_path, city_index, grad_flag, grid_num, cover_rate)

if __name__ == '__main__':
    main()
