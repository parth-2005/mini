import numpy as np


class SuperpixelFeatures:
    """Per-superpixel [mean, p25, median, p75] features (PrcfeatureExtraction.m).

    The pixel grouping is computed once, so each `extract` call is a single
    sort per band. Percentiles use MATLAB's prctile rule (Hazen).
    """

    def __init__(self, labels, n):
        lab = np.asarray(labels).ravel() - 1
        self.n = n
        self.order = np.argsort(lab, kind="stable")
        self.lab_sorted = lab[self.order]
        self.counts = np.bincount(lab, minlength=n)
        self.starts = np.cumsum(self.counts) - self.counts

    def _quantile(self, s, p):
        n = np.maximum(self.counts, 1)
        pos = np.clip(n * p + 0.5, 1, n)
        lo = np.floor(pos).astype(int)
        hi = np.ceil(pos).astype(int)
        frac = pos - lo
        i_lo = np.minimum(self.starts + lo - 1, len(s) - 1)
        i_hi = np.minimum(self.starts + hi - 1, len(s) - 1)
        return s[i_lo] * (1 - frac) + s[i_hi] * frac

    def extract(self, image_vector):
        """image_vector: (P, b) array -> (n, 4b) features; empty superpixels -> 0."""
        image_vector = np.asarray(image_vector, dtype=float)
        b = image_vector.shape[1]
        out = np.zeros((self.n, 4 * b))
        nonempty = self.counts > 0
        for k in range(b):
            v = image_vector[self.order, k]
            vmin = v.min()
            v0 = v - vmin
            gap = v0.max() + 1.0
            s = np.sort(v0 + gap * self.lab_sorted) - gap * self.lab_sorted + vmin
            mean = np.bincount(self.lab_sorted, weights=v, minlength=self.n) / np.maximum(self.counts, 1)
            out[:, k] = mean
            out[:, b + k] = self._quantile(s, 0.25)
            out[:, 2 * b + k] = self._quantile(s, 0.5)
            out[:, 3 * b + k] = self._quantile(s, 0.75)
        out[~nonempty] = 0.0
        return out
