import numpy as np


def image_normalized(image, kind):
    """Port of image_normlized.m. `kind` is 'optical' or 'sar'."""
    image = np.nan_to_num(np.asarray(image, dtype=float), nan=0.0)
    if kind == "sar":
        pos = np.abs(image) > 0
        image = image.copy()
        image[~pos] = image[pos].min()
        image = np.log(image + 1)
    elif kind != "optical":
        raise ValueError(f"unknown image type: {kind!r}")
    lo, hi = image.min(), image.max()
    return (image - lo) / (hi - lo)


def remove_outlier(y, n=3):
    """Port of remove_outlier.m: clip values above mean + n*std to the max inlier."""
    x = np.array(y, dtype=float)
    outliers = (x - x.mean()) > n * x.std(ddof=1)
    if outliers.any():
        x[outliers] = x[~outliers].max()
    return x
