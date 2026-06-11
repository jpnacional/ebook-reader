import html as H
import os
from .pdf_loader import FITZ_AVAILABLE


def build_html(
    pages_text: list[str],
    all_chapters: list[dict],
    selected_indices: list[int],
    pdf_path: str,
    page_images: dict[int, list[str]],
) -> str:
    title = os.path.splitext(os.path.basename(pdf_path))[0]
    sel_chapters = [all_chapters[i] for i in selected_indices]

    # ── Nav: grouped <optgroup> by kind ───────────────────────────────────────
    KIND_LABEL = {
        "front":   "Front Matter",
        "chapter": "Chapters",
        "back":    "Back Matter",
    }

    # Build optgroups preserving order, collapsing consecutive same-group entries
    options_html_parts = []
    cur_group = None
    for i, ch in zip(selected_indices, sel_chapters):
        group = KIND_LABEL.get(ch["kind"], "Chapters")
        if group != cur_group:
            if cur_group is not None:
                options_html_parts.append("</optgroup>")
            options_html_parts.append(f'<optgroup label="{group}">')
            cur_group = group
        options_html_parts.append(
            f'<option value="ch{i}">{H.escape(ch["title"])}'
            f' (p.{ch["start_page"] + 1})</option>'
        )
    if cur_group is not None:
        options_html_parts.append("</optgroup>")
    options_html = "\n".join(options_html_parts)

    # ── Chapter sections ──────────────────────────────────────────────────────
    sections = []
    for i, ch in zip(selected_indices, sel_chapters):
        paras: list[str] = []
        for page_index in ch["pages"]:
            paras.append(
                f'<p class="page-marker" data-page="{page_index + 1}">'
                f'— PDF page {page_index + 1} —</p>'
            )
            for img_tag in page_images.get(page_index, []):
                paras.append(img_tag)
            text = pages_text[page_index]
            if text.strip():
                for paragraph in text.split("\n\n"):
                    paragraph = paragraph.strip()
                    if paragraph:
                        paras.append(f"<p>{H.escape(paragraph)}</p>")
            else:
                paras.append("<p><em>(no extractable text on this page)</em></p>")

        sections.append(
            f'<section class="chapter" id="ch{i}" data-kind="{H.escape(ch["kind"])}">\n'
            f'<h2>{H.escape(ch["title"])}</h2>\n'
            + "\n".join(paras)
            + "\n</section>"
        )

    body_html = "\n\n".join(sections)
    ch_ids_js = "[" + ", ".join(f'"ch{i}"' for i in selected_indices) + "]"
    storage_key = "ebk_" + "".join(c for c in title if c.isalnum())
    img_note = "" if FITZ_AVAILABLE else " · install PyMuPDF for images"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{H.escape(title)}</title>
<style>
/* ── Tokens ── */
:root {{
  --bg:          #fdf6e3;
  --fg:          #2c2c2c;
  --muted:       #999;
  --accent:      #5a3e2b;
  --accent-dim:  #8a6a52;
  --nav-bg:      #fff8ef;
  --nav-border:  #e0d0b8;
  --page-mark:   #ccc;
  --search-hi:   #ffe066;
  --font-size:   18px;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg:#1c1c1c; --fg:#ddd; --muted:#666;
    --accent:#c9a96e; --accent-dim:#9a7a4e;
    --nav-bg:#252525; --nav-border:#3a3a3a;
    --page-mark:#444; --search-hi:#7a6000;
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; animation: none !important; }}
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* ── Nav bar ── */
#nav {{
  position: sticky; top: 0; z-index: 100;
  background: var(--nav-bg);
  border-bottom: 1px solid var(--nav-border);
  display: flex; flex-wrap: wrap;
  align-items: center; gap: .4rem;
  padding: .5rem .8rem;
}}
.nav-btn {{
  background: var(--accent); color: #fff;
  border: none; border-radius: 5px;
  padding: .35rem .75rem; font-size: .82rem;
  cursor: pointer; white-space: nowrap;
  user-select: none; flex-shrink: 0;
  transition: background .15s;
}}
.nav-btn:hover {{ background: var(--accent-dim); }}
.nav-btn:disabled {{ opacity: .3; cursor: default; background: var(--accent); }}
.nav-btn.ghost {{
  background: transparent; color: var(--accent);
  border: 1px solid var(--nav-border);
}}
.nav-btn.ghost:hover {{ background: var(--nav-border); }}

#chapter-select {{
  flex: 1; min-width: 120px; font-size: .82rem;
  padding: .35rem .5rem;
  border: 1px solid var(--nav-border); border-radius: 5px;
  background: var(--bg); color: var(--fg);
}}

/* Progress bar */
#progress-bar {{
  width: 100%; height: 3px;
  background: var(--nav-border);
  order: 99; flex-basis: 100%;
  margin: .2rem -.8rem -.5rem;
  padding: 0 0;
  overflow: hidden;
}}
#progress-fill {{
  height: 100%; width: 0%;
  background: var(--accent);
  transition: width .25s ease;
}}

