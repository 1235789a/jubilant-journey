from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from distribution_os.models import (
    Account,
    AdapterMaturity,
    AssetStatus,
    DistributionMode,
    HealthStatus,
    Publication,
    JobType,
    RouteDecision,
    RuleStatus,
    new_id,
)
from distribution_os.health import HealthMonitor
from distribution_os.hashing import content_hash

from support import ApplicationTestCase


class FailureGateTests(ApplicationTestCase):
    def test_unverified_rules_block_live_but_allow_dry_package(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        dry = self.app.router.route(asset=asset, platform=platform, dry_run=True)
        live = self.app.router.route(asset=asset, platform=platform, dry_run=False)
        self.assertTrue(dry.can_package)
        self.assertEqual(dry.decision, RouteDecision.REVIEW_REQUIRED)
        self.assertFalse(live.can_publish)
        self.assertIn("LIVE_REQUIRES_VERIFIED_RULES", live.blockers)
        self.assertIn("REAL_PUBLISHING_DISABLED", live.blockers)

    def test_distribution_worker_never_packages_a_blocked_live_job(self) -> None:
        job = self.app.queue.enqueue(
            job_type=JobType.PUBLISH,
            idempotency_key="malformed-live-request",
            asset_id="asset_linklens_extension",
            platform_id="chrome_web_store",
            payload={"dry_run": False},
        )
        claimed = self.app.queue.claim_next()
        assert claimed
        result = self.app.distribution.execute(claimed)
        self.assertEqual(result.status.value, "BLOCKED")
        self.assertEqual(self.app.registry.list_publications(), [])

    def test_adapter_output_rejects_path_traversal_asset_id(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        adapter = self.app.adapters.get("chrome_web_store")
        assert asset and platform and adapter
        asset.asset_id = "../escape"
        with self.assertRaises(ValueError):
            adapter.prepare(asset, platform, self.settings.platform_ready_dir)

    def test_minor_account_hits_age_gate(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        platform.rule_status = RuleStatus.VERIFIED
        platform.adapter_maturity = AdapterMaturity.P3
        platform.live_publish = True
        platform.age_requirement = 18
        account = Account(
            account_id="acct_minor",
            platform_id=platform.platform_id,
            account_type="INDIVIDUAL",
            brand_name="Minor test",
            owner_type="INDIVIDUAL",
            age_status="MINOR",
            status="ACTIVE",
            credential_reference="TEST_TOKEN",
            channels=[],
            health_status=HealthStatus.HEALTHY,
            payout_ready=True,
        )
        route = self.app.router.route(
            asset=asset, platform=platform, account=account, dry_run=False
        )
        self.assertIn("AGE_GATE", route.blockers)

    def test_missing_credential_simulates_expired_or_unavailable_token(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        platform.rule_status = RuleStatus.VERIFIED
        platform.adapter_maturity = AdapterMaturity.P3
        platform.live_publish = True
        account = Account(
            account_id="acct_no_token",
            platform_id=platform.platform_id,
            account_type="PUBLISHER",
            brand_name="No token",
            owner_type="INDIVIDUAL",
            age_status="ADULT_VERIFIED",
            status="ACTIVE",
            credential_reference=None,
            channels=[],
            health_status=HealthStatus.DEGRADED,
            payout_ready=True,
        )
        route = self.app.router.route(
            asset=asset, platform=platform, account=account, dry_run=False
        )
        self.assertIn("CREDENTIAL_REQUIRED", route.blockers)

    def test_duplicate_publication_is_detected(self) -> None:
        self.app.distribution.request_dry_run(
            "asset_linklens_extension", "chrome_web_store"
        )
        self.app.distribution.run_until_empty()
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        route = self.app.router.route(asset=asset, platform=platform, dry_run=True)
        self.assertEqual(route.decision, RouteDecision.ALREADY_PUBLISHED)

    def test_exclusivity_conflict_blocks_package(self) -> None:
        asset = self.app.registry.get_asset("asset_ai_search_field_guide")
        amazon = self.app.registry.get_platform("amazon_kdp")
        assert asset and amazon
        asset.distribution_mode = DistributionMode.EXCLUSIVE
        asset.metadata["exclusive_platform_id"] = "amazon_kdp"
        self.app.registry.upsert_asset(asset)
        self.app.registry.record_publication(
            Publication(
                publication_id=new_id("pub"),
                asset_id=asset.asset_id,
                platform_id="draft2digital",
                account_id="DRY_RUN",
                asset_version=asset.master_version,
                content_hash=content_hash(Path(asset.master_source)),
                status="DRY_RUN_READY",
                mode="DRY_RUN",
                output_url=None,
                adapter_version="1.0.0",
                job_id="manual-test",
            )
        )
        route = self.app.router.route(asset=asset, platform=amazon, dry_run=True)
        self.assertEqual(route.decision, RouteDecision.BLOCKED)
        self.assertIn("EXCLUSIVITY_CONFLICT", route.blockers)

    def test_outdated_rule_health(self) -> None:
        platform = self.app.registry.get_platform("chrome_web_store")
        assert platform
        platform.rule_status = RuleStatus.VERIFIED
        platform.last_verified_at = "2020-01-01T00:00:00+00:00"
        self.app.registry.upsert_platform(platform)
        result = HealthMonitor(self.app).check_platform(platform.platform_id)
        self.assertEqual(result["status"], "RULE_OUTDATED")

    def test_adapter_failure_retries_and_opens_only_its_circuit(self) -> None:
        adapter = self.app.adapters.get("chrome_web_store")
        assert adapter
        original = adapter.prepare

        def explode(*args, **kwargs):
            raise RuntimeError("simulated API failure")

        adapter.prepare = explode  # type: ignore[method-assign]
        try:
            self.app.distribution.request_dry_run(
                "asset_linklens_extension", "chrome_web_store"
            )
            [first] = self.app.distribution.run_until_empty(max_jobs=1)
            self.assertEqual(first.status.value, "RETRYING")
            first.scheduled_at = "2000-01-01T00:00:00+00:00"
            self.app.queue._save(first)
            [second] = self.app.distribution.run_until_empty(max_jobs=1)
            self.assertEqual(second.status.value, "RETRYING")
            self.assertEqual(self.app.circuit_breaker.state("chrome_web_store"), "OPEN")
            self.assertEqual(self.app.circuit_breaker.state("amazon_kdp"), "CLOSED")
        finally:
            adapter.prepare = original  # type: ignore[method-assign]
