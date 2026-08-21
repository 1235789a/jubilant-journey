from __future__ import annotations

from pathlib import Path

from .config import Settings
from .hashing import content_hash
from .models import (
    Account,
    AdapterMaturity,
    Asset,
    AssetStatus,
    DistributionMode,
    Platform,
    ReviewLevel,
    RouteDecision,
    RouteResult,
    RuleStatus,
)
from .registry import Registry
from .safety import CircuitBreaker, KillSwitch
from .scoring import platform_score


class RuleEngine:
    HARD_BLOCK_POLICY_VALUES = {"BLOCKED", "REJECT", "INFRINGEMENT", "DISALLOWED"}

    def evaluate(
        self,
        *,
        asset: Asset,
        platform: Platform,
        account: Account | None,
        dry_run: bool,
        current_publication_platforms: set[str],
    ) -> tuple[list[str], list[str]]:
        blockers: list[str] = []
        warnings: list[str] = []

        if asset.vertical_id not in platform.verticals_supported:
            blockers.append("VERTICAL_NOT_SUPPORTED")
        if asset.status not in {AssetStatus.READY, AssetStatus.ACTIVE, AssetStatus.PUBLISHING}:
            blockers.append("ASSET_NOT_READY")
        minimum_quality = float(asset.metadata.get("minimum_quality", 60))
        if asset.quality_score < minimum_quality:
            blockers.append("MINIMUM_QUALITY_NOT_MET")
        if not bool(asset.metadata.get("rights_confirmed", False)):
            blockers.append("RIGHTS_NOT_CONFIRMED")
        if str(asset.metadata.get("policy_status", "UNKNOWN")).upper() in self.HARD_BLOCK_POLICY_VALUES:
            blockers.append("BLOCKED_BY_POLICY")

        exclusive_target = asset.metadata.get("exclusive_platform_id")
        if asset.distribution_mode is DistributionMode.EXCLUSIVE:
            if exclusive_target and exclusive_target != platform.platform_id:
                blockers.append("BLOCKED_BY_EXCLUSIVITY")
            if current_publication_platforms - {platform.platform_id}:
                blockers.append("EXCLUSIVITY_CONFLICT")
        elif asset.distribution_mode is DistributionMode.UNDECIDED:
            warnings.append("DISTRIBUTION_MODE_UNDECIDED")

        if platform.rule_status is not RuleStatus.VERIFIED:
            warnings.append(f"RULE_STATUS_{platform.rule_status.value}")
        if platform.adapter_maturity is AdapterMaturity.P0:
            blockers.append("ADAPTER_REGISTRY_ONLY")

        if account is None:
            warnings.append("ACCOUNT_NOT_CONFIGURED")
        else:
            if account.platform_id != platform.platform_id:
                blockers.append("ACCOUNT_PLATFORM_MISMATCH")
            if account.status != "ACTIVE":
                warnings.append("ACCOUNT_NOT_ACTIVE")
            if account.country in platform.country_restrictions:
                blockers.append("BLOCKED_BY_REGION")
            if account.age_status == "MINOR":
                warnings.append(
                    "GUARDIAN_REQUIRED"
                    if platform.guardian_supported
                    else "BLOCKED_BY_AGE"
                )
            elif platform.age_requirement and account.age_status not in {
                "ADULT_VERIFIED",
                "GUARDIAN_MANAGED",
            }:
                warnings.append("AGE_NOT_VERIFIED")

        if not dry_run:
            if platform.rule_status is not RuleStatus.VERIFIED:
                blockers.append("LIVE_REQUIRES_VERIFIED_RULES")
            if platform.adapter_maturity is not AdapterMaturity.P3:
                blockers.append("LIVE_ADAPTER_NOT_SUPPORTED")
            if not platform.live_publish:
                blockers.append("PLATFORM_LIVE_PUBLISH_LOCKED")
            if account is None or not account.credential_reference:
                blockers.append("CREDENTIAL_REQUIRED")
            if account is None or not account.payout_ready:
                blockers.append("PAYOUT_NOT_READY")
            if account and account.age_status == "MINOR":
                blockers.append("AGE_GATE")
            if platform.manual_only_actions:
                blockers.append("MANUAL_ACTION_REQUIRED")

        return list(dict.fromkeys(blockers)), list(dict.fromkeys(warnings))


