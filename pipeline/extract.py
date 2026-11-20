"""Turn the saved Wikisource pages into clean Hebrew entries, in book order.
  py -3.13 extract.py   -> data/entries.jsonl (one entry per line) and a short report
Book order comes from the letter index pages (their [[/name/]] links). Paragraph rules match the test of 20-Nov-2026:
abbreviation tooltips, edit links and page markers are dropped; h2/h3/p/li become paragraphs; list items get "• ".
"""
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "data" / "wikisource" / "pages"
BOOK = "תולדות תנאים ואמוראים"
LETTERS = "אבגדהוזחטיכלמנסעפצקרשת"


def paragraphs(html: str) -> tuple[list[str], list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    scans = [s["title"] for s in soup.select(".pagenum[title]")]
    for sel in (".TooltipSpan", ".mw-editsection", ".pagenum", "sup.reference", "style", "script"):
        for e in soup.select(sel):
            e.decompose()
    root = soup.select_one(".prp-pages-output")
    root = root.parent if root else soup
    for t in root.find_all("table"):  # the navigation header of the book template
        t.decompose()
    for li in root.find_all("li"):
        li.insert(0, "• ")
    out = []
    for e in root.find_all(["h2", "h3", "p", "li"]):
        if e.name == "p" and e.find_parent("li"):
            continue
        s = re.sub(r"\s+", " ", e.get_text()).strip()
        if s:
            out.append(("## " if e.name in ("h2", "h3") else "") + s)
    return out, scans


def main():
    pages = {}
    for f in PAGES.glob("*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        pages[d["title"]] = d
    order = []
    for i, letter in enumerate(LETTERS):
        idx = pages.get(f"{BOOK}/{letter}")
        if not idx:
            continue
        for name in re.findall(r"\[\[/(.+?)/?(?:\|[^\]]*)?\]\]", idx["wikitext"]):
            order.append((letter, name.strip().rstrip("/")))
    seen, rows = set(), []
    for n, (letter, name) in enumerate(order):
        title = f"{BOOK}/{letter}/{name}"
        d = pages.get(title)
        if not d or title in seen:
            continue
        seen.add(title)
        paras, scans = paragraphs(d["html"])
        m = re.search(r'<pages index="([^"]+)"[^>]*from=(\d+) to=(\d+)', d["wikitext"])
        rows.append({"pageid": d["pageid"], "order": n, "letter": letter, "name": name, "title": title,
                     "scan": m.group(1) if m else "", "from": int(m.group(2)) if m else None,
                     "to": int(m.group(3)) if m else None, "scans": scans, "paras": paras,
                     "chars": sum(len(p) for p in paras)})
    # entries that exist but are not linked from a letter index go at the end of their letter
    for title, d in pages.items():
        parts = title.split("/")
        if len(parts) == 3 and title not in seen:
            paras, scans = paragraphs(d["html"])
            rows.append({"pageid": d["pageid"], "order": 10**6 + LETTERS.find(parts[1]) * 10**4, "letter": parts[1],
                         "name": parts[2], "title": title, "scan": "", "from": None, "to": None, "scans": scans,
                         "paras": paras, "chars": sum(len(p) for p in paras), "unlisted": True})
    rows.sort(key=lambda r: (LETTERS.find(r["letter"]), r["order"]))
    with (ROOT / "data" / "entries.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    body = [r for r in rows if r["chars"] >= 40]
    print(f"{len(pages)} pages, {len(order)} index links, {len(rows)} entries, {len(body)} with text, "
          f"{sum(r['chars'] for r in rows):,} Hebrew characters")
    for letter in LETTERS:
        rs = [r for r in rows if r["letter"] == letter]
        if rs:
            print(f"  {letter}: {len(rs)} entries, {sum(1 for r in rs if r['chars'] >= 40)} with text, "
                  f"{sum(r['chars'] for r in rs):,} chars, {sum(1 for r in rs if r.get('unlisted'))} unlisted")


if __name__ == "__main__":
    main()
