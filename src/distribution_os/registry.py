from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from .database import Database
from .models import (
    Account,
    AdapterMaturity,
    Asset,
    AssetStatus,
    DistributionMode,
    Experiment,
    HealthStatus,
    HumanReview,
    Metric,
    Platform,
    Publication,
    RuleRecord,
    RuleStatus,
    Vertical,
    VerticalPriority,
    Variant,
    new_id,
    to_dict,
    to_json,
    utc_now,
)


def _platform(data: dict[str, Any]) -> Platform:
    payload = dict(data)
    payload["adapter_maturity"] = AdapterMaturity(payload["adapter_maturity"])
    payload["rule_status"] = RuleStatus.parse(payload["rule_status"])
    return Platform(**payload)


def _asset(data: dict[str, Any]) -> Asset:
    payload = dict(data)
    payload["status"] = AssetStatus(payload["status"])
    payload["distribution_mode"] = DistributionMode(payload["distribution_mode"])
    return Asset(**payload)


def _account(data: dict[str, Any]) -> Account:
    payload = dict(data)
    payload["health_status"] = HealthStatus(payload["health_status"])
    return Account(**payload)


def _vertical(data: dict[str, Any]) -> Vertical:
    payload = dict(data)
    payload["priority"] = VerticalPriority(payload["priority"])
    return Vertical(**payload)


def _rule(data: dict[str, Any]) -> RuleRecord:
    payload = dict(data)
    payload["status"] = RuleStatus.parse(payload["status"])
    return RuleRecord(**payload)


DEFAULT_PLATFORM: dict[str, Any] = {
    "official_docs": [],
    "natural_traffic_score": 50.0,
    "monetization_type": "UNVERIFIED",
    "distribution_type": "MARKETPLACE",
    "age_requirement": None,
    "guardian_supported": None,
    "identity_verification_required": None,
    "publisher_account_type": ["UNVERIFIED"],
    "multi_product_allowed": None,
    "multi_channel_allowed": None,
    "duplicate_personal_account_allowed": False,
    "exclusivity_rules": "UNVERIFIED",
    "ai_content_policy": "UNVERIFIED",
    "automation_policy": "UNVERIFIED",
    "api_available": None,
    "cli_available": None,
    "browser_automation_allowed": None,
    "manual_only_actions": [
        "account registration",
        "identity or age verification",
        "contract acceptance",
        "tax and payout setup",
        "captcha or security challenge",
        "final public submission",
    ],
    "publishing_cost": None,
    "platform_fee": "UNVERIFIED",
    "revenue_share": "UNVERIFIED",
    "payout_method": ["UNVERIFIED"],
    "payout_threshold": "UNVERIFIED",
    "country_restrictions": [],
    "rate_limits": "UNVERIFIED",
    "content_limits": "UNVERIFIED",
    "review_process": "UNVERIFIED",
    "adapter_name": None,
    "adapter_version": None,
    "adapter_maturity": "P0",
    "rule_status": "UNVERIFIED",
    "rule_version": "seed-2026-08-19",
    "last_verified_at": None,
    "live_publish": False,
    "notes": "Seed registry record; a current platform-specific review is required.",
}


