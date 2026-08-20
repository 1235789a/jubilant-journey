from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from .hashing import stable_key
from .models import Job, JobType

if TYPE_CHECKING:
    from .application import Application


class MaintenanceScheduler:
    """Creates idempotent maintenance jobs; an OS timer invokes `tick` daily."""

    def __init__(self, application: Application):
        self.app = application

    def enqueue_daily(self, now: datetime | None = None) -> list[Job]:
        instant = now or datetime.now(UTC)
        date_key = instant.astimezone(UTC).date().isoformat()
        return [
            self.app.queue.enqueue(
                job_type=JobType.HEALTH_CHECK,
                idempotency_key=stable_key("daily-health", date_key),
                priority=90,
                payload={"schedule": "DAILY", "date": date_key},
            )
        ]
