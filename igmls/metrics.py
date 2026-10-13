import numpy as np


def performance(cm, gt):
    """Port of performance.m. Returns dict with tp, fp, tn, fn, oa, kappa, f1."""
    gt = np.asarray(gt, dtype=float)
    cm = np.asarray(cm, dtype=float)
    n = gt.size
    nu = np.sum(gt == 0)
    nc = np.sum(gt != 0)
    diff = cm - gt
    fp = np.sum(diff > 0)
    fn = np.sum(diff < 0)
    tp = nc - fn
    tn = nu - fp
    oa = 1 - fp / n - fn / n
    pra = (tp + tn) / n
    pre = ((tp + fp) * (tp + fn) + (fn + tn) * (fp + tn)) / n**2
    kappa = (pra - pre) / (1 - pre)
    f1 = 2 * tp / (2 * tp + fp + fn)
    return dict(tp=int(tp), fp=int(fp), tn=int(tn), fn=int(fn), oa=oa, kappa=kappa, f1=f1)
