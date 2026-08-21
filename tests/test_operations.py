from __future__ import annotations

from datetime import UTC, datetime

from distribution_os.database import Database

from support import ApplicationTestCase


class OperationsTests(ApplicationTestCase):
    def test_online_backup_is_complete_and_refuses_overwrite(self) -> None:
        destination = self.settings.database_path.parent / "backup.db"
        result = self.app.database.backup(destination)
        self.assertEqual(result["integrity_check"], "ok")
        snapshot = Database(destination)
        self.assertEqual(
            snapshot.fetch_one("SELECT COUNT(*) AS n FROM platforms")["n"], 31
        )
        with self.assertRaises(FileExistsError):
            self.app.database.backup(destination)

    def test_daily_scheduler_is_idempotent_and_persists_health(self) -> None:
        instant = datetime(2026, 8, 19, 12, tzinfo=UTC)
        first = self.app.scheduler.enqueue_daily(instant)[0]
        second = self.app.scheduler.enqueue_daily(instant)[0]
        self.assertEqual(first.job_id, second.job_id)
        [completed] = self.app.worker.run_until_empty()
        self.assertEqual(completed.status.value, "SUCCESS")
        count = self.app.database.fetch_one(
            "SELECT COUNT(*) AS n FROM health_snapshots"
        )
        self.assertEqual(count["n"], 31)
