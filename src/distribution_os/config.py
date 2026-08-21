from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path) -> None:
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value[:1] == value[-1:] and value.startswith(("'", '"')):
            value = value[1:-1]
        if key and key.replace("_", "").isalnum():
            os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class Settings:
    project_root: Path
    database_path: Path
    platform_ready_dir: Path
    dry_run: bool = True
    real_publishing: bool = False
    review_level: str = "L0"
    rule_freshness_days: int = 30
    circuit_breaker_threshold: int = 3
    circuit_breaker_cooldown_seconds: int = 3600
    job_max_retries: int = 3
    job_base_backoff_seconds: int = 30
    host: str = "127.0.0.1"
    port: int = 8787

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> "Settings":
        root = (project_root or Path.cwd()).resolve()
        _load_env_file(root / ".env")
        db_url = os.getenv("DATABASE_URL", "sqlite:///data/distribution_os.db")
        if not db_url.startswith("sqlite:///"):
            raise ValueError("V1 supports sqlite:/// DATABASE_URL values only")
        raw_db_path = Path(db_url.removeprefix("sqlite:///"))
        db_path = raw_db_path if raw_db_path.is_absolute() else root / raw_db_path
        ready = Path(os.getenv("PLATFORM_READY_DIR", "platform_ready"))
        ready_path = ready if ready.is_absolute() else root / ready
        return cls(
            project_root=root,
            database_path=db_path,
            platform_ready_dir=ready_path,
            dry_run=_bool("DRY_RUN", True),
            real_publishing=_bool("REAL_PUBLISHING", False),
            review_level=os.getenv("REVIEW_LEVEL", "L0").upper(),
            rule_freshness_days=int(os.getenv("RULE_FRESHNESS_DAYS", "30")),
            circuit_breaker_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "3")),
            circuit_breaker_cooldown_seconds=int(
                os.getenv("CIRCUIT_BREAKER_COOLDOWN_SECONDS", "3600")
            ),
            job_max_retries=int(os.getenv("JOB_MAX_RETRIES", "3")),
            job_base_backoff_seconds=int(
                os.getenv("JOB_BASE_BACKOFF_SECONDS", "30")
            ),
            host=os.getenv("HOST", "127.0.0.1"),
            port=int(os.getenv("PORT", "8787")),
        )

    def ensure_directories(self) -> None:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.platform_ready_dir.mkdir(parents=True, exist_ok=True)
