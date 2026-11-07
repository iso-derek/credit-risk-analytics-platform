# Security policy

## Supported scope

Security fixes are applied to the latest `main` branch. This educational application
is not approved for production lending decisions or storage of private applicant data.

## Reporting a vulnerability

Use GitHub private vulnerability reporting for this repository when available. Do not
open a public issue containing exploit details, secrets, personal data or unpublished
vulnerability information.

Include the affected commit, reproduction steps, impact, and any suggested mitigation.
No bounty or response-time commitment is offered.

## Data boundary

- The default dataset is generated locally and is synthetic.
- The optional public dataset is downloaded from a fixed HTTPS UCI URL with connection
  and read timeouts, an early content-length check, and a hard 15 MB streaming cap.
- The dashboard has no upload control, login system, database or secret requirement.
- Downloaded dashboard exports can contain applicant-level synthetic or public-cohort
  rows. Review them before sharing and never substitute private applicant data.
- Public deployment requires a separate privacy, hosting and access-control review.

## Automated checks

Compatibility tests run on Python 3.12 and 3.13 on Windows and Ubuntu. A separate
weekly and pull-request workflow audits `requirements-tested.txt` with pinned
`pip-audit`. Dependabot monitors Python and GitHub Actions dependencies.

An audit finding requires investigation; the absence of a published advisory does not
prove the application or dependency set is secure.