class PlatformRouter:
    def __init__(
        self,
        registry: Registry,
        settings: Settings,
        rule_engine: RuleEngine,
        kill_switch: KillSwitch,
        circuit_breaker: CircuitBreaker,
    ):
        self.registry = registry
        self.settings = settings
        self.rule_engine = rule_engine
        self.kill_switch = kill_switch
        self.circuit_breaker = circuit_breaker

    def route(
        self,
        *,
        asset: Asset,
        platform: Platform,
        account: Account | None = None,
        dry_run: bool = True,
        approval_review_id: str | None = None,
        risk_level: str = "HIGH",
    ) -> RouteResult:
        source_hash = content_hash(Path(asset.master_source))
        account_key = account.account_id if account else "DRY_RUN"
        existing = self.registry.find_publication(
            source_hash,
            platform.platform_id,
            account_key,
            asset.master_version,
        )
        if existing:
            return RouteResult(
                decision=RouteDecision.ALREADY_PUBLISHED,
                can_package=False,
                can_publish=False,
                score=platform_score(asset, platform),
                warnings=[existing.output_url or "publication exists"],
            )

        publications = self.registry.publications_for_asset(asset.asset_id)
        current_platforms = {
            item.platform_id
            for item in publications
            if item.status not in {"CANCELLED", "UNPUBLISHED"}
        }
        blockers, warnings = self.rule_engine.evaluate(
            asset=asset,
            platform=platform,
            account=account,
            dry_run=dry_run,
            current_publication_platforms=current_platforms,
        )

        circuit_state = self.circuit_breaker.state(platform.platform_id)
        if circuit_state == "OPEN":
            blockers.append("PLATFORM_CIRCUIT_OPEN")
        elif circuit_state == "HALF_OPEN":
            warnings.append("PLATFORM_CIRCUIT_HALF_OPEN")

        if not dry_run:
            if self.settings.dry_run:
                blockers.append("SYSTEM_DRY_RUN_ENABLED")
            if not self.settings.real_publishing:
                blockers.append("REAL_PUBLISHING_DISABLED")
            if not self.kill_switch.publishing_enabled():
                blockers.append("GLOBAL_KILL_SWITCH_ACTIVE")
            try:
                review_level = ReviewLevel(self.settings.review_level)
            except ValueError:
                blockers.append("REVIEW_LEVEL_INVALID")
            else:
                review = self.registry.get_review(approval_review_id)
                review_approved = bool(
                    review
                    and review.status == "APPROVED"
                    and review.action == "APPROVE_LIVE_PUBLICATION"
                    and review.asset_id == asset.asset_id
                    and review.platform_id == platform.platform_id
                )
                if review_level is ReviewLevel.L0 and not review_approved:
                    blockers.append("L0_HUMAN_APPROVAL_REQUIRED")
                elif (
                    review_level is ReviewLevel.L1
                    and risk_level.upper() in {"HIGH", "CRITICAL"}
                    and not review_approved
                ):
                    blockers.append("L1_HIGH_RISK_APPROVAL_REQUIRED")

        package_blockers = {
            "VERTICAL_NOT_SUPPORTED",
            "ASSET_NOT_READY",
            "MINIMUM_QUALITY_NOT_MET",
            "RIGHTS_NOT_CONFIRMED",
            "BLOCKED_BY_POLICY",
            "BLOCKED_BY_EXCLUSIVITY",
            "EXCLUSIVITY_CONFLICT",
            "ADAPTER_REGISTRY_ONLY",
            "ACCOUNT_PLATFORM_MISMATCH",
            "BLOCKED_BY_REGION",
            "PLATFORM_CIRCUIT_OPEN",
        }
        can_package = not any(item in package_blockers for item in blockers)
        can_publish = not blockers and not warnings and not dry_run
        if blockers and not can_package:
            decision = RouteDecision.BLOCKED
        elif dry_run and warnings:
            decision = RouteDecision.REVIEW_REQUIRED
        elif dry_run:
            decision = RouteDecision.ALLOW_DRY_RUN
        elif can_publish:
            decision = RouteDecision.ALLOW_LIVE
        else:
            decision = RouteDecision.BLOCKED
        return RouteResult(
            decision=decision,
            can_package=can_package,
            can_publish=can_publish,
            score=platform_score(asset, platform),
            blockers=list(dict.fromkeys(blockers)),
            warnings=list(dict.fromkeys(warnings)),
        )

    def rank_candidates(self, asset: Asset) -> list[dict[str, float | str]]:
        candidates = [
            platform
            for platform in self.registry.list_platforms()
            if asset.vertical_id in platform.verticals_supported
            and platform.adapter_maturity is not AdapterMaturity.P0
        ]
        ranked = [
            {
                "platform_id": platform.platform_id,
                "platform_name": platform.platform_name,
                "score": platform_score(asset, platform),
            }
            for platform in candidates
        ]
        return sorted(ranked, key=lambda item: (-float(item["score"]), str(item["platform_id"])))

    def recommended_targets(self, asset: Asset) -> list[str]:
        ranked = self.rank_candidates(asset)
        if not ranked:
            return []
        explicit = asset.metadata.get("exclusive_platform_id")
        if asset.distribution_mode is DistributionMode.EXCLUSIVE:
            if explicit:
                return [
                    str(item["platform_id"])
                    for item in ranked
                    if item["platform_id"] == explicit
                ]
            return [str(ranked[0]["platform_id"])]
        if asset.distribution_mode is DistributionMode.UNDECIDED:
            return []
        return [str(item["platform_id"]) for item in ranked]
