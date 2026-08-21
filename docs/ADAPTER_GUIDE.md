# Adapter Guide

An adapter converts one master asset into a platform-ready artifact. It never decides portfolio strategy or bypasses account policy.

## Add a platform

1. Add a conservative record to `config/platforms.json`.
2. Link primary official documentation and leave uncertain fields `UNVERIFIED`.
3. Implement `PlatformAdapter` only when real package behavior exists.
4. Register the adapter in `Application.create()`.
5. Add unit, integration, and failure tests.
6. Raise maturity honestly.

Minimal skeleton:

```python
class ExampleAdapter(PlatformAdapter):
    name = "example"
    version = "1.0.0"
    supported_platforms = frozenset({"example_store"})

    def validate(self, asset, platform):
        ...  # deterministic local checks

    def generate_metadata(self, asset, platform):
        ...  # platform-native listing fields

    def prepare(self, asset, platform, output_root):
        ...  # write only under platform_ready/
```

Unimplemented live methods inherit `NOT_SUPPORTED`.

## Package requirements

Every P1/P2 package must include:

- the exact upload artifact;
- platform-native metadata;
- a machine-readable validation result;
- `PUBLISH_PLAN.md` listing manual steps and explicitly saying no upload occurred;
- adapter version and asset version in the Publication record.

Use a temporary directory and move/copy into the exact final target only after successful validation. Never write credentials into a package. Never silently overwrite an unrelated path.

## Browser extension pattern

Keep one Manifest V3 source. Adapt only the manifest and packaging differences. Chrome and Edge remove Firefox-specific settings; Firefox receives a Gecko ID and minimum version. A generated archive still needs target-browser runtime testing and platform review.

## Ebook pattern

Keep manuscript and book metadata independent of a retailer. Generate one valid EPUB, then retailer/aggregator-specific metadata and plans. Draft2Digital is one aggregator route; do not generate redundant jobs for its downstream stores. `WIDE` plus `kdp_select=true` is a hard validation failure.

## Versioning

Increment adapter version when output format, required metadata, policy validation, or behavior changes. Existing Publications retain the version that created them. A platform schema change should not force a core version change.

## Moving toward P3

P3 is a separate security project. It requires official API/CLI authorization, scoped credentials, sandbox tests, rate limits, timeouts, rollback/unpublish semantics, idempotent remote reconciliation, current verified rules, L0 approval, and an explicit user decision to unlock that platform. Browser automation is not a substitute when it violates terms or encounters identity/captcha/security controls.
