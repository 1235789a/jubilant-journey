from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ..models import AdapterResult, Asset, Platform, to_dict, utc_now
from .base import PlatformAdapter, output_target


PLATFORM_NAMES = {
    "chrome_web_store": "chrome",
    "edge_addons": "edge",
    "firefox_addons": "firefox",
}


class BrowserExtensionAdapter(PlatformAdapter):
    name = "browser_extension"
    version = "1.0.0"
    supported_platforms = frozenset(PLATFORM_NAMES)

    def validate(self, asset: Asset, platform: Platform) -> AdapterResult:
        source = Path(asset.master_source)
        manifest_path = source / "manifest.json"
        errors: list[str] = []
        warnings: list[str] = []
        if not source.is_dir():
            errors.append("MASTER_SOURCE_NOT_DIRECTORY")
        if not manifest_path.is_file():
            errors.append("MANIFEST_MISSING")
            return AdapterResult(status="INVALID", errors=errors)
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return AdapterResult(status="INVALID", errors=[f"MANIFEST_INVALID: {exc}"])
        for key in ("name", "version", "manifest_version"):
            if key not in manifest:
                errors.append(f"MANIFEST_FIELD_MISSING:{key}")
        if manifest.get("manifest_version") != 3:
            warnings.append("V1 adapter is tested with Manifest V3")
        if platform.platform_id == "firefox_addons" and "background" in manifest:
            warnings.append("Firefox compatibility requires extension runtime testing")
        policy = self.check_policy(asset, platform)
        errors.extend(policy.errors)
        return AdapterResult(
            status="VALID" if not errors else "INVALID",
            errors=errors,
            warnings=warnings,
        )

    def generate_metadata(self, asset: Asset, platform: Platform) -> dict[str, Any]:
        listing = asset.metadata.get("listing", {})
        return {
            "platform": platform.platform_id,
            "title": listing.get("title", asset.name),
            "summary": listing.get("summary", asset.metadata.get("summary", "")),
            "description": listing.get(
                "description", asset.metadata.get("description", "")
            ),
            "category": asset.category,
            "tags": asset.tags,
            "language": asset.language,
            "privacy_policy_url": asset.metadata.get("privacy_policy_url"),
            "support_url": asset.metadata.get("support_url"),
            "ai_usage": asset.metadata.get("ai_usage", "UNDECLARED"),
            "generated_at": utc_now(),
            "dry_run": True,
        }

    def _adapt_manifest(
        self, manifest: dict[str, Any], asset: Asset, platform: Platform
    ) -> dict[str, Any]:
        adapted = json.loads(json.dumps(manifest))
        if platform.platform_id == "firefox_addons":
            browser_settings = adapted.setdefault("browser_specific_settings", {})
            gecko = browser_settings.setdefault("gecko", {})
            gecko.setdefault("id", asset.metadata.get("firefox_addon_id", f"{asset.asset_id}@local.invalid"))
            gecko.setdefault("strict_min_version", "109.0")
        else:
            adapted.pop("browser_specific_settings", None)
        return adapted

    def prepare(
        self, asset: Asset, platform: Platform, output_root: Path
    ) -> AdapterResult:
        validation = self.validate(asset, platform)
        if validation.status != "VALID":
            return validation
        source = Path(asset.master_source)
        platform_slug = PLATFORM_NAMES[platform.platform_id]
        target = output_target(
            output_root, platform_slug, asset.asset_id, asset.master_version
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".package-") as temp_name:
            temp = Path(temp_name)
            build_dir = temp / "build"
            shutil.copytree(
                source,
                build_dir,
                ignore=shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc"),
            )
            manifest_path = build_dir / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_path.write_text(
                json.dumps(
                    self._adapt_manifest(manifest, asset, platform),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            archive = temp / f"{asset.asset_id}-{platform_slug}-{asset.master_version}.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                for item in sorted(build_dir.rglob("*")):
                    if item.is_file():
                        bundle.write(item, item.relative_to(build_dir).as_posix())
            (temp / "metadata.json").write_text(
                json.dumps(self.generate_metadata(asset, platform), indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            (temp / "validation.json").write_text(
                json.dumps(to_dict(validation), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
            (temp / "PUBLISH_PLAN.md").write_text(
                "\n".join(
                    [
                        f"# {platform.platform_name} dry-run package",
                        "",
                        "This directory is local output only. No upload occurred.",
                        "",
                        "Human actions still required:",
                        *[f"- {action}" for action in platform.manual_only_actions],
                        "- Re-read current official policy and approve the L0 review.",
                        "- Test the exact archive in the target browser.",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(temp, target)
        return AdapterResult(
            status="PACKAGE_READY",
            artifact_path=str(target),
            metadata=self.generate_metadata(asset, platform),
            warnings=validation.warnings,
        )
