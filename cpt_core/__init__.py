"""Core numerical tools and benchmark scoring for CPT research."""
from .fusion import fit_predict, niw_update, reference_prior_center, local_calibration

__all__ = ["fit_predict", "niw_update", "reference_prior_center", "local_calibration"]
