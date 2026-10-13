# Problem inventory — P5 / IGmLs

**Project:** Iterative Global Mapping–Local Searching for heterogeneous change detection with
unregistered images (problem statement: `docs/assets/problem-statement-P5.jpeg`).

**Organisation.** Each problem sits in exactly one category, chosen by where the fix has to happen
(data, method, implementation, evaluation, reproducibility, project definition).

**Evidence tags.** **[V]** verified directly in the repo or by running code. **[I]** inferred or not
checkable in the current environment.

**Training note.** IGmLs is unsupervised and training-free. A training set is not required; what is
required is a held-out set for tuning and a separate set for testing (A9).

## A. Data
| ID | Problem | Evidence |
|---|---|---|
| A1 | No heterogeneous (SAR↔optical) pairs; both bundled sets are optical↔optical | V |
| A2 | The paper's controlled-misregistration example (6 px, 3°) has no data and no generation script | V |
| A3 | No ground-truth registration (transform or displacement field); alignment quality cannot be measured | V |
| A4 | Misregistration in the bundled pairs is uncharacterised. Dataset2 shows non-uniform shifts (≈ −5 to −25 px vertical, −10 to +9 px horizontal on edge-map phase correlation); Dataset1 is inconclusive | V |
| A5 | Only two pairs; no variety in scene, resolution, season, sensor or change type | V |
| A6 | Provenance, sensors, GSD, acquisition dates and licence of both datasets undocumented | V |
| A7 | Change ground truth exists only in the image-1 frame; annotation quality and border handling unverified | V/I |
| A8 | Change/no-change class imbalance uncharacterised (biases OA) | I |
| A9 | No tuning/test split; window size was hand-set per dataset (`wh` 18 vs 9) | V |
| A10 | No SAR preprocessing chain (calibration, speckle handling, geocoding, co-location); only a log transform exists | V |

## B. Method / algorithm
| ID | Problem | Evidence |
|---|---|---|
| B1 | "Global mapping" is implicit (KNN library structure); no explicit global transform estimate | V |
| B2 | Motion model is per-superpixel integer translation; no rotation, scale, affine or non-rigid model | V |
| B3 | Search range fixed to ±`wh`; larger misregistration fails silently; `wh` needs prior knowledge | V |
| B4 | Integer offsets at stride `ws`=3; no subpixel refinement | V |
| B5 | Offsets estimated independently per superpixel; no smoothness or rigidity constraint on the displacement field | V |
| B6 | Superpixels come from image 1 only; homogeneous regions give ambiguous offsets (aperture problem) | V/I |
| B7 | Features are per-band mean and quartiles only; weak for SAR speckle, no texture or structure | V |
| B8 | Cross-modal difference assumes neighbourhood structure is preserved across modalities; degrades when much of the scene changed | I |
| B9 | No convergence/stopping criterion; `Niter` fixed at 2; improvement not guaranteed (Dataset2 F1 fell 0.68 → 0.53 in the port) | V |
| B10 | Unary change term uses an Otsu threshold, assuming a bimodal difference distribution | V |
| B11 | Many hyperparameters (`Nf`, `Nc`, `kmax`, `alfa`, `gama`, `wh`, `ws`); no sensitivity study | V |
| B12 | A border of width `wh` is cropped and never assessed | V |
| B13 | Asymmetric: image 1 is always the reference; no bidirectional consistency check | V |
| B14 | Scaling unknown: template count grows as (2·wh/ws+1)² and memory with `Nf`·4·bands | V/I |

## C. Implementation / port
| ID | Problem | Evidence |
|---|---|---|
| C1 | GMMSP replaced by SLIC (not equivalent); F1 moves ≈ ±0.1 with `compactness` | V |
| C2 | No numerical parity with MATLAB; port correctness unproven (no MATLAB/Octave available) | V |
| C3 | Graph cut uses SciPy max-flow with int-scaled capacities (PyMaxflow would not build here) | V |
| C4 | Edge-capacity convention (doubling for both arc directions) is an unconfirmed reading of `graphCutMex` | I |
| C5 | Tie-breaking, percentile and Otsu details reimplemented by hand and only partly unit-tested | V |
| C6 | Thin tests: 5 tests; synthetic pair is intensity-inverted, not SAR-like | V |
| C7 | Original-code defects: undefined `CMplotRGB`, dead tile helpers, unused outputs (removed or replaced in port) | V |
| C8 | No profiling, no GPU or large-scene strategy | I |
| C9 | Demo has no `--type-1/--type-2 sar` option or config file | V |

## D. Evaluation
| ID | Problem |
|---|---|
| D1 | No baselines (e.g. SCASC; register-then-detect pipelines) |
| D2 | No registration-accuracy metric (displacement RMSE) |
| D3 | Only pixel-level OA, kappa, F1; no per-class, boundary or object-level metrics |
| D4 | No ablations (global-only, local-only, no iteration, SLIC vs GMMSP) |
| D5 | No robustness sweeps over misregistration magnitude, rotation, noise or speckle level |
| D6 | No variance or significance testing across runs and parameters |
| D7 | No runtime or memory benchmark |
| D8 | No written evaluation protocol (tuning set, metrics, success thresholds) |

## E. Reproducibility / engineering
| ID | Problem | Evidence |
|---|---|---|
| E1 | Dependencies unpinned; Python 3.14 and library versions not recorded | V |
| E2 | No CI; no data download or run scripts | V |
| E3 | The original MATLAB release depended on prebuilt third-party MEX binaries (Linux/Windows only); not carried over | V |
| E4 | Licence compatibility of GMMSP and graphCutMex unchecked | I |

## F. Project definition
| ID | Problem |
|---|---|
| F1 | No original contribution defined; re-implementing a published paper is not sufficient for a graduation project |
| F2 | No acceptance criteria for "done" beyond the P5 paragraph |
| F3 | Deployment target undecided (Google Earth Engine was considered and set aside: the algorithm needs superpixel graph-cut and per-superpixel loops that do not fit its execution model) |
| F4 | Attribution of the original authors' work must be kept explicit in all deliverables |
| F5 | Team, timeline and compute budget not recorded |

## Priority order
1. **A1, A2, A3, A9** — without data nothing else is measurable.
2. **C2** — parity with MATLAB, or reference figures from the paper to compare against.
3. **F1** — the contribution, which decides which of B1–B14 to attack.
4. **D1, D8** — baselines and a written protocol.
