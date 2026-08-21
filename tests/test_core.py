from __future__ import annotations

import os
import tempfile
from pathlib import Path

from distribution_os.analytics import calculate_yield_score
from distribution_os.hashing import content_hash, stable_key
from distribution_os.models import (
    Account,
    AssetStatus,
    HealthStatus,
    HumanReview,
    JobStatus,
    JobType,
    RuleStatus,
    new_id,
)
from distribution_os.scoring import evaluate_vertical, platform_score
from distribution_os.security import EnvironmentCredentialProvider, redact

from support import ApplicationTestCase


class HashingTests(ApplicationTestCase):
    def test_content_hash_is_deterministic_and_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "a.txt").write_text("one", encoding="utf-8")
            first = content_hash(root)
            self.assertEqual(first, content_hash(root))
            (root / "a.txt").write_text("two", encoding="utf-8")
            self.assertNotEqual(first, content_hash(root))

    def test_stable_key(self) -> None:
        self.assertEqual(stable_key("a", 1), stable_key("a", 1))
        self.assertNotEqual(stable_key("a", 1), stable_key("a", 2))


class ScoringTests(ApplicationTestCase):
    def test_platform_score_is_bounded(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        score = platform_score(asset, platform)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)

    def test_vertical_evaluator_outputs_priority(self) -> None:
        result = evaluate_vertical(
            natural_traffic=90,
            ai_automation=90,
            monetization_distance=80,
            multi_platformability=90,
            multi_productability=90,
            maintenance_cost=80,
            legal_risk=80,
        )
        self.assertEqual(result.priority.value, "P0")

    def test_yield_score_accounts_for_human_time(self) -> None:
        lean = calculate_yield_score(
            revenue_value=100,
            traffic_value=0,
            user_value=0,
            geo_brand_value=0,
            strategic_value=0,
            token_cost=1,
            human_time_cost=1,
            maintenance_cost=1,
            platform_cost=0,
            risk_cost=0,
        )
        labor_heavy = calculate_yield_score(
            revenue_value=100,
            traffic_value=0,
            user_value=0,
            geo_brand_value=0,
            strategic_value=0,
            token_cost=1,
            human_time_cost=100,
            maintenance_cost=1,
            platform_cost=0,
            risk_cost=0,
        )
        self.assertGreater(lean, labor_heavy)


class QueueTests(ApplicationTestCase):
    def test_enqueue_is_idempotent(self) -> None:
        first = self.app.queue.enqueue(job_type=JobType.GENERATE, idempotency_key="same")
        second = self.app.queue.enqueue(job_type=JobType.GENERATE, idempotency_key="same")
        self.assertEqual(first.job_id, second.job_id)
        self.assertEqual(len(self.app.queue.list()), 1)

    def test_claim_complete_and_retry_to_dead_letter(self) -> None:
        job = self.app.queue.enqueue(job_type=JobType.GENERATE, idempotency_key="retry")
        claimed = self.app.queue.claim_next()
        assert claimed
        self.assertEqual(claimed.status, JobStatus.RUNNING)
        retried = self.app.queue.fail(claimed, "transient")
        self.assertEqual(retried.status, JobStatus.RETRYING)
        retried.scheduled_at = "2000-01-01T00:00:00+00:00"
        self.app.queue._save(retried)
        claimed = self.app.queue.claim_next()
        assert claimed
        retried = self.app.queue.fail(claimed, "transient again")
        self.assertEqual(retried.status, JobStatus.RETRYING)
        retried.scheduled_at = "2000-01-01T00:00:00+00:00"
        self.app.queue._save(retried)
        claimed = self.app.queue.claim_next()
        assert claimed
        terminal = self.app.queue.fail(claimed, "terminal")
        self.assertEqual(terminal.status, JobStatus.DEAD_LETTER)

    def test_kill_switch_cancels_publish_only(self) -> None:
        publish = self.app.queue.enqueue(job_type=JobType.PUBLISH, idempotency_key="publish")
        dry_run = self.app.queue.enqueue(
            job_type=JobType.PUBLISH,
            idempotency_key="dry-run-publish",
            payload={"dry_run": True},
        )
        generate = self.app.queue.enqueue(job_type=JobType.GENERATE, idempotency_key="generate")
        self.app.kill_switch.stop(reason="test")
        self.assertEqual(self.app.queue.get(publish.job_id).status, JobStatus.CANCELLED)
        self.assertEqual(self.app.queue.get(dry_run.job_id).status, JobStatus.PENDING)
        self.assertEqual(self.app.queue.get(generate.job_id).status, JobStatus.PENDING)

    def test_circuit_breaker_is_platform_isolated(self) -> None:
        self.app.circuit_breaker.record_failure("chrome_web_store", "one")
        self.app.circuit_breaker.record_failure("chrome_web_store", "two")
        self.assertEqual(self.app.circuit_breaker.state("chrome_web_store"), "OPEN")
        self.assertEqual(self.app.circuit_breaker.state("amazon_kdp"), "CLOSED")


class SecurityTests(ApplicationTestCase):
    def test_environment_credential_provider_uses_reference_only(self) -> None:
        os.environ["TEST_DOS_TOKEN"] = "secret-value"
        try:
            self.assertEqual(
                EnvironmentCredentialProvider().get("TEST_DOS_TOKEN"), "secret-value"
            )
            with self.assertRaises(ValueError):
                EnvironmentCredentialProvider().get("raw-token-value")
        finally:
            os.environ.pop("TEST_DOS_TOKEN", None)

    def test_redaction_is_recursive(self) -> None:
        result = redact({"token": "abc", "nested": {"password": "def"}, "safe": 1})
        self.assertEqual(result["token"], "[REDACTED]")
        self.assertEqual(result["nested"]["password"], "[REDACTED]")
        self.assertEqual(result["safe"], 1)

    def test_duplicate_active_publisher_is_rejected(self) -> None:
        account = Account(
            account_id="acct_one",
            platform_id="chrome_web_store",
            account_type="PUBLISHER",
            brand_name="MultiHub",
            owner_type="INDIVIDUAL",
            age_status="MINOR",
            status="ACTIVE",
            credential_reference=None,
            channels=[],
            health_status=HealthStatus.ACTION_REQUIRED,
        )
        self.app.registry.upsert_account(account)
        account.account_id = "acct_two"
        with self.assertRaises(Exception):
            self.app.registry.upsert_account(account)

    def test_l0_live_route_requires_matching_approved_review(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        assert asset and platform
        without_review = self.app.router.route(
            asset=asset, platform=platform, dry_run=False
        )
        self.assertIn("L0_HUMAN_APPROVAL_REQUIRED", without_review.blockers)

        review = self.app.registry.create_review(
            HumanReview(
                review_id=new_id("review"),
                job_id=None,
                asset_id=asset.asset_id,
                platform_id=platform.platform_id,
                action="APPROVE_LIVE_PUBLICATION",
                reason="test-only approval record",
            )
        )
        self.app.registry.resolve_review(review.review_id, "APPROVED")
        with_review = self.app.router.route(
            asset=asset,
            platform=platform,
            dry_run=False,
            approval_review_id=review.review_id,
        )
        self.assertNotIn("L0_HUMAN_APPROVAL_REQUIRED", with_review.blockers)
        self.assertFalse(with_review.can_publish)
