from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from .audit import AuditLogger
from .config import Settings
from .database import Database
from .models import utc_now


class KillSwitch:
    KEY = "global_publish_enabled"

    def __init__(self, database: Database, audit: AuditLogger):
        self.db = database
        self.audit = audit

    def initialize(self) -> None:
        if self.db.get_setting(self.KEY) is None:
            self.db.set_setting(self.KEY, False, utc_now())

    def publishing_enabled(self) -> bool:
        return bool(self.db.get_setting(self.KEY, False))

    def stop(self, actor: str = "operator", reason: str = "Global kill switch") -> None:
        self.db.set_setting(self.KEY, False, utc_now())
        finished_at = utc_now()
        rows = self.db.fetch_all(
            """
            SELECT job_id, data_json FROM jobs
            WHERE status IN ('PENDING', 'RETRYING') AND job_type='PUBLISH'
            """
        )
        for row in rows:
            payload = json.loads(row["data_json"])
            if bool(payload.get("payload", {}).get("dry_run", False)):
                continue
            payload["status"] = "CANCELLED"
            payload["finished_at"] = finished_at
            payload.setdefault("logs", []).append(
                f"{finished_at} cancelled by global kill switch"
            )
            self.db.execute(
                """
                UPDATE jobs SET status='CANCELLED', finished_at=?, data_json=?
                WHERE job_id=?
                """,
                (
                    finished_at,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    row["job_id"],
                ),
            )
        self.audit.log(
            actor=actor,
            action="STOP_ALL_PUBLISHING",
            target_type="SYSTEM",
            target_id=None,
            reason=reason,
            result="SUCCESS",
        )

    def request_enable(self, actor: str = "operator") -> None:
        self.audit.log(
            actor=actor,
            action="REQUEST_ENABLE_PUBLISHING",
            target_type="SYSTEM",
            target_id=None,
            reason="V1 requires code/config review before enabling",
            result="REVIEW_REQUIRED",
        )
        raise PermissionError("V1 cannot enable real publishing from the dashboard")


class CircuitBreaker:
    def __init__(self, database: Database, settings: Settings):
        self.db = database
        self.settings = settings

    def _ensure(self, platform_id: str) -> None:
        self.db.execute(
            """
            INSERT INTO circuit_breakers(platform_id) VALUES (?)
            ON CONFLICT(platform_id) DO NOTHING
            """,
            (platform_id,),
        )

    def state(self, platform_id: str) -> str:
        self._ensure(platform_id)
        row = self.db.fetch_one(
            "SELECT state, opened_at FROM circuit_breakers WHERE platform_id=?",
            (platform_id,),
        )
        if row is None:
            return "CLOSED"
        if row["state"] == "OPEN" and row["opened_at"]:
            opened = datetime.fromisoformat(row["opened_at"])
            if datetime.now(UTC) - opened >= timedelta(
                seconds=self.settings.circuit_breaker_cooldown_seconds
            ):
                self.db.execute(
                    "UPDATE circuit_breakers SET state='HALF_OPEN' WHERE platform_id=?",
                    (platform_id,),
                )
                return "HALF_OPEN"
        return str(row["state"])

    def record_success(self, platform_id: str) -> None:
        self._ensure(platform_id)
        self.db.execute(
            """
            UPDATE circuit_breakers
            SET failure_count=0, state='CLOSED', opened_at=NULL, last_error=NULL
            WHERE platform_id=?
            """,
            (platform_id,),
        )

    def record_failure(self, platform_id: str, error: str) -> str:
        self._ensure(platform_id)
        with self.db.transaction(immediate=True) as connection:
            row = connection.execute(
                "SELECT failure_count FROM circuit_breakers WHERE platform_id=?",
                (platform_id,),
            ).fetchone()
            failures = int(row["failure_count"]) + 1
            state = (
                "OPEN"
                if failures >= self.settings.circuit_breaker_threshold
                else "CLOSED"
            )
            connection.execute(
                """
                UPDATE circuit_breakers
                SET failure_count=?, state=?, opened_at=?, last_failure_at=?, last_error=?
                WHERE platform_id=?
                """,
                (
                    failures,
                    state,
                    utc_now() if state == "OPEN" else None,
                    utc_now(),
                    error[:1000],
                    platform_id,
                ),
            )
        return state

    def all_states(self) -> list[dict[str, object]]:
        return [
            dict(row)
            for row in self.db.fetch_all(
                "SELECT * FROM circuit_breakers ORDER BY platform_id"
            )
        ]
