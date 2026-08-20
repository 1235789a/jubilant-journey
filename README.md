# Distribution OS V1

Local-first operating system for producing, adapting, packaging, measuring, and reviewing a portfolio of internet assets across policy-compliant distribution channels.

> Safety defaults: `DRY_RUN=true`, `REAL_PUBLISHING=false`, `REVIEW_LEVEL=L0`.

## What works in V1

- SQLite registries for verticals, assets, platform rules, platforms, accounts, variants, publications, jobs, metrics, experiments, reviews, audit events, token usage, and health.
- Rule engine and router with age, region, policy, exclusivity, payout, quality, duplicate, kill-switch, and circuit-breaker gates.
- Idempotent lightweight job queue with retry backoff and a dead-letter state.
- P2 dry-run adapters for Chrome, Edge, Firefox, Amazon KDP, and Draft2Digital.
- Two end-to-end examples: a Manifest V3 browser extension and an EPUB 3 ebook.
- FastAPI control API and a responsive operator dashboard.
- Platform-isolated health monitoring, human queue, token/human-time accounting, and audit log.
- Idempotent daily maintenance tick plus verified online SQLite backup and non-secret export.
- 31-platform seed registry. No live publishing adapter is enabled.

## Quick start

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
cp .env.example .env
distribution-os init
distribution-os demo
distribution-os tick
distribution-os serve
```

Open <http://127.0.0.1:8787>. The demo writes publish-ready packages under `platform_ready/` but never uploads them.

The base install has no third-party runtime dependencies and uses the built-in HTTP server. For FastAPI/OpenAPI support, install `pip install -e '.[web]'`; the CLI selects it automatically.

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Documentation

- [Architecture](ARCHITECTURE.md) and [decisions](DECISIONS.md)
- [Runtime rules](RULES.md) and [security](docs/SECURITY.md)
- [Platform Registry](docs/PLATFORM_REGISTRY.md) and [Adapter Guide](docs/ADAPTER_GUIDE.md)
- [Operations](docs/OPERATIONS.md), [deployment](docs/DEPLOYMENT.md), and [testing](docs/TESTING.md)
- [Roadmap](docs/ROADMAP.md) and [V1 report](docs/V1_REPORT.md)

Read the safety documents before changing publishing settings.
