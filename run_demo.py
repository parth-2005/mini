"""Python port of IGmLs_demo.m. Usage: python run_demo.py --dataset 2"""
import argparse
import time
from pathlib import Path

import imageio.v3 as iio
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from skimage.segmentation import find_boundaries

from igmls import IGmLsOptions, igmls, performance
from igmls.normalize import remove_outlier
from igmls.viz import cm_plot_rgb

WINDOW = {1: 18, 2: 9}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=int, choices=[1, 2], default=2)
    ap.add_argument("--data-dir", default="datasets")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    d = Path(args.data_dir)
    image_1 = iio.imread(d / f"Dataset{args.dataset}_im1.bmp")  # reference
    image_2 = iio.imread(d / f"Dataset{args.dataset}_im2.bmp")
    gt = iio.imread(d / f"Dataset{args.dataset}_gt.bmp").astype(float)
    if gt.ndim == 3:
        gt = gt[..., 0]
    gt = gt / gt.max()

    opt = IGmLsOptions(Nf=2500, Nc=500, Niter=2, wh=WINDOW[args.dataset], ws=3, alfa=0.01, gama=2)
    t0 = time.time()
    cm_iter, di_iter, info = igmls(image_1, image_2, opt)
    print(f"IGmLs total time: {time.time() - t0:.1f} s")

    out = Path(args.out)
    out.mkdir(exist_ok=True)
    fig, axes = plt.subplots(opt.Niter, 3, figsize=(15, 5 * opt.Niter), squeeze=False)
    for i in range(opt.Niter):
        m = performance(cm_iter[:, :, i], gt)
        print(f"Iteration {i + 1}: OA = {m['oa']:.3f}; Kc = {m['kappa']:.3f}; F1 = {m['f1']:.3f}")
        axes[i, 0].imshow(remove_outlier(di_iter[:, :, i]), cmap="gray")
        axes[i, 0].set_title(f"DI of iteration {i + 1}")
        axes[i, 1].imshow(cm_plot_rgb(cm_iter[:, :, i], gt))
        axes[i, 1].set_title(f"CM of iteration {i + 1}")
        bw = find_boundaries(cm_iter[:, :, i].astype(int), mode="inner")
        overlay = np.array(image_1[..., :3]).copy()
        overlay[bw] = (255, 0, 0)
        axes[i, 2].imshow(overlay)
        axes[i, 2].set_title("CM boundary on image 1")
        for ax in axes[i]:
            ax.axis("off")
    fig.tight_layout()
    fig.savefig(out / f"dataset{args.dataset}_results.png", dpi=100)
    np.savez_compressed(out / f"dataset{args.dataset}_maps.npz", cm=cm_iter, di=di_iter, dre=info["dre"])
    print(f"saved to {out}/")


if __name__ == "__main__":
    main()
