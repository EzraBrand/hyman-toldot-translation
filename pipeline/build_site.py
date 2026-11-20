"""Build the machine-translation pages of the hyman-toldot site from data/entries.jsonl + data/en/.
  py -3.13 build_site.py [SITE_DIR]   (default ..\\hyman-toldot)  -> SITE_DIR/mt/index.html, SITE_DIR/mt/<pageid>.html
Entries shorter than MIN_CHARS (mostly "see entry X" cross-references) get no page; the index lists them in gray.
"""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from translate import MIN_CHARS, MODEL, english  # noqa: E402
from numcheck import is_raw_ocr  # noqa: E402

SITE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT.parent / "hyman-toldot"
MT = SITE / "mt"
WS = "https://he.wikisource.org/wiki/"
LETTER_NAMES = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", ["Alef", "Bet", "Gimel", "Dalet", "He", "Vav", "Zayin", "Ḥet", "Tet",
                    "Yod", "Kaf", "Lamed", "Mem", "Nun", "Samekh", "Ayin", "Pe", "Tsadi", "Qof", "Resh", "Shin", "Tav"]))
REVIEWED = {"ר' אבא (סתם)": "../r-abba-stam.html", "ר' יוחנן": "../r-yohanan.html"}
MODEL_NAME = "Gemini 4 Argon" if "argon" in MODEL else MODEL

CSS = """:root{--bg:#faf8f4;--text:#222;--muted:#666;--accent:#7a4b1e;--rule:#ddd5c8;--note-bg:#f6efe2;--note-border:#b8894f;--gray:#8a8378}
@media (prefers-color-scheme:dark){:root{--bg:#1c1b19;--text:#e6e2da;--muted:#a39d92;--accent:#e0b07a;--rule:#3a3631;--note-bg:#2a2723;--note-border:#a07a48;--gray:#8f897f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:18px/1.6 Georgia,"Times New Roman",serif}
main{max-width:1100px;margin:0 auto;padding:32px 16px 80px}
a{color:var(--accent)}
h1{font-size:1.9rem;margin:0 0 2px;color:var(--accent)}
.he-title{direction:rtl;font-family:"Frank Ruehl CLM","FrankRuehl","David","SBL Hebrew","Times New Roman",serif;font-size:1.35rem;color:var(--muted);margin:0 0 14px}
.nav{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:.88rem;color:var(--muted);margin:0 0 18px}
.note{background:var(--note-bg);border-left:4px solid var(--note-border);padding:10px 16px;border-radius:4px;font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:.88rem;line-height:1.5;margin:0 0 26px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:28px;padding:12px 0;border-bottom:1px solid var(--rule)}
.he{direction:rtl;text-align:right;font-family:"Frank Ruehl CLM","FrankRuehl","David","SBL Hebrew","Times New Roman",serif;font-size:1.2rem;line-height:1.7}
.en p,.he p{margin:0}
.row.head .en{font-weight:bold;color:var(--accent)} .row.head .he{font-weight:bold}
.tr{color:var(--gray)}
.ocrnote{display:block;font-family:system-ui,-apple-system,\"Segoe UI\",sans-serif;font-size:.8rem;color:#a33;margin-bottom:4px}
.missing{color:var(--muted);font-style:italic}
@media (max-width:760px){.row{grid-template-columns:1fr;gap:6px}}
footer{margin-top:3em;padding-top:1em;border-top:1px solid var(--rule);font-size:.85rem;color:var(--muted);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
.letter{margin:2em 0 .4em;color:var(--accent);font-size:1.25rem}
ul.idx{list-style:none;padding:0;margin:0;columns:2;column-gap:32px}
ul.idx li{break-inside:avoid;padding:3px 0;font-size:1rem}
ul.idx .hn{direction:rtl;unicode-bidi:isolate;color:var(--muted);font-family:"Frank Ruehl CLM","David","SBL Hebrew",serif;font-size:1.05rem}
ul.idx li.xref{color:var(--muted);font-size:.9rem}
@media (max-width:760px){ul.idx{columns:1}}
.wc{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:.78rem;color:var(--muted);white-space:nowrap}
#q{width:100%;max-width:420px;font-size:1rem;padding:8px 10px;border:1px solid var(--rule);border-radius:4px;background:var(--bg);color:var(--text);margin:8px 0 4px}
"""


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def en_html(s: str) -> str:
    s = esc(s)
    return re.sub(r"\[([^\[\]]*)\]", r'<span class="tr">[\1]</span>', s)


def ws_url(title: str) -> str:
    return WS + quote(title.replace(" ", "_"), safe="/'()")


