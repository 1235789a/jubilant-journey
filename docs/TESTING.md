# Testing

Run:

```bash
make check
```

## Coverage in V1

Unit tests cover content hashing, stable idempotency keys, Platform Score, Vertical Evaluator, Yield Score, CredentialProvider, recursive redaction, account multiplicity, queue claim/retry/DLQ, Kill Switch, and circuit isolation.

Adapter tests cover three browser variants from one source, explicit live `NOT_SUPPORTED`, EPUB structure, and KDP Select conflict detection.

Integration tests cover all 31 Registry objects, five P2 dry-run destinations, two structurally different verticals, 3+ asset batching, Publication records, Human Queue creation, mock-label integrity, and actual HTTP Dashboard/API responses.

Failure tests cover unverified rules, age blocking, missing/expired credential representation, duplicate publication, exclusivity conflict, stale rule health, simulated adapter/API failure, retry, and platform-isolated circuit opening.

## Test invariants

- No test makes a real external publication.
- No test needs a credential or real identity.
- No test changes platform accounts or accepts contracts.
- Every generated artifact lives in a temporary directory.
- `MOCK` metrics remain visibly labeled.
- P3 coverage must remain zero unless a separately authorized live project changes it.

## Adding a regression

Write the failing test first, reproduce the exact state transition, then repair the smallest responsible boundary. If the bug involved persistent schema, add a migration test. If it involved a platform rule, include the primary official evidence and a rule-version update.
