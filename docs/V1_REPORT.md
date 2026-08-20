# Distribution OS V1 Report

Report date: 2026-08-19

## Outcome

V1 is a runnable safety-first Distribution OS, not an auto-posting script. It manages shared assets, platforms, accounts, jobs, publications, metrics, experiments, human reviews, audits, token usage, health, rules, and adapters in one local control plane.

## Completed and runnable

- 31-platform seed Registry with complete merged runtime objects and primary official documentation links.
- Vertical, Platform, Rule, Asset, Account, Variant, Publication, Metric, Experiment, Review, Audit, token, human-time, circuit, health, and settings persistence.
- Fail-closed Rule Engine and Platform Router.
- Transactional SQLite Job Queue with idempotency, exponential backoff, stuck recovery, DLQ, and priority.
- SHA-256 duplicate protection plus a unique Publication identity.
- Global Kill Switch and isolated per-platform circuit breakers.
- Credential reference/provider boundary and recursive log redaction.
- Platform Score, Vertical Evaluator, Yield Score, and recommendation primitives.
- Human Queue with L0 default and durable asset/platform-scoped approval validation for any future live route.
- Health checks for rule freshness, adapter declarations, circuits, and stuck/failed jobs.
- Date-keyed daily maintenance jobs and a central fail-closed worker dispatcher.
- Online SQLite backup with integrity verification and SHA-256 output, plus JSON data export.
- Responsive Dashboard with Overview, Assets, Platforms, Accounts, Jobs, Publications, Analytics, Experiments, Human Queue, Rules, Health, Logs, and Settings.
- Zero-dependency HTTP runtime plus optional FastAPI/OpenAPI transport.
- Dockerfile and GitHub Actions CI.

## End-to-end dry-run chains

### Browser extension

One Manifest V3 master source produces three deterministic packages:

- Chrome Web Store — P2
- Microsoft Edge Add-ons — P2
- Firefox Add-ons — P2

Each package contains the adapted build, upload zip, metadata, validation, and manual publish plan.

### International ebook

One Markdown manuscript plus retailer-neutral metadata produces EPUB 3 packages for:

- Amazon KDP — P2
- Draft2Digital — P2

The adapter rejects a `WIDE` asset enrolled in KDP Select and treats Draft2Digital as one aggregator rather than duplicating downstream store jobs.

## Not implemented or intentionally blocked

- Live publishing: no P3 adapter exists.
- 26 platforms are Registry-only P0.
- Account registration, identity, guardian, captcha, security challenge, contracts, tax, payout, fees, and final submission are Human Queue/manual.
- Facebook workflow logic is not reinvented; only a connector interface exists.
- Automatic `KILL` does not execute; the system emits advice only.
- Remote authenticated hosting, PostgreSQL, remote secret manager, and remote rollback are deferred.

## Platform coverage

| Maturity | Count | Meaning |
|---|---:|---|
| P0 | 26 | Registry only |
| P1 | 0 | No package-only intermediate adapter claimed |
| P2 | 5 | Automated local validation and dry-run package |
| P3 | 0 | No live publication |

Full 31-row matrix: [PLATFORM_REGISTRY.md](PLATFORM_REGISTRY.md).

## Vertical coverage

| Vertical | V1 state | Pilot count |
|---|---|---:|
| 国内网文 | Registry/evaluator; rules need review | 0 |
| 国际电子书 | End-to-end P2 | 1 |
| 浏览器插件 | End-to-end P2 across three stores | 1 |
| 开发者插件 / 工具 | Registry/evaluator | 0 |
| B2B SaaS 生态应用 | Registry/evaluator | 0 |
| App | Disabled pending age/account review | 0 |
| 游戏 / 小游戏 | Registry/evaluator; itch.io recommended next | 0 |
| 数字素材 / 游戏资产 | Registry/evaluator | 0 |
| GEO / AI Search brand | Five attention channels registered; connector work deferred | Brand mainline |

The system does not manufacture 24 low-quality pilots merely to meet a maximum.

## Architecture

The system is a modular monolith: transport and Dashboard call services; services call Registry/Router/Queue; adapters contain platform differences; SQLite owns durable state. New products require data only. New platforms require config plus an adapter. New verticals require config plus genuinely new transformation logic. Core policy remains shared.

## Test result

Final local suite: 37/37 passing.

Validated areas include unit, adapter, integration, actual HTTP, and failure behavior: 31 Registry records, two different verticals, five packages, three-asset batching, duplicate protection, exclusivity, age, missing credentials, stale rules, adapter failure, retry, DLQ, circuit isolation, Kill Switch, EPUB structure, browser manifest variants, and redaction.

## Safety state

```text
DRY_RUN=true
REAL_PUBLISHING=false
REVIEW_LEVEL=L0
GLOBAL_PUBLISH_ENABLED=false
PLATFORM live_publish=false for all 31
P3 adapters=0
```

Even a mistaken environment-variable change cannot publish in V1 because platform and adapter hard gates still fail.

## Token accounting

Runtime token schema and dashboard ratios are implemented: total tokens, tokens/asset, tokens/publication, and tokens/revenue. Provider, model, task, input, output, cached tokens, estimated cost, asset, and job are supported.

The internal ChatGPT/Codex token usage of this build session is not exposed to the repository process, so V1 reports it as **not observable**, not zero. No estimate was fabricated. The demo records zero token usage because its two adapters are deterministic local transformations without model calls.

## Human time

Human-time schema and per-job/asset recording are implemented. The build session was not tracked from its first minute, so construction time is **not retroactively claimed**. Demo metric rows contain 20 mock human minutes in total and are visibly marked `MOCK`; they are not actual operating labor.

## Technical debt

- FastAPI and standard-library transports currently expose parallel endpoint wrappers; consolidate them behind one response service as endpoints grow.
- SQLite JSON payload migrations are intentionally lightweight; formal numbered migrations are needed before multi-user deployment.
- Health checks validate configured state, not remote credential/API health, because no live integration is authorized.
- EPUB generation supports the V1 manuscript structure, not every Markdown feature, image, footnote, or accessibility case.
- Browser packages still require real browser runtime testing and final privacy/listing assets.
- Rule evidence has no historical diff table yet.
- Yield weights are global defaults; vertical-specific calibration needs real data.
- Backup creation is tested; restore remains an explicit manual recovery procedure and still needs a scripted restore drill.

## Next 10 tasks

1. Verify itch.io rules completely and implement the next P1/P2 low-cost game package adapter.
2. Add domestic-web-novel chapter/metadata packaging without platform publication.
3. Add rule evidence history and policy diffs.
4. Add a guarded restore command and automated restore drill.
5. Add metric jobs only when an authorized adapter exists, with strict rate budgets.
6. Connect the existing Facebook workflow through the connector boundary.
7. Import actual Codex/API token records automatically.
8. Calibrate per-vertical Yield weights with real outcomes.
9. Add authenticated remote access only if needed.
10. Consider one P3 platform only after legal eligibility, full rule verification, explicit authorization, sandbox reconciliation, rollback, and security review.
