import re

_MATTER_RE = re.compile(
    r"^\s*(cover|title\s+page|table\s+of\s+contents?|contents?|toc"
    r"|foreword|preface|introduction|prologue"
    r"|part\s+(\d+|[IVXLCDMivxlcdm]+|one|two|three|four|five|six|seven|eight|nine|ten)"
    r"|volume\s+(\d+|[IVXLCDMivxlcdm]+)"
    r"|epilogue|afterword|about\s+the\s+author|acknowledgements?"
    r"|appendix(\s+\w+)?|glossary|index|bibliography|notes)\s*[:\-–—]?\s*.*$",
    re.IGNORECASE,
)

_BACK_MATTER_TITLES = re.compile(
    r"^\s*(epilogue|afterword|about\s+the\s+author|acknowledgements?"
    r"|appendix(\s+\w+)?|glossary|index|bibliography|notes)\s*[:\-–—]?\s*.*$",
    re.IGNORECASE,
)

TOC_DENSITY_THRESHOLD = 3
_TOC_LOCATOR_RE = re.compile(r"(\.{3,}|\s{4,})\s*\d+\s*$")
_PREFIX_RE = re.compile(r"^\s*([A-Za-z]+)\s+([0-9]+|[IVXLCDMivxlcdm]+)")


def _is_toc_page(text: str, chapter_re: re.Pattern) -> bool:
    lines = text.splitlines()
    ch_matches = [line.strip() for line in lines if chapter_re.match(line.strip())]
    if len(ch_matches) >= TOC_DENSITY_THRESHOLD:
        locator_hits = sum(1 for line in ch_matches if _TOC_LOCATOR_RE.search(line))
        if locator_hits > 0 or len(ch_matches) >= 5:
            return True
    return False


def _dominant_matter_heading(text: str) -> str | None:
    lines = text.splitlines()
    window = lines[:max(3, len(lines) // 3)]
    for line in window:
        stripped = line.strip()
        if stripped and len(stripped) <= 60 and _MATTER_RE.match(stripped):
            return stripped
    return None


def _matter_kind(title: str) -> str:
    """Classify a matter heading as 'front' or 'back'."""
    if _BACK_MATTER_TITLES.match(title.strip()):
        return "back"
    return "front"


def detect_chapters(pages_text: list[str], chapter_re: re.Pattern) -> list[dict]:
    """
    Scan pages and return a list of section dicts, each with:
      title       str   — display name
      pages       list  — 0-based PDF page indices
      start_page  int   — first page index
      kind        str   — 'front' | 'toc' | 'chapter' | 'back'
    """
    chapters = []
    cur_title = None
    cur_pages: list[int] = []
    cur_kind = "front"

    for idx, text in enumerate(pages_text):
        # Priority 1: TOC page — absorbed into current bucket, never its own section
        if _is_toc_page(text, chapter_re):
            cur_pages.append(idx)
            continue

        # Priority 2: front/back matter keyword
        matter = _dominant_matter_heading(text)
        if matter:
            if cur_pages:
                chapters.append({
                    "title": cur_title or "(Front Matter)",
                    "pages": cur_pages,
                    "start_page": cur_pages[0],
                    "kind": cur_kind,
                })
            cur_title = matter
            cur_pages = [idx]
            cur_kind = _matter_kind(matter)
            continue

        # Priority 3: chapter heading
        found_heading = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and chapter_re.match(stripped):
                if cur_pages:
                    chapters.append({
                        "title": cur_title or "(Front Matter)",
                        "pages": cur_pages,
                        "start_page": cur_pages[0],
                        "kind": cur_kind,
                    })
                cur_title = stripped
                cur_pages = [idx]
                cur_kind = "chapter"
                found_heading = True
                break

        # Priority 4: continuation
        if not found_heading:
            cur_pages.append(idx)

    if cur_pages:
        chapters.append({
            "title": cur_title or "(Front Matter)",
            "pages": cur_pages,
            "start_page": cur_pages[0],
            "kind": cur_kind,
        })

    # Deduplicate: merge entries sharing the same "Keyword N" prefix.
    # TOC and matter sections are never merged.
    def heading_key(chapter: dict) -> str | None:
        if chapter["kind"] in ("front", "back"):
            return None
        match = _PREFIX_RE.match(chapter["title"].strip())
        if match:
            return f"{match.group(1).lower()} {match.group(2).lower()}"
        return chapter["title"].lower().strip()

    seen: dict[str, int] = {}
    deduped: list[dict] = []

    for chapter in chapters:
        key = heading_key(chapter)
        if key and key in seen:
            deduped[seen[key]]["pages"].extend(chapter["pages"])
        else:
            if key:
                seen[key] = len(deduped)
            deduped.append(chapter)

    for chapter in deduped:
        chapter["pages"] = sorted(set(chapter["pages"]))
        if chapter["pages"]:
            chapter["start_page"] = chapter["pages"][0]

    return deduped