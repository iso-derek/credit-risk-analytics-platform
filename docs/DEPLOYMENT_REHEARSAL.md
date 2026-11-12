# Private deployment rehearsal

The repository now includes portable container packaging for a Python-compatible
host. It does not create a public deployment, authentication layer, private-data
connection or paid cloud resource.

## Release image contract

- Python 3.13 and the exact `requirements-tested.txt` dependency target.
- Only application, theme, source and non-secret configuration files are copied.
- The process runs as the unprivileged `app` user on port 8502.
- Streamlit telemetry is disabled and the server runs headless.
- Docker checks Streamlit's loopback `/_stcore/health` endpoint.
- CI builds the image, proves the runtime UID is not root, starts it, waits for
  health, captures logs and removes the container.

## Local rehearsal

With Docker installed:

```bash
docker build --tag credit-risk-app:local .
docker run --rm --publish 127.0.0.1:8502:8502 credit-risk-app:local
```

Open `http://127.0.0.1:8502`. Binding the host side to `127.0.0.1` keeps the local
rehearsal off other network interfaces.

## Approval gate

Before hosting, the owner must choose an access-controlled Python container service;
assign named model-risk, data-quality and engineering owners; approve logging and
retention; restrict data to synthetic or approved public sources; configure TLS and
authentication outside the container; and repeat compatibility, security and health
checks from the exact release commit.

The image is not approved for private applicant data or production lending decisions.
Passing health and vulnerability checks demonstrates technical readiness only, not
model validity, privacy compliance or operational acceptance.
