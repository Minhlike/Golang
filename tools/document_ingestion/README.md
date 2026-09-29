# Local document cache

From the repository root (Python 3.10+):

```powershell
python -m venv tools/document_ingestion/.venv
tools/document_ingestion/.venv/Scripts/python.exe -m pip install -r tools/document_ingestion/requirements.txt
tools/document_ingestion/.venv/Scripts/python.exe tools/document_ingestion/doccache.py ingest reference.pdf
tools/document_ingestion/.venv/Scripts/python.exe tools/document_ingestion/doccache.py search <document-id> "GOMAXPROCS"
tools/document_ingestion/.venv/Scripts/python.exe tools/document_ingestion/doccache.py show <document-id> 0001
tools/document_ingestion/.venv/Scripts/python.exe -m unittest discover -s tools/document_ingestion -v
```

Ingest local PDF/DOCX/PPTX/MD/TXT once; re-ingest after source changes. A cache
hit requires matching source SHA-256, converter name/version, pipeline/schema
versions and hashes for the Markdown and every chunk. Bump `PIPELINE_VERSION`
when normalization, chunking or index behavior changes. Search first
(`--mode text|exact|heading|regex`),
then read only matching chunks. Search scans local chunks but returns only short
matches; it never prints the whole document. Cache/venv are ignored by Git.

Never edit cached Markdown. Open the original for images, diagrams, table
verification, layout or ambiguous extraction: Markdown is NOT visual truth.
Page provenance is unknown (`null`), not inferred. Warnings stay in JSON metadata;
`document.md` contains only normalized extracted text. Empty extraction fails.
Headings/paragraphs guide deterministic
9000-character chunks; oversized code/table blocks remain whole. Heading tree
uses parent offsets. No OCR, LLM, cloud API, plugins or embeddings are enabled.
Only ingest trusted local files; this is not a sandbox. A leftover `.lock` after
process termination needs manual removal only after confirming no writer runs.

`book/**/*.md` remains the book's authoring truth; `Golang_Master.pdf` is the
publication/visual artifact. Do not reverse-convert it to author the book.
