from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import Settings
from .database import Database
from .models import Job, JobStatus, JobType, new_id, to_json, utc_now
from .safety import CircuitBreaker


def _job(data: dict[str, Any]) -> Job:
    payload = dict(data)
    payload["job_type"] = JobType(payload["job_type"])
    payload["status"] = JobStatus(payload["status"])
    return Job(**payload)


class JobQueue:
    def __init__(
        self, database: Database, settings: Settings, circuit_breaker: CircuitBreaker
    ):
        self.db = database
        self.settings = settings
        self.circuit_breaker = circuit_breaker

    def enqueue(
        self,
        *,
        job_type: JobType,
        idempotency_key: str,
        asset_id: str | None = None,
        platform_id: str | None = None,
        account_id: str | None = None,
        priority: int = 50,
        payload: dict[str, Any] | None = None,
        scheduled_at: str | None = None,
    ) -> Job:
        existing = self.db.fetch_one(
            "SELECT data_json FROM jobs WHERE idempotency_key=?", (idempotency_key,)
        )
        if existing:
            return _job(json.loads(existing["data_json"]))
        job = Job(
            job_id=new_id("job"),
            asset_id=asset_id,
            platform_id=platform_id,
            account_id=account_id,
            job_type=job_type,
            priority=priority,
            status=JobStatus.PENDING,
            idempotency_key=idempotency_key,
            payload=payload or {},
            scheduled_at=scheduled_at or utc_now(),
            max_retries=self.settings.job_max_retries,
        )
        self._insert(job)
        return job

    def _insert(self, job: Job) -> None:
        self.db.execute(
            """
            INSERT INTO jobs(
                job_id, asset_id, platform_id, account_id, job_type, priority,
                status, idempotency_key, scheduled_at, retry_count, data_json,
                created_at, started_at, finished_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.job_id,
                job.asset_id,
                job.platform_id,
                job.account_id,
                job.job_type.value,
                job.priority,
                job.status.value,
                job.idempotency_key,
                job.scheduled_at,
                job.retry_count,
                to_json(job),
                job.created_at,
                job.started_at,
                job.finished_at,
            ),
        )

    def _save(self, job: Job) -> None:
        self.db.execute(
            """
            UPDATE jobs SET status=?, scheduled_at=?, retry_count=?, data_json=?,
                started_at=?, finished_at=? WHERE job_id=?
            """,
            (
                job.status.value,
                job.scheduled_at,
                job.retry_count,
                to_json(job),
                job.started_at,
                job.finished_at,
                job.job_id,
            ),
        )

    def get(self, job_id: str) -> Job | None:
        row = self.db.fetch_one("SELECT data_json FROM jobs WHERE job_id=?", (job_id,))
        return None if row is None else _job(json.loads(row["data_json"]))

    def list(self, limit: int = 200) -> list[Job]:
        rows = self.db.fetch_all(
            "SELECT data_json FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        return [_job(json.loads(row["data_json"])) for row in rows]

    def claim_next(self) -> Job | None:
        with self.db.transaction(immediate=True) as connection:
            row = connection.execute(
                """
                SELECT job_id, data_json FROM jobs
                WHERE status IN ('PENDING', 'RETRYING') AND scheduled_at <= ?
                ORDER BY priority DESC, created_at ASC LIMIT 1
                """,
                (utc_now(),),
            ).fetchone()
            if row is None:
                return None
            job = _job(json.loads(row["data_json"]))
            job.status = JobStatus.RUNNING
            job.started_at = utc_now()
            job.logs.append(f"{job.started_at} claimed")
            connection.execute(
                """
                UPDATE jobs SET status='RUNNING', started_at=?, data_json=?
                WHERE job_id=? AND status IN ('PENDING', 'RETRYING')
                """,
                (job.started_at, to_json(job), job.job_id),
            )
            if connection.total_changes != 1:
                return None
            return job

    def complete(
        self,
        job: Job,
        *,
        output_url: str | None = None,
        token_usage: int = 0,
        message: str = "completed",
    ) -> Job:
        job.status = JobStatus.SUCCESS
        job.finished_at = utc_now()
        job.output_url = output_url
        job.token_usage += token_usage
        job.logs.append(f"{job.finished_at} {message}")
        self._save(job)
        if job.platform_id:
            self.circuit_breaker.record_success(job.platform_id)
        return job

    def wait_for_human(self, job: Job, reason: str) -> Job:
        job.status = JobStatus.WAITING_HUMAN
        job.error = reason
        job.logs.append(f"{utc_now()} waiting for human: {reason}")
        self._save(job)
        return job

    def block(self, job: Job, reason: str) -> Job:
        job.status = JobStatus.BLOCKED
        job.error = reason
        job.finished_at = utc_now()
        job.logs.append(f"{job.finished_at} blocked: {reason}")
        self._save(job)
        return job

    def fail(self, job: Job, error: Exception | str) -> Job:
        message = str(error)[:2000]
        job.error = message
        job.retry_count += 1
        job.logs.append(f"{utc_now()} failure {job.retry_count}: {message}")
        if job.platform_id:
            self.circuit_breaker.record_failure(job.platform_id, message)
        if job.retry_count > job.max_retries:
            job.status = JobStatus.DEAD_LETTER
            job.finished_at = utc_now()
        else:
            job.status = JobStatus.RETRYING
            delay = self.settings.job_base_backoff_seconds * (2 ** (job.retry_count - 1))
            job.scheduled_at = (datetime.now(UTC) + timedelta(seconds=delay)).isoformat()
        self._save(job)
        return job

    def recover_stuck(self, timeout_minutes: int = 30) -> int:
        threshold = (datetime.now(UTC) - timedelta(minutes=timeout_minutes)).isoformat()
        rows = self.db.fetch_all(
            "SELECT data_json FROM jobs WHERE status='RUNNING' AND started_at < ?",
            (threshold,),
        )
        for row in rows:
            self.fail(_job(json.loads(row["data_json"])), "stuck job recovered")
        return len(rows)

    def counts(self) -> dict[str, int]:
        rows = self.db.fetch_all("SELECT status, COUNT(*) AS n FROM jobs GROUP BY status")
        return {str(row["status"]): int(row["n"]) for row in rows}
