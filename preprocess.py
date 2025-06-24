import rasterio
import numpy as np
from scipy.ndimage import distance_transform_edt

# Training global stats (from your code)
band_means = [0.00015076, 0.00021958, 0.13130338, 0.03614379]
band_stds  = [0.00021598, 0.00033735, 0.01487704, 0.0088344]

def fill_nan_with_nearest(arr):
    """
    Fill NaN values in a 2D array using nearest-neighbor interpolation.
    """
    mask = np.isnan(arr)
    if not np.any(mask):
        return arr

    # Get indices of nearest non-NaN cells
    _, indices = distance_transform_edt(mask, return_indices=True)

    # Copy original array
    filled = arr.copy()
    # Replace only NaN values using the nearest non-NaN values
    filled[mask] = arr[tuple(indices)][mask]

    return filled

def preprocess_image(image_path):
    with rasterio.open(image_path) as src:
        bands = src.read([1, 2, 3, 4])  # shape: (4, H, W)
    
    # Add a batch dimension (since we're processing one image, batch size is 1)
    bands = np.expand_dims(bands, axis=0)  # shape: (1, 4, H, W)

    # Fill NaNs with nearest neighbors for each band
    for i in range(4):
        bands[0, i] = fill_nan_with_nearest(bands[0, i])

    # Normalize each band using the global training stats
    for i in range(4):
        bands[0, i] = (bands[0, i] - band_means[i]) / band_stds[i]

    # Optional: Fill any remaining NaNs with zero (if any are left after filling)
    bands = np.nan_to_num(bands, nan=0.0)

    # Transpose to (batch_size, height, width, channels) which is (1, H, W, 4)
    bands = np.transpose(bands, (0, 2, 3, 1))  # shape: (1, H, W, 4)

    return bands