/* Search bar (hidden by default) */
#search-bar {{
  display: none; flex-basis: 100%;
  order: 98; padding: .3rem 0 0;
  gap: .4rem; align-items: center;
}}
#search-bar.open {{ display: flex; }}
#search-input {{
  flex: 1; font-size: .85rem;
  padding: .3rem .6rem;
  border: 1px solid var(--nav-border); border-radius: 5px;
  background: var(--bg); color: var(--fg);
}}
#search-count {{
  font-size: .75rem; color: var(--muted);
  white-space: nowrap; min-width: 3.5rem; text-align: right;
}}

/* ── Body ── */
body {{
  background: var(--bg); color: var(--fg);
  font-family: Georgia, "Times New Roman", serif;
  font-size: var(--font-size); line-height: 1.8;
}}
#content {{
  max-width: 680px; margin: 0 auto;
  padding: 1.5rem 1.2rem 5rem;
}}
h1 {{ font-size: 1.4rem; color: var(--accent); margin-bottom: .25rem; }}
.subtitle {{ font-size: .78rem; color: var(--muted); margin-bottom: 2rem; }}

/* ── Sections ── */
.chapter {{ display: none; }}
.chapter.active {{ display: block; }}
.chapter h2 {{
  font-size: 1.1rem; color: var(--accent);
  margin: 0 0 1.2rem; padding-bottom: .4rem;
  border-bottom: 1px solid var(--nav-border);
}}
p {{ margin-bottom: 1rem; }}
.page-marker {{
  font-size: .7rem; color: var(--page-mark);
  text-align: right; margin: 1rem 0 .4rem;
  user-select: none; letter-spacing: .04em;
}}

/* ── Images ── */
.page-img {{
  display: block; max-width: 100%; height: auto;
  margin: 1rem auto; border-radius: 4px;
}}

/* ── Search highlights ── */
mark.sh {{
  background: var(--search-hi);
  color: inherit; border-radius: 2px;
  padding: 0 1px;
}}
mark.sh.current {{
  outline: 2px solid var(--accent);
}}
</style>
</head>
<body>

<nav id="nav">
  <button class="nav-btn" id="btn-prev" onclick="navigate(-1)" title="Previous (←)" disabled>&#8592;</button>

  <select id="chapter-select" onchange="goTo(this.value)">
{options_html}
  </select>

  <button class="nav-btn" id="btn-next" onclick="navigate(1)" title="Next (→)">&#8594;</button>

  <!-- Font size -->
  <button class="nav-btn ghost" id="btn-font-sm" onclick="setFont(-1)" title="Smaller text">A&#8315;</button>
  <button class="nav-btn ghost" id="btn-font-lg" onclick="setFont(1)"  title="Larger text">A&#8314;</button>

  <!-- Search toggle -->
  <button class="nav-btn ghost" id="btn-search" onclick="toggleSearch()" title="Search (/)">&#128269;</button>

  <!-- Progress -->
  <div id="progress-bar"><div id="progress-fill"></div></div>

  <!-- Search bar (revealed on demand) -->
  <div id="search-bar">
    <input id="search-input" type="search" placeholder="Search in chapter…"
           oninput="onSearchInput()" onkeydown="onSearchKey(event)">
    <span id="search-count"></span>
    <button class="nav-btn ghost" onclick="stepMatch(1)">&#8595;</button>
    <button class="nav-btn ghost" onclick="stepMatch(-1)">&#8593;</button>
    <button class="nav-btn ghost" onclick="closeSearch()">&#10005;</button>
  </div>
</nav>

<div id="content">
  <h1>{H.escape(title)}</h1>
  <p class="subtitle" id="subtitle">Loading…</p>

{body_html}
</div>

<script>
const CHAPTERS  = {ch_ids_js};
const STORE_KEY = "{storage_key}";
let cur = 0;
let fontSize = parseInt(localStorage.getItem(STORE_KEY + "_fs") || "18", 10);

/* ── Font size ── */
function applyFont() {{
  document.documentElement.style.setProperty("--font-size", fontSize + "px");
  localStorage.setItem(STORE_KEY + "_fs", fontSize);
}}

function setFont(dir) {{
  fontSize = Math.min(28, Math.max(13, fontSize + dir * 2));
  applyFont();
}}

/* ── Chapter display ── */
function show(idx, save) {{
  document.querySelectorAll(".chapter").forEach(el => el.classList.remove("active"));
  const el = document.getElementById(CHAPTERS[idx]);
  el.classList.add("active");
  document.getElementById("chapter-select").value = CHAPTERS[idx];
  document.getElementById("btn-prev").disabled = (idx === 0);
  document.getElementById("btn-next").disabled = (idx === CHAPTERS.length - 1);
  window.scrollTo(0, 0);
  cur = idx;
  updateProgress();
  updateSubtitle();
  clearSearch();
  if (save !== false) localStorage.setItem(STORE_KEY, String(idx));
}}

