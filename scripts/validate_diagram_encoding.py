#!/usr/bin/env python3
"""Fail fast when visual sources contain common UTF-8 mojibake markers."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / "scripts" / "reconstruct_visuals.py", *sorted((ROOT / "assets" / "diagrams").glob("*.puml"))]
MARKERS = ("Ã", "Ä", "Â", "Æ", "á»", "áº", "â€", "ï¿½", "�")


def main() -> int:
    hits = 0
    for path in TARGETS:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if any(marker in line for marker in MARKERS):
                print(f"MOJIBAKE {path.relative_to(ROOT)}:{number}: {line}")
                hits += 1
    print(f"MOJIBAKE_HITS={hits}")
    return 1 if hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
