# Development status

**Updated:** 12 November 2026
**Phase:** Project B, milestone B10 — model governance and release gate

## Completed through this branch

- Selectively ported PR #18's launchers, compatibility CI, tested dependency target,
  quick start, project metadata and research-run evidence without importing any
  modelling code from the older leakage-prone stack.
- Preserved four disjoint train/calibration/validation/final-test partitions.
- Preserved validation-only probability/ranking selection and final-test-only
  evaluation and portfolio scoring.
- Added explicit applicant-ID regression checks proving the reported portfolio is
  exactly the final test set and excludes train, calibration and validation IDs.
- Pinned the direct dependencies used by compatibility and security CI.
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
- Completed clean launcher setup, launcher tests, recorded synthetic research,
  loopback health check and readiness-gated Chromium screenshots.
- Added native financial-dashboard theming and analyst-facing chart labels without
  custom CSS.
- Added bounded HTTPS streaming for the public benchmark, automated vulnerability
  auditing, Dependabot coverage and security/data-boundary documentation.
- Upgraded Streamlit to 1.67 and constrained Pillow 13 after the initial audit found
  published Pillow 12.3 advisories.
- Added a machine-checkable timestamped-cohort boundary, delayed-outcome maturity
  accounting, owned signal routing, a validation CLI and an operating runbook.
- Added a non-root Python 3.13 release container, minimal build context, loopback
  health contract and CI build/start/health/cleanup smoke rehearsal.
- Added an intended-use model card and machine-checkable release gate that verifies
  repository evidence while preserving external validation and approval blockers.

## Tests and acceptance

- Fresh project environment: 46 tests passed on Python 3.13.
- Strict dependency audit reported no known vulnerabilities after the constrained
  Streamlit and Pillow upgrade.
- Python compilation passed and `pip check` reported no broken requirements.
- Tests cover final-test isolation, subgroup suppression and uncertainty, portfolio
  reconciliation, drift bins, timestamped cohort validation, delayed outcomes,
  owned signal routing, exports, launcher provenance and Streamlit controls.
- Readiness-gated Chromium captures verify the Portfolio, Drift monitoring and
  Subgroup diagnostics views after real rendering.

## Known issues and blockers

- Subgroup evidence is conditional on one holdout cohort and is not a regulatory
  fairness assessment; temporal evidence remains absent.
- The real benchmark is one 2005 Taiwan credit-card cohort; transfer and temporal
  validity are not established.
- LGD is assumed and statement balance is an exposure proxy, not observed loss.
- No public deployment or hosted private rehearsal has been approved. The portable
  container rehearsal is CI-only. Older PRs #9–16 must not be bulk-merged.

## Next three priorities

1. Choose and approve an access-controlled container host for a private demo rehearsal.
2. Assign named people to the monitoring owner roles before a private rehearsal.
3. Obtain external or temporal validation before broadening research claims.

## Remaining before stable release

- Independent review of subgroup/fairness evidence without regulatory-compliance claims.
- External or temporal validation, or tightly constrained transfer claims.
- Hosted private deployment rehearsal and operating-owner acceptance.
- Explicit approval remains required before any public or private deployment.
