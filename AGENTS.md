# AGENTS.md — Distribution OS

This file is the operating contract for every coding agent entering this repository. Read it before editing anything.

## 1. Mission

Distribution OS is a local-first operating system for a personal entrepreneur to produce, adapt, package, distribute, measure, and review a portfolio of legitimate internet assets. Its advantage is more products across more policy-compatible platforms at lower marginal cost—not duplicate personal accounts, fake engagement, or policy evasion.

The shared abstractions are `Vertical`, `Platform`, `Account`, `Asset`, `Variant`, `Adapter`, `Publication`, `Job`, `Metric`, `Rule`, `Credential`, `Review`, and `Experiment`. Do not build a separate mini-system per vertical.

## 2. Non-negotiable safety state

V1 must remain:

```text
DRY_RUN=true
REAL_PUBLISHING=false
REVIEW_LEVEL=L0
GLOBAL_PUBLISH_ENABLED=false
DUPLICATE_PERSONAL_ACCOUNTS=false
ONE_PLATFORM_ONE_PUBLISHER=true
MULTI_CHANNEL=PLATFORM_NATIVE_ONLY
```

No agent may silently relax these defaults. A platform cannot perform a live action unless its rule state is `VERIFIED`, its adapter is P3, its own `live_publish` flag is true, every account/age/region/payout/policy/exclusivity/quality/duplicate gate passes, the circuit is closed, global publishing is enabled, and the review policy permits the action. V1 intentionally has no P3 adapters and no enable endpoint.

## 3. Minor-user constraints

The operator is currently underage. Never:

- falsify an age, identity, address, tax fact, publisher entity, or guardian relationship;
- bypass identity verification, account limits, payment requirements, contracts, captcha, security controls, or age gates;
- register duplicate personal accounts or create an account farm;
- use a guardian's identity without a platform-supported, real guardian process;
- represent a prepared package as a submitted or approved listing.

When a platform requires majority age, return `BLOCKED_BY_AGE` or `GUARDIAN_REQUIRED`. Development, local testing, metadata preparation, and dry-run packaging may continue when policy permits. Registration, identity, contracts, tax, payout, fees, and final submission go to Human Queue.

## 4. Forbidden features

Reject any request to add bulk false registration, captcha bypass, fingerprint spoofing, IP disguise, fake downloads, fake reviews, fake likes, fake comments, rank manipulation, moderation evasion, AI-detection evasion, contract avoidance, or exclusivity circumvention. If a vertical only works with such behavior, mark it `REJECT`.

## 5. Architecture

- `src/distribution_os/application.py`: composition root.
- `models.py`: canonical enums and dataclasses.
- `database.py`: SQLite schema and migrations.
- `registry.py`: asset/platform/account/publication/metric/experiment/review repositories.
- `router.py`: fail-closed hard gates and route decisions.
- `jobs.py`: durable idempotent queue, backoff, recovery, DLQ.
- `adapters/`: only platform-specific transformation behavior.
- `distribution.py`: route → adapter → publication orchestration.
- `safety.py`: global kill switch and per-platform circuit breaker.
- `health.py`: rule freshness, circuit, adapter, and stuck-job checks.
- `scheduler.py` / `worker.py`: idempotent daily maintenance and central job dispatch.
- `analytics.py`: metric aggregation, token/human cost, Yield Score advice.
- `api.py`: optional FastAPI transport.
- `stdlib_server.py`: zero-dependency dashboard/API transport.
- `dashboard/`: operator UI only; no policy logic belongs here.
- `config/platforms.json`: seed facts and official documentation references.
- `config/verticals.json`: initial vertical evaluator inputs and pilot caps.

Core code must not import a concrete marketplace SDK. Platform changes belong in Registry data or a Platform Adapter.

## 6. Adapter contract

Every adapter subclasses `PlatformAdapter` and implements at least:

```text
validate
prepare
generate_metadata
check_policy
check_duplicates
estimate_cost
publish
update
unpublish
fetch_metrics
health_check
```

Methods that are not supported return `AdapterResult(status="NOT_SUPPORTED")`; never fake success. Package output belongs under:

```text
platform_ready/<platform>/<asset_id>/<asset_version>/
```

Every package includes the artifact, metadata, validation result, and `PUBLISH_PLAN.md` stating that no upload occurred. Use one master source plus transforms; do not fork three whole repositories for three browser stores.

Adapter maturity must be honest:

