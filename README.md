# ebook_reader

Converts a PDF file into a self-contained HTML ebook optimized for phone reading. The generated HTML includes chapter navigation, inline images, search, font sizing, and PDF page markers.

---

## Features

- Detects chapter boundaries from a heading sample provided by the user
- Automatically groups front/back matter and identifies TOC pages
- Deduplicates repeated headings caused by headers or footers
- Embeds images as base64 data URIs when PyMuPDF is available
- Generates a fully self-contained `.html` file with no external dependencies
- HTML reader includes chapter dropdown, Prev/Next buttons, keyboard navigation, search, and font resizing
- Supports dry-run mode to preview detected sections without building HTML

---

## Project Structure

```
ebook_reader/
├── ebook_reader.py
└── ebook_reader_pkg/
    ├── __init__.py
    ├── __main__.py
    ├── chapters.py
    ├── cli.py
    ├── html.py
    ├── images.py
    ├── pdf_loader.py
    └── utils.py
```

### Module responsibilities

- `ebook_reader.py`
  - Root launcher that delegates to the package CLI.
- `ebook_reader_pkg/__main__.py`
  - Enables running the package as `python -m ebook_reader_pkg`.
- `ebook_reader_pkg/cli.py`
  - Parses command-line arguments and orchestrates PDF loading, chapter detection, optional dry-run output, image extraction, and HTML generation.
- `ebook_reader_pkg/pdf_loader.py`
  - Extracts PDF text page-by-page.
  - Uses PyMuPDF (`fitz`) first for better layout and paragraph handling.
  - Falls back to `pypdf` or `PyPDF2` if PyMuPDF is unavailable.
- `ebook_reader_pkg/chapters.py`
  - Detects chapter sections, front/back matter, and TOC pages.
  - Builds a strict heading regex from the user sample.
  - Deduplicates repeated chapter headings.
- `ebook_reader_pkg/images.py`
  - Extracts inline page images using PyMuPDF.
  - Skips small decorative images under 80×80 pixels.
- `ebook_reader_pkg/html.py`
  - Generates the self-contained HTML output.
  - Creates navigation UI, search, font resizing, progress bar, and chapter sections.
- `ebook_reader_pkg/utils.py`
  - Shared utilities: regex builders, text cleanup, colour formatting, and range parsing.

---

## Requirements

| Package | Purpose | Required |
|---|---|---|
| `pypdf` or `PyPDF2` | PDF text extraction fallback | Yes |
| `pymupdf` | Better text extraction and image support | Recommended |

Install dependencies:

```bash
pip install pypdf pymupdf
```

---

## Usage

```bash
python ebook_reader/ebook_reader.py <file.pdf> "<chapter sample>" [chapter_range] [output.html]
```

Or as a package:

```bash
python -m ebook_reader_pkg <file.pdf> "<chapter sample>" [chapter_range] [output.html]
```

### Optional dry-run mode

```bash
python -m ebook_reader_pkg <file.pdf> "<chapter sample>" --dry-run
```

This prints detected sections and exits without generating HTML.

### Arguments

| Argument | Required | Description |
|---|---|---|
| `file.pdf` | Yes | Path to the source PDF |
| `"chapter sample"` | Yes | Example heading text that appears in the PDF |
| `chapter_range` | No | Chapter numbers to include, e.g. `1-3,5` |
| `output.html` | No | Output file path; defaults to `<pdf_name>_ebook.html` |

### Chapter sample format

The sample should match how headings appear in the PDF, including keyword and numbering. If the sample includes a separator such as `:`, `-`, `–`, or `—`, that separator is required in matches.

Examples:

| PDF heading | Sample |
|---|---|
| `Chapter 1: The Beginning` | `"Chapter 1:"` |
| `CHAPTER ONE` | `"CHAPTER ONE"` |
| `Section 2 – Notes` | `"Section 2"` |
| `Part III` | `"Part III"` |

---

## Examples

```bash
# Convert an entire PDF
python ebook_reader/ebook_reader.py book.pdf "Chapter 1:"

# Convert only chapters 2 through 5
python ebook_reader/ebook_reader.py book.pdf "Chapter 1:" 2-5

# Convert selected chapters only
python ebook_reader/ebook_reader.py book.pdf "Chapter 1:" 1,3,5

# Convert and save to a custom location
python ebook_reader/ebook_reader.py book.pdf "Chapter 1:" 1-10 C:/Users/Nash/Desktop/my_book.html

# Dry run to preview detected sections
python -m ebook_reader_pkg book.pdf "Section 1" --dry-run
```

---

## HTML output

The generated HTML is fully self-contained and includes:

- Sticky navigation bar
- Chapter dropdown with section grouping
- Prev/Next navigation buttons
- Keyboard support for left/right chapter switching
- Search within the current chapter
- Font size controls
- Progress bar
- PDF page markers for each source page

---

## Notes

- The HTML file embeds images only when PyMuPDF is installed.
- Text extraction depends on PDF layout; results may vary by source document.
- Headings rendered as images cannot be detected by the current chapter parser.
