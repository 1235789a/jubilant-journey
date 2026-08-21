# Operations

## Ten-minute daily routine

1. Open Overview and confirm the banner says dry-run, real publishing false, L0, global publish disabled.
2. Read “Today needs you”; handle only the highest-risk Human Queue items.
3. Check failed/blocked/DLQ jobs and the affected platform circuit.
4. Check Health for rule freshness and missing adapters/credentials.
5. Review token, human-time, cost, and revenue deltas.
6. Accept no automatic `KILL`; decisions remain recommendations in V1.

## Commands

```bash
make init       # schema + 31-platform registry + two pilot assets
make demo       # five P2 local packages + clearly marked mock metrics
make serve      # dashboard on 127.0.0.1:8787
make tick       # idempotent daily health job
make test       # all tests
make check      # JSON, compile, tests, dashboard JS syntax
```

Create a consistent online SQLite backup (the destination must not already exist):

```bash
distribution-os backup backups/distribution-os-YYYY-MM-DD.db
```

The command uses SQLite's online backup API, runs `integrity_check`, and returns a SHA-256 digest. Export non-secret state separately:

```bash
distribution-os export backups/export-YYYY-MM-DD.json
```

SQLite plus `platform_ready/` are the operational data to back up. The database command does not include generated packages, so archive those separately when they are costly to reproduce.

Run `distribution-os tick` once per day with cron, launchd, or Windows Task Scheduler. The date-keyed job is idempotent, so a duplicate timer invocation does not duplicate snapshots. V1 does not schedule remote metric fetching because it has no authorized live adapters.

## Human Queue policy

Human review is required for registration, identity, age, guardian relationship, captcha, security challenges, contracts, tax, payout, fees, final publication, and high-risk policy ambiguity. Approving a dry-run package does not unlock live submission.

## Failure response

- One transient failure: inspect the job log and scheduled retry.
- Repeated platform failure: circuit opens; inspect only that platform.
- `DEAD_LETTER`: repair input/adapter/rule before creating a new versioned job.
- Duplicate: verify the existing Publication; do not delete the constraint.
- Rule outdated: refresh official evidence before further work.
- Global concern: press `STOP ALL PUBLISHING`; generation and analytics continue.

## Rollback

Core code rolls back through Git. Adapter output is versioned by asset and adapter version. V1 does not mutate remote platforms, so remote rollback/unpublish is intentionally absent. Before any future P3 adapter, implement and test remote reconciliation and rollback.

## Mock data

`distribution-os demo` inserts two metric rows with `source=MOCK` when the metric table is empty. They only demonstrate analytics. Delete or use a fresh database before evaluating real performance; never include mock values in a business claim.
