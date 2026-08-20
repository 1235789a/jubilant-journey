# Security

## Threat model

Primary risks are credential leakage, unauthorized public release, duplicate publication, policy/contract violation, age or identity misrepresentation, cross-platform failure propagation, malicious package input, and misleading telemetry.

## Controls in V1

- Fail-closed `DRY_RUN`, `REAL_PUBLISHING`, review, platform, adapter, and global kill gates.
- No P3 adapters and no dashboard endpoint to enable live publishing.
- Credential references only; environment resolution through `CredentialProvider`.
- Recursive audit redaction for secrets, tokens, cookies, sessions, and authorization values.
- SHA-256 content identities and unique Publication constraints.
- Transactional unique Job idempotency keys.
- One active publisher identity per platform/brand database constraint.
- Per-platform circuit breakers, exponential backoff, timeout-ready job model, and DLQ.
- Human Queue for age, identity, captcha, contracts, tax, payout, fees, and final submission.
- Output path isolation under `platform_ready/`.
- Local bind address defaults to `127.0.0.1`.
- CI receives read-only repository permissions.

## Secrets

Never put secrets in `.env.example`, source, prompts, fixtures, SQLite payloads, package metadata, screenshots, logs, issues, commits, or PR text. `.env` is ignored. Production should move from environment variables to an OS keychain or managed secret service while keeping the same `CredentialProvider` boundary.

Rotate a credential immediately if it appears in Git history. Removing it from the current file is insufficient.

## Minor and identity safety

Age and identity are hard facts, not configuration conveniences. A guardian flow must be both real and supported by the platform. `GUARDIAN_REQUIRED` is a manual state; it never means the system may populate another person's identity. Account transfer, tax, banking, and contracts remain manual.

## Dashboard exposure

The built-in server has no authentication because it is intended for localhost. Do not bind it publicly. For remote use, place it behind authenticated TLS access, set network restrictions, protect the data/output volumes, and complete a separate deployment security review.

## Reporting

Do not publish a suspected vulnerability in a public issue with exploit details or secrets. Contact the repository owner privately and include reproduction steps with redacted data.
