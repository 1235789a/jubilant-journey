from __future__ import annotations

from typing import TYPE_CHECKING

from .health import HealthMonitor
from .models import Job, JobType

if TYPE_CHECKING:
    from .application import Application


class Worker:
    """Central job dispatcher; unsupported job types fail closed."""

    def __init__(self, application: Application):
        self.app = application

    def execute(self, job: Job) -> Job:
        if job.job_type is JobType.PUBLISH:
            return self.app.distribution.execute(job)
        if job.job_type is JobType.HEALTH_CHECK:
            result = HealthMonitor(self.app).run(persist=True)
            self.app.audit.log(
                actor="maintenance_worker",
                action="HEALTH_CHECK",
                target_type="SYSTEM",
                target_id=None,
                reason="Scheduled daily health check",
                input_data=job.payload,
                output_data={
                    "healthy": result["healthy"],
                    "total": result["total"],
                    "failed_jobs": result["failed_jobs"],
                },
                result="SUCCESS",
            )
            return self.app.queue.complete(job, message="daily health check completed")
        return self.app.queue.block(
            job, f"No V1 worker handler for {job.job_type.value}"
        )

    def run_until_empty(self, max_jobs: int = 100) -> list[Job]:
        completed: list[Job] = []
        for _ in range(max_jobs):
            job = self.app.queue.claim_next()
            if job is None:
                break
            try:
                completed.append(self.execute(job))
            except Exception as exc:
                completed.append(self.app.queue.fail(job, exc))
        return completed
