"""Point and prediction-interval metrics for supplied reference observations."""
import numpy as np


def prediction_metrics(reference, median, intervals=None):
    y, p = np.asarray(reference,dtype=float),np.asarray(median,dtype=float)
    if (y.ndim != 1 or y.shape != p.shape or not len(y)
        or not np.isfinite(y).all() or not np.isfinite(p).all() or (y <= 0).any()):
        raise ValueError("Positive references and finite aligned predictions required")
    out = {"mean_relative_absolute_error":float(np.mean(np.abs(p/y-1))),
           "mean_absolute_error":float(np.mean(np.abs(p-y)))}
    if intervals is not None:
        pi = np.asarray(intervals,dtype=float)
        if pi.shape != (len(y),2) or not np.isfinite(pi).all() or (pi[:,0] > pi[:,1]).any():
            raise ValueError("Expected ordered, finite lower/upper interval pairs")
        out.update(coverage=float(np.mean((y >= pi[:,0]) & (y <= pi[:,1]))),
                   mean_interval_width=float(np.mean(pi[:,1]-pi[:,0])))
    return out
