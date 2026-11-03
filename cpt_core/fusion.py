"""Bayesian error calibration and correlated fusion of positive strength predictions.

Arrays use records by methods, with strengths in kPa. The calibrated log error is
log(formula prediction / reference strength). Prediction intervals condition on
the supplied methods, inputs, and optimized weights.
"""
import numpy as np
from scipy.special import logsumexp
from scipy.stats import t as student_t
from .solver import simplex_minimum

DEFAULT_PRIOR = {"kappa": 1.0, "covariance_df": 4.0,
                 "log_scale": 0.5, "correlation": 0.5}


def niw_update(errors, prior_center=None, prior=None):
    """Update mean/covariance and their Student-t predictive distribution."""
    e = np.asarray(errors, dtype=float)
    if e.ndim != 2 or min(e.shape) < 1 or not np.isfinite(e).all():
        raise ValueError("Expected finite calibration errors, records by methods")
    n, m = e.shape
    c = np.zeros(m) if prior_center is None else np.asarray(prior_center, dtype=float)
    if c.shape != (m,) or not np.isfinite(c).all():
        raise ValueError("Prior center must have one finite value per method")
    p = dict(DEFAULT_PRIOR if prior is None else prior)
    k0, df0 = float(p["kappa"]), float(p["covariance_df"])
    scale, rho = float(p["log_scale"]), float(p["correlation"])
    if not np.isfinite([k0, df0, scale, rho]).all() or min(k0, df0, scale) <= 0 or not 0 <= rho < 1:
        raise ValueError("Invalid prior parameters")
    centered = e - c
    mean = centered.mean(axis=0)
    dev = centered - mean
    kappa, nu = k0 + n, m + 1 + df0 + n
    psi = df0 * scale**2 * ((1-rho)*np.eye(m) + rho*np.ones((m,m)))
    psi = psi + dev.T @ dev + k0*n/kappa*np.outer(mean, mean)
    df = nu - m + 1
    shape = (kappa+1)/(kappa*df)*psi
    covariance = shape*df/(df-2)
    np.linalg.cholesky(covariance)
    return dict(n=n, m=m, kappa=kappa, nu=nu, df=df, mu=c+n/kappa*mean,
                psi=psi, shape=shape, covariance=covariance, prior=p, prior_center=c.copy())


def reference_prior_center(method_predictions, qnet_kpa, reference_factor):
    """Anchor mean equivalent cone factors using CPT inputs only."""
    f = np.asarray(method_predictions, dtype=float)
    q = np.asarray(qnet_kpa, dtype=float)
    if (f.ndim != 2 or min(f.shape) < 1 or q.shape != (len(f),)
        or not np.isfinite(f).all() or not np.isfinite(q).all()
        or (f <= 0).any() or (q <= 0).any()
        or not np.isfinite(reference_factor) or reference_factor <= 0):
        raise ValueError("Positive finite method predictions, qnet and reference factor required")
    log_mean_factor = logsumexp(np.log(q)[:,None]-np.log(f),axis=0)-np.log(len(f))
    return np.log(reference_factor)-log_mean_factor


def fit_predict(calibration_predictions, reference_strengths, target_predictions,
                prior_center=None, prior=None):
    """Calibrate a fixed method combination and return medians and 90/95% intervals."""
    a, b, y = (np.asarray(v,dtype=float) for v in
               (calibration_predictions,target_predictions,reference_strengths))
    if (a.ndim != 2 or b.ndim != 2 or min(a.shape) < 1 or min(b.shape) < 1
        or a.shape[1] != b.shape[1] or y.shape != (len(a),)
        or not all(np.isfinite(v).all() and (v > 0).all() for v in (a,b,y))):
        raise ValueError("Positive aligned calibration, reference and target arrays required")
    post = niw_update(np.log(a)-np.log(y)[:,None],prior_center,prior)
    weights, diagnostics = simplex_minimum(post["covariance"])
    location = (np.log(b)-post["mu"]) @ weights
    scale = float(np.sqrt(weights @ post["shape"] @ weights))
    levels = np.array([.025,.05,.5,.95,.975])
    log_quantiles = location[None,:]+scale*student_t.ppf(levels,post["df"])[:,None]
    if not np.isfinite(log_quantiles).all() or np.abs(log_quantiles).max() > 700:
        raise ValueError("Unrepresentable predictive quantiles")
    q = np.exp(log_quantiles)
    return dict(median=q[2],pi90=q[[1,3]].T,pi95=q[[0,4]].T,
                weights=weights,log_location=location,log_scale=scale,
                df=post["df"],posterior=post,diagnostics=diagnostics)


def local_calibration(qnet_reference, reference_strengths, qnet_target):
    """Fit one cone factor by averaging log(qnet / reference strength)."""
    q, y, qt = (np.asarray(v,dtype=float) for v in
                (qnet_reference,reference_strengths,qnet_target))
    if (q.ndim != 1 or y.shape != q.shape or qt.ndim != 1 or not len(q) or not len(qt)
        or not all(np.isfinite(v).all() and (v > 0).all() for v in (q,y,qt))):
        raise ValueError("Positive paired reference values and target inputs required")
    factor = float(np.exp(np.mean(np.log(q/y))))
    return {"cone_factor":factor,"median":qt/factor}
