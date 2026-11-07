# Drift monitoring contract

The dashboard compares the training partition with the untouched final-test partition
using Population Stability Index (PSI). Numeric bin edges are fixed from training
quantiles. Categorical fields include explicit unseen and missing buckets. The score
view compares the fitted model's training and final-test PD distributions.

The table also reports reference/current missingness and the change in missing rate.
PSI signals are labelled below 0.10, 0.10–0.25 and above 0.25 for descriptive triage.
Those common heuristic bands are not pass/fail limits and do not trigger model action.

## Limits

- Both partitions come from the same randomly divided cohort. This is not temporal,
  external or live-production monitoring.
- Training score distributions are in-sample and are used only as a distributional
  reference, not as an unbiased performance estimate.
- PSI identifies distribution differences, not their cause or business impact.
- Input and score stability do not establish stable discrimination, calibration,
  fairness, loss accuracy or lending suitability.
- A production implementation needs timestamped cohorts, delayed-outcome handling,
  data-quality service levels, alert ownership and documented response procedures.
