import numpy as np


def cm_plot_rgb(cm, gt):
    """Replacement for the missing CMplotRGB: TP white, TN black, FP red, FN green."""
    cm = np.asarray(cm) > 0
    gt = np.asarray(gt) > 0
    out = np.zeros(cm.shape + (3,))
    out[cm & gt] = (1, 1, 1)
    out[cm & ~gt] = (1, 0, 0)
    out[~cm & gt] = (0, 1, 0)
    return out
