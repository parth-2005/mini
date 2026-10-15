"""Summarise <out>/results.csv into a figure and a markdown table.

Usage: python experiments/plot_california.py [--out results/california]
"""
import argparse
import csv
import collections
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/california")
out = Path(ap.parse_args().out)
rows = list(csv.DictReader(open(out / "results.csv")))
g = collections.defaultdict(list)
for r in rows:
    g[(r["kind"], int(r["mag"]), r["method"])].append(r)
methods = sorted({r["method"] for r in rows})
n_crops = len({r["crop"] for r in rows})


def mean(kind, mag, method, field):
    return float(np.mean([float(x[field]) for x in g[(kind, mag, method)]]))


def series(kind, field):
    # the registered condition is stored as kind "none", mag 0; it is the x = 0 point of every curve
    mags = [0] + sorted({m for k, m, _ in g if k == kind})
    return mags, {meth: [mean("none" if m == 0 else kind, m, meth, field) for m in mags] for meth in methods}


fig, ax = plt.subplots(2, 2, figsize=(11, 7))
for j, (kind, xl) in enumerate([("shift", "diagonal shift N: (N, N) px, i.e. N·√2 px displacement"),
                                ("rot", "rotation (deg)")]):
    for i, (field, yl) in enumerate([("f1", "F1 (change class)"), ("rmse", "displacement RMSE (px)")]):
        mags, s = series(kind, field)
        for meth, y in s.items():
            ax[i, j].plot(mags, y, marker="o", label=meth)
        ax[i, j].set_xlabel(xl)
        ax[i, j].set_ylabel(yl)
        ax[i, j].grid(alpha=0.3)
ax[0, 0].legend()
fig.suptitle(f"California (Landsat-8 ↔ Sentinel-1): controlled misregistration, mean of {n_crops} crops")
fig.tight_layout()
fig.savefig(out / "california_sweep.png", dpi=110)

lines = ["| condition | method | F1 | kappa | disp. RMSE (px) | within 3 px |", "|---|---|---|---|---|---|"]
for kind, mag in sorted({(k, m) for k, m, _ in g}, key=lambda t: (["none", "shift", "rot"].index(t[0]), t[1])):
    for meth in methods:
        v = lambda f: mean(kind, mag, meth, f)
        cond = {"none": "registered", "shift": f"shift ({mag},{mag}) px", "rot": f"rot {mag}°"}[kind]
        lines.append(f"| {cond} | {meth} | {v('f1'):.3f} | {v('kappa'):.3f} | {v('rmse'):.1f} | {v('within3'):.2f} |")
(out / "table.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines[:5]))