class Registry:
    def __init__(self, database: Database):
        self.db = database

    def seed_platforms(self, source: Path) -> int:
        records = json.loads(source.read_text(encoding="utf-8"))
        for record in records:
            self.upsert_platform(_platform({**DEFAULT_PLATFORM, **record}))
        return len(records)

    def upsert_vertical(self, vertical: Vertical) -> None:
        vertical.updated_at = utc_now()
        self.db.execute(
            """
            INSERT INTO verticals(
                vertical_id, name, status, priority, evaluated_score,
                data_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vertical_id) DO UPDATE SET
                name=excluded.name, status=excluded.status,
                priority=excluded.priority, evaluated_score=excluded.evaluated_score,
                data_json=excluded.data_json, updated_at=excluded.updated_at
            """,
            (
                vertical.vertical_id,
                vertical.name,
                vertical.status,
                vertical.priority.value,
                vertical.evaluated_score,
                to_json(vertical),
                vertical.updated_at,
            ),
        )

    def get_vertical(self, vertical_id: str) -> Vertical | None:
        row = self.db.fetch_one(
            "SELECT data_json FROM verticals WHERE vertical_id=?", (vertical_id,)
        )
        return None if row is None else _vertical(json.loads(row["data_json"]))

    def list_verticals(self) -> list[Vertical]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM verticals ORDER BY evaluated_score DESC, name"
        )
        return [_vertical(json.loads(row["data_json"])) for row in rows]

    def upsert_platform(self, platform: Platform) -> None:
        now = utc_now()
        self.db.execute(
            """
            INSERT INTO platforms(
                platform_id, platform_name, rule_status, adapter_maturity,
                data_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform_id) DO UPDATE SET
                platform_name=excluded.platform_name,
                rule_status=excluded.rule_status,
                adapter_maturity=excluded.adapter_maturity,
                data_json=excluded.data_json,
                updated_at=excluded.updated_at
            """,
            (
                platform.platform_id,
                platform.platform_name,
                platform.rule_status.value,
                platform.adapter_maturity.value,
                to_json(platform),
                now,
            ),
        )

    def get_platform(self, platform_id: str) -> Platform | None:
        row = self.db.fetch_one(
            "SELECT data_json FROM platforms WHERE platform_id = ?", (platform_id,)
        )
        return None if row is None else _platform(json.loads(row["data_json"]))

    def list_platforms(self) -> list[Platform]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM platforms ORDER BY platform_name"
        )
        return [_platform(json.loads(row["data_json"])) for row in rows]

    def upsert_rule(self, rule: RuleRecord) -> None:
        self.db.execute(
            """
            INSERT INTO rules(
                rule_id, platform_id, rule_version, status, data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform_id, rule_version) DO UPDATE SET
                status=excluded.status, data_json=excluded.data_json
            """,
            (
                rule.rule_id,
                rule.platform_id,
                rule.rule_version,
                rule.status.value,
                to_json(rule),
                rule.created_at,
            ),
        )

    def list_rules(self, platform_id: str | None = None) -> list[RuleRecord]:
        if platform_id:
            rows = self.db.fetch_all(
                "SELECT data_json FROM rules WHERE platform_id=? ORDER BY created_at DESC",
                (platform_id,),
            )
        else:
            rows = self.db.fetch_all(
                "SELECT data_json FROM rules ORDER BY platform_id, created_at DESC"
            )
        return [_rule(json.loads(row["data_json"])) for row in rows]

    def upsert_asset(self, asset: Asset) -> None:
        asset.updated_at = utc_now()
        self.db.execute(
            """
            INSERT INTO assets(
                asset_id, name, vertical_id, status, priority, data_json,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(asset_id) DO UPDATE SET
                name=excluded.name,
                vertical_id=excluded.vertical_id,
                status=excluded.status,
                priority=excluded.priority,
                data_json=excluded.data_json,
                updated_at=excluded.updated_at
            """,
            (
                asset.asset_id,
                asset.name,
                asset.vertical_id,
                asset.status.value,
                asset.priority,
                to_json(asset),
                asset.created_at,
                asset.updated_at,
            ),
        )

    def get_asset(self, asset_id: str) -> Asset | None:
        row = self.db.fetch_one(
            "SELECT data_json FROM assets WHERE asset_id = ?", (asset_id,)
        )
        return None if row is None else _asset(json.loads(row["data_json"]))

    def list_assets(self) -> list[Asset]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM assets ORDER BY priority DESC, created_at DESC"
        )
        return [_asset(json.loads(row["data_json"])) for row in rows]

    def set_asset_status(self, asset_id: str, status: AssetStatus) -> Asset:
        asset = self.get_asset(asset_id)
        if asset is None:
            raise KeyError(f"Unknown asset: {asset_id}")
        asset.status = status
        self.upsert_asset(asset)
        return asset

    def upsert_account(self, account: Account) -> None:
        self.db.execute(
            """
            INSERT INTO accounts(
                account_id, platform_id, brand_name, status, health_status,
                data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(account_id) DO UPDATE SET
                platform_id=excluded.platform_id,
                brand_name=excluded.brand_name,
                status=excluded.status,
                health_status=excluded.health_status,
                data_json=excluded.data_json
            """,
            (
                account.account_id,
                account.platform_id,
                account.brand_name,
                account.status,
                account.health_status.value,
                to_json(account),
                account.created_at,
            ),
        )

    def get_account(self, account_id: str | None) -> Account | None:
        if not account_id:
            return None
        row = self.db.fetch_one(
            "SELECT data_json FROM accounts WHERE account_id = ?", (account_id,)
        )
        return None if row is None else _account(json.loads(row["data_json"]))

    def list_accounts(self) -> list[Account]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM accounts ORDER BY platform_id, brand_name"
        )
        return [_account(json.loads(row["data_json"])) for row in rows]

    def find_publication(
        self,
        content_hash: str,
        platform_id: str,
        account_id: str,
        asset_version: str,
    ) -> Publication | None:
        row = self.db.fetch_one(
            """
            SELECT data_json FROM publications
            WHERE content_hash=? AND platform_id=? AND account_id=?
              AND asset_version=?
            """,
            (content_hash, platform_id, account_id, asset_version),
        )
        return None if row is None else Publication(**json.loads(row["data_json"]))

    def publications_for_asset(self, asset_id: str) -> list[Publication]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM publications WHERE asset_id = ? ORDER BY created_at",
            (asset_id,),
        )
        return [Publication(**json.loads(row["data_json"])) for row in rows]

    def record_publication(self, publication: Publication) -> Publication:
        self.db.execute(
            """
            INSERT INTO publications(
                publication_id, asset_id, platform_id, account_id, asset_version,
                content_hash, status, mode, data_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                publication.publication_id,
                publication.asset_id,
                publication.platform_id,
                publication.account_id,
                publication.asset_version,
                publication.content_hash,
                publication.status,
                publication.mode,
                to_json(publication),
                publication.created_at,
                publication.updated_at,
            ),
        )
        return publication

    def find_variant(
        self,
        *,
        asset_id: str,
        platform_id: str,
        asset_version: str,
        adapter_version: str,
        content_hash: str,
    ) -> Variant | None:
        row = self.db.fetch_one(
            """
            SELECT data_json FROM variants
            WHERE asset_id=? AND platform_id=? AND asset_version=?
              AND adapter_version=? AND content_hash=?
            """,
            (asset_id, platform_id, asset_version, adapter_version, content_hash),
        )
        return None if row is None else Variant(**json.loads(row["data_json"]))

    def record_variant(self, variant: Variant) -> Variant:
        self.db.execute(
            """
            INSERT INTO variants(
                variant_id, asset_id, platform_id, asset_version, adapter_name,
                adapter_version, content_hash, status, data_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                variant.variant_id,
                variant.asset_id,
                variant.platform_id,
                variant.asset_version,
                variant.adapter_name,
                variant.adapter_version,
                variant.content_hash,
                variant.status,
                to_json(variant),
                variant.created_at,
            ),
        )
        return variant

    def list_variants(self) -> list[Variant]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM variants ORDER BY created_at DESC"
        )
        return [Variant(**json.loads(row["data_json"])) for row in rows]

    def list_publications(self) -> list[Publication]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM publications ORDER BY created_at DESC"
        )
        return [Publication(**json.loads(row["data_json"])) for row in rows]

    def record_metric(self, metric: Metric) -> Metric:
        self.db.execute(
            """
            INSERT INTO metrics(metric_id, asset_id, platform_id, timestamp, source, data_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                metric.metric_id,
                metric.asset_id,
                metric.platform_id,
                metric.timestamp,
                metric.source,
                to_json(metric),
            ),
        )
        return metric

    def list_metrics(self) -> list[Metric]:
        rows = self.db.fetch_all("SELECT data_json FROM metrics ORDER BY timestamp DESC")
        return [Metric(**json.loads(row["data_json"])) for row in rows]

    def upsert_experiment(self, experiment: Experiment) -> None:
        self.db.execute(
            """
            INSERT INTO experiments(experiment_id, vertical, platform, decision, data_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(experiment_id) DO UPDATE SET
                decision=excluded.decision, data_json=excluded.data_json
            """,
            (
                experiment.experiment_id,
                experiment.vertical,
                experiment.platform,
                experiment.decision,
                to_json(experiment),
            ),
        )

    def list_experiments(self) -> list[Experiment]:
        rows = self.db.fetch_all("SELECT data_json FROM experiments ORDER BY experiment_id")
        return [Experiment(**json.loads(row["data_json"])) for row in rows]

    def create_review(self, review: HumanReview) -> HumanReview:
        existing = self.db.fetch_one(
            """
            SELECT data_json FROM human_reviews
            WHERE COALESCE(job_id, '')=COALESCE(?, '')
              AND action=? AND status='PENDING'
            """,
            (review.job_id, review.action),
        )
        if existing:
            return HumanReview(**json.loads(existing["data_json"]))
        self.db.execute(
            """
            INSERT INTO human_reviews(
                review_id, job_id, asset_id, platform_id, action, status, risk_level,
                data_json, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review.review_id,
                review.job_id,
                review.asset_id,
                review.platform_id,
                review.action,
                review.status,
                review.risk_level,
                to_json(review),
                review.created_at,
                review.resolved_at,
            ),
        )
        return review

    def list_reviews(self, status: str | None = None) -> list[HumanReview]:
        if status:
            rows = self.db.fetch_all(
                "SELECT data_json FROM human_reviews WHERE status=? ORDER BY created_at",
                (status,),
            )
        else:
            rows = self.db.fetch_all(
                "SELECT data_json FROM human_reviews ORDER BY created_at DESC"
            )
        return [HumanReview(**json.loads(row["data_json"])) for row in rows]

    def get_review(self, review_id: str | None) -> HumanReview | None:
        if not review_id:
            return None
        row = self.db.fetch_one(
            "SELECT data_json FROM human_reviews WHERE review_id=?", (review_id,)
        )
        return None if row is None else HumanReview(**json.loads(row["data_json"]))

    def resolve_review(self, review_id: str, status: str) -> HumanReview:
        row = self.db.fetch_one(
            "SELECT data_json FROM human_reviews WHERE review_id=?", (review_id,)
        )
        if row is None:
            raise KeyError(f"Unknown review: {review_id}")
        review = HumanReview(**json.loads(row["data_json"]))
        review.status = status
        review.resolved_at = utc_now()
        self.db.execute(
            """
            UPDATE human_reviews SET status=?, resolved_at=?, data_json=?
            WHERE review_id=?
            """,
            (review.status, review.resolved_at, to_json(review), review.review_id),
        )
        return review

    def overview_counts(self) -> dict[str, int]:
        result: dict[str, int] = {}
        queries = {
            "assets": "SELECT COUNT(*) AS n FROM assets",
            "active_assets": "SELECT COUNT(*) AS n FROM assets WHERE status IN ('READY','PUBLISHING','ACTIVE')",
            "platforms": "SELECT COUNT(*) AS n FROM platforms",
            "verticals": "SELECT COUNT(*) AS n FROM verticals",
            "jobs": "SELECT COUNT(*) AS n FROM jobs",
            "publications": "SELECT COUNT(*) AS n FROM publications",
            "variants": "SELECT COUNT(*) AS n FROM variants",
            "human_required": "SELECT COUNT(*) AS n FROM human_reviews WHERE status='PENDING'",
        }
        for key, query in queries.items():
            row = self.db.fetch_one(query)
            result[key] = 0 if row is None else int(row["n"])
        return result

    def serialize_all(self, values: list[Any]) -> list[dict[str, Any]]:
        return [to_dict(value) for value in values]
