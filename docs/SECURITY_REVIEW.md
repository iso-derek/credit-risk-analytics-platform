# Security and data-boundary review

**Reviewed:** 8 November 2026

## Attack surface

The Streamlit UI accepts only bounded selection and numeric widgets. It has no file
upload, arbitrary URL input, SQL connection, authentication flow, secret, email or
third-party write integration. Export buttons return in-memory CSV or ZIP artifacts.

The only application-initiated network request is the optional public UCI benchmark.
Its URL is fixed in source and HTTPS-only. The response is streamed with connection
and read timeouts, checked against declared size before iteration, and aborted if the
accumulated body exceeds 15 MB. The SHA-256 digest is retained in study metadata.

The launcher executes fixed argument lists without a shell. Research-only extra
arguments are parsed by the downstream CLI; other launcher modes reject extras.

## Dependency controls

- Direct reproducibility dependencies remain pinned in `requirements-tested.txt`.
- Compatibility CI installs that exact target and runs `pip check` and the test suite.
- Dependency-security CI installs pinned `pip-audit==2.10.1` and audits the tested
  requirement target on pushes, pull requests, manual runs and a weekly schedule.
- Dependabot monitors both Python packages and GitHub Actions.

The first audit during this review reported Pillow 12.3.0 advisories fixed in 13.0.0.
The tested target was upgraded from Streamlit 1.65 to 1.67, whose Pillow constraint
allows 13.x, and Pillow 13.0.0 was added explicitly to the tested target. The audit
then passed with no known vulnerabilities reported. This history is retained rather
than silently presenting the first scan as clean.

## Residual risks

- Transitive dependencies are resolved at install time rather than hash-locked.
- GitHub Actions are referenced by major version tags, not immutable commit hashes.
- The public dataset host, certificate chain and upstream content remain external
  dependencies; a size cap and digest do not authenticate research meaning.
- There is no application authentication or authorization because no private-host
  deployment has been approved.
- Downloaded exports can be redistributed outside the application boundary.
- Vulnerability databases are incomplete and can change after a passing audit.

## Deployment gate

Before any hosted demo, select a Python-compatible host, restrict the app to synthetic
or approved public data, review access/logging/retention, define an operating owner,
and rerun dependency and compatibility checks from the release commit.

The release container runs as a non-root user, copies no local data or evidence
folders, and is smoke-tested through the loopback Streamlit health endpoint. TLS,
authentication, network policy and secret management remain host responsibilities.
