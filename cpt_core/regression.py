"""Local Bayesian linear regression with checked one-dimensional quadrature.

Supply a six-column design matrix (intercept plus five predictor slots), centered
log reference strengths, and a zero coefficient-prior center for the data-only
baseline. Returns log-strength samples; add the reference-data log center before
converting them to strengths. Input preprocessing is supplied by the caller.
"""
import warnings
import numpy as np
from scipy.integrate import simpson, cumulative_trapezoid, quad, IntegrationWarning

SCALES = np.array([2., .5, .5, .5, .5, .5])

def decomposition(z, y, center):
    z = np.asarray(z, float)
    y = np.asarray(y, float)
    center = np.asarray(center, float)
    if z.shape != (len(y), 6) or center.shape != (6,) or (not len(y)):
        raise ValueError('Invalid regression dimensions')
    if not all((np.isfinite(v).all() for v in (z, y, center))):
        raise ValueError('Nonfinite regression input')
    u, d, vt = np.linalg.svd(z * SCALES, full_matrices=True)
    residual = y - z @ center
    k = len(d)
    a = u[:, :k].T @ residual
    perp = float(np.sum((residual - u[:, :k] @ a) ** 2)) if len(y) > k else 0.0
    return dict(n=len(y), d=d, a=a, vt=vt, perp=perp, center=center)


def log_density(t, dec):
    t = np.asarray(t, float)
    lv = 2 * t
    ld = np.log(np.maximum(dec['d'] ** 2, np.finfo(float).tiny))
    den = np.logaddexp(lv[..., None], ld)
    invv = np.exp(np.clip(-lv, -745, 700))
    ll = -0.5 * ((dec['n'] - len(ld)) * lv + den.sum(-1) + dec['perp'] * invv + (dec['a'] ** 2 * np.exp(np.clip(-den, -745, 700))).sum(-1))
    return ll - 2 * np.exp(np.clip(lv, -745, 700)) + t


def posterior_grid(dec):
    grids = []
    for count in (8193, 16385, 32769):
        t = np.linspace(-25.0, 3.0, count)
        logp = log_density(t, dec)
        shift = float(logp.max())
        p = np.exp(logp - shift)
        integral = float(simpson(p, x=t))
        cdf = cumulative_trapezoid(p, x=t, initial=0)
        cdf /= cdf[-1]
        quantiles = np.exp(np.interp([0.025, 0.5, 0.975], cdf, t))
        lognorm = float(np.log(integral) + shift)
        grids.append((t, p / integral, cdf, quantiles, lognorm))
        if len(grids) > 1:
            prev = grids[-2]
            norm_error = abs(np.expm1(lognorm - prev[4]))
            qerror = float(np.max(abs(quantiles - prev[3]) / (1 + abs(quantiles))))
            if norm_error < 1e-07 and qerror < 1e-05:
                break
    else:
        raise ValueError('Sigma integration did not converge')
    mode = float(t[np.argmax(p)])

    def integrand(v):
        value = float(log_density(v, dec) - shift)
        if not np.isfinite(value) or value > 700:
            raise ValueError('Unbounded or nonfinite posterior tail')
        return float(np.exp(value))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', IntegrationWarning)
            left, le = quad(integrand, -25.0, mode, epsabs=1e-10, epsrel=1e-09)
            right, re = quad(integrand, mode, 3.0, epsabs=1e-10, epsrel=1e-09)
            tl, tle = quad(integrand, -np.inf, -25.0, epsabs=1e-11)
            tr, tre = quad(integrand, 3.0, np.inf, epsabs=1e-11)
    except IntegrationWarning as exc:
        raise ValueError('Adaptive integration warning') from exc
    tails = (tl + tr) / (left + right)
    tail_upper = (tl + tr + tle + tre) / (left + right)
    quad_estimated_error = (le + re) / (left + right)
    quad_error = abs((left + right) / integral - 1)
    if not np.isfinite([tail_upper, quad_error, quad_estimated_error]).all() or tail_upper >= 1e-08 or quad_error >= 1e-07 or (quad_estimated_error >= 1e-07):
        raise ValueError('Independent quadrature or tail check failed')
    diag = dict(pass_=True, grid_points=len(t), sigma_quantiles=quantiles.tolist(), refinement_norm_error=norm_error, refinement_quantile_error=qerror, adaptive_quad_relative_error=quad_error, outside_tail_mass=tails, quad_estimated_relative_error=quad_estimated_error, outside_tail_upper=tail_upper, inference='Gaussian marginalization + checked one-dimensional quadrature')
    return (t, p / integral, cdf, diag)


def conditional(dec, sigmas):
    sigmas = np.atleast_1d(sigmas)
    k = len(dec['d'])
    den = sigmas[:, None] ** 2 + dec['d'] ** 2
    loc = np.zeros((len(sigmas), 6))
    scales = np.ones_like(loc)
    loc[:, :k] = dec['d'] * dec['a'] / den
    scales[:, :k] = sigmas[:, None] / np.sqrt(den)
    return (loc, scales)


def fit_predict(z, y, zt, center, seed, size=8192):
    dec = decomposition(z, y, center)
    t, density, cdf, diag = posterior_grid(dec)
    rng = np.random.default_rng(seed)
    u = (np.arange(size) + rng.random(size)) / size
    rng.shuffle(u)
    sigma = np.exp(np.interp(u, cdf, t))
    loc, scales = conditional(dec, sigma)
    eta = (loc + scales * rng.normal(size=loc.shape)) @ dec['vt']
    theta = dec['center'] + eta * SCALES
    samples = theta @ zt.T + sigma[:, None] * rng.normal(size=(size, len(zt)))
    sg = np.exp(t)
    gloc, gs = conditional(dec, sg)
    h = zt * SCALES @ dec['vt'].T
    mu = zt @ dec['center'] + gloc @ h.T
    var = gs ** 2 @ (h ** 2).T + sg[:, None] ** 2
    exact_mean = simpson(mu * density[:, None], x=t, axis=0)
    exact_var = simpson((var + mu ** 2) * density[:, None], x=t, axis=0) - exact_mean ** 2
    if not np.isfinite(samples).all() or not np.isfinite(exact_var).all() or (exact_var <= 0).any():
        raise ValueError('Invalid predictive distribution')
    diag.update(exact_log_mean=exact_mean.tolist(), exact_log_variance=exact_var.tolist(), posterior_sigma_mean=float(simpson(sg * density, x=t)), future_noise_included=True)
    return (samples, {'theta': theta, 'sigma': sigma}, diag)
