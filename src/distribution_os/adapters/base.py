from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
import re
from typing import Any

from ..models import AdapterResult, Asset, Platform


SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def output_target(
    output_root: Path, platform_slug: str, asset_id: str, asset_version: str
) -> Path:
    for label, value in {
        "platform_slug": platform_slug,
        "asset_id": asset_id,
        "asset_version": asset_version,
    }.items():
        if not SAFE_SEGMENT.fullmatch(value):
            raise ValueError(f"Unsafe {label}: {value!r}")
    root = output_root.resolve()
    target = (root / platform_slug / asset_id / asset_version).resolve()
    if not target.is_relative_to(root):
        raise ValueError("Adapter output escaped platform_ready root")
    return target


class PlatformAdapter(ABC):
    """Stable boundary between the core OS and a distribution destination."""

    name = "base"
    version = "0.0.0"
    supported_platforms: frozenset[str] = frozenset()

    @abstractmethod
    def validate(self, asset: Asset, platform: Platform) -> AdapterResult: ...

    @abstractmethod
    def prepare(
        self, asset: Asset, platform: Platform, output_root: Path
    ) -> AdapterResult: ...

    def transform(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(status="NOT_SUPPORTED")

    @abstractmethod
    def generate_metadata(self, asset: Asset, platform: Platform) -> dict[str, Any]: ...

    def check_policy(self, asset: Asset, platform: Platform) -> AdapterResult:
        if not asset.metadata.get("rights_confirmed", False):
            return AdapterResult(status="BLOCKED", errors=["RIGHTS_NOT_CONFIRMED"])
        return AdapterResult(status="VALID")

    def check_duplicates(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(
            status="NOT_SUPPORTED",
            warnings=["Duplicate checks are enforced by Publication Registry"],
        )

    def estimate_cost(self, asset: Asset, platform: Platform) -> dict[str, float]:
        return {"platform_cost": float(platform.publishing_cost or 0), "token_cost": 0.0}

    def publish(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(
            status="NOT_SUPPORTED",
            errors=["V1 ships no live publishing implementation"],
        )

    def update(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(status="NOT_SUPPORTED")

    def unpublish(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(status="NOT_SUPPORTED")

    def fetch_metrics(self, asset: Asset, platform: Platform) -> AdapterResult:
        return AdapterResult(status="NOT_SUPPORTED")

    def health_check(self, platform: Platform) -> AdapterResult:
        return AdapterResult(status="HEALTHY")


class AdapterRegistry:
    def __init__(self) -> None:
        self._by_platform: dict[str, PlatformAdapter] = {}

    def register(self, adapter: PlatformAdapter) -> None:
        for platform_id in adapter.supported_platforms:
            if platform_id in self._by_platform:
                raise ValueError(f"Adapter already registered for {platform_id}")
            self._by_platform[platform_id] = adapter

    def get(self, platform_id: str) -> PlatformAdapter | None:
        return self._by_platform.get(platform_id)

    def coverage(self) -> dict[str, dict[str, str]]:
        return {
            platform_id: {"name": adapter.name, "version": adapter.version}
            for platform_id, adapter in sorted(self._by_platform.items())
        }


class FacebookConnector(ABC):
    """Boundary for an existing compliant Facebook workflow; V1 does not replace it."""

    @abstractmethod
    def import_schedule(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def import_logs(self) -> list[dict[str, Any]]: ...

    @abstractmethod
    def import_metrics(self) -> list[dict[str, Any]]: ...
