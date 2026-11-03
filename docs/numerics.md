# Numerical interfaces

## Calibrated fusion

`fit_predict(calibration_predictions, reference_strengths, target_predictions)` takes:

- A positive `n x m` matrix of candidate-method predictions at reference points.
- The `n` measured reference strengths.
- A positive `k x m` matrix at target points, with the same method-column order.

All strengths are in kPa. Reference observations enter calibration only. Method
selection and measurement-to-formula mapping are supplied by the caller.

Errors are `log(method_prediction / reference_strength)`. The default
normal-inverse-Wishart prior has mean strength `kappa0 = 1`, covariance degrees of
freedom `nu0 = m + 5`, log-error scale `0.5`, and cross-method correlation `0.5`.
The posterior predictive distribution is Student-t. The solver minimizes predictive
error variance under nonnegative weights summing to one. It enumerates active sets
and checks the Karush-Kuhn-Tucker conditions; it accepts up to 12 methods.

Outputs contain predictive medians, 90% and 95% intervals, weights, log locations,
scale, degrees of freedom and posterior parameters. Intervals integrate error-mean
and covariance uncertainty conditional on the supplied inputs, method combination
and fitted weights. Method-selection and weight-decision uncertainty are not
separately propagated.

## Reference prior and cone-factor calibration

`reference_prior_center` uses supplied method predictions, net cone resistance and
a source-supported reference cone factor to calculate the error-prior center. Its
inputs can include reference and target CPT measurements but no target strength
labels. A reference value is provided by the caller after checking its source and
applicability; this package does not select a regional recommendation automatically.

To examine its incremental effect, compute the reference center for the same
method columns used in the zero-center comparison. The reference changes the prior
center, followed by a fresh calibration and weight calculation. It is not a hard
bound on the predicted strengths.

`local_calibration` estimates one factor from the geometric mean of reference
`qnet / strength` values. For fixed reference predictions, supply `qnet / factor`
directly. For a reference relation with a local probabilistic update, supply that
single prediction column to `fit_predict` with a zero prior center.

## Data-only Bayesian regression kernel

`cpt_core.regression.fit_predict` implements Gaussian coefficient marginalization
and checked one-dimensional quadrature over the residual standard deviation. Supply
a six-column design matrix (intercept plus five standardized predictor slots),
centered log reference strengths, target design matrix, zero prior center, and seed.
Coefficient prior standard deviations are `(2, 0.5, 0.5, 0.5, 0.5, 0.5)` and the
residual standard deviation has a half-normal prior of scale `0.5`.

The caller supplies preprocessing. In the study, site input variables were
standardized using the known reference and target inputs, and the response center
used reference strengths only. Predictor choices differ with available measurements;
the generic kernel does not choose or reconstruct these site configurations.
The function returns centered log-predictive samples including future residual
noise. Add the reference response center before exponentiating.

## Evaluation

`prediction_metrics` computes mean relative absolute error, mean absolute error,
interval coverage and mean width on supplied evaluation labels. Returned errors
and coverage are fractions rather than percentages. Group/repetition aggregation
must be applied according to the experiment being analyzed.

The synthetic example is an API demonstration. Original site data, candidate
method caches and the complete experimental runners are outside this package.
