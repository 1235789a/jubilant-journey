from __future__ import annotations

from pathlib import Path

from .adapters import AdapterRegistry
from .audit import AuditLogger
from .config import Settings
from .hashing import content_hash, stable_key
from .jobs import JobQueue
from .models import (
    HumanReview,
    Job,
    JobType,
    Publication,
    RouteDecision,
    new_id,
    Variant,
    to_dict,
)
from .registry import Registry
from .router import PlatformRouter


class DistributionService:
    def __init__(
        self,
        *,
        settings: Settings,
        registry: Registry,
        adapters: AdapterRegistry,
        router: PlatformRouter,
        queue: JobQueue,
        audit: AuditLogger,
    ):
        self.settings = settings
        self.registry = registry
        self.adapters = adapters
        self.router = router
        self.queue = queue
        self.audit = audit

    def request_dry_run(
        self,
        asset_id: str,
        platform_id: str,
        account_id: str | None = None,
        priority: int = 50,
    ) -> Job:
        asset = self.registry.get_asset(asset_id)
        if asset is None:
            raise KeyError(f"Unknown asset: {asset_id}")
        digest = content_hash(Path(asset.master_source))
        return self.queue.enqueue(
            job_type=JobType.PUBLISH,
            idempotency_key=stable_key(
                "dry-run", asset_id, platform_id, account_id or "DRY_RUN", asset.master_version, digest
            ),
            asset_id=asset_id,
            platform_id=platform_id,
            account_id=account_id,
            priority=priority,
            payload={"dry_run": True},
        )

    def execute(self, job: Job) -> Job:
        if job.job_type is not JobType.PUBLISH:
            return self.queue.block(job, f"Unsupported worker job type: {job.job_type.value}")
        asset = self.registry.get_asset(job.asset_id or "")
        platform = self.registry.get_platform(job.platform_id or "")
        account = self.registry.get_account(job.account_id)
        if asset is None or platform is None:
            return self.queue.block(job, "Asset or platform disappeared")
        dry_run = bool(job.payload.get("dry_run", True))
        route = self.router.route(
            asset=asset,
            platform=platform,
            account=account,
            dry_run=dry_run,
            approval_review_id=job.payload.get("approval_review_id"),
            risk_level=str(asset.metadata.get("risk_level", "HIGH")),
        )
        if route.decision is RouteDecision.ALREADY_PUBLISHED:
            self.audit.log(
                actor="distribution_worker",
                action="DISTRIBUTE",
                target_type="ASSET",
                target_id=asset.asset_id,
                reason="Duplicate protection",
                input_data={"platform_id": platform.platform_id},
                output_data=to_dict(route),
                result="ALREADY_PUBLISHED",
            )
            return self.queue.complete(job, message="ALREADY_PUBLISHED")
        if not dry_run and not route.can_publish:
            reason = ", ".join(route.blockers + route.warnings) or "Live route blocked"
            self.audit.log(
                actor="distribution_worker",
                action="LIVE_DISTRIBUTE",
                target_type="ASSET",
                target_id=asset.asset_id,
                reason=reason,
                input_data={"platform_id": platform.platform_id},
                output_data=to_dict(route),
                result="BLOCKED",
            )
            return self.queue.block(job, reason)
        if not route.can_package:
            reason = ", ".join(route.blockers) or "Route blocked"
            self.audit.log(
                actor="distribution_worker",
                action="DISTRIBUTE",
                target_type="ASSET",
                target_id=asset.asset_id,
                reason=reason,
                input_data={"platform_id": platform.platform_id},
                output_data=to_dict(route),
                result="BLOCKED",
            )
            return self.queue.block(job, reason)
        adapter = self.adapters.get(platform.platform_id)
        if adapter is None:
            return self.queue.block(job, "Adapter is registry-only")
        if route.warnings or route.blockers:
            self.registry.create_review(
                HumanReview(
                    review_id=new_id("review"),
                    job_id=job.job_id,
                    asset_id=asset.asset_id,
                    platform_id=platform.platform_id,
                    action="REVIEW_DRY_RUN_PACKAGE",
                    reason=", ".join(route.warnings + route.blockers),
                    risk_level="HIGH" if route.blockers else "MEDIUM",
                )
            )
        result = adapter.prepare(asset, platform, self.settings.platform_ready_dir)
        if result.status != "PACKAGE_READY" or not result.artifact_path:
            reason = ", ".join(result.errors) or result.status
            self.audit.log(
                actor="distribution_worker",
                action="ADAPTER_PREPARE",
                target_type="ASSET",
                target_id=asset.asset_id,
                reason=reason,
                output_data=to_dict(result),
                result="FAILED",
            )
            return self.queue.fail(job, reason)
        digest = content_hash(Path(asset.master_source))
        variant = self.registry.find_variant(
            asset_id=asset.asset_id,
            platform_id=platform.platform_id,
            asset_version=asset.master_version,
            adapter_version=adapter.version,
            content_hash=digest,
        )
        if variant is None:
            variant = self.registry.record_variant(
                Variant(
                    variant_id=new_id("variant"),
                    asset_id=asset.asset_id,
                    platform_id=platform.platform_id,
                    asset_version=asset.master_version,
                    adapter_name=adapter.name,
                    adapter_version=adapter.version,
                    content_hash=digest,
                    artifact_path=result.artifact_path,
                    status="PACKAGE_READY",
                    metadata=result.metadata,
                )
            )
        publication = Publication(
            publication_id=new_id("pub"),
            asset_id=asset.asset_id,
            platform_id=platform.platform_id,
            account_id=account.account_id if account else "DRY_RUN",
            asset_version=asset.master_version,
            content_hash=digest,
            status=(
                "REVIEW_REQUIRED_PACKAGE"
                if route.decision is RouteDecision.REVIEW_REQUIRED
                else "DRY_RUN_READY"
            ),
            mode="DRY_RUN" if dry_run else "LIVE",
            output_url=result.artifact_path,
            adapter_version=adapter.version,
            job_id=job.job_id,
            variant_id=variant.variant_id,
        )
        try:
            self.registry.record_publication(publication)
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                return self.queue.complete(job, message="ALREADY_PUBLISHED")
            raise
        self.audit.log(
            actor="distribution_worker",
            action="ADAPTER_PREPARE",
            target_type="PUBLICATION",
            target_id=publication.publication_id,
            reason="Dry-run package generated",
            input_data={
                "asset_id": asset.asset_id,
                "platform_id": platform.platform_id,
                "adapter": adapter.name,
            },
            output_data={
                "artifact_path": result.artifact_path,
                "route": to_dict(route),
            },
            result="SUCCESS",
        )
        return self.queue.complete(
            job,
            output_url=result.artifact_path,
            message=f"{result.status}; no upload performed",
        )

    def run_until_empty(self, max_jobs: int = 100) -> list[Job]:
        completed: list[Job] = []
        for _ in range(max_jobs):
            job = self.queue.claim_next()
            if job is None:
                break
            try:
                completed.append(self.execute(job))
            except Exception as exc:
                completed.append(self.queue.fail(job, exc))
        return completed
