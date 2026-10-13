import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import breadth_first_order, maximum_flow

from .normalize import remove_outlier


def _otsu_level(x):
    """MATLAB graythresh for a double image: clamp to [0,1], 256 bins, Otsu."""
    q = np.round(np.clip(x, 0.0, 1.0) * 255).astype(int)
    p = np.bincount(q.ravel(), minlength=256) / q.size
    k = np.arange(1, 257)
    omega = np.cumsum(p)
    mu = np.cumsum(p * k)
    mu_t = mu[-1]
    with np.errstate(divide="ignore", invalid="ignore"):
        sigma = (mu_t * omega - mu) ** 2 / (omega * (1 - omega))
    sigma = np.nan_to_num(sigma, nan=0.0, posinf=0.0)
    idx = np.mean(np.flatnonzero(sigma == sigma.max()) + 1)
    return (idx - 1) / 255


def _min_cut_labels(term_src, term_snk, edges_i, edges_j, edge_cap):
    """Binary min-cut. Label 1 = sink side. Capacities are float; scaled to int32."""
    n = len(term_src)
    # shift per node so both terminal capacities are non-negative
    m = np.minimum(term_src, term_snk)
    src, snk = term_src - m, term_snk - m
    total = src.sum() + snk.sum() + edge_cap.sum()
    scale = 2e9 / max(total, 1e-12)
    s, t = n, n + 1
    rows = np.concatenate([np.full(n, s), np.arange(n), edges_i])
    cols = np.concatenate([np.arange(n), np.full(n, t), edges_j])
    caps = np.concatenate([src, snk, edge_cap]) * scale
    graph = csr_matrix((np.round(caps).astype(np.int32), (rows, cols)), shape=(n + 2, n + 2))
    flow = maximum_flow(graph, s, t).flow
    resid = (graph - flow).tocsr()
    resid.data = np.where(resid.data > 0, 1, 0).astype(np.int32)
    resid.eliminate_zeros()
    # nodes that can still reach the sink in the residual graph are on the sink side
    reach = breadth_first_order(resid.T.tocsr(), t, directed=True, return_predecessors=False)
    labels = np.zeros(n, dtype=int)
    labels[reach[reach < n]] = 1
    return labels


def solve_energy_mrf(f, D, sup_img, opt):
    """Port of solveEnergyMRF.m. Returns 0/1 labels per superpixel (1 = change)."""
    h, w = sup_img.shape
    n = int(sup_img.max())
    lab = sup_img - 1

    rr, cc = np.indices(sup_img.shape)
    counts = np.bincount(lab.ravel(), minlength=n)
    cx = np.floor(np.bincount(lab.ravel(), rr.ravel(), n) / counts + 0.5)
    cy = np.floor(np.bincount(lab.ravel(), cc.ravel(), n) / counts + 0.5)

    # touching neighbours (8-neighbourhood, as in the MATLAB loops)
    adj = np.zeros((n, n), dtype=bool)
    a = lab[1:h - 1, 1:w - 1]
    for dy, dx in [(1, -1), (0, 1), (1, 0), (1, 1)]:
        b = lab[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx]
        m = a != b
        adj[a[m], b[m]] = True
    adj |= adj.T

    # R-adjacency by centroid distance
    R = 2 * np.floor(np.sqrt(h * w / n) + 0.5)
    d2 = (cx[:, None] - cx[None, :]) ** 2 + (cy[:, None] - cy[None, :]) ** 2
    near = d2 < R**2
    np.fill_diagonal(near, False)
    adj |= near

    i, j = np.nonzero(adj)
    Dpq = (f[i] - f[j]) ** 2
    dist = np.maximum(np.hypot(cx[i] - cx[j], cy[i] - cy[j]), 1)
    sigma = Dpq.mean()
    Vpq = np.exp(-Dpq / (2 * sigma + np.finfo(float).eps)) / dist
    gama = opt.gama * f.sum() / Vpq.sum()
    # graphCutMex receives both (i,j) and (j,i) rows, so each directed arc ends up doubled
    edge_cap = 2 * gama * Vpq

    fy = np.maximum(np.sqrt((D**2).sum(axis=1)) - opt.wh, 0)
    alfa = opt.alfa * f.sum() / (fy.sum() + np.finfo(float).eps)
    cost_change = f + alfa * fy  # termWeights(:,2): cost of label 0 (no change)
    lamda = _otsu_level(remove_outlier(f))  # termWeights(:,1): cost of label 1 (change)
    return _min_cut_labels(np.full(n, lamda), cost_change, i, j, edge_cap)
