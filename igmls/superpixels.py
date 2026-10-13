import numpy as np
from skimage.segmentation import slic


def gmmsp_segmentation(image, n_seg, compactness=0.2):
    """Stand-in for GMMSP_segmentation.m, using SLIC (GMMSP has no Python build).

    Returns labels in 1..N (contiguous) and N. `image` is (h, w, b) in [0, 1].
    """
    h, w, b = image.shape
    if b == 1:
        img3 = np.repeat(image, 3, axis=2)
    elif b == 2:
        img3 = np.concatenate([image, np.zeros((h, w, 1))], axis=2)
    elif b == 3:
        img3 = image
    else:
        flat = image.reshape(-1, b)
        flat = flat - flat.mean(axis=0)
        _, _, vt = np.linalg.svd(flat, full_matrices=False)
        img3 = (flat @ vt[:3].T).reshape(h, w, 3)
    img3 = np.clip(img3, 0.0, 1.0)
    seg = slic(img3, n_segments=n_seg, compactness=compactness, sigma=0,
               convert2lab=False, start_label=1, channel_axis=-1)
    _, inv = np.unique(seg, return_inverse=True)
    labels = inv.reshape(h, w) + 1
    return labels, int(labels.max())