function navigate(dir) {{
  const next = cur + dir;
  if (next >= 0 && next < CHAPTERS.length) show(next);
}}

function goTo(id) {{
  const idx = CHAPTERS.indexOf(id);
  if (idx !== -1) show(idx);
}}

/* ── Progress bar ── */
function updateProgress() {{
  const pct = CHAPTERS.length <= 1 ? 100 : Math.round((cur / (CHAPTERS.length - 1)) * 100);
  document.getElementById("progress-fill").style.width = pct + "%";
}}

/* ── Subtitle: "Chapter 3 of 12 · p.42" ── */
function updateSubtitle() {{
  const chapterCount = {len(sel_chapters)};
  const option = document.getElementById("chapter-select").selectedOptions[0];
  const _pRe = new RegExp("\\(p\\.([0-9]+)\\)");
  const pageHint = option ? _pRe.exec(option.text) : null;
  const pageStr = pageHint ? " · PDF p." + pageHint[1] : "";
  document.getElementById("subtitle").textContent =
    `Chapter ${{cur + 1}} of ${{chapterCount}}${{pageStr}}{img_note}`;
}}

/* ── Search ── */
let matches = [];
let matchIdx = 0;

function toggleSearch() {{
  const bar = document.getElementById("search-bar");
  if (bar.classList.toggle("open")) {{
    document.getElementById("search-input").focus();
  }} else {{
    closeSearch();
  }}
}}

function closeSearch() {{
  document.getElementById("search-bar").classList.remove("open");
  clearSearch();
  document.getElementById("search-input").value = "";
}}

function clearSearch() {{
  document.querySelectorAll("mark.sh").forEach(m => {{
    const parent = m.parentNode;
    parent.replaceChild(document.createTextNode(m.textContent), m);
    parent.normalize();
  }});
  matches = [];
  matchIdx = 0;
  document.getElementById("search-count").textContent = "";
}}

function onSearchInput() {{
  clearSearch();
  const query = document.getElementById("search-input").value.trim();
  if (!query || query.length < 2) return;

  const section = document.getElementById(CHAPTERS[cur]);
  const walker = document.createTreeWalker(section, NodeFilter.SHOW_TEXT);
  const textNodes = [];
  let node;
  while ((node = walker.nextNode())) {{
    if (!["SCRIPT","STYLE","MARK"].includes(node.parentElement.tagName))
      textNodes.push(node);
  }}

  const re = new RegExp(query.replace(new RegExp("[.*+?^${{}}()|\\[\\]\\\\\\\\]", "g"), "\\\\$&"), "gi");
  textNodes.forEach(tn => {{
    const text = tn.textContent;
    if (!re.test(text)) return;
    re.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0, m;
    while ((m = re.exec(text)) !== null) {{
      frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const mark = document.createElement("mark");
      mark.className = "sh";
      mark.textContent = m[0];
      frag.appendChild(mark);
      last = m.index + m[0].length;
    }}
    frag.appendChild(document.createTextNode(text.slice(last)));
    tn.parentNode.replaceChild(frag, tn);
  }});

  matches = Array.from(section.querySelectorAll("mark.sh"));
  if (matches.length) {{
    matchIdx = 0;
    highlightMatch();
  }}
  document.getElementById("search-count").textContent =
    matches.length ? `${{matchIdx + 1}}/${{matches.length}}` : "0 found";
}}

function highlightMatch() {{
  matches.forEach(m => m.classList.remove("current"));
  if (!matches.length) return;
  matches[matchIdx].classList.add("current");
  matches[matchIdx].scrollIntoView({{ block: "center", behavior: "smooth" }});
  document.getElementById("search-count").textContent =
    `${{matchIdx + 1}}/${{matches.length}}`;
}}

function stepMatch(dir) {{
  if (!matches.length) return;
  matchIdx = (matchIdx + dir + matches.length) % matches.length;
  highlightMatch();
}}

function onSearchKey(e) {{
  if (e.key === "Enter")  {{ e.preventDefault(); stepMatch(e.shiftKey ? -1 : 1); }}
  if (e.key === "Escape") {{ closeSearch(); }}
}}

/* ── Keyboard navigation ── */
document.addEventListener("keydown", function(e) {{
  const tag = document.activeElement ? document.activeElement.tagName : "";
  if (tag === "SELECT" || tag === "INPUT") return;
  if (e.key === "ArrowLeft")  {{ e.preventDefault(); navigate(-1); }}
  if (e.key === "ArrowRight") {{ e.preventDefault(); navigate(1);  }}
  if (e.key === "/") {{ e.preventDefault(); toggleSearch(); }}
}});

/* ── Init ── */
applyFont();
const saved = parseInt(localStorage.getItem(STORE_KEY) || "0", 10);
const startIdx = (saved >= 0 && saved < CHAPTERS.length) ? saved : 0;
show(startIdx, false);
</script>
</body>
</html>
"""