# Development status

**Updated:** 8 November 2026
**Phase:** Project B, milestone B7 — security and dependency hardening

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

## Tests and acceptance

- Fresh project environment: 31 tests passed on Python 3.13.
- Strict dependency audit reported no known vulnerabilities after the constrained
  Streamlit and Pillow upgrade.
- Python compilation passed and `pip check` reported no broken requirements.
- Tests cover final-test isolation, subgroup suppression and uncertainty, portfolio
  reconciliation, drift bins, exports, launcher provenance and Streamlit controls.
- Readiness-gated Chromium captures verify the Portfolio, Drift monitoring and
  Subgroup diagnostics views after real rendering.

## Known issues and blockers

- Subgroup evidence is conditional on one holdout cohort and is not a regulatory
  fairness assessment; temporal evidence remains absent.
- The real benchmark is one 2005 Taiwan credit-card cohort; transfer and temporal
  validity are not established.
- LGD is assumed and statement balance is an exposure proxy, not observed loss.
- No public deployment or private-host rehearsal has been approved. Older PRs #9–16
  must not be bulk-merged.

## Next three priorities

1. Choose and approve a Python-compatible hosting target for a private demo rehearsal.
2. Define production monitoring ownership and timestamped cohort requirements.
3. Obtain external or temporal validation before broadening research claims.

## Remaining before stable release

- Independent review of subgroup/fairness evidence without regulatory-compliance claims.
- External or temporal validation, or tightly constrained transfer claims.
- Private-host deployment rehearsal and operating-owner acceptance.
- Explicit approval remains required before any public or private deployment.
