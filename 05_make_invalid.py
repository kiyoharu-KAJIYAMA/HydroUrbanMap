import os

def check_and_save_nonprf(city_num, mask_path, nonprf_path):
    """
    Check if the mask file for the specified city exists.
    If not, record the city ID in the nonprf_flag.txt file.

    Parameters:
    - city_num (int): ID of the city
    - mask_path (str): Path to the city mask binary file
    - nonprf_path (str): Path to the log file where cities with missing masks are recorded
    """

    # Check existence of the city mask
    if not os.path.exists(mask_path):
        print(f"[INFO] No mask found for city {city_num}")

        # Ensure directory exists for the nonprf_flag file
        os.makedirs(os.path.dirname(nonprf_path), exist_ok=True)

        # Determine file writing mode: overwrite if city_num is 1, otherwise append
        mode = 'w' if city_num == 1 else 'a'

        # Write the missing mask information
        with open(nonprf_path, mode) as f:
            f.write(f"{city_num}|NoMASK\n")

        print(f"[LOG] {city_num}|NoMASK written to {nonprf_path}")
        return False
    else:
        print(f"[INFO] Valid mask found for city {city_num}")
        return True

# Example usage
if __name__ == "__main__":
    workdir = "/your/directory/path"
    nonprf_path = f"{workdir}/nonprf_flag.txt"
    for city_num in range(1, 1861):
      mask_path = f"{workdir}/vld_cty_/city_{city_num:08d}.gl5"
      check_and_save_nonprf(city_num, mask_path, nonprf_path)