def page(title: str, body: str, desc: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
{body}
<footer>
  <p>Aaron Hyman, <em>Toldot Tannaim ve-Amoraim</em> (London, 1910). Hebrew text from Hebrew Wikisource (public domain).
  English: machine translation by {MODEL_NAME}, not reviewed. Code and translations: MIT license.
  <a href="https://github.com/EzraBrand/hyman-toldot-translation">GitHub repository</a>.</p>
</footer>
</main>
</body>
</html>
"""


def words(r: dict) -> int:
    """Hebrew word count of the entry text (heading excluded)."""
    return sum(len(p.split()) for p in r["paras"] if not p.startswith("## "))


def en_title(r: dict, en: list) -> str:
    if r["paras"] and r["paras"][0].startswith("## ") and en and en[0]:
        return re.sub(r"^#+\s*", "", en[0]).strip()
    return r["name"]


def main():
    rows = [json.loads(l) for l in (ROOT / "data" / "entries.jsonl").open(encoding="utf-8")]
    MT.mkdir(parents=True, exist_ok=True)
    (MT / "style.css").write_text(CSS, encoding="utf-8")
    full = [r for r in rows if r["chars"] >= MIN_CHARS]
    ens = {r["pageid"]: english(r["pageid"], len(r["paras"])) for r in full}
    built = [r for r in full if any(ens[r["pageid"]])]
    titles = {r["pageid"]: en_title(r, ens[r["pageid"]]) for r in built}
    for i, r in enumerate(built):
        en = ens[r["pageid"]]
        prev_, next_ = (built[i - 1] if i else None), (built[i + 1] if i + 1 < len(built) else None)
        nav = [f'<a href="index.html">All entries</a>', f'<a href="{ws_url(r["title"])}">Hebrew on Wikisource</a>']
        if r.get("from"):
            pages = f'{r["from"]}' + (f'–{r["to"]}' if r["to"] != r["from"] else "")
            scan = r["scans"][0] if r["scans"] else ""
            nav.append(f'<a href="{ws_url(scan)}">scan p. {pages}</a>' if scan else f"scan p. {pages}")
        if r["name"] in REVIEWED:
            nav.append(f'<a href="{REVIEWED[r["name"]]}"><strong>reviewed translation</strong></a>')
        pn = []
        if prev_:
            pn.append(f'<a href="{prev_["pageid"]}.html">← {esc(titles[prev_["pageid"]])}</a>')
        if next_:
            pn.append(f'<a href="{next_["pageid"]}.html">{esc(titles[next_["pageid"]])} →</a>')
        body = [f'<h1>{esc(titles[r["pageid"]])}</h1>',
                f'<p class="he-title">{esc(r["name"])}</p>',
                f'<p class="nav">Letter {LETTER_NAMES.get(r["letter"], r["letter"])} · ' + " · ".join(nav) + "</p>",
                f'<div class="note">Machine translation ({MODEL_NAME}), not reviewed. Hyman\'s own (parentheses) are '
                f'kept; [gray brackets] are the translator\'s additions. Check every reading against the Hebrew.</div>']
        for j, he in enumerate(r["paras"]):
            head = he.startswith("## ")
            if head and j == 0:
                continue  # the entry heading is already the page title
            he_t = he[3:] if head else he
            e = en[j]
            e_html = en_html(re.sub(r"^#+\s*", "", e)) if e else '<span class="missing">(not translated)</span>'
            if is_raw_ocr(he):
                e_html = ('<span class="ocrnote">The Hebrew of this paragraph on Wikisource is uncorrected OCR (columns '
                          'mixed, letters confused). The translation is not reliable; read the scan.</span> ' + e_html)
            body.append(f'<div class="row{" head" if head else ""}" id="p{j}"><div class="en"><p>{e_html}</p></div>'
                        f'<div class="he" lang="he"><p>{esc(he_t)}</p></div></div>')
        body.append(f'<p class="nav" style="margin-top:20px">{" · ".join(pn)}</p>')
        (MT / f'{r["pageid"]}.html').write_text(page(f'{titles[r["pageid"]]} — Hyman, Toldot Tannaim ve-Amoraim',
                                                     "\n".join(body), f'Hyman on {titles[r["pageid"]]}: English machine translation and Hebrew.'),
                                               encoding="utf-8")
    # index
    built_ids = {r["pageid"] for r in built}
    out = ['<h1>Hyman, <em>Toldot Tannaim ve-Amoraim</em>: machine translation</h1>',
           '<p class="he-title">אהרן הימן, תולדות תנאים ואמוראים</p>',
           '<p class="nav"><a href="../index.html">Project home</a> · '
           f'<a href="{ws_url("תולדות תנאים ואמוראים")}">Hebrew on Wikisource</a></p>',
           f'<div class="note">{len(built)} entries in English, machine-translated by {MODEL_NAME} from the Hebrew Wikisource '
           'text, paragraph by paragraph next to the Hebrew. Not reviewed. Gray entries are short cross-references '
           '("see entry …") or entries not transcribed on Wikisource yet. The number after each entry is its length '
           'in Hebrew words.</div>',
           '<input id="q" type="search" placeholder="Filter by English or Hebrew name…" aria-label="Filter entries">']
    for letter in LETTER_NAMES:
        rs = [r for r in rows if r["letter"] == letter]
        if not rs:
            continue
        out.append(f'<h2 class="letter">{LETTER_NAMES[letter]} <span class="hn">{letter}</span></h2><ul class="idx">')
        for r in rs:
            if r["pageid"] in built_ids:
                out.append(f'<li><a href="{r["pageid"]}.html">{esc(titles[r["pageid"]])}</a> '
                           f'<span class="hn">{esc(r["name"])}</span> '
                           f'<span class="wc" title="Hebrew words">{words(r):,} words</span></li>')
            else:
                txt = " ".join(p for p in r["paras"] if not p.startswith("## "))
                if r["chars"] >= MIN_CHARS:
                    txt = "(not translated yet)"
                elif not txt:
                    txt = "(no text on Wikisource)"
                out.append(f'<li class="xref"><span class="hn">{esc(r["name"])}</span> — '
                           f'<span class="hn">{esc(txt)}</span></li>' if not txt.startswith("(") else
                           f'<li class="xref"><span class="hn">{esc(r["name"])}</span> {txt}</li>')
        out.append("</ul>")
    out.append("""<script>
const q=document.getElementById('q');
q.addEventListener('input',()=>{const v=q.value.trim().toLowerCase();
document.querySelectorAll('ul.idx li').forEach(li=>{li.style.display=!v||li.textContent.toLowerCase().includes(v)?'':'none'});
document.querySelectorAll('h2.letter').forEach(h=>{const ul=h.nextElementSibling;
h.style.display=[...ul.children].some(li=>li.style.display!=='none')?'':'none'});});
</script>""")
    (MT / "index.html").write_text(page("Hyman, Toldot Tannaim ve-Amoraim: machine translation", "\n".join(out),
                                        "All entries of Hyman's Toldot Tannaim ve-Amoraim in English machine translation."),
                                   encoding="utf-8")
    print(f"{len(built)} entry pages + index in {MT}")
    write_status(rows, built_ids)


def write_status(rows: list[dict], built_ids: set) -> None:
    """Refresh the status table between the markers in SITE/README.md."""
    import datetime
    readme = SITE / "README.md"
    if not readme.exists():
        return
    listed = ROOT / "data" / "wikisource" / "list.json"
    n_pages = len(json.loads(listed.read_text(encoding="utf-8"))) if listed.exists() else 0
    n_saved = len(list((ROOT / "data" / "wikisource" / "pages").glob("*.json")))
    cost = sum(json.loads(f.read_text(encoding="utf-8")).get("cost", 0) for f in (ROOT / "data" / "en").glob("*.json"))
    lines = [f"As of {datetime.datetime.now().strftime('%d-%b-%Y %H:%M')} (Israel time).", "",
             f"- Wikisource pages fetched: {n_saved:,} of {n_pages:,} (entry pages plus 22 letter index pages).",
             f"- Entries with an English page: **{len(built_ids):,}**. Translation cost so far: ${cost:.2f}.", "",
             "| Letter | Entries fetched | With text | Translated | Hebrew characters |", "|---|---|---|---|---|"]
    for letter, name in LETTER_NAMES.items():
        rs = [r for r in rows if r["letter"] == letter]
        if rs:
            lines.append(f"| {name} ({letter}) | {len(rs)} | {sum(1 for r in rs if r['chars'] >= MIN_CHARS)} | "
                         f"{sum(1 for r in rs if r['pageid'] in built_ids)} | {sum(r['chars'] for r in rs):,} |")
    t = readme.read_text(encoding="utf-8")
    t = re.sub(r"(<!-- status:start -->\n).*?(\n<!-- status:end -->)", lambda m: m.group(1) + "\n".join(lines) + m.group(2),
               t, flags=re.S)
    readme.write_text(t, encoding="utf-8")


if __name__ == "__main__":
    main()
