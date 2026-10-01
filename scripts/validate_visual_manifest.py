"""Check publication asset provenance and source/output integrity locally."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest = json.loads((ROOT / "assets/visual-manifest.json").read_text(encoding="utf-8"))
    required = {
        "asset_id", "type", "chapter_section", "purpose", "source", "creator",
        "license", "license_reference", "retrieved_at", "redistribution_status",
        "modifications", "caption_vi", "alt_text_vi", "factual_verification",
        "local_asset_path", "sha256", "review_status",
    }
    errors = []
    indexed = {}
    for item in manifest["assets"]:
        missing = [key for key in required if not item.get(key)]
        path = (ROOT / item["local_asset_path"]).resolve()
        if missing:
            errors.append(f"{item['asset_id']}: missing {missing}")
        if not path.is_relative_to(ROOT / "assets") or not path.is_file():
            errors.append(f"{item['asset_id']}: invalid local asset")
            continue
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            errors.append(f"{item['asset_id']}: image checksum mismatch")
        if item["type"] == "TECH_DIAGRAM":
            source = ROOT / item["source"]
            if hashlib.sha256(source.read_text(encoding="utf-8").encode("utf-8")).hexdigest() != item["source_sha256"]:
                errors.append(f"{item['asset_id']}: source checksum mismatch")
            if item.get("style_source"):
                style = (ROOT / item["style_source"]).resolve()
                if (not style.is_relative_to(ROOT / "assets") or not style.is_file()
                        or hashlib.sha256(style.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
                        != item.get("style_sha256")):
                    errors.append(f"{item['asset_id']}: shared style checksum mismatch")
        if path in indexed:
            errors.append(f"{item['asset_id']}: duplicate manifest path")
        indexed[path] = item
    used = set()
    for md in sorted((ROOT / "book/chapters").glob("*.md")) + sorted((ROOT / "book/appendices").glob("*.md")):
        for match in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", md.read_text(encoding="utf-8")):
            path = (md.parent / match[2]).resolve()
            used.add(path)
            if path not in indexed:
                errors.append(f"{md.name}: unregistered image {match[2]}")
            elif indexed[path]["alt_text_vi"] != match[1]:
                errors.append(f"{md.name}: alt text differs from manifest")
    for error in errors:
        print(error)
    print(f"VISUAL_MANIFEST={'FAIL' if errors else 'PASS'}; PUBLICATION_ASSETS={len(used)}")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
