import re
import sys

DIM, CYAN, GREEN, YELLOW, RED, RESET = (
    "\033[2m", "\033[96m", "\033[92m", "\033[93m", "\033[91m", "\033[0m"
)


def _c(text: str, code: str) -> str:
    return f"{code}{text}{RESET}" if sys.stdout.isatty() else text

ROMAN = r"[IVXLCDMivxlcdm]+"
WORD_NUMS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|"
    r"sixteen|seventeen|eighteen|nineteen|twenty"
)
_HYPHEN_SPACE = re.compile(r"([a-zA-Z])\s+-\s+([a-zA-Z])")


def clean_text(text: str) -> str:
    return _HYPHEN_SPACE.sub(r"\1-\2", text)


def build_chapter_re(sample: str) -> re.Pattern:
    sample = sample.strip()
    m = re.match(r"([A-Za-z]+)", sample)
    if not m:
        print(_c(f"Error: could not parse a keyword from sample '{sample}'.", RED))
        sys.exit(1)

    keyword = re.escape(m.group(1))
    number_pat = rf"(\d+|{ROMAN}|{WORD_NUMS})"
    sep_m = re.search(
        rf"{re.escape(m.group(1))}\s*(?:\d+|{ROMAN}|{WORD_NUMS})\s*([:\-\u2013\u2014])",
        sample,
        re.IGNORECASE,
    )
    sep_pat = (
        rf"\s*{re.escape(sep_m.group(1))}\s*" if sep_m else rf"\s*[:\-\u2013\u2014]?\s*"
    )

    pattern = (
        rf"^\s*{keyword}\b"
        rf"\s+{number_pat}"
        rf"{sep_pat}"
        rf".{{0,150}}$"
    )
    return re.compile(pattern, re.IGNORECASE)


def parse_chapter_ranges(range_text: str, num_chapters: int) -> list[int]:
    indices = set()
    for part in range_text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a < 1 or b < a:
                raise ValueError(f"Invalid range: '{part}'")
            indices.update(range(a - 1, b))
        else:
            n = int(part)
            if n < 1:
                raise ValueError(f"Invalid chapter number: '{part}'")
            indices.add(n - 1)

    valid = sorted(i for i in indices if 0 <= i < num_chapters)
    if not valid:
        raise ValueError(
            f"No valid chapters in '{range_text}'. Book has {num_chapters} chapter(s) (1–{num_chapters})."
        )
    return valid
