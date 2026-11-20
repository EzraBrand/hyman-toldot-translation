"""Download all entries of Hyman, Toldot Tannaim ve-Amoraim from Hebrew Wikisource (run by the owner; resumable).
  py -3.13 fetch_wikisource.py            -> data/wikisource/list.json + data/wikisource/pages/<pageid>.json
  py -3.13 fetch_wikisource.py א          -> only letter Alef
To stay under the anonymous API rate limit (HTTP 429 at 5 calls a second, 20-Nov-2026), entries are rendered 20 at a
time: one action=parse call whose text transcludes 20 entry pages, split again on marker lines. Wikitext comes from
one query call per 50 pages. Each page file holds title, wikitext and rendered HTML. Pages already saved are skipped.
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "wikisource"
PAGES = OUT / "pages"
API = "https://he.wikisource.org/w/api.php"
BOOK = "תולדות תנאים ואמוראים/"
DELAY = 3.0  # seconds between calls
BATCH = 20
S = requests.Session()
S.headers["User-Agent"] = "hyman-toldot-translation/0.2 (research; github.com/EzraBrand/hyman-toldot-translation)"


def api(**params):
    params |= {"format": "json", "formatversion": "2", "maxlag": "5"}
    for attempt in range(10):
        wait = 30 * (attempt + 1)
        try:
            r = S.post(API, data=params, timeout=120)
            if r.status_code == 200 and "error" not in r.json():
                time.sleep(DELAY)
                return r.json()
            if r.headers.get("Retry-After", "").isdigit():
                wait = max(wait, int(r.headers["Retry-After"]) + 5)
            print(f"  HTTP {r.status_code} {r.text[:80]!r}, waiting {wait} s (attempt {attempt + 1}/10)", flush=True)
        except Exception as e:
            print(f"  {e}, waiting {wait} s (attempt {attempt + 1}/10)", flush=True)
        time.sleep(wait)
    raise RuntimeError("API failed 10 times")


def list_pages(prefix: str) -> list[dict]:
    out, cont = [], {}
    while True:
        d = api(action="query", list="allpages", apprefix=prefix, apnamespace=0, aplimit=500,
                apfilterredir="nonredirects", **cont)
        out += d["query"]["allpages"]
        if "continue" not in d:
            return out
        cont = {"apcontinue": d["continue"]["apcontinue"]}


def wikitexts(titles: list[str]) -> dict[str, str]:
    d = api(action="query", prop="revisions", rvprop="content", rvslots="main", titles="|".join(titles))
    return {p["title"]: p["revisions"][0]["slots"]["main"]["content"] for p in d["query"]["pages"] if "revisions" in p}


def render(batch: list[dict]) -> dict[int, str]:
    text = "\n".join(f'\n<p id="ENTRYMARK{p["pageid"]}">ENTRYMARK{p["pageid"]}</p>\n{{{{:{p["title"]}}}}}\n'
                     for p in batch)
    html = api(action="parse", text=text, contentmodel="wikitext", prop="text", disablelimitreport=1,
               title=batch[0]["title"])["parse"]["text"]
    parts = re.split(r'<p id="ENTRYMARK(\d+)">ENTRYMARK\d+\s*</p>', html)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def main():
    prefix = BOOK + (sys.argv[1] + "/" if len(sys.argv) > 1 else "")
    PAGES.mkdir(parents=True, exist_ok=True)
    pages = list_pages(prefix)
    (OUT / "list.json").write_text(json.dumps(pages, ensure_ascii=False, indent=0), encoding="utf-8")
    todo = [p for p in pages if not (PAGES / f"{p['pageid']}.json").exists()]
    print(f"{len(pages)} pages under {prefix}; {len(todo)} to fetch, {BATCH} per call", flush=True)
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        try:
            wt = {}
            for j in range(0, len(batch), 50):
                wt |= wikitexts([p["title"] for p in batch[j:j + 50]])
            html = render(batch)
            for p in batch:
                if p["pageid"] in html and p["title"] in wt:
                    (PAGES / f"{p['pageid']}.json").write_text(json.dumps(
                        {"pageid": p["pageid"], "title": p["title"], "wikitext": wt[p["title"]],
                         "html": html[p["pageid"]]}, ensure_ascii=False), encoding="utf-8")
                else:
                    print(f"MISSING {p['title']}", flush=True)
        except Exception as e:
            print(f"FAILED batch at {batch[0]['title']}: {e}", flush=True)
        print(f"{min(i + BATCH, len(todo))}/{len(todo)}", flush=True)
    done = sum(1 for p in pages if (PAGES / f"{p['pageid']}.json").exists())
    print(f"finished: {done}/{len(pages)} saved" + ("" if done == len(pages) else " (INCOMPLETE: run again)"), flush=True)


if __name__ == "__main__":
    main()
