# Subgroup diagnostics

The dashboard reports conditional model diagnostics for supported segments in the
untouched final-test cohort. For the UCI benchmark, `SEX`, `EDUCATION`, `MARRIAGE`
and an age band are retained for evaluation but are not model predictors. For the
synthetic demonstration, the available operational groupings are employment,
home ownership, loan purpose and age band.

For each sufficiently large group containing both observed outcomes, the audit
reports applicant and default counts, mean predicted PD, observed default rate,
Brier score, ROC-AUC, calibration gap, high-risk flag rate, true- and false-positive
rates, and precision at the selected threshold. The observed rate and calibration
gap include 95% applicant-level bootstrap intervals.

## Interpretation limits

- Results are conditional on the fitted model and this final-test cohort. The
  bootstrap does not include model-refitting, temporal or dataset-shift uncertainty.
- Groups below the selected minimum size and groups with only one observed outcome
  are suppressed rather than assigned unstable or undefined performance metrics.
- Threshold diagnostics describe errors at a research threshold; they do not set an
  approval policy and do not incorporate utility, affordability or legal criteria.
- Excluding a demographic field from predictors does not establish fairness because
  other inputs can act as proxies and historical outcomes can encode disparities.
- These diagnostics are not a regulatory fairness assessment, causal analysis,
  production validation or compliance certification.

The downloadable CSV records both reported and suppressed groups so limitations
remain visible in downstream review.

## Intersectional view

The optional second grouping field combines two supported evaluation dimensions.
The same minimum-size and two-outcome suppression rules apply to every intersection.
Sparse combinations therefore remain visible as suppressed rows instead of receiving
unstable metrics. This is exploratory evidence, not proof that unreported or
suppressed intersections perform equivalently.
