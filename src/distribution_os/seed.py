from __future__ import annotations

import json
from pathlib import Path

from .application import Application
from .models import (
    Asset,
    AssetStatus,
    DistributionMode,
    Experiment,
    Metric,
    RuleRecord,
    Vertical,
    new_id,
    utc_now,
)
from .scoring import evaluate_vertical


def seed(application: Application) -> dict[str, int]:
    root = application.settings.project_root
    platform_count = application.registry.seed_platforms(root / "config" / "platforms.json")
    vertical_records = json.loads(
        (root / "config" / "verticals.json").read_text(encoding="utf-8")
    )
    for record in vertical_records:
        evaluation = evaluate_vertical(**record["scores"])
        application.registry.upsert_vertical(
            Vertical(
                vertical_id=record["vertical_id"],
                name=record["name"],
                status=record["status"],
                pilot_limit=int(record["pilot_limit"]),
                scores={key: float(value) for key, value in record["scores"].items()},
                evaluated_score=evaluation.score,
                priority=evaluation.priority,
            )
        )
    for platform in application.registry.list_platforms():
        application.registry.upsert_rule(
            RuleRecord(
                rule_id=f"rule_{platform.platform_id}_{platform.rule_version}",
                platform_id=platform.platform_id,
                rule_version=platform.rule_version,
                status=platform.rule_status,
                scope="SEED_CURRENT_SNAPSHOT",
                evidence_urls=platform.official_docs,
                facts={
                    "age_requirement": platform.age_requirement,
                    "guardian_supported": platform.guardian_supported,
                    "identity_verification_required": platform.identity_verification_required,
                    "exclusivity_rules": platform.exclusivity_rules,
                    "ai_content_policy": platform.ai_content_policy,
                    "automation_policy": platform.automation_policy,
                    "manual_only_actions": platform.manual_only_actions,
                },
                verified_at=platform.last_verified_at,
                notes=platform.notes,
            )
        )
    application.database.set_setting("DRY_RUN", True, utc_now())
    application.database.set_setting("REAL_PUBLISHING", False, utc_now())
    application.database.set_setting("REVIEW_LEVEL", "L0", utc_now())
    application.database.set_setting("DUPLICATE_PERSONAL_ACCOUNTS", False, utc_now())
    application.database.set_setting("ONE_PLATFORM_ONE_PUBLISHER", True, utc_now())
    application.database.set_setting("MULTI_CHANNEL", "PLATFORM_NATIVE_ONLY", utc_now())

    assets = [
        Asset(
            asset_id="asset_linklens_extension",
            name="LinkLens Local Notes",
            vertical_id="browser_extension",
            product_type="BROWSER_EXTENSION",
            status=AssetStatus.READY,
            master_source=str((root / "examples" / "browser_extension").resolve()),
            master_version="0.1.0",
            language="en",
            market="GLOBAL",
            category="productivity",
            tags=["notes", "research", "privacy", "productivity"],
            distribution_mode=DistributionMode.WIDE,
            priority=80,
            human_owner="operator",
            production_cost=0,
            token_cost=0,
            estimated_value=25,
            quality_score=88,
            metadata={
                "rights_confirmed": True,
                "policy_status": "ALLOWED",
                "minimum_quality": 70,
                "summary": "Private per-page notes stored only in browser local storage.",
                "description": "A small, transparent pilot extension used to prove one-source multi-store packaging.",
                "privacy_policy_url": None,
                "support_url": None,
                "ai_usage": "AI_ASSISTED",
                "firefox_addon_id": "linklens@distribution-os.invalid",
                "platform_scores": {
                    "chrome_web_store": {"fit": 92, "monetization": 55, "maintenance": 82, "risk": 55},
                    "edge_addons": {"fit": 88, "monetization": 45, "maintenance": 84, "risk": 55},
                    "firefox_addons": {"fit": 82, "monetization": 40, "maintenance": 70, "risk": 55}
                }
            },
        ),
        Asset(
            asset_id="asset_ai_search_field_guide",
            name="A Practical Field Guide to AI Search Visibility",
            vertical_id="international_ebook",
            product_type="EBOOK",
            status=AssetStatus.READY,
            master_source=str((root / "examples" / "ebook" / "master.md").resolve()),
            master_version="0.1.0",
            language="en",
            market="GLOBAL",
            category="business/marketing",
            tags=["AI search", "GEO", "visibility", "experimentation"],
            distribution_mode=DistributionMode.WIDE,
            priority=75,
            human_owner="operator",
            production_cost=0,
            token_cost=0,
            estimated_value=20,
            quality_score=84,
            metadata={
                "rights_confirmed": True,
                "policy_status": "ALLOWED",
                "minimum_quality": 70,
                "ai_usage": "AI_ASSISTED",
                "kdp_select": False,
                "book": {
                    "title": "A Practical Field Guide to AI Search Visibility",
                    "author": "MultiHub GEO",
                    "identifier": "urn:uuid:3bd42b26-57a0-45f4-900c-005966e29181",
                    "description": "A concise experimental manuscript for Distribution OS dry-run validation."
                },
                "platform_scores": {
                    "amazon_kdp": {"fit": 85, "monetization": 72, "maintenance": 75, "risk": 50},
                    "draft2digital": {"fit": 90, "monetization": 65, "maintenance": 82, "risk": 50}
                }
            },
        ),
    ]
    for asset in assets:
        if application.registry.get_asset(asset.asset_id) is None:
            application.registry.upsert_asset(asset)

    experiments = [
        Experiment(
            experiment_id="exp_browser_extension_pilot",
            hypothesis="One Manifest V3 source can produce three policy-reviewable store packages.",
            vertical="browser_extension",
            platform="chrome_web_store,edge_addons,firefox_addons",
            start_date="2026-08-19",
            token_budget=200000,
            time_budget=240,
            money_budget=0,
            success_metric="Three deterministic P2 dry-run packages with no duplicate publication",
            failure_metric="Adapter-specific core fork or policy hard block",
        ),
        Experiment(
            experiment_id="exp_ebook_pilot",
            hypothesis="One Markdown manuscript can become valid EPUB-based packages for direct and aggregator routes.",
            vertical="international_ebook",
            platform="amazon_kdp,draft2digital",
            start_date="2026-08-19",
            token_budget=150000,
            time_budget=180,
            money_budget=0,
            success_metric="Two deterministic P2 dry-run packages with explicit exclusivity metadata",
            failure_metric="Invalid EPUB or accidental downstream duplicate routing",
        ),
    ]
    for experiment in experiments:
        application.registry.upsert_experiment(experiment)
    return {
        "platforms": platform_count,
        "verticals": len(vertical_records),
        "assets": len(assets),
        "experiments": len(experiments),
    }


