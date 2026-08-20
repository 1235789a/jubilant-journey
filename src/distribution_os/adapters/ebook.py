from __future__ import annotations

import html
import json
import re
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..models import AdapterResult, Asset, Platform, to_dict, utc_now
from .base import PlatformAdapter, output_target


PLATFORM_NAMES = {"amazon_kdp": "amazon_kdp", "draft2digital": "draft2digital"}


class EbookAdapter(PlatformAdapter):
    name = "ebook_epub3"
    version = "1.0.0"
    supported_platforms = frozenset(PLATFORM_NAMES)

    def validate(self, asset: Asset, platform: Platform) -> AdapterResult:
        source = Path(asset.master_source)
        errors: list[str] = []
        warnings: list[str] = []
        if not source.is_file() or source.suffix.lower() not in {".md", ".markdown"}:
            errors.append("MASTER_SOURCE_MUST_BE_MARKDOWN")
        elif len(source.read_text(encoding="utf-8").strip()) < 100:
            errors.append("MANUSCRIPT_TOO_SHORT_FOR_PILOT")
        book = asset.metadata.get("book", {})
        for key in ("title", "author", "identifier"):
            if not book.get(key):
                errors.append(f"BOOK_METADATA_MISSING:{key}")
        if asset.distribution_mode.value == "WIDE" and asset.metadata.get("kdp_select", False):
            errors.append("KDP_SELECT_EXCLUSIVITY_CONFLICT")
        if platform.platform_id == "amazon_kdp" and asset.metadata.get("ai_usage") in {
            None,
            "UNDECLARED",
        }:
            warnings.append("KDP_AI_DISCLOSURE_REVIEW_REQUIRED")
        policy = self.check_policy(asset, platform)
        errors.extend(policy.errors)
        return AdapterResult(
            status="VALID" if not errors else "INVALID",
            errors=errors,
            warnings=warnings,
        )

    def generate_metadata(self, asset: Asset, platform: Platform) -> dict[str, Any]:
        book = dict(asset.metadata.get("book", {}))
        return {
            **book,
            "platform": platform.platform_id,
            "language": asset.language,
            "market": asset.market,
            "category": asset.category,
            "tags": asset.tags,
            "distribution_mode": asset.distribution_mode.value,
            "kdp_select": bool(asset.metadata.get("kdp_select", False)),
            "ai_usage": asset.metadata.get("ai_usage", "UNDECLARED"),
            "rights_confirmed": bool(asset.metadata.get("rights_confirmed", False)),
            "generated_at": utc_now(),
            "dry_run": True,
        }

    @staticmethod
    def _markdown_to_xhtml(markdown: str, title: str) -> str:
        blocks: list[str] = []
        paragraph: list[str] = []

        def flush() -> None:
            if paragraph:
                text = " ".join(part.strip() for part in paragraph)
                blocks.append(f"<p>{html.escape(text)}</p>")
                paragraph.clear()

        for raw in markdown.splitlines():
            line = raw.strip()
            if not line:
                flush()
                continue
            heading = re.match(r"^(#{1,3})\s+(.+)$", line)
            if heading:
                flush()
                level = len(heading.group(1))
                blocks.append(f"<h{level}>{html.escape(heading.group(2))}</h{level}>")
            else:
                paragraph.append(line)
        flush()
        body = "\n".join(blocks)
        return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head><title>{html.escape(title)}</title><meta charset="utf-8" /></head>
<body>{body}</body>
</html>
"""

    def _write_epub(self, asset: Asset, destination: Path) -> None:
        book = asset.metadata["book"]
        manuscript = Path(asset.master_source).read_text(encoding="utf-8")
        title = str(book["title"])
        author = str(book["author"])
        identifier = str(book["identifier"])
        xhtml = self._markdown_to_xhtml(manuscript, title)
        container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>
"""
        nav = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head><body><nav epub:type="toc"><h1>Contents</h1>
<ol><li><a href="content.xhtml">{html.escape(title)}</a></li></ol></nav></body></html>
"""
        modified_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        package = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="{html.escape(asset.language)}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">{html.escape(identifier)}</dc:identifier>
    <dc:title>{html.escape(title)}</dc:title><dc:creator>{html.escape(author)}</dc:creator>
    <dc:language>{html.escape(asset.language)}</dc:language>
    <meta property="dcterms:modified">{modified_at}</meta>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
    <item id="content" href="content.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="content"/></spine>
</package>
"""
        with zipfile.ZipFile(destination, "w") as epub:
            epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
            epub.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
            epub.writestr("OEBPS/package.opf", package, compress_type=zipfile.ZIP_DEFLATED)
            epub.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
            epub.writestr("OEBPS/content.xhtml", xhtml, compress_type=zipfile.ZIP_DEFLATED)

    def prepare(
        self, asset: Asset, platform: Platform, output_root: Path
    ) -> AdapterResult:
        validation = self.validate(asset, platform)
        if validation.status != "VALID":
            return validation
        slug = PLATFORM_NAMES[platform.platform_id]
        target = output_target(output_root, slug, asset.asset_id, asset.master_version)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix=".package-") as temp_name:
            temp = Path(temp_name)
            epub_path = temp / f"{asset.asset_id}-{asset.master_version}.epub"
            self._write_epub(asset, epub_path)
            (temp / "metadata.json").write_text(
                json.dumps(self.generate_metadata(asset, platform), ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )
            (temp / "validation.json").write_text(
                json.dumps(to_dict(validation), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            (temp / "PUBLISH_PLAN.md").write_text(
                "\n".join(
                    [
                        f"# {platform.platform_name} dry-run package",
                        "",
                        "No upload, enrollment, contract acceptance, or payment occurred.",
                        "",
                        "Human actions still required:",
                        *[f"- {action}" for action in platform.manual_only_actions],
                        "- Inspect the EPUB in at least two readers.",
                        "- Confirm current content, AI disclosure, rights, tax, payout, and exclusivity rules.",
                        "- Approve the L0 review before any future live action.",
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
