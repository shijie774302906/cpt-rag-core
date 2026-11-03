"""Nonnegative, unit-sum minimum-variance weights with a KKT check."""
import itertools
import numpy as np

def simplex_minimum(covariance):
    q = np.asarray(covariance, float)
    m = len(q)
    if q.shape != (m, m) or m < 1 or m > 12 or (not np.isfinite(q).all()):
        raise ValueError('Invalid covariance')
    if not np.allclose(q, q.T, rtol=0, atol=1e-12):
        raise ValueError('Covariance must be symmetric')
    np.linalg.cholesky(q)
    qscale = max(float(np.max(np.diag(q))), 1e-15)
    a = q / qscale
    best = None
    for size in range(1, m + 1):
        for subset in itertools.combinations(range(m), size):
            ix = list(subset)
            v = np.linalg.solve(a[np.ix_(ix, ix)], np.ones(size))
            if v.sum() <= 0:
                continue
            v /= v.sum()
            if v.min() < -1e-10:
                continue
            w = np.zeros(m)
            w[ix] = np.maximum(v, 0)
            w /= w.sum()
            value = float(w @ a @ w)
            if best is None or value < best[0]:
                best = (value, w)
    if best is None:
        raise ValueError('No feasible weights')
    _, w = best
    grad = a @ w
    risk = float(w @ a @ w)
    active = w > 1e-08
    kkt = max(float(np.max(np.abs(grad[active] - risk))), float(max(0.0, np.max(risk - grad[~active]))) if (~active).any() else 0.0)
    if kkt > 1e-07 or abs(w.sum() - 1) > 1e-12 or w.min() < 0:
        raise ValueError('QP KKT or simplex failure')
    return (w, dict(kkt_error=kkt, log_predictive_variance=float(w @ q @ w)))
