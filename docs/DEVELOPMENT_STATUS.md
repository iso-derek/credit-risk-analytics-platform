# Development status

**Updated:** 7 November 2026
**Phase:** Project B, milestone B5 — reference-to-holdout drift contracts

## Completed through this branch

- Selectively ported PR #18's launchers, compatibility CI, tested dependency target,
  quick start, project metadata and research-run evidence without importing any
  modelling code from the older leakage-prone stack.
- Preserved four disjoint train/calibration/validation/final-test partitions.
- Preserved validation-only probability/ranking selection and final-test-only
  evaluation and portfolio scoring.
- Added explicit applicant-ID regression checks proving the reported portfolio is
  exactly the final test set and excludes train, calibration and validation IDs.
- Pinned all eight direct dependencies used by compatibility CI.
- Added final-test-only subgroup discrimination, calibration and threshold-error
  diagnostics with deterministic applicant-bootstrap uncertainty.
- Added explicit suppression for small groups and groups with only one observed
  outcome, plus downloadable audit output and interpretation limits.
- Kept UCI demographic evaluation fields outside the model predictor contract.
- Added raw held-out predictor missingness before pipeline imputation.
- Added reconciling segment exposure and expected-loss shares with descriptive HHI
  concentration measures and explicit assumption limits.
- Added optional two-field subgroup intersections under the existing minimum-size
  and two-outcome suppression contract.
- Added fixed-reference PSI for predictors and scores, explicit unseen/missing
  buckets, missing-rate deltas and non-production interpretation limits.

## Tests

- Fresh isolated Python 3.12 baseline: 13 tests passed in 4.164 seconds.
- Python compilation passed and `pip check` reported no broken requirements.
- The tests mutate final-test outcomes and verify that model choice and predictions
  do not change, while final-test metrics do change.

## Known issues and blockers

- Subgroup evidence is conditional on one holdout cohort and is not a regulatory
  fairness assessment; intersectional and temporal evidence remain absent.
- The real benchmark is one 2005 Taiwan credit-card cohort; transfer and temporal
  validity are not established.
- LGD is assumed and statement balance is an exposure proxy, not observed loss.
- Main has no reviewed visual acceptance, complete documentation, or deployment
  acceptance. Older PRs #9–16 must not be bulk-merged.

## Next three priorities

1. Reconcile only safe UI/documentation ideas from the older stack.
2. Perform real screenshots, clean-install and deployment rehearsal.
3. Define production monitoring ownership and timestamped cohort requirements.
   real screenshots, clean-install and deployment rehearsal.

## Remaining before stable release

- Subgroup/fairness evidence without regulatory-compliance claims.
- External or temporal validation, or tightly constrained transfer claims.
- Analyst workflow polish, comprehensive README, screenshots and acceptance tests.
- Security/dependency review and explicit approval before merge or deployment.
