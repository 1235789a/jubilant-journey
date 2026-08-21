# Roadmap

## V1 four-day build mapping

### Day 1 — Core OS: complete

Registries, schema, queue, Rule Engine, Router, audit, credentials boundary, Kill Switch, circuit breaker, adapter interface, dashboard skeleton, CI, and 31 seed records.

### Day 2 — Browser extension chain: complete at P2

One Manifest V3 source produces Chrome, Edge, and Firefox variants; packages include manifests, zip builds, metadata, validation, and human publish plans.

### Day 3 — International ebook chain: complete at P2

Markdown plus metadata produces EPUB 3 packages for KDP and Draft2Digital with AI/exclusivity review fields and aggregator-aware routing.

### Day 4 — Batch and resilience: complete for V1

3+ asset batching, retry/backoff, DLQ, circuit isolation, Kill Switch, Human Queue, token and human-time schemas, health, analytics, duplicate protection, HTTP dashboard, and failure tests.

## Next 10 tasks

1. Perform a complete official-rule review for itch.io and build a P1/P2 low-cost game package adapter.
2. Add a domestic-web-novel vertical adapter that packages chapters/metadata only; keep every platform P0 until contract and AI rules are current.
3. Add a rule-evidence history table and dashboard diff for policy changes.
4. Add SQLite online backup/restore commands and a restore drill test.
5. Add scheduled local health/metric jobs with jitter and a strict rate-limit budget.
6. Connect the existing Facebook workflow through `FacebookConnector` for schedule/log/metric import only.
7. Add token-provider importers so Codex/API usage is recorded automatically instead of manually.
8. Add per-vertical Yield Score weights and consecutive-period recommendation history.
9. Add authenticated remote dashboard mode only if remote access becomes necessary.
10. Select one platform for a separately authorized P3 design review after the operator is legally eligible and every account/policy requirement is satisfied.

## Explicitly deferred

Live publication, account creation, identity verification, captcha handling, contracts, tax, payouts, payment, public hosting, automatic project deletion, and 26 non-pilot adapters are not hidden TODOs; they are deliberately blocked or planned work.
