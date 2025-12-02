#!/usr/bin/env python3
"""
Generate a Markdown table (Program | Summary) from a JS file similar to `bbd.js`.

How to use:
- Paste the full contents of your JS file into the JS_SOURCE string below (between the triple quotes).
  OR
- Leave JS_SOURCE empty and set JS_FILE_PATH to the path of your JS file (default: /mnt/data/bbd.js).

Example:
    python3 make_md_table.py               # reads from JS_SOURCE if set, otherwise reads JS_FILE_PATH
    python3 make_md_table.py --out table.md
"""
from pathlib import Path
import re
import html
import argparse
from typing import List, Tuple, Optional

# -----------------------------
# Edit one of these to provide your JS input:
# Option A: Paste your bbd.js contents here (easy to change)
JS_SOURCE = """
# Paste the entire contents of your bbd.js here between the triple quotes.
# For example:
# const data = [
#   { cpy: "cpy1", url: "https://example.com/1", ovrvw: "Overview 1" },
#   { cpy: "cpy2", url: "https://example.com/2", ovrvw: "Overview 2" },
# ];
"""
# Option B: Or leave JS_SOURCE empty and point to a file path
JS_FILE_PATH = "/storage/emulated/0/hunt_stuffs/BBD/bbd.js"
# -----------------------------

# Regex patterns (safe for single- or double-quoted values; ovrvw allows multiline)
RE_CPY = re.compile(r'\bcpy\s*:\s*(?:"([^"]+)"|\'([^\']+)\')', re.IGNORECASE)
RE_URL = re.compile(r'\burl\s*:\s*(?:"([^"]+)"|\'([^\']+)\')', re.IGNORECASE)
RE_OVRVW = re.compile(r'\bovrvw\s*:\s*(?:"([\s\S]*?)"|\'([\s\S]*?)\')', re.IGNORECASE | re.DOTALL)

def _first_group(match: Optional[re.Match]) -> Optional[str]:
    if not match:
        return None
    return match.group(1) if match.group(1) is not None else match.group(2)

def strip_html_and_cleanup(s: str) -> str:
    """Remove basic HTML tags, unescape entities, collapse whitespace."""
    s = re.sub(r'<[^>]+>', '', s)             # remove tags
    s = html.unescape(s)                      # unescape HTML entities
    s = re.sub(r'[\r\n]+', ' ', s)            # collapse newlines
    s = re.sub(r'\s+', ' ', s).strip()        # collapse spaces
    return s

def extract_entries(js_text: str) -> List[Tuple[str, str, str]]:
    """
    Return list of tuples (cpy, url, ovrvw).
    Strategy:
      - Find all 'cpy' positions and treat the text until the next 'cpy' (or EOF) as the object window.
      - Search for url and ovrvw within that window.
    """
    cpy_matches = list(RE_CPY.finditer(js_text))
    entries: List[Tuple[str, str, str]] = []

    for idx, cm in enumerate(cpy_matches):
        cpy_raw = _first_group(cm)
        if not cpy_raw:
            continue
        start = cm.end()
        end = cpy_matches[idx + 1].start() if idx + 1 < len(cpy_matches) else len(js_text)
        window = js_text[start:end]

        url_raw = _first_group(RE_URL.search(window))
        ovrvw_raw = _first_group(RE_OVRVW.search(window))

        # If either url or ovrvw missing in window, try a slightly broader search (best-effort)
        if not url_raw:
            broader = js_text[start:end + 2000] if end + 2000 <= len(js_text) else js_text[start:]
            url_raw = _first_group(RE_URL.search(broader))
        if not ovrvw_raw:
            broader = js_text[start:end + 2000] if end + 2000 <= len(js_text) else js_text[start:]
            ovrvw_raw = _first_group(RE_OVRVW.search(broader))

        if cpy_raw and url_raw and ovrvw_raw:
            cpy = cpy_raw.strip()
            url = url_raw.strip()
            summary = strip_html_and_cleanup(ovrvw_raw)
            entries.append((cpy, url, summary))

    return entries

def make_markdown_table(rows: List[Tuple[str, str, str]]) -> str:
    md_lines = ["| Program | Summary |", "|---|---|"]
    for cpy, url, summary in rows:
        # Escape pipe chars in summary so markdown table isn't broken
        safe_summary = summary.replace("|", "\\|")
        # Program links formatted as [cpy](url)
        md_lines.append("| [{}]({}) | {} |".format(cpy, url, safe_summary))
    return "\n".join(md_lines)

def main():
    parser = argparse.ArgumentParser(description="Generate markdown table from bbd.js-like JS content")
    parser.add_argument("--out", "-o", help="Write markdown to this file (otherwise prints to stdout)")
    parser.add_argument("--source-file", help="Override default JS_FILE_PATH")
    args = parser.parse_args()

    # Determine JS input
    if JS_SOURCE and JS_SOURCE.strip() and not JS_SOURCE.strip().startswith("# Paste the entire"):
        js_text = JS_SOURCE
    else:
        source_path = Path(args.source_file) if args.source_file else Path(JS_FILE_PATH)
        if not source_path.exists():
            raise SystemExit(f"ERROR: JS source not provided in JS_SOURCE and file not found: {source_path}")
        js_text = source_path.read_text(encoding="utf-8")

    entries = extract_entries(js_text)
    if not entries:
        raise SystemExit("No entries with cpy + url + ovrvw were found in the provided JS content.")

    md = make_markdown_table(entries)

    if args.out:
        Path(args.out).write_text(md, encoding="utf-8")
        print("Wrote markdown table with {} rows to {}".format(len(entries), args.out))
    else:
        print(md)

if __name__ == "__main__":
    main()
