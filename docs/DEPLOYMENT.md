# Deployment

## Recommended V1: local

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
distribution-os init
distribution-os demo
distribution-os serve
```

The zero-dependency server listens on `127.0.0.1:8787`. Install `.[web]` for FastAPI/OpenAPI. Keep `data/`, `platform_ready/`, and `.env` outside version control.

Configure the host OS to run `distribution-os tick` daily. This avoids an always-on scheduler process and remains portable across cron, launchd, and Windows Task Scheduler.

## Docker

```bash
docker build -t distribution-os:v1 .
docker run --rm -p 127.0.0.1:8787:8787 \
  -v "$PWD/data:/app/data" \
  -v "$PWD/platform_ready:/app/platform_ready" \
  distribution-os:v1
```

The image runs as an unprivileged user and preserves the safety defaults. Do not add secrets to the image or Dockerfile.

## GitHub

The repository CI validates JSON, compiles Python, runs the complete test suite, and checks dashboard JavaScript. GitHub is source deployment, not proof of a public production service. This V1 intentionally does not create paid hosting, public DNS, marketplace accounts, or external cloud resources.

## Remote dashboard

Remote hosting is not recommended until authentication, TLS, CSRF protection, secure secret storage, encrypted backups, access logs, and network restrictions are added. Never expose the built-in server directly to the public internet.

## Environment safety

Production-style environments must still start with:

```text
DRY_RUN=true
REAL_PUBLISHING=false
REVIEW_LEVEL=L0
```

Changing those variables alone can never produce live publication in V1 because all platforms have `live_publish=false` and all adapters are below P3.
