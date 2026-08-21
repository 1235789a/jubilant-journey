# Runtime Rules

## Live-publication hard gates

All gates must pass. A single failure prevents the real action.

| Gate | Pass condition | Failure state |
|---|---|---|
| Global mode | `DRY_RUN=false`, `REAL_PUBLISHING=true` | `SYSTEM_DRY_RUN_ENABLED` / `REAL_PUBLISHING_DISABLED` |
| Kill switch | global publishing enabled | `GLOBAL_KILL_SWITCH_ACTIVE` |
| Platform | `live_publish=true` | `PLATFORM_LIVE_PUBLISH_LOCKED` |
| Rules | current `VERIFIED` record | `LIVE_REQUIRES_VERIFIED_RULES` |
| Adapter | P3 live implementation | `LIVE_ADAPTER_NOT_SUPPORTED` |
| Account | correct, active, healthy publisher | account block/review |
| Age | majority or explicitly supported guardian path | `AGE_GATE` |
| Region | destination and payout are legal | `BLOCKED_BY_REGION` |
| Identity | legitimate verified identity | Human Queue |
| Credential | valid referenced secret | `CREDENTIAL_REQUIRED` |
| Payout | tax and payout ready | `PAYOUT_NOT_READY` |
| Policy | current content/AI/license rules pass | `BLOCKED_BY_POLICY` |
| Exclusivity | no contract or distribution conflict | `BLOCKED_BY_EXCLUSIVITY` |
| Duplicate | publication identity absent | `ALREADY_PUBLISHED` |
| Quality | asset meets its declared floor | `MINIMUM_QUALITY_NOT_MET` |
| Circuit | closed/approved half-open probe | `PLATFORM_CIRCUIT_OPEN` |
| Review | current review level authorizes action | Human Queue |

## Dry-run behavior

Dry-run may produce a local package while accounts, age, credentials, payout, or full rule verification remain unresolved. It still blocks unsupported verticals, unready assets, low quality, unconfirmed rights, disallowed content, region restrictions, exclusivity conflicts, registry-only adapters, duplicates, and open circuits.

## Review levels

- L0: every real publication requires human approval. V1 default.
- L1: only explicitly classified low-risk tasks may automate; high-risk stays manual.
- L2: stable, observed tasks may automate. It never overrides age, identity, contract, tax, payout, policy, exclusivity, captcha, or security controls.

## Distribution modes

- `WIDE`: route only to compatible non-conflicting destinations.
- `EXCLUSIVE`: route only to the recorded exclusive destination and block existing conflicts.
- `HYBRID`: rules must describe the allowed subset.
- `UNDECIDED`: packaging may continue with review; live publication cannot.

## Account multiplicity

One legitimate publisher identity per platform/brand is the default. Multiple products are allowed when the platform supports them. Multiple channels/pages/workspaces/brands are allowed only as platform-native constructs. Duplicate personal accounts remain false.
