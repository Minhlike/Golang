"""Local, non-AI document conversion and selective retrieval."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

CACHE_ROOT = Path(__file__).resolve().parents[2] / "runtime/document-cache"
SUPPORTED = {".pdf", ".docx", ".pptx", ".md", ".txt"}
TARGET_CHARS = 9000  # Roughly 1500–3000 tokens; not a measured token count.
SCHEMA = 1
PIPELINE_VERSION = 1  # Bump when normalization, chunking, or index semantics change.
CONVERTER = "markitdown"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def document_id(path: Path) -> str:
    stem = re.sub(r"[^a-z0-9_-]", "-", path.stem.lower()).strip("-")[:40] or "document"
    return stem + "-" + digest(str(path).encode("utf-8"))[:16]


def safe_id(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]+", value):
        raise ValueError("Invalid document/chunk ID")
    return value


def convert(path: Path) -> str:
    from markitdown import MarkItDown, StreamInfo

    # Narrow local stream API: no URL ingestion, plugins, LLM or cloud client.
    with path.open("rb") as stream:
        return MarkItDown(enable_plugins=False).convert_stream(
            stream, stream_info=StreamInfo(extension=path.suffix.lower())
        ).markdown


def validate_format(path: Path):
    """Reject wrong-extension fallback before MarkItDown can treat it as text."""
    if path.suffix.lower() == ".pdf":
        from pdfminer.pdfpage import PDFPage
        with path.open("rb") as stream:
            if not stream.read(1024).lstrip().startswith(b"%PDF-"):
                raise ValueError("Malformed PDF header")
            stream.seek(0)
            if next(PDFPage.get_pages(stream, check_extractable=True), None) is None:
                raise ValueError("Malformed or empty PDF page tree")
    elif path.suffix.lower() in {".docx", ".pptx"}:
        from defusedxml.ElementTree import fromstring
        part = "word/document.xml" if path.suffix.lower() == ".docx" else "ppt/presentation.xml"
        with zipfile.ZipFile(path) as archive:
            fromstring(archive.read("[Content_Types].xml"))
            root = fromstring(archive.read(part))
            expected = ("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document"
                        if path.suffix.lower() == ".docx" else
                        "{http://schemas.openxmlformats.org/presentationml/2006/main}presentation")
            if root.tag != expected:
                raise ValueError("Malformed Office document root")


def normalize(text: str) -> str:
    # Only line endings and a final newline; preserve prose and Markdown syntax.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("UNKNOWN/UNEXTRACTED: no extractable text; no successful cache created")
    return text if text.endswith("\n") else text + "\n"


def blocks(text: str):
    """Offset-preserving blocks; fenced code and pipe tables remain indivisible."""
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    i = 0
    while i < len(lines):
        start = i
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})", lines[i])
        heading = re.match(r"^ {0,3}(#{1,6})\s+(.+?)\s*#*\s*$", lines[i])
        if fence:
            marker = fence[1]
            i += 1
            while i < len(lines):
                closing = re.match(r"^ {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}\s*$", lines[i])
                i += 1
                if closing:
                    break
        elif heading or not lines[i].strip():
            i += 1
        elif lines[i].startswith(("    ", "\t")):
            i += 1
            while i < len(lines):
                if lines[i].startswith(("    ", "\t")):
                    i += 1
                elif not lines[i].strip() and i + 1 < len(lines) and lines[i + 1].startswith(("    ", "\t")):
                    i += 1
                else:
                    break
        elif "|" in lines[i] and i + 1 < len(lines) and re.fullmatch(r"[\s|:\-]+", lines[i + 1].strip()) and "-" in lines[i + 1]:
            i += 2
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                i += 1
        else:
            i += 1
            while i < len(lines) and lines[i].strip():
                if re.match(r"^ {0,3}(#{1,6}\s|`{3,}|~{3,})", lines[i]):
                    break
                # A table can follow prose without a blank line.
                if i + 1 < len(lines) and "|" in lines[i] and re.fullmatch(r"[\s|:\-]+", lines[i + 1].strip()):
                    break
                i += 1
        yield offsets[start], offsets[i], heading


def chunk_document(text: str, target: int = TARGET_CHARS):
    chunks, headings, stack = [], [], []
    start, end, path = 0, 0, []

    def emit():
        if end > start:
            content = text[start:end]
            terms = Counter(re.findall(r"\w+", content.casefold()))
            chunks.append({"id": f"{len(chunks) + 1:04d}", "heading_path": list(path),
                           "source_page_start": None, "source_page_end": None,
                           "char_start": start, "char_end": end,
                           "sha256": digest(content.encode("utf-8")),
                           "keywords": sorted(terms, key=lambda t: (-terms[t], t))[:64]})

    for a, b, heading in blocks(text):
        if heading or (end > start and b - start > target):
            emit()
            start = a
        if heading:
            level, title = len(heading[1]), heading[2]
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            node = {"title": title, "level": level, "char_start": a, "page": None,
                    "parent": stack[-1]["char_start"] if stack else None}
            headings.append(node)
            stack.append(node)
        path = [node["title"] for node in stack]
        end = b
    emit()
    return chunks, headings


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_index(root: Path, doc_id: str):
    folder = root / safe_id(doc_id)
    index = json.loads((folder / "index.json").read_text(encoding="utf-8"))
    if index.get("document_id") != doc_id or not generated_files_valid(folder, index):
        raise ValueError("Cache integrity check failed; re-ingest the source")
    return folder, index


def generated_files_valid(folder: Path, index: dict) -> bool:
    """Validate local paths and every generated Markdown file before reading."""
    try:
        if (folder.is_symlink() or any((folder / name).is_symlink()
                for name in ("source.json", "index.json", "document.md", "chunks"))):
            return False
        content = (folder / "document.md").read_bytes()
        if digest(content) != index["markdown_sha256"] or not index["chunks"]:
            return False
        markdown = content.decode("utf-8")
        ids = [safe_id(chunk["id"]) for chunk in index["chunks"]]
        if len(ids) != len(set(ids)):
            return False
        chunk_dir = folder / "chunks"
        if {item.name for item in chunk_dir.iterdir()} != {chunk_id + ".md" for chunk_id in ids}:
            return False
        expected_offset = 0
        for chunk_id, chunk in zip(ids, index["chunks"]):
            start, end = chunk["char_start"], chunk["char_end"]
            path = chunk_dir / (chunk_id + ".md")
            if path.is_symlink() or start != expected_offset or end <= start:
                return False
            chunk_bytes = path.read_bytes()
            expected = markdown[start:end].encode("utf-8")
            if chunk_bytes != expected or digest(chunk_bytes) != chunk["sha256"]:
                return False
            expected_offset = end
        return expected_offset == len(markdown)
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        return False


def cache_valid(folder: Path, sha: str, converter_name: str = CONVERTER,
                converter_version: str | None = None) -> bool:
    try:
        source = json.loads((folder / "source.json").read_text(encoding="utf-8"))
        index = json.loads((folder / "index.json").read_text(encoding="utf-8"))
        expected_version = converter_version or version(converter_name)
        if not (source["sha256"] == sha and source["converter"] == converter_name
                and source["converter_version"] == expected_version
                and source["pipeline_version"] == PIPELINE_VERSION
                and index["schema"] == SCHEMA and index["pipeline_version"] == PIPELINE_VERSION
                and source == index["document"]
                and index["document"]["sha256"] == sha
                and index["document"]["converter"] == converter_name
                and index["document"]["converter_version"] == expected_version
                and index["document"]["pipeline_version"] == PIPELINE_VERSION):
            return False
        return generated_files_valid(folder, index)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def ingest(path: Path, root: Path = CACHE_ROOT, converter=None):
    path = path.resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in SUPPORTED:
        raise ValueError("Unsupported local file: PDF/DOCX/PPTX/MD/TXT only")
    root.mkdir(parents=True, exist_ok=True)
    doc_id = document_id(path)
    folder = root / doc_id
    lock = root / (doc_id + ".lock")
    # Refuse concurrent writers rather than risking a mixed generation.
    lock.open("x").close()
    try:
        sha = file_digest(path)
        converter_version = version(CONVERTER)
        if cache_valid(folder, sha, CONVERTER, converter_version):
            return "CACHE_HIT", doc_id
        status = "CACHE_INVALID" if folder.exists() else "CACHE_MISS"
        validate_format(path)
        markdown = normalize((converter or convert)(path))
        if file_digest(path) != sha:
            raise ValueError("Source changed during conversion; retry ingestion")
        warnings = ["UNKNOWN/UNEXTRACTED: visual content and extraction completeness are not verified; inspect original."]
        chunks, headings = chunk_document(markdown)
        source = {"source_path": str(path), "sha256": sha, "size_bytes": path.stat().st_size,
                  "converted_at": datetime.now(timezone.utc).isoformat(),
                  "converter": CONVERTER, "converter_version": converter_version,
                  "pipeline_version": PIPELINE_VERSION}
        index = {"schema": SCHEMA, "pipeline_version": PIPELINE_VERSION,
                 "document_id": doc_id, "document": source,
                 "markdown_sha256": digest(markdown.encode("utf-8")), "page_mapping": None,
                 "warnings": warnings, "heading_tree": headings, "chunks": chunks}
        # Generate fully before replacing the previous valid generation.
        with tempfile.TemporaryDirectory(prefix=doc_id + "-", dir=root) as staging:
            staged = Path(staging) / "generation"
            (staged / "chunks").mkdir(parents=True)
            (staged / "document.md").write_text(markdown, encoding="utf-8", newline="\n")
            write_json(staged / "source.json", source)
            write_json(staged / "index.json", index)
            for chunk in chunks:
                (staged / "chunks" / (chunk["id"] + ".md")).write_text(
                    markdown[chunk["char_start"]:chunk["char_end"]], encoding="utf-8", newline="\n")
            backup = Path(staging) / "previous"
            if folder.exists():
                folder.rename(backup)
            try:
                staged.rename(folder)
            except OSError:
                if backup.exists():
                    backup.rename(folder)
                raise
        return status, doc_id
    finally:
        lock.unlink()


def search(root: Path, doc_id: str, query: str, mode: str = "text"):
    folder, index = read_index(root, doc_id)
    pattern = re.compile(query if mode == "regex" else re.escape(query),
                         0 if mode == "exact" else re.IGNORECASE)
    matches = []
    for chunk in index["chunks"]:
        heading = " / ".join(chunk["heading_path"])
        content = heading if mode == "heading" else (folder / "chunks" / (safe_id(chunk["id"]) + ".md")).read_text(encoding="utf-8")
        match = pattern.search(content)
        if match:
            matches.append({"id": chunk["id"], "heading_path": chunk["heading_path"],
                            "page": chunk["source_page_start"],
                            "snippet": content[max(0, match.start() - 60):match.end() + 100]})
    return matches


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-root", type=Path, default=CACHE_ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ingest").add_argument("file", type=Path)
    find = commands.add_parser("search")
    find.add_argument("document_id")
    find.add_argument("query")
    find.add_argument("--mode", choices=("text", "exact", "heading", "regex"), default="text")
    show = commands.add_parser("show")
    show.add_argument("document_id")
    show.add_argument("chunk_id")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        if args.command == "ingest":
            status, doc_id = ingest(args.file, args.cache_root)
            print(json.dumps({"status": status, "document_id": doc_id}))
        elif args.command == "search":
            print(json.dumps(search(args.cache_root, args.document_id, args.query, args.mode), ensure_ascii=False, indent=2))
        else:
            folder, index = read_index(args.cache_root, args.document_id)
            if args.chunk_id not in {c["id"] for c in index["chunks"]}:
                raise ValueError("Unknown chunk ID")
            print((folder / "chunks" / (safe_id(args.chunk_id) + ".md")).read_text(encoding="utf-8"), end="")
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
