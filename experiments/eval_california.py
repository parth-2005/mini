"""Controlled-misregistration evaluation on the UiT California Landsat-8 <-> Sentinel-1 pair.

Image 2 (SAR) is shifted or rotated by a known amount; the change ground truth stays in the
image-1 frame. For each condition we compare IGmLs with several search windows against a
zero-window baseline (wh=0: same difference measure and MRF, no local search).

Usage: python experiments/eval_california.py [--crops 3] [--out results/california]
"""
import argparse
import csv
import time
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import rotate, shift

from igmls import IGmLsOptions, igmls, performance

CROP, MARGIN = 512, 32
METHODS = {"no-search (wh=0)": 0, "IGmLs wh=9": 9, "IGmLs wh=18": 18}
CONDITIONS = [("none", 0)] + [("shift", s) for s in (3, 6, 9, 12)] + [("rot", r) for r in (1, 2, 3, 4)]


def transform(window, kind, mag):
    """Return (transformed window, truth) where truth[x] = landing_position(x) - x (rows, cols)."""
    h, w = window.shape[:2]
    rr, cc = np.indices((h, w), dtype=float)
    if kind == "none":
        return window, np.zeros((h, w, 2))
    if kind == "shift":
        out = shift(window, (mag, mag, 0), order=1, mode="nearest")
        return out, np.full((h, w, 2), float(mag))
    out = rotate(window, mag, axes=(0, 1), reshape=False, order=1, mode="nearest")
    # coordinates rotated the opposite way give each original pixel's landing position
    land_r = rotate(rr, -mag, reshape=False, order=1, mode="nearest")
    land_c = rotate(cc, -mag, reshape=False, order=1, mode="nearest")
    return out, np.stack([land_r - rr, land_c - cc], axis=2)


def pick_crops(roi, n):
    h, w = roi.shape
    cands = []
    for r in range(MARGIN, h - CROP - MARGIN, CROP):
        for c in range(MARGIN, w - CROP - MARGIN, CROP):
            cands.append((roi[r:r + CROP, c:c + CROP].mean(), r, c))
    return [(r, c) for frac, r, c in sorted(cands, reverse=True) if frac > 0.05][:n]


def disp_error(dre, sup, wh, truth):
    """RMSE (px) and share within 3 px of the true displacement, over all pixels."""
    est = dre[sup - 1]  # (ht1, wt1, 2), crop interior
    tr = truth[wh:wh + est.shape[0], wh:wh + est.shape[1]]
    err = np.linalg.norm(est - tr, axis=2)
    return float(np.sqrt((err**2).mean())), float((err <= 3).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mat", default="data/UiT_HCD_California_2017.mat")
    ap.add_argument("--crops", type=int, default=3)
    ap.add_argument("--out", default="results/california")
    args = ap.parse_args()

    d = sio.loadmat(args.mat)
    t1, t2, roi = d["t1_L8_clipped"], d["logt2_clipped"], d["ROI"].astype(float)
    crops = pick_crops(roi, args.crops)
    print("crops (row, col):", crops, flush=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for ci, (r, c) in enumerate(crops):
        sl = (slice(r, r + CROP), slice(c, c + CROP))
        wl = (slice(r - MARGIN, r + CROP + MARGIN), slice(c - MARGIN, c + CROP + MARGIN))
        a, gt = t1[sl], roi[sl]
        for kind, mag in CONDITIONS:
            win, truth_full = transform(t2[wl], kind, mag)
            b = win[MARGIN:MARGIN + CROP, MARGIN:MARGIN + CROP]
            truth = truth_full[MARGIN:MARGIN + CROP, MARGIN:MARGIN + CROP]
            for name, wh in METHODS.items():
                t0 = time.time()
                opt = IGmLsOptions(Nf=1000, Nc=200, Niter=2, wh=wh, ws=3 if wh else 1)
                cm, _, info = igmls(a, b, opt)
                # score only the interior that was actually assessed (wh border is cropped)
                m = performance(cm[wh:CROP - wh, wh:CROP - wh, -1], gt[wh:CROP - wh, wh:CROP - wh])
                rmse, within = disp_error(info["dre"][-1], info["superpixels"], wh, truth)
                rows.append(dict(crop=ci, kind=kind, mag=mag, method=name, f1=m["f1"], kappa=m["kappa"],
                                 oa=m["oa"], rmse=rmse, within3=within, sec=time.time() - t0))
                print(f"crop{ci} {kind:5s}{mag:>3} {name:17s} F1={m['f1']:.3f} k={m['kappa']:.3f} "
                      f"RMSE={rmse:5.1f}px", flush=True)
    with open(out / "results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print("saved", out / "results.csv")


if __name__ == "__main__":
    main()
