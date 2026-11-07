# Development status

**Updated:** 7 November 2026
**Phase:** Project B, milestone B1 — protected baseline reconciliation

## Completed on this branch

- Selectively ported PR #18's launchers, compatibility CI, tested dependency target,
  quick start, project metadata and research-run evidence without importing any
  modelling code from the older leakage-prone stack.
- Preserved four disjoint train/calibration/validation/final-test partitions.
- Preserved validation-only probability/ranking selection and final-test-only
  evaluation and portfolio scoring.
- Added explicit applicant-ID regression checks proving the reported portfolio is
  exactly the final test set and excludes train, calibration and validation IDs.
- Pinned all eight direct dependencies used by compatibility CI.

## Tests

- Fresh isolated Python 3.12 baseline: 13 tests passed in 4.164 seconds.
- Python compilation passed and `pip check` reported no broken requirements.
- The tests mutate final-test outcomes and verify that model choice and predictions
  do not change, while final-test metrics do change.

## Known issues and blockers

- No subgroup fairness audit or subgroup uncertainty is implemented yet.
- The real benchmark is one 2005 Taiwan credit-card cohort; transfer and temporal
  validity are not established.
- LGD is assumed and statement balance is an exposure proxy, not observed loss.
- Main has no reviewed visual acceptance, complete documentation, or deployment
  acceptance. Older PRs #9–16 must not be bulk-merged.

## Next three priorities

1. Add subgroup discrimination, calibration and threshold-error diagnostics with
   uncertainty and explicit minimum-sample limitations.
2. Add accessible missingness, segment and expected-loss portfolio diagnostics.
3. Reconcile only safe UI/documentation ideas from the older stack, then perform
   real screenshots, clean-install and deployment rehearsal.

## Remaining before stable release

- Subgroup/fairness evidence without regulatory-compliance claims.
- External or temporal validation, or tightly constrained transfer claims.
- Analyst workflow polish, comprehensive README, screenshots and acceptance tests.
- Security/dependency review and explicit approval before merge or deployment.
