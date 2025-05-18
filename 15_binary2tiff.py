import numpy as np
import rasterio
from rasterio.transform import from_origin
import os

def bin2tif(loadpath, savepath):
    """
    Convert .gl5 binary file to GeoTIFF format.

    Parameters:
    - loadpath: path to .gl5 binary file
    - savepath: path to output GeoTIFF file
    """
    data = np.fromfile(loadpath, dtype='float32')
    data = data.reshape([2160, 4320])  # Global 5 arc-minute resolution

    # Set georeferencing: origin at top-left (west, north), 5 arc-min resolution
    west = -180
    north = 90
    transform = from_origin(west, north, 5/60, 5/60)

    with rasterio.open(
        savepath,
        'w',
        driver='GTiff',
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=str(data.dtype),
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.nodata = 0
        dst.write(data, 1)

    print(f"[SAVED] {savepath}")

def main():
    """
    Convert multiple .gl5 binary files into GeoTIFF format with new filenames.
    """

    # Define input and output files
    file_map = {
        # mask
        'city_clrd0000.gl5': 'mask_0000.tif',
        # inlet
        'inlet_clrd0000.gl5': 'inlet_0000.tif',
        # outlet
        'outlet_clrd0000.gl5': 'outlet_0000.tif',
        # aqueduct layers
        'aqd_layer001.gl5': 'aqueduct_layer001.tif',
        'aqd_layer002.gl5': 'aqueduct_layer002.tif',
        'aqd_layer003.gl5': 'aqueduct_layer003.tif',
        'aqd_layer004.gl5': 'aqueduct_layer004.tif',
    }

    # Base input and output directory (edit as needed)
    input_dir = '/your/directory/path'
    output_dir = '/your/directory/path'

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Process each file
    for infile, outfile in file_map.items():
        loadpath = os.path.join(input_dir, infile)
        savepath = os.path.join(output_dir, outfile)

        if os.path.exists(loadpath):
            bin2tif(loadpath, savepath)
        else:
            print(f"[SKIPPED] {loadpath} not found")

if __name__ == '__main__':
    main()
