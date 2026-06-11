import os
import sys
from .chapters import detect_chapters
from .html import build_html
from .images import extract_page_images
from .pdf_loader import FITZ_AVAILABLE, load_pdf
from .utils import _c, build_chapter_re, parse_chapter_ranges, DIM, GREEN, RED, YELLOW

USAGE = """
ebook_reader  —  PDF → phone-ready HTML with chapter navigation

Usage:
  python -m ebook_reader_pkg <file.pdf> "<chapter sample>" [chapter_range] [output.html]
  python -m ebook_reader_pkg <file.pdf> "<chapter sample>" --dry-run

Arguments:
  file.pdf          Path to the source PDF.
  chapter sample    A heading as it appears in the book, e.g. "Chapter 1:" or "Section 2"
  chapter_range     (optional) Chapters to include, e.g. 1-3,5
  output.html       (optional) Output path. Default: <pdf_name>_ebook.html beside the PDF.

Flags:
  --dry-run         Detect and print chapters without generating any HTML output.
  -h, --help        Show this message and exit.

Examples:
  python -m ebook_reader_pkg book.pdf "Chapter 1:"
  python -m ebook_reader_pkg book.pdf "Section 1" 2-5
  python -m ebook_reader_pkg book.pdf "Chapter 1:" 1-3 ~/Desktop/my_book.html
  python -m ebook_reader_pkg book.pdf "Chapter 1:" --dry-run
""".strip()


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print(USAGE)
        sys.exit(0)

    # Extract flags before positional parsing
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if len(args) < 2:
        print(_c("Error: at least two arguments required — pdf path and chapter sample.", RED))
        print()
        print(USAGE)
        sys.exit(1)

    pdf_path = args[0]
    chapter_sample = args[1]
    chapter_filter = None
    output_path = None

    if len(args) == 3:
        if args[2].lower().endswith(".html"):
            output_path = args[2]
        else:
            chapter_filter = args[2]
    elif len(args) == 4:
        chapter_filter = args[2]
        output_path = args[3]
    elif len(args) > 4:
        print(_c("Error: too many arguments.", RED))
        print()
        print(USAGE)
        sys.exit(1)

    # ── Load ──────────────────────────────────────────────────────────────────
    print(_c(f"\n  Loading {os.path.basename(pdf_path)}…", DIM))
    pages_text = load_pdf(pdf_path)
    print(_c(f"  {len(pages_text)} pages found.", DIM))

    # ── Detect chapters ───────────────────────────────────────────────────────
    chapter_re = build_chapter_re(chapter_sample)
    print(_c(f"  Heading pattern: {chapter_re.pattern}", DIM))

    chapters = detect_chapters(pages_text, chapter_re)
    if not chapters:
        print(_c(
            f"\nError: No headings matching '{chapter_sample}' were found.\n"
            f"       Check the sample matches the keyword in the book\n"
            f"       (e.g. 'Chapter 1', 'CHAPTER ONE', 'Section 2').",
            RED,
        ))
        sys.exit(1)

    # Group for display
    _KIND_LABEL = {"front": "Front Matter", "toc": "TOC", "chapter": "Chapter", "back": "Back Matter"}
    print(_c(f"\n  {len(chapters)} section(s) detected:\n", DIM))
    cur_group = None
    for index, chapter in enumerate(chapters, 1):
        group = _KIND_LABEL.get(chapter["kind"], chapter["kind"])
        if group != cur_group:
            print(_c(f"  [{group}]", DIM))
            cur_group = group
        print(_c(
            f"    {index:>3}. {chapter['title']}  (starts PDF p.{chapter['start_page'] + 1})",
            DIM,
        ))
    print()

    # ── Dry run: stop here ────────────────────────────────────────────────────
    if dry_run:
        print(_c("  Dry run complete — no HTML generated.", GREEN))
        print()
        sys.exit(0)

    # ── Chapter filter ────────────────────────────────────────────────────────
    if chapter_filter:
        try:
            selected_indices = parse_chapter_ranges(chapter_filter, len(chapters))
        except ValueError as exc:
            print(_c(f"\nError: {exc}", RED))
            sys.exit(1)
    else:
        selected_indices = list(range(len(chapters)))

    # ── Images ────────────────────────────────────────────────────────────────
    all_selected_pages: list[int] = []
    for chapter_index in selected_indices:
        all_selected_pages.extend(chapters[chapter_index]["pages"])
    all_selected_pages = sorted(set(all_selected_pages))

    if FITZ_AVAILABLE:
        print(_c(f"  Extracting images from {len(all_selected_pages)} pages…", DIM))
        page_images = extract_page_images(pdf_path, all_selected_pages)
        total_imgs = sum(len(images) for images in page_images.values())
        print(_c(f"  {total_imgs} image(s) extracted.\n", DIM))
    else:
        print(_c(
            "  Note: PyMuPDF not installed — images skipped, text via pypdf.\n"
            "        For better layout accuracy and images: pip install pymupdf\n",
            YELLOW,
        ))
        page_images = {}

    # ── Output path ───────────────────────────────────────────────────────────
    if not output_path:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(pdf_path)),
            base + "_ebook.html",
        )

    output_path = os.path.expanduser(output_path)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # ── Build & save ──────────────────────────────────────────────────────────
    content = build_html(pages_text, chapters, selected_indices, pdf_path, page_images)
    try:
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(content)
        size_kb = os.path.getsize(output_path) // 1024
        print(_c(f"  ✓  Saved → {output_path}  ({size_kb} KB)", GREEN))
        print(_c("     Open in any phone or desktop browser — no app needed.", DIM))
        print()
    except Exception as exc:
        print(_c(f"\n  Error saving: {exc}", RED))
        sys.exit(1)