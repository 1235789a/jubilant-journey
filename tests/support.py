from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from distribution_os.application import Application
from distribution_os.config import Settings
from distribution_os.seed import seed


REPO_ROOT = Path(__file__).resolve().parents[1]


class ApplicationTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        temp = Path(self.temporary.name)
        self.settings = Settings(
            project_root=REPO_ROOT,
            database_path=temp / "distribution.db",
            platform_ready_dir=temp / "platform_ready",
            dry_run=True,
            real_publishing=False,
            review_level="L0",
            circuit_breaker_threshold=2,
            circuit_breaker_cooldown_seconds=1,
            job_max_retries=2,
            job_base_backoff_seconds=1,
        )
        self.app = Application.create(self.settings)
        seed(self.app)

    def tearDown(self) -> None:
        self.temporary.cleanup()
