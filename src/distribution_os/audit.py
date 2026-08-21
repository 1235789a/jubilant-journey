from __future__ import annotations

import json
from typing import Any

from .database import Database
from .models import utc_now
from .security import redact


class AuditLogger:
    def __init__(self, database: Database):
        self.db = database

    def log(
        self,
        *,
        actor: str,
        action: str,
        target_type: str,
        target_id: str | None,
        reason: str,
        input_data: dict[str, Any] | None = None,
        output_data: dict[str, Any] | None = None,
        token_usage: int = 0,
        result: str,
    ) -> None:
        self.db.execute(
            """
            INSERT INTO audit_logs(
                timestamp, actor, action, target_type, target_id, reason,
                input_json, output_json, token_usage, result
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utc_now(),
                actor,
                action,
                target_type,
                target_id,
                reason,
                json.dumps(redact(input_data or {}), ensure_ascii=False, sort_keys=True),
                json.dumps(redact(output_data or {}), ensure_ascii=False, sort_keys=True),
                token_usage,
                result,
            ),
        )

    def recent(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.db.fetch_all(
            "SELECT * FROM audit_logs ORDER BY audit_id DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in rows]
