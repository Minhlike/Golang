"""Reject character-art flow diagrams while preserving code, output and file trees."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TEXT_LANGUAGES = {"", "text", "plaintext", "ascii", "diagram"}
FLOW = re.compile(
    r"[▼▲►◄┌┐┘]|^\s*[→←]|^\s*[│|]\s*$|"
    r"\[[^\n]+\].*(?:--?>|──)|(?:--?>|──).*\[[^\n]+\]|"
    r"^\s*\+[-+]{3,}\+\s*$",
    re.MULTILINE,
)


def character_diagrams(text: str) -> list[int]:
    """Return opening fence lines; directory listings are intentional text assets."""
    found = []
    fence = None
    body = []
    for number, line in enumerate(text.splitlines(), 1):
        opening = re.fullmatch(r"\s*(`{3,}|~{3,})(.*)", line)
        if fence is None and opening:
            fence, language, start = opening[1], opening[2].strip().lower(), number
            body = []
        elif fence is not None and re.fullmatch(r"\s*" + re.escape(fence) + r"\s*", line):
            content = "\n".join(body)
            nonempty = [item.strip() for item in body if item.strip()]
            file_tree = bool(nonempty and re.fullmatch(r"[\w./\\-]+[/\\]", nonempty[0])
                             and not re.search(r"[▼▲►◄→←┌┐┘]", content))
            if language in TEXT_LANGUAGES and not file_tree and FLOW.search(content):
                found.append(start)
            fence = None
        elif fence is not None:
            body.append(line)
    return found


def validate(paths=None) -> list[str]:
    if paths is None:
        paths = sorted((ROOT / "book/chapters").glob("*.md")) + sorted(
            (ROOT / "book/appendices").glob("*.md"))
    return [f"{path}:{line}: replace character-art diagram with a rendered figure"
            for path in paths for line in character_diagrams(path.read_text(encoding="utf-8"))]


if __name__ == "__main__":
    issues = validate()
    for issue in issues:
        print(issue)
    print(f"CHARACTER_ART_DIAGRAMS={len(issues)}")
    raise SystemExit(bool(issues))
