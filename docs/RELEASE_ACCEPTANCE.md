# Release acceptance rehearsal

**Rehearsed:** 7 November 2026  
**Baseline:** merged `main` commit `1a0e18f` plus the release-acceptance branch

## Completed checks

- Created a fresh repository-local environment through `launch.py setup` using
  Python 3.12 and `requirements-tested.txt`.
- Ran all 26 tests through `launch.py tests`; all passed.
- Ran `pip check`; no broken dependencies were reported.
- Ran `launch.py research --dataset synthetic`; the workflow completed and wrote a
  timestamped manifest, dependency inventory, execution log and changed artifacts.
- Started the dashboard on loopback port 8507 and received HTTP 200.
- Used a real Chromium renderer with readiness checks for the page title and
  held-out-applicant metric before capturing the Portfolio view.
- Navigated the rendered app and captured the Drift monitoring and Subgroup
  diagnostics views after their headings became visible.

## Evidence

- `screenshots/portfolio-release.png`
- `screenshots/drift-release.png`
- `screenshots/subgroup-release.png`

The screenshots use the synthetic demonstration. They verify rendering and workflow,
not empirical lending performance. The UCI source still requires network access and
remains a single historical cohort.

## Deployment position

No public deployment was created. The application is ready for a Python-compatible
Streamlit host rehearsal, but release approval still requires an explicit hosting
choice, secrets/data review, and confirmation that only non-sensitive demonstration
data will be exposed.
