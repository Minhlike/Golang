#!/usr/bin/env python3
"""Compare diagram labels and topology with the approved textual baseline."""

from __future__ import annotations

import difflib
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "546bf47250ade7fdff7ab82b25c15ad1bcbf5ff4"
DIAGRAMS = ROOT / "assets" / "diagrams"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def semantic_lines(text: str) -> list[str]:
    # PlantUML offers equivalent spellings for a rectangle and a note. Normalize
    # them before comparing human-facing text and graph relationships.
    text = re.sub(
        r'rectangle\s+"(.*?)"\s+as\s+(\w+)',
        lambda match: f"rectangle {match.group(2)} [" + match.group(1) + "]",
        text,
        flags=re.DOTALL,
    )
    text = text.replace("\\n", "\n").replace('\\"', '"')
    raw_lines = text.splitlines()
    lines: list[str] = []
    in_style = False
    in_skin_block = False
    index = 0
    while index < len(raw_lines):
        raw = raw_lines[index]
        line = raw.strip()
        if line == "<style>":
            in_style = True
            index += 1
            continue
        if line == "</style>":
            in_style = False
            index += 1
            continue
        if in_style:
            index += 1
            continue
        if line.startswith("skinparam ") and line.endswith("{"):
            in_skin_block = True
            index += 1
            continue
        if in_skin_block:
            if line == "}":
                in_skin_block = False
            index += 1
            continue
        if line.startswith("skinparam "):
            index += 1
            continue
        if line in {"left to right direction", "top to bottom direction"}:
            index += 1
            continue
        rectangle = re.match(r"rectangle\s+(\w+)\s+\[(.*)$", line)
        if rectangle:
            name, first = rectangle.groups()
            body = [first]
            index += 1
            while not body[-1].endswith("]") and index < len(raw_lines):
                body.append(raw_lines[index].strip())
                index += 1
            body[-1] = body[-1][:-1]
            lines.append(f"rectangle {name} [" + "\n".join(body).strip() + "]")
            continue
        if line.startswith("note "):
            if " : " in line:
                prefix, first = line.split(" : ", 1)
                body = [first]
                index += 1
                while index < len(raw_lines) and raw_lines[index].strip() not in {"@enduml", "end note"} and not raw_lines[index].strip().startswith("note "):
                    body.append(raw_lines[index].strip())
                    index += 1
                lines.append(prefix + " : " + "\n".join(body))
                continue
            prefix = line
            body = []
            index += 1
            while index < len(raw_lines) and raw_lines[index].strip() != "end note":
                body.append(raw_lines[index].strip())
                index += 1
            lines.append(prefix + " : " + "\n".join(body))
            index += 1
            continue
        if line:
            lines.append(line)
        index += 1
    return lines


def baseline_text(name: str) -> str:
    spec = f"{BASELINE}:assets/diagrams/{name}"
    completed = subprocess.run(
        ["git", "show", spec], cwd=ROOT, check=True, capture_output=True
    )
    return completed.stdout.decode("utf-8")


def main() -> int:
    errors = 0
    for path in sorted(DIAGRAMS.glob("*.puml")):
        actual = semantic_lines(path.read_text(encoding="utf-8"))
        expected = semantic_lines(baseline_text(path.name))
        if actual != expected:
            errors += 1
            print(f"SEMANTIC_MISMATCH {path.relative_to(ROOT)}")
            print("\n".join(difflib.unified_diff(expected, actual, lineterm="")))
    if errors:
        print(f"DIAGRAM_TEXT_MATCHES_546BF47_SEMANTICALLY=NO; MISMATCHED_FILES={errors}")
        return 1
    print("DIAGRAM_TEXT_MATCHES_546BF47_SEMANTICALLY=YES")
    print("FIGURE_LABELS_CHANGED=0")
    print("FIGURE_SEMANTICS_CHANGED=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
