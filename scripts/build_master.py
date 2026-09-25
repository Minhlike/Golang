"""
Wrapper script to build Golang_Master.pdf.
Aliases to scripts/build_pdf.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.build_pdf import build

if __name__ == "__main__":
    build()
