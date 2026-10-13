import numpy as np
import pytest

from igmls import IGmLsOptions, igmls, performance
from igmls.features import SuperpixelFeatures
from igmls.mrf import solve_energy_mrf
from igmls.normalize import remove_outlier


def _hazen(x, p):
    x = np.sort(x)
    n = len(x)
    pos = np.clip(n * p + 0.5, 1, n)
    lo, hi = int(np.floor(pos)), int(np.ceil(pos))
    return x[lo - 1] * (1 - (pos - lo)) + x[hi - 1] * (pos - lo)


def test_features_match_matlab_prctile():
    rng = np.random.default_rng(0)
    lab = rng.integers(1, 6, size=(20, 20))
    img = rng.random((400, 2))
    got = SuperpixelFeatures(lab, 5).extract(img)
    for s in range(5):
        v = img[lab.ravel() == s + 1]
        for k in range(2):
            want = [v[:, k].mean(), _hazen(v[:, k], .25), _hazen(v[:, k], .5), _hazen(v[:, k], .75)]
            np.testing.assert_allclose(got[s, [k, 2 + k, 4 + k, 6 + k]], want, atol=1e-9)


def test_performance_counts():
    gt = np.array([[0, 1], [1, 0]])
    cm = np.array([[0, 1], [0, 1]])
    m = performance(cm, gt)
    assert (m["tp"], m["fp"], m["tn"], m["fn"]) == (1, 1, 1, 1)
    assert m["oa"] == pytest.approx(0.5)


def test_remove_outlier_clips_to_max_inlier():
    y = np.r_[np.ones(50), 100.0]
    assert remove_outlier(y).max() == 1.0


def test_mrf_separates_two_regions():
    sup = np.kron(np.arange(1, 17).reshape(4, 4), np.ones((8, 8), dtype=int))
    f = np.full(16, 0.05)
    f[[5, 6, 9, 10]] = 0.9  # central block clearly "changed"
    opt = IGmLsOptions(wh=0, gama=0.5)
    labels = solve_energy_mrf(f, np.zeros((16, 2)), sup, opt)
    assert set(np.flatnonzero(labels)) == {5, 6, 9, 10}


def test_igmls_recovers_shift_and_change():
    """Heterogeneous-ish pair (image 2 is intensity-inverted), shifted, with one changed block."""
    rng = np.random.default_rng(1)
    base = np.kron(rng.random((14, 14)), np.ones((10, 10)))
    base = base + 0.02 * rng.standard_normal(base.shape)
    shift = (3, -3)  # img2[x] = f(img1[x - shift])
    img2 = 1.0 - np.roll(base, shift, axis=(0, 1))
    img2[60:90, 60:90] = rng.random((30, 30))  # change
    gt = np.zeros(base.shape)
    gt[60 - shift[0]:90 - shift[0], 60 - shift[1]:90 - shift[1]] = 1  # in image-1 coordinates
    opt = IGmLsOptions(Nf=300, Nc=60, Niter=2, wh=6, ws=3)
    cm, di, info = igmls(base, img2, opt)
    dre = info["dre"][-1]
    # img2 is sampled at x + dre, so the dominant displacement equals the shift
    vals, counts = np.unique(dre, axis=0, return_counts=True)
    assert tuple(vals[counts.argmax()]) == shift
    m = performance(cm[:, :, -1], gt)
    assert m["oa"] > 0.8