- P0: registry only
- P1: deterministic package generation
- P2: automated dry-run validation and package generation
- P3: live publishing

Changing maturity requires tests, documentation, current official rule evidence, and explicit review. P3 additionally requires an explicit user authorization project; it is not a routine refactor.

## 7. Data and idempotency

SQLite is authoritative. Preserve schema compatibility and add small migrations in `Database.initialize()` when changing an existing table. Do not place secrets in JSON payloads.

Publication identity is:

```text
content_hash + platform_id + account_id + asset_version
```

Job idempotency keys must include the logical operation, asset, platform, account/dry-run identity, asset version, and source hash. An agent restart must not duplicate a chapter, listing, or release.

`WIDE`, `EXCLUSIVE`, `HYBRID`, and `UNDECIDED` are explicit asset values. Never infer `WIDE` merely because multiple platforms are registered. Contract-specific exclusivity always wins.

## 8. Credentials and audit

Database and source may store only `credential_reference`. Real secrets resolve through `CredentialProvider` from environment variables or a future secret manager. Never log raw headers, cookies, OAuth tokens, refresh tokens, API keys, passwords, or sessions. Use recursive `redact()` before audit output.

Every material action needs an audit event with actor, timestamp, action, target, reason, redacted input, output, token usage where observable, and result.

## 9. Jobs and failure behavior

All operational work is a `Job`. Supported statuses include pending, running, success, retrying, waiting-human, blocked, cancelled, and dead-letter. Retries use exponential backoff. A platform failure increments only that platform's circuit. Do not make Chrome failure pause ebooks or GEO analytics.

The global kill switch cancels pending/retrying publish jobs only. Generation and analytics remain available.

Daily maintenance uses a date-keyed `HEALTH_CHECK` job and is safe to invoke repeatedly from cron/Task Scheduler. Do not create in-process daemon scheduling when an OS timer is sufficient.

## 10. Platform rules

Use primary official sources. A checked documentation URL is not equivalent to a fully verified account/product/country/contract rule set. Unknown facts stay `UNVERIFIED`; stale facts become `OUTDATED`/`RULE_OUTDATED`; ambiguous real actions go to `REVIEW_REQUIRED`.

Update `config/platforms.json` and rule evidence instead of hard-coding marketplace facts into core logic. `last_verified_at` must mean an actual review occurred; do not stamp it merely to silence health warnings.

## 11. Coding conventions

- Python 3.12, standard library first, type hints on public boundaries.
- Keep modules small and dependency direction inward: transport → services → core/repository.
- Prefer explicit enums and dataclasses over magic strings at core boundaries.
- Use UTC ISO-8601 timestamps.
- Use `pathlib.Path`; validate paths before deletion or replacement.
- Keep live network mutations out of unit tests.
- No unnecessary framework, queue, cache, or cloud dependency.
- Comments explain constraints and decisions, not obvious syntax.
- Do not edit generated `platform_ready/` output by hand.

## 12. Testing requirements

Run before every handoff:

```bash
make check
```

At minimum, changes to core behavior must cover:

- Router and Rule Engine hard gates;
- hash/idempotency and duplicate publications;
- Platform Score / Vertical Evaluator / Yield Score math;
- adapter validation and deterministic package output;
- queue claim, backoff, DLQ, stuck recovery;
- age, region, exclusivity, payout, credential, and policy failures;
- circuit isolation and global kill switch;
- two different vertical end-to-end dry runs;
- actual dashboard HTTP and API response.

Mocks must be visibly labeled `MOCK` and must never be described as live performance.

## 13. Documentation requirements

When behavior changes, update the relevant file among `README.md`, `DECISIONS.md`, `ARCHITECTURE.md`, `RULES.md`, and `docs/`. If a platform fact changes, update the platform record, evidence URL, verification date, notes, and tests if routing changes.

## 14. Definition of Done

A change is done only when:

1. It uses shared core abstractions and does not fork a vertical-specific OS.
2. Safety defaults remain fail-closed.
3. No secret or identity data entered source, prompts, logs, fixtures, or SQLite.
4. Unsupported actions say `NOT_SUPPORTED`, `REVIEW_REQUIRED`, or a precise block state.
5. Idempotency, audit, failure isolation, and human escalation are preserved.
6. Relevant unit, integration, and failure tests pass.
7. The dashboard/API reports the new state honestly.
8. Documentation and Registry evidence are current.
9. `git diff --check` and `make check` pass.
10. The final handoff distinguishes implemented, stubbed, and blocked work.
