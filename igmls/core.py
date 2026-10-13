from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.ndimage import uniform_filter
from scipy.spatial import cKDTree

from .features import SuperpixelFeatures
from .mrf import solve_energy_mrf
from .normalize import image_normalized
from .superpixels import gmmsp_segmentation


@dataclass
class IGmLsOptions:
    type_1: str = "optical"  # 'optical' or 'sar'
    type_2: str = "optical"
    Nf: int = 2500  # fine superpixels
    Nc: int = 500  # coarse superpixels (library)
    Niter: int = 2
    wh: int = 9  # search window half-height
    ww: Optional[int] = None  # defaults to wh
    ws: int = 3  # search stride
    alfa: float = 0.01
    gama: float = 2.0
    kmax: Optional[int] = None  # defaults to round(sqrt(Nc))
    compactness: float = 0.2  # SLIC compactness (stand-in for GMMSP)

    def __post_init__(self):
        if self.ww is None:
            self.ww = self.wh
        if self.kmax is None:
            self.kmax = int(np.floor(np.sqrt(self.Nc) + 0.5))


def _knn(tree, queries, k):
    d, idx = tree.query(queries, k=k)
    return d, idx


def igmls(image_1, image_2, opt):
    """Port of IGmLs_main.m.

    image_1 is the reference; image_2 is searched at offsets within +/-wh, +/-ww.
    Returns (CM_iter, DI_iter, info) where CM_iter/DI_iter are
    (H, W, Niter) maps (zero in the wh/ww border) and info has the per-iteration
    displacement of every fine superpixel ('dre') and the last aligned image 2.
    """
    wh, ww, ws = opt.wh, opt.ww, opt.ws
    img1 = np.asarray(image_1, dtype=float)
    img2 = np.asarray(image_2, dtype=float)
    if img1.ndim == 2:
        img1 = img1[..., None]
    if img2.ndim == 2:
        img2 = img2[..., None]

    # --- pre-processing ---
    img1 = uniform_filter(img1, size=(5, 5, 1), mode="reflect")
    img2 = uniform_filter(img2, size=(5, 5, 1), mode="reflect")
    img1 = image_normalized(img1, opt.type_1)
    img2 = image_normalized(img2, opt.type_2)
    img1 = img1[wh:img1.shape[0] - wh, ww:img1.shape[1] - ww, :]
    ht1, wt1, bt1 = img1.shape
    ht2, wt2, bt2 = img2.shape

    lab_f, Nf = gmmsp_segmentation(img1, opt.Nf, opt.compactness)
    lab_c, Nc = gmmsp_segmentation(img1, opt.Nc, opt.compactness)
    feat_f = SuperpixelFeatures(lab_f, Nf)
    feat_c = SuperpixelFeatures(lab_c, Nc)
    t1_fine = feat_f.extract(img1.reshape(-1, bt1))
    t1_coarse = feat_c.extract(img1.reshape(-1, bt1))

    # --- image 2 feature templates, one per candidate offset ---
    img2_flat = img2.reshape(-1, bt2)
    t2_coarse = feat_c.extract(img2[wh:wh + ht1, ww:ww + wt1, :].reshape(-1, bt2))
    n_h = 2 * wh // ws + 1
    n_w = 2 * ww // ws + 1
    t2_templates = {}
    for a in range(n_h):
        for b in range(n_w):
            dh, dw = -wh + a * ws, -ww + b * ws
            sub = img2[wh + dh:wh + dh + ht1, ww + dw:ww + dw + wt1, :]
            t2_templates[a, b] = feat_f.extract(sub.reshape(-1, bt2))

    # --- iterative global mapping / local search ---
    labels = np.zeros((opt.Niter, Nf), dtype=int)
    fmin_iter = np.zeros((opt.Niter, Nf))
    dre_iter = np.zeros((opt.Niter, Nf, 2), dtype=int)
    keep = np.ones(Nc, dtype=bool)
    lab_f0 = lab_f - 1
    rows = np.arange(ht1)[:, None]
    cols = np.arange(wt1)[None, :]
    img2_new = None

    for it in range(opt.Niter):
        lib1 = t1_coarse[keep]
        lib2 = t2_coarse[keep]
        k = min(opt.kmax, len(lib1))
        d1, id1 = _knn(cKDTree(lib1), t1_fine, k)
        id1, d1 = id1[:, 1:], d1[:, 1:]
        mean_dx = d1.mean(axis=1)
        tree2 = cKDTree(lib2)

        f = np.zeros((n_h, n_w, Nf))
        for (a, b), t2f in t2_templates.items():
            d2, id2 = _knn(tree2, t2f, k)
            id2, d2 = id2[:, 1:], d2[:, 1:]
            dist_xy = np.linalg.norm(lib1[id2] - t1_fine[:, None, :], axis=2).mean(axis=1)
            dist_yx = np.linalg.norm(lib2[id1] - t2f[:, None, :], axis=2).mean(axis=1)
            f[a, b] = (dist_xy - mean_dx) / bt1 + (dist_yx - d2.mean(axis=1)) / bt2

        # local search: best offset per superpixel (column-major tie-breaking as in MATLAB)
        flat = f.transpose(2, 1, 0).reshape(Nf, -1)
        best = flat.argmin(axis=1)
        fmin = flat[np.arange(Nf), best]
        dre = np.stack([(best % n_h) * ws - wh, (best // n_h) * ws - ww], axis=1)

        labels[it] = solve_energy_mrf(fmin, dre, lab_f, opt)

        # re-align image 2 superpixel by superpixel, refresh the library
        src_r = rows + wh + dre[lab_f0, 0]
        src_c = cols + ww + dre[lab_f0, 1]
        img2_new = img2[src_r, src_c, :]
        t2_coarse = feat_c.extract(img2_new.reshape(-1, bt2))
        cm_pix = labels[it][lab_f0].ravel()
        with np.errstate(invalid="ignore", divide="ignore"):
            change_p = np.bincount((lab_c - 1).ravel(), cm_pix, Nc) / feat_c.counts
        new_keep = change_p < 0.5
        # Guard (not in the MATLAB original): if the MRF labels nearly everything as change the
        # library would be empty (KNN needs >= 2 entries), so keep the previous one.
        if new_keep.sum() > 1:
            keep = new_keep

        dre_iter[it] = dre
        rng = fmin.max() - fmin.min()
        fmin_iter[it] = (fmin - fmin.min()) / rng if rng > 0 else 0.0

    pad = ((wh, wh), (ww, ww))
    cm_iter = np.stack([np.pad(labels[i][lab_f0].astype(float), pad) for i in range(opt.Niter)], axis=2)
    di_iter = np.stack([np.pad(fmin_iter[i][lab_f0], pad) for i in range(opt.Niter)], axis=2)
    info = dict(dre=dre_iter, img2_aligned=img2_new, superpixels=lab_f)
    return cm_iter, di_iter, info
