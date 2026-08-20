from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from support import ApplicationTestCase


class BrowserAdapterTests(ApplicationTestCase):
    def test_three_store_variants_from_one_source(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        assert asset
        outputs = {}
        for platform_id in ("chrome_web_store", "edge_addons", "firefox_addons"):
            platform = self.app.registry.get_platform(platform_id)
            adapter = self.app.adapters.get(platform_id)
            assert platform and adapter
            result = adapter.prepare(asset, platform, self.settings.platform_ready_dir)
            self.assertEqual(result.status, "PACKAGE_READY")
            target = Path(result.artifact_path)
            manifest = json.loads((target / "build" / "manifest.json").read_text())
            outputs[platform_id] = manifest
            self.assertTrue(next(target.glob("*.zip")).is_file())
        self.assertNotIn("browser_specific_settings", outputs["chrome_web_store"])
        self.assertIn("browser_specific_settings", outputs["firefox_addons"])

    def test_live_publish_is_explicitly_not_supported(self) -> None:
        asset = self.app.registry.get_asset("asset_linklens_extension")
        platform = self.app.registry.get_platform("chrome_web_store")
        adapter = self.app.adapters.get("chrome_web_store")
        assert asset and platform and adapter
        self.assertEqual(adapter.publish(asset, platform).status, "NOT_SUPPORTED")


class EbookAdapterTests(ApplicationTestCase):
    def test_epub_package_is_structurally_valid(self) -> None:
        asset = self.app.registry.get_asset("asset_ai_search_field_guide")
        platform = self.app.registry.get_platform("amazon_kdp")
        adapter = self.app.adapters.get("amazon_kdp")
        assert asset and platform and adapter
        result = adapter.prepare(asset, platform, self.settings.platform_ready_dir)
        self.assertEqual(result.status, "PACKAGE_READY")
        epub_path = next(Path(result.artifact_path).glob("*.epub"))
        with zipfile.ZipFile(epub_path) as epub:
            self.assertEqual(epub.namelist()[0], "mimetype")
            self.assertEqual(epub.getinfo("mimetype").compress_type, zipfile.ZIP_STORED)
            self.assertEqual(epub.read("mimetype"), b"application/epub+zip")
            ElementTree.fromstring(epub.read("META-INF/container.xml"))
            ElementTree.fromstring(epub.read("OEBPS/package.opf"))
            ElementTree.fromstring(epub.read("OEBPS/content.xhtml"))

    def test_kdp_select_conflict_is_rejected(self) -> None:
        asset = self.app.registry.get_asset("asset_ai_search_field_guide")
        platform = self.app.registry.get_platform("amazon_kdp")
        adapter = self.app.adapters.get("amazon_kdp")
        assert asset and platform and adapter
        asset.metadata["kdp_select"] = True
        result = adapter.validate(asset, platform)
        self.assertEqual(result.status, "INVALID")
        self.assertIn("KDP_SELECT_EXCLUSIVITY_CONFLICT", result.errors)
