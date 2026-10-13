# Porting notes: MATLAB → Python

File names below refer to the authors' original MATLAB release, which is not included in this repository.

## File mapping

| MATLAB | Python |
|---|---|
| `IGmLs_demo.m` | `run_demo.py` |
| `auxi_funcs/IGmLs_main.m` | `igmls/core.py` (`igmls`) |
| `auxi_funcs/solveEnergyMRF.m` | `igmls/mrf.py` (`solve_energy_mrf`) |
| `auxi_funcs/PrcfeatureExtraction.m` | `igmls/features.py` (`SuperpixelFeatures`) |
| `auxi_funcs/image_normlized.m`, `remove_outlier.m` | `igmls/normalize.py` |
| `auxi_funcs/GMMSP_segmentation.m` | `igmls/superpixels.py` (`gmmsp_segmentation`, SLIC) |
| `auxi_funcs/performance.m` | `igmls/metrics.py` (`performance`, adds F1) |
| `CMplotRGB` (undefined in original) | `igmls/viz.py` (`cm_plot_rgb`) |
| `mosaic_map.m`, `image2subimage.m`, `subimage2image.m` | not ported (visualisation / dead code) |

## Library mapping

| MATLAB | Python |
|---|---|
| `mx_GMMSP` | `skimage.segmentation.slic` |
| `graphCutMex` | `scipy.sparse.csgraph.maximum_flow` + residual BFS |
| `knnsearch` / `pdist2` | `scipy.spatial.cKDTree` / `numpy.linalg.norm` |
| `graythresh` | reimplemented in `mrf._otsu_level` |
| `prctile` | Hazen rule in `SuperpixelFeatures._quantile` |
| `fspecial('average')` + `imfilter` | `scipy.ndimage.uniform_filter` |

## Known deviations

1. **Superpixels.** SLIC replaces GMMSP; they are not equivalent. `compactness` (default 0.2) is a new
   free parameter, and F1 changed by about ±0.1 across 0.05–1.0 in our sweep.
2. **Max-flow.** SciPy's integer max-flow replaces Boykov–Kolmogorov. Capacities are scaled to int32.
   Verified equal to brute-force minimum cuts on small random graphs, not on production-size graphs.
3. **Edge weights.** `graphCutMex` receives both (i,j) and (j,i) rows; we double the capacity to match
   that reading. Unconfirmed against the original solver's semantics.
4. **KNN size.** MATLAB queried `k = Nf` neighbours for image 1 and sliced to `kmax`; we query `kmax`
   directly (same result, far less memory).
5. **Outputs.** The port also returns the per-iteration displacement field and last aligned image 2.
6. **Not run against MATLAB.** No MATLAB/Octave was available; parity is unverified.

## Observed results (SLIC, defaults)

| Dataset | F1 iter 1 → 2 | OA iter 2 | Kappa iter 2 |
|---|---|---|---|
| 1 | 0.716 → 0.757 | 0.966 | 0.739 |
| 2 | 0.680 → 0.530 | 0.876 | 0.461 |

These are *our* numbers, not paper numbers.
