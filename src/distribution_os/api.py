from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .application import Application
from .health import HealthMonitor
from .models import to_dict, utc_now
from .seed import seed


def create_api(application: Application | None = None) -> FastAPI:
    state = application or Application.create()
    seed(state)
    api = FastAPI(
        title="Distribution OS",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url=None,
    )
    dashboard_dir = Path(__file__).with_name("dashboard")
    api.mount("/static", StaticFiles(directory=dashboard_dir), name="static")

    @api.get("/")
    def index() -> FileResponse:
        return FileResponse(dashboard_dir / "index.html")

    @api.get("/api/overview")
    def overview() -> dict[str, object]:
        counts = state.registry.overview_counts()
        jobs = state.queue.counts()
        health = HealthMonitor(state).run(persist=False)
        analytics = state.analytics.aggregate()
        tokens = state.analytics.token_summary()
        today = utc_now()[:10]
        today_row = state.database.fetch_one(
            "SELECT COUNT(*) AS n FROM jobs WHERE created_at LIKE ?", (f"{today}%",)
        )
        return {
            "counts": counts,
            "jobs": jobs,
            "jobs_today": int(today_row["n"] if today_row else 0),
            "health": {key: value for key, value in health.items() if key != "platforms"},
            "analytics": analytics,
            "tokens": tokens,
            "safety": {
                "dry_run": state.settings.dry_run,
                "real_publishing": state.settings.real_publishing,
                "review_level": state.settings.review_level,
                "global_publish_enabled": state.kill_switch.publishing_enabled(),
            },
            "human_queue": state.registry.serialize_all(
                state.registry.list_reviews("PENDING")[:5]
            ),
            "recent_jobs": state.registry.serialize_all(state.queue.list(8)),
        }

    @api.get("/api/assets")
    def assets() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_assets())

    @api.get("/api/verticals")
    def verticals() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_verticals())

    @api.get("/api/platforms")
    def platforms() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_platforms())

    @api.get("/api/accounts")
    def accounts() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_accounts())

    @api.get("/api/jobs")
    def jobs() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.queue.list())

    @api.get("/api/publications")
    def publications() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_publications())

    @api.get("/api/variants")
    def variants() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_variants())

    @api.get("/api/analytics")
    def analytics() -> dict[str, object]:
        return {
            "aggregate": state.analytics.aggregate(),
            "tokens": state.analytics.token_summary(),
            "metrics": state.registry.serialize_all(state.registry.list_metrics()),
            "mock_data_present": any(
                metric.source == "MOCK" for metric in state.registry.list_metrics()
            ),
        }

    @api.get("/api/experiments")
    def experiments() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_experiments())

    @api.get("/api/human-queue")
    def human_queue() -> list[dict[str, object]]:
        return state.registry.serialize_all(state.registry.list_reviews())

    @api.get("/api/rules")
    def rules() -> list[dict[str, object]]:
        rows = []
        for rule in state.registry.list_rules():
            platform = state.registry.get_platform(rule.platform_id)
            rows.append(
                {
                    **to_dict(rule),
                    "platform_name": platform.platform_name if platform else rule.platform_id,
                    "rule_status": rule.status.value,
                    "last_verified_at": rule.verified_at,
                    "official_docs": rule.evidence_urls,
                    **rule.facts,
                }
            )
        return rows

    @api.get("/api/health")
    def health() -> dict[str, object]:
        return HealthMonitor(state).run(persist=False)

    @api.get("/api/logs")
    def logs() -> list[dict[str, object]]:
        records = state.audit.recent()
        for record in records:
            for key in ("input_json", "output_json"):
                try:
                    record[key] = json.loads(str(record[key]))
                except json.JSONDecodeError:
                    pass
        return records

    @api.get("/api/settings")
    def settings() -> dict[str, object]:
        return {
            "DRY_RUN": state.settings.dry_run,
            "REAL_PUBLISHING": state.settings.real_publishing,
            "REVIEW_LEVEL": state.settings.review_level,
            "GLOBAL_PUBLISH_ENABLED": state.kill_switch.publishing_enabled(),
            "DUPLICATE_PERSONAL_ACCOUNTS": state.database.get_setting(
                "DUPLICATE_PERSONAL_ACCOUNTS", False
            ),
            "ONE_PLATFORM_ONE_PUBLISHER": state.database.get_setting(
                "ONE_PLATFORM_ONE_PUBLISHER", True
            ),
            "MULTI_CHANNEL": state.database.get_setting(
                "MULTI_CHANNEL", "PLATFORM_NATIVE_ONLY"
            ),
            "database": str(state.settings.database_path),
            "platform_ready_dir": str(state.settings.platform_ready_dir),
            "adapter_coverage": state.adapters.coverage(),
        }

    @api.post("/api/kill-switch/stop")
    def stop_all_publishing() -> dict[str, object]:
        state.kill_switch.stop(actor="dashboard", reason="Operator pressed STOP ALL PUBLISHING")
        return {"ok": True, "global_publish_enabled": False}

    @api.post("/api/reviews/{review_id}/{decision}")
    def resolve_review(review_id: str, decision: str) -> dict[str, object]:
        allowed = {"APPROVED", "REJECTED", "CANCELLED"}
        decision = decision.upper()
        if decision not in allowed:
            raise HTTPException(400, f"Decision must be one of {sorted(allowed)}")
        review = state.registry.resolve_review(review_id, decision)
        state.audit.log(
            actor="dashboard",
            action="RESOLVE_REVIEW",
            target_type="HUMAN_REVIEW",
            target_id=review_id,
            reason=decision,
            result="SUCCESS",
        )
        return to_dict(review)

    return api


app = create_api()
