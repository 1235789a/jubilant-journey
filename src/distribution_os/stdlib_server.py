from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .application import Application
from .health import HealthMonitor
from .models import to_dict, utc_now
from .seed import seed


def api_payload(application: Application, endpoint: str) -> Any:
    endpoint = endpoint.strip("/")
    if endpoint == "overview":
        counts = application.registry.overview_counts()
        jobs = application.queue.counts()
        health = HealthMonitor(application).run(persist=False)
        today = utc_now()[:10]
        today_row = application.database.fetch_one(
            "SELECT COUNT(*) AS n FROM jobs WHERE created_at LIKE ?", (f"{today}%",)
        )
        return {
            "counts": counts,
            "jobs": jobs,
            "jobs_today": int(today_row["n"] if today_row else 0),
            "health": {key: value for key, value in health.items() if key != "platforms"},
            "analytics": application.analytics.aggregate(),
            "tokens": application.analytics.token_summary(),
            "safety": {
                "dry_run": application.settings.dry_run,
                "real_publishing": application.settings.real_publishing,
                "review_level": application.settings.review_level,
                "global_publish_enabled": application.kill_switch.publishing_enabled(),
            },
            "human_queue": application.registry.serialize_all(
                application.registry.list_reviews("PENDING")[:5]
            ),
            "recent_jobs": application.registry.serialize_all(application.queue.list(8)),
        }
    if endpoint == "assets":
        return application.registry.serialize_all(application.registry.list_assets())
    if endpoint == "verticals":
        return application.registry.serialize_all(application.registry.list_verticals())
    if endpoint == "platforms":
        return application.registry.serialize_all(application.registry.list_platforms())
    if endpoint == "accounts":
        return application.registry.serialize_all(application.registry.list_accounts())
    if endpoint == "jobs":
        return application.registry.serialize_all(application.queue.list())
    if endpoint == "publications":
        return application.registry.serialize_all(application.registry.list_publications())
    if endpoint == "variants":
        return application.registry.serialize_all(application.registry.list_variants())
    if endpoint == "analytics":
        metrics = application.registry.list_metrics()
        return {
            "aggregate": application.analytics.aggregate(),
            "tokens": application.analytics.token_summary(),
            "metrics": application.registry.serialize_all(metrics),
            "mock_data_present": any(item.source == "MOCK" for item in metrics),
        }
    if endpoint == "experiments":
        return application.registry.serialize_all(application.registry.list_experiments())
    if endpoint == "human-queue":
        return application.registry.serialize_all(application.registry.list_reviews())
    if endpoint == "rules":
        rows = []
        for rule in application.registry.list_rules():
            platform = application.registry.get_platform(rule.platform_id)
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
    if endpoint == "health":
        return HealthMonitor(application).run(persist=False)
    if endpoint == "logs":
        records = application.audit.recent()
        for record in records:
            for key in ("input_json", "output_json"):
                try:
                    record[key] = json.loads(str(record[key]))
                except json.JSONDecodeError:
                    pass
        return records
    if endpoint == "settings":
        return {
            "DRY_RUN": application.settings.dry_run,
            "REAL_PUBLISHING": application.settings.real_publishing,
            "REVIEW_LEVEL": application.settings.review_level,
            "GLOBAL_PUBLISH_ENABLED": application.kill_switch.publishing_enabled(),
            "DUPLICATE_PERSONAL_ACCOUNTS": application.database.get_setting(
                "DUPLICATE_PERSONAL_ACCOUNTS", False
            ),
            "ONE_PLATFORM_ONE_PUBLISHER": application.database.get_setting(
                "ONE_PLATFORM_ONE_PUBLISHER", True
            ),
            "MULTI_CHANNEL": application.database.get_setting(
                "MULTI_CHANNEL", "PLATFORM_NATIVE_ONLY"
            ),
            "database": str(application.settings.database_path),
            "platform_ready_dir": str(application.settings.platform_ready_dir),
            "adapter_coverage": application.adapters.coverage(),
            "server": "stdlib-fallback",
        }
    raise KeyError(endpoint)


def handler_for(application: Application) -> type[BaseHTTPRequestHandler]:
    dashboard = Path(__file__).with_name("dashboard").resolve()

    class Handler(BaseHTTPRequestHandler):
        server_version = "DistributionOS/0.1"

        def _json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _file(self, target: Path) -> None:
            try:
                resolved = target.resolve(strict=True)
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if not resolved.is_relative_to(dashboard) or not resolved.is_file():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            body = resolved.read_bytes()
            content_type = mimetypes.guess_type(resolved.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path == "/":
                self._file(dashboard / "index.html")
                return
            if path.startswith("/static/"):
                self._file(dashboard / path.removeprefix("/static/"))
                return
            if path.startswith("/api/"):
                try:
                    self._json(api_payload(application, path.removeprefix("/api/")))
                except KeyError:
                    self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path == "/api/kill-switch/stop":
                application.kill_switch.stop(
                    actor="dashboard", reason="Operator pressed STOP ALL PUBLISHING"
                )
                self._json({"ok": True, "global_publish_enabled": False})
                return
            if path.startswith("/api/reviews/"):
                parts = path.strip("/").split("/")
                if len(parts) == 4 and parts[0:2] == ["api", "reviews"]:
                    review_id, decision = parts[2], parts[3].upper()
                    if decision not in {"APPROVED", "REJECTED", "CANCELLED"}:
                        self._json({"error": "invalid decision"}, HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        review = application.registry.resolve_review(review_id, decision)
                    except KeyError:
                        self._json({"error": "review not found"}, HTTPStatus.NOT_FOUND)
                        return
                    application.audit.log(
                        actor="dashboard",
                        action="RESOLVE_REVIEW",
                        target_type="HUMAN_REVIEW",
                        target_id=review_id,
                        reason=decision,
                        result="SUCCESS",
                    )
                    self._json(to_dict(review))
                    return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            print(f"dashboard {self.address_string()} {format % args}")

    return Handler


def serve(
    application: Application | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
) -> None:
    state = application or Application.create()
    seed(state)
    server = ThreadingHTTPServer((host, port), handler_for(state))
    print(f"Distribution OS dashboard: http://{host}:{port}")
    print("Server: standard-library fallback (install project dependencies for FastAPI)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
