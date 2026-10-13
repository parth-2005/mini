# Benchmark references for the California (Landsat-8 ↔ Sentinel-1) dataset

> Numbers below were pulled from the papers' web versions with an automated extractor and some are
> read off bar charts. **Verify against the PDFs before citing them in a report.**

## The dataset
Landsat-8 (5 Jan 2017) and Sentinel-1A GRD (18 Feb 2017), a flood in Sacramento, Yuba and Sutter
counties, 3500×2000 px (N = 7·10⁶). Ground truth was derived from a Sentinel-1 pair. Our file
`UiT_HCD_California_2017.mat` matches this size and has 4.4 % changed pixels.
Released by Luppino et al.: <https://sites.google.com/view/luppino/data>.

## Published results to compare against
| Source | Methods | Reported on California |
|---|---|---|
| Luppino et al., *Unsupervised image regression for heterogeneous change detection*, arXiv 1909.05948 (TGRS 2019) | GPR, SVR, RFR, HPT regression | kappa 0.04–0.46, AUC 0.69–0.91, OA 0.87–0.93 depending on patch size and training-set size |
| Luppino et al., *Code-aligned autoencoders…*, arXiv 2004.07011 (TNNLS 2022); **code: <https://github.com/llu025/Heterogeneous_CD>** | CAN, SCCN, ACE-Net, X-Net, proposed | kappa ≈ 0.20 (CAN, SCCN), 0.25–0.30 (ACE-Net), 0.30–0.35 (X-Net), 0.45–0.50 (proposed), read from a bar chart. Images were resampled to 850×500 |
| *Self-supervised remote sensing images change detection at pixel-level*, arXiv 2105.08501 | PixSSL, PatchSSL, CAA, SCCN | F1 0.51–0.57, kappa 0.46–0.53, OA 90–95 % |
| Sun et al., IGmLs, IJCV 2026, doi 10.1007/s11263-025-02719-6 | IGmLs vs SCASC etc. | **Not retrieved.** Needs the paper PDF (misregistered-pair numbers are what we need most) |

Other repositories with the same benchmark sets: `yulisun/riem` (RIEM, Sun et al.), `omega-rs/cstn`.
Not yet checked: whether SCASC, INLPG or AGSCC have public code.

## Our port under the same protocol
Full scene resampled to 850×500 (bilinear for images, nearest for ground truth), registered input,
`Nf=2500`, `Nc=500`, `Niter=2`, SLIC superpixels. Score excludes the `wh` border.

| Method | OA | kappa | F1 |
|---|---|---|---|
| no-search (`wh=0`), iteration 1 | 0.944 | 0.383 | 0.412 |
| no-search (`wh=0`), iteration 2 | 0.943 | 0.351 | 0.381 |
| IGmLs `wh=9`, iteration 1 | 0.938 | 0.270 | 0.303 |
| IGmLs `wh=9`, iteration 2 | 0.940 | 0.228 | 0.259 |

Reading: without search, kappa 0.38 sits inside the published range for unsupervised methods
(X-Net ≈ 0.30–0.35). Turning the local search on makes it *worse* on already-registered data, which is
consistent with the near-random offsets found in `results-california.md`. Both iterations degrade.

## Caveats on comparability
- Published scores use the whole scene, usually resampled; our crop experiments (5–12 % changed) are
  not comparable to them. The table above is the like-for-like one.
- Some papers train on that scene's other date pairs (self-supervised); IGmLs is training-free.
- Resampling method and ground-truth thresholding affect scores and are not always documented.
