import os
import sys
from .utils import _c, DIM, RED, clean_text

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("Error: pypdf is required.  Run: pip install pypdf")
        sys.exit(1)

try:
    import fitz
except ImportError:
    fitz = None

FITZ_AVAILABLE = fitz is not None


def _load_via_fitz(path: str) -> list[str]:
    doc = fitz.open(path)
    pages = []
    for page in doc:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1] / 20), b[0]))
        paragraphs = []
        for block in blocks:
            raw = block[4].strip()
            if raw:
                paragraphs.append(clean_text(raw))
        pages.append("\n\n".join(paragraphs))
    doc.close()
    return pages


def _load_via_pypdf(path: str) -> list[str]:
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        raw = page.extract_text() or ""
        pages.append(clean_text(raw))
    return pages


def load_pdf(path: str) -> list[str]:
    if not os.path.isfile(path):
        print(_c(f"Error: '{path}' not found.", RED))
        sys.exit(1)

    if FITZ_AVAILABLE:
        try:
            pages = _load_via_fitz(path)
            print(_c("  Text extracted with PyMuPDF (better layout accuracy).", DIM))
            return pages
        except Exception as exc:
            print(_c(f"  PyMuPDF extraction failed ({exc}), falling back to pypdf…", RED))

    try:
        pages = _load_via_pypdf(path)
        print(_c("  Text extracted with pypdf.", DIM))
        return pages
    except Exception as exc:
        print(_c(f"Error reading PDF: {exc}", RED))
        sys.exit(1)
