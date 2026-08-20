from __future__ import annotations

import json
import shutil
from pathlib import Path

from distribution_os.models import Asset, AssetStatus, DistributionMode
from distribution_os.seed import demo

from support import ApplicationTestCase, REPO_ROOT


class EndToEndTests(ApplicationTestCase):
    def test_two_different_verticals_end_to_end(self) -> None:
        result = demo(self.app)
        self.assertEqual(result["processed_jobs"], 5)
        self.assertEqual(result["statuses"], ["SUCCESS"] * 5)
        publications = self.app.registry.list_publications()
        self.assertEqual(len(publications), 5)
        self.assertEqual(len(self.app.registry.list_variants()), 5)
        self.assertTrue(all(item.variant_id for item in publications))
        self.assertEqual(
            {self.app.registry.get_asset(item.asset_id).vertical_id for item in publications},
            {"browser_extension", "international_ebook"},
        )
        self.assertTrue(all(item.mode == "DRY_RUN" for item in publications))
        self.assertTrue(all(Path(item.output_url).is_dir() for item in publications))

        repeated = demo(self.app)
        self.assertEqual(repeated["processed_jobs"], 0)
        self.assertEqual(repeated["reused_jobs"], 5)
        self.assertEqual(repeated["statuses"], ["SUCCESS"] * 5)
        self.assertEqual(len(self.app.registry.list_publications()), 5)

    def test_all_31_seed_platforms_are_registry_objects(self) -> None:
        platforms = self.app.registry.list_platforms()
        self.assertEqual(len(platforms), 31)
        self.assertEqual(sum(item.adapter_maturity.value == "P2" for item in platforms), 5)
        self.assertFalse(any(item.adapter_maturity.value == "P3" for item in platforms))
        self.assertFalse(any(item.live_publish for item in platforms))

    def test_nine_vertical_records_are_evaluated(self) -> None:
        verticals = self.app.registry.list_verticals()
        self.assertEqual(len(verticals), 9)
        self.assertTrue(all(0 <= item.evaluated_score <= 100 for item in verticals))
        self.assertEqual(
            self.app.registry.get_vertical("app").status,
            "DISABLED_PENDING_REVIEW",
        )
        self.assertEqual(len(self.app.registry.list_rules()), 31)

    def test_router_ranks_wide_and_exclusive_targets(self) -> None:
        asset = self.app.registry.get_asset("asset_ai_search_field_guide")
        assert asset
        ranked = self.app.router.rank_candidates(asset)
        self.assertEqual({item["platform_id"] for item in ranked}, {"amazon_kdp", "draft2digital"})
        self.assertEqual(len(self.app.router.recommended_targets(asset)), 2)
        asset.distribution_mode = DistributionMode.EXCLUSIVE
        asset.metadata.pop("exclusive_platform_id", None)
        self.assertEqual(len(self.app.router.recommended_targets(asset)), 1)

    def test_three_assets_batch_without_core_changes(self) -> None:
        source_base = REPO_ROOT / "examples" / "browser_extension"
        for index in range(3):
            source = Path(self.temporary.name) / f"extension-{index}"
            shutil.copytree(source_base, source)
            manifest_path = source / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["name"] = f"Batch Pilot {index}"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            asset = Asset(
                asset_id=f"asset_batch_{index}",
                name=f"Batch Pilot {index}",
                vertical_id="browser_extension",
                product_type="BROWSER_EXTENSION",
                status=AssetStatus.READY,
                master_source=str(source),
                master_version="0.1.0",
                language="en",
                market="GLOBAL",
                category="productivity",
                tags=["batch"],
                distribution_mode=DistributionMode.WIDE,
                priority=50 + index,
                human_owner="test",
                quality_score=80,
                metadata={"rights_confirmed": True, "policy_status": "ALLOWED"},
            )
            self.app.registry.upsert_asset(asset)
            self.app.distribution.request_dry_run(asset.asset_id, "chrome_web_store")
        jobs = self.app.distribution.run_until_empty()
        self.assertEqual(len(jobs), 3)
        self.assertTrue(all(job.status.value == "SUCCESS" for job in jobs))
        self.assertEqual(len(self.app.registry.list_publications()), 3)

    def test_dry_run_creates_human_review_not_live_action(self) -> None:
        self.app.distribution.request_dry_run(
            "asset_linklens_extension", "chrome_web_store"
        )
        [job] = self.app.distribution.run_until_empty()
        self.assertEqual(job.status.value, "SUCCESS")
        self.assertFalse(self.app.kill_switch.publishing_enabled())
        self.assertEqual(self.app.registry.list_publications()[0].mode, "DRY_RUN")
        self.assertEqual(len(self.app.registry.list_reviews("PENDING")), 1)
