"""Risk metrics for complete integer-cost probability distributions."""
import numpy as np


def risk_metrics(pmf, alpha=0.9, overflow=0.):
    """Reject a truncated distribution: small tail mass alone bounds no tail mean."""
    p = np.asarray(pmf, dtype=float)
    if not 0 < alpha < 1:
        raise ValueError('alpha must lie in (0,1)')
    if p.ndim != 1 or not np.all(np.isfinite(p)) or np.any(p < 0):
        raise ValueError('invalid PMF')
    if overflow != 0 or not np.isclose(p.sum(), 1., atol=1e-10, rtol=0):
        raise ValueError('complete PMF required; increase cutoff or bound residual costs')
    z = np.arange(len(p))
    var = int(np.searchsorted(np.cumsum(p), alpha-1e-12))
    cvar = var + float(np.dot(np.maximum(z-var, 0), p))/(1-alpha)
    return dict(mean=float(z@p), var=var, cvar=cvar)