def demo(application: Application) -> dict[str, object]:
    seed(application)
    routes = [
        ("asset_linklens_extension", "chrome_web_store"),
        ("asset_linklens_extension", "edge_addons"),
        ("asset_linklens_extension", "firefox_addons"),
        ("asset_ai_search_field_guide", "amazon_kdp"),
        ("asset_ai_search_field_guide", "draft2digital"),
    ]
    jobs = [application.distribution.request_dry_run(asset, platform) for asset, platform in routes]
    completed = application.distribution.run_until_empty(max_jobs=20)
    current_jobs = [application.queue.get(job.job_id) or job for job in jobs]
    if not application.registry.list_metrics():
        application.registry.record_metric(
            Metric(
                metric_id=new_id("metric"),
                asset_id="asset_linklens_extension",
                platform_id="chrome_web_store",
                timestamp=utc_now(),
                impressions=120,
                views=38,
                installs=7,
                active_users=5,
                revenue=0,
                cost=0,
                token_cost=0,
                human_minutes=8,
                source="MOCK",
            )
        )
        application.registry.record_metric(
            Metric(
                metric_id=new_id("metric"),
                asset_id="asset_ai_search_field_guide",
                platform_id="amazon_kdp",
                timestamp=utc_now(),
                impressions=300,
                views=42,
                downloads=3,
                revenue=0,
                cost=0,
                token_cost=0,
                human_minutes=12,
                source="MOCK",
            )
        )
    return {
        "requested_jobs": len(jobs),
        "processed_jobs": len(completed),
        "reused_jobs": len(jobs) - len(completed),
        "statuses": [job.status.value for job in current_jobs],
        "outputs": [job.output_url for job in current_jobs],
        "metrics_are_mock": True,
    }
