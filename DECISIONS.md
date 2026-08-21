# Distribution OS V1 — Architecture Decisions

Date: 2026-08-19

## D-001: Modular monolith, not microservices

Use one Python application with clean module boundaries. It runs locally, costs almost nothing when idle, and remains portable. Platform adapters are plug-ins behind a stable interface; a platform failure cannot require a core rewrite.

## D-002: Python 3.12 + standard-library HTTP/FastAPI + SQLite

The base runtime has no third-party dependency and serves the dashboard with Python's HTTP server; an optional FastAPI extra provides a typed OpenAPI transport. SQLite is the system of record in V1, with repositories and JSON payload boundaries that can later move to PostgreSQL. No Redis, Kubernetes, or message broker is required.

## D-003: Durable database queue

Jobs live in SQLite. Claims are transactional, idempotency keys are unique, retries use exponential backoff, and terminal failures enter `DEAD_LETTER`. This is sufficient for one operator and dozens—not millions—of jobs.

## D-004: Safety is fail-closed

Initial settings are immutable-by-default safety controls:

- `DRY_RUN=true`
- `REAL_PUBLISHING=false`
- `REVIEW_LEVEL=L0`
- `DUPLICATE_PERSONAL_ACCOUNTS=false`
- `ONE_PLATFORM_ONE_PUBLISHER=true`
- `MULTI_CHANNEL=PLATFORM_NATIVE_ONLY`

Live publication needs all of: global publishing enabled, platform live flag enabled, a `VERIFIED` rule state, a healthy account, adult/guardian eligibility, valid payout readiness, no exclusivity conflict, no duplicate, minimum quality, closed circuit, and explicit human approval at L0.

## D-005: Dry-run may package while live publication is blocked

Unknown rules, missing credentials, age constraints, or manual-only actions create a Human Queue item. They do not prevent safe local package generation. Content-policy failures, exclusivity conflicts, duplicate content, and quality failures block even dry-run packaging where applicable.

## D-006: Platform rule state is separate from user eligibility

`rule_status` describes the registry record; account and user eligibility are evaluated at route time. The canonical unknown state is `UNVERIFIED`; legacy input `RULES_UNVERIFIED` is normalized to it. A currently underage operator receives `BLOCKED_BY_AGE` or `GUARDIAN_REQUIRED` decisions without falsifying platform data.

## D-007: No secrets in source or SQLite

Records contain only `credential_reference`. `CredentialProvider` resolves it from environment variables or a future secret manager. Audit logging redacts values that resemble tokens, passwords, cookies, or authorization headers.

## D-008: Adapter maturity is explicit

- P0: registry only
- P1: deterministic package generation
- P2: automated dry-run validation and package generation
- P3: live publishing

V1 implements P2 for the three browser stores and two ebook routes. Every other seed platform is P0. P3 is intentionally zero.

## D-009: First two vertical proofs

The first chain is a browser extension: one source, three manifest/build variants. The second is an ebook: Markdown plus metadata transformed into EPUB 3 and platform packages. This proves the core is not merely a plug-in manager.

## D-010: Platform rules are versioned evidence, not guesses

The seed registry links official documentation. A documentation check does not equal complete policy verification; therefore records remain `UNVERIFIED` or `REVIEW_REQUIRED` until every hard gate has been reviewed for the specific account, country, product, contract, and current date. Rules older than the configured freshness window surface as `RULE_OUTDATED`.

## D-011: No real publishing code in V1

The `publish()` interface exists but all shipped adapters return `NOT_SUPPORTED` for live actions. Human registration, identity verification, captcha, contracts, tax, payment, and release buttons remain manual-only.

## D-012: Metrics mocks are visibly marked

The demo may insert metrics with `source=MOCK` solely to prove analytics. They are never presented as marketplace results or revenue.

## D-013: GEO channels stay brand-scoped

X, Facebook, LinkedIn, Reddit, and YouTube are registered as public-attention channels for MultiHub GEO / AI Search. Other assets are not automatically sprayed into these accounts. Facebook is a connector boundary for an existing workflow, not a replacement implementation.

## D-014: L0 approval is a durable, scoped record

A future live route cannot treat an arbitrary boolean as human approval. Under L0 it must reference an `APPROVED` Human Review whose action, asset, and platform match that publication. L1 applies the same requirement to high/critical-risk work. V1 still has no public live-job creation path and no P3 adapter.
