from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from .models import HealthStatus, new_id, utc_now

if TYPE_CHECKING:
    from .application import Application


class HealthMonitor:
    def __init__(self, application: Application):
        self.app = application

    def check_platform(self, platform_id: str) -> dict[str, object]:
        platform = self.app.registry.get_platform(platform_id)
        if platform is None:
            return {"platform_id": platform_id, "status": HealthStatus.BROKEN.value, "reasons": ["NOT_REGISTERED"]}
        reasons: list[str] = []
        status = HealthStatus.HEALTHY
        if platform.last_verified_at is None:
            status = HealthStatus.ACTION_REQUIRED
            reasons.append("RULES_NEVER_VERIFIED")
        else:
            verified_at = datetime.fromisoformat(platform.last_verified_at)
            if datetime.now(UTC) - verified_at > timedelta(days=self.app.settings.rule_freshness_days):
                status = HealthStatus.RULE_OUTDATED
                reasons.append("RULE_FRESHNESS_EXPIRED")
        if platform.rule_status.value != "VERIFIED" and status is HealthStatus.HEALTHY:
            status = HealthStatus.ACTION_REQUIRED
            reasons.append(f"RULE_STATUS_{platform.rule_status.value}")
        circuit = self.app.circuit_breaker.state(platform_id)
        if circuit == "OPEN":
            status = HealthStatus.BROKEN
            reasons.append("CIRCUIT_OPEN")
        elif circuit == "HALF_OPEN" and status is not HealthStatus.BROKEN:
            status = HealthStatus.DEGRADED
            reasons.append("CIRCUIT_HALF_OPEN")
        adapter = self.app.adapters.get(platform_id)
        if platform.adapter_maturity.value != "P0" and adapter is None:
            status = HealthStatus.BROKEN
            reasons.append("DECLARED_ADAPTER_MISSING")
        return {
            "platform_id": platform_id,
            "platform_name": platform.platform_name,
            "status": status.value,
            "reasons": reasons,
            "circuit": circuit,
            "adapter_maturity": platform.adapter_maturity.value,
            "last_verified_at": platform.last_verified_at,
        }

    def run(self, persist: bool = True) -> dict[str, object]:
        platforms = [self.check_platform(item.platform_id) for item in self.app.registry.list_platforms()]
        self.app.queue.recover_stuck()
        counts: dict[str, int] = {}
        for item in platforms:
            status = str(item["status"])
            counts[status] = counts.get(status, 0) + 1
            if persist:
                self.app.database.execute(
                    """
                    INSERT INTO health_snapshots(
                        snapshot_id, timestamp, component_type, component_id, status, details_json
                    ) VALUES (?, ?, 'PLATFORM', ?, ?, ?)
                    """,
                    (
                        new_id("health"),
                        utc_now(),
                        item["platform_id"],
                        item["status"],
                        json.dumps(item, ensure_ascii=False, sort_keys=True),
                    ),
                )
        failed_jobs = self.app.database.fetch_one(
            "SELECT COUNT(*) AS n FROM jobs WHERE status IN ('FAILED','DEAD_LETTER','BLOCKED')"
        )
        return {
            "checked_at": utc_now(),
            "summary": counts,
            "healthy": counts.get("HEALTHY", 0),
            "total": len(platforms),
            "failed_jobs": int(failed_jobs["n"] if failed_jobs else 0),
            "global_publish_enabled": self.app.kill_switch.publishing_enabled(),
            "dry_run": self.app.settings.dry_run,
            "real_publishing": self.app.settings.real_publishing,
            "platforms": platforms,
        }
