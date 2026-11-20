"""Which model should translate Hyman, Toldot Tannaim ve-Amoraim? Test of cost, speed and accuracy (20-Nov-2026).
  py -3.13 translate_test.py run [model ...]   -> out/MODEL__ENTRY.json   (skips files that exist)
  py -3.13 translate_test.py table             -> cost, time, alignment per model
  py -3.13 translate_test.py side ENTRY        -> out/side_ENTRY.md (Hebrew + every model, paragraph by paragraph)
Key: OPENROUTER_KEY_FILE, default ..\\bochart-hierozoicon.txt. One call per entry; paragraphs are sent as a numbered
JSON list and must come back as a list of the same length.
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "source"
OUT = ROOT / "out"
KEY_FILE = Path(os.environ.get("OPENROUTER_KEY_FILE", ROOT.parent / "bochart-hierozoicon.txt"))
ENTRIES = {"abba-stam": "R' Abba (stam)", "abba-bar-zavda": "R' Abba bar Zavda"}
MODELS = {
    "flash": ("google/gemini-3.8-flash", "low"),
    "flash-hi": ("google/gemini-3.8-flash", "high"),
    "argon": ("google/gemini-4-argon", "low"),
    "haiku": ("anthropic/claude-haiku-5.5", None),
    "sonnet": ("anthropic/claude-sonnet-5.5", "low"),
    "opus": ("anthropic/claude-opus-5.5", "low"),
    "gpt": ("openai/gpt-6.1-sol", "low"),
}
PROMPT = """You translate rabbinic Hebrew into English. The text is the entry "{entry}" from Aaron Hyman, Toldot Tannaim
ve-Amoraim (London 1910), a biographical dictionary of the Tannaim and Amoraim. Hyman writes dense scholarly Hebrew full
of abbreviations and short references to the Bavli, Yerushalmi, Tosefta and midrashim, and he quotes Aramaic.

Rules:
- Translate accurately and completely; do not summarise, do not add commentary.
- Write every abbreviation out in the English (א"ר = R' X said; ט"ס = scribal error; צ"ל = one must read; בל"ס = without
  doubt; ג"כ = also; ר"ה as a person = Rav Huna; ר"ז = R' Zeira; ר"ל/רשב"ל = Resh Lakish; ע"ז = Avodah Zarah, etc.).
  Decide from context which expansion is meant.
- References in standard English form: Berakhot 49a, Shabbat 135b (a final "." = a, ":" = b); a Yerushalmi reference
  "פ"א ה"ב" = Yerushalmi Shabbat 1:2 (ס"ה = end of halakhah, ספ"/ס"פ = end of chapter, ר"פ = start of chapter);
  midrash "פכ"ד-ד" = 24:4. Bavli tractates without "Bavli"; Yerushalmi tractates with "Yerushalmi" when Hyman's context
  shows the Yerushalmi (a chapter + halakhah reference always is).
- Names: R' Yoḥanan, R' Ḥanina, R' Ḥiyya, Rav Ḥisda, Resh Lakish, Shmuel, Rava, Rabbah; ḥ for ח. "Rabbenu ha-Kadosh"
  and "Rabbi" for the Patriarch = R' Yehuda HaNasi. Use "Eretz Yisrael", not "Land of Israel"; "Babylonia".
- Quoted Talmudic Hebrew/Aramaic: translate it, inside quotation marks.
- Hyman's own parentheses stay as (parentheses). Words you add for sense go in [square brackets].
- Numbers, dates, page and chapter references: give exactly what Hyman wrote, only converted to digits. Never correct
  them in the text, even when you think Hyman or the printer is wrong; then add your suggestion in brackets after
  it, e.g. "Bava Batra 168a [perhaps 165a]".
- Where a reading is truly unclear, translate the likely sense and add [?].

Paragraphs (JSON list of [number, Hebrew]):
{paras}

Answer with JSON only: a list of {n} strings, the English of paragraphs 1 to {n}, in order."""


def paragraphs(entry: str) -> list[str]:
    t = (SRC / f"{entry}.he.txt").read_text(encoding="utf-8")
    return [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]


def call(model: str, effort: str | None, prompt: str) -> tuple[str, float, float, dict]:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    body = {"model": model, "max_tokens": 20000, "messages": [{"role": "user", "content": prompt}],
            "usage": {"include": True}}
    if effort:
        body["reasoning"] = {"effort": effort}
    t = time.time()
    r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": "Bearer " + key},
                      json=body, timeout=900)
    d = r.json()
    if not r.ok or "error" in d:
        raise RuntimeError(f"HTTP {r.status_code}: {str(d.get('error', d))[:300]}")
    u = d.get("usage") or {}
    return d["choices"][0]["message"]["content"] or "", time.time() - t, u.get("cost") or 0.0, u


def one(name: str, entry: str) -> str:
    out = OUT / f"{name}__{entry}.json"
    if out.exists():
        return f"{name} {entry}: done already"
    paras = paragraphs(entry)
    model, effort = MODELS[name]
    prompt = PROMPT.format(entry=ENTRIES[entry], n=len(paras),
                           paras=json.dumps([[i + 1, p] for i, p in enumerate(paras)], ensure_ascii=False))
    try:
        text, secs, cost, usage = call(model, effort, prompt)
    except Exception as e:
        return f"{name} {entry}: FAILED {e}"
    m = re.search(r"\[.*\]", text, re.S)
    try:
        en = json.loads(m.group()) if m else []
    except Exception:
        en = []
    out.write_text(json.dumps({"model": model, "effort": effort, "entry": entry, "seconds": round(secs, 1),
                               "cost": cost, "usage": usage, "n_paras": len(paras), "n_answers": len(en),
                               "english": en, "raw": text if not en else ""}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    return f"{name} {entry}: {len(en)}/{len(paras)} paragraphs, {secs:.0f} s, ${cost:.4f}"


def table() -> None:
    rows = {}
    for f in OUT.glob("*__*.json"):
        d = json.loads(f.read_text(encoding="utf-8"))
        name = f.stem.split("__")[0]
        r = rows.setdefault(name, {"cost": 0.0, "secs": 0.0, "n": 0, "ok": 0, "words": 0})
        r["cost"] += d["cost"]; r["secs"] += d["seconds"]; r["n"] += 1
        r["ok"] += d["n_answers"] == d["n_paras"]; r["words"] += sum(len(s.split()) for s in d["english"])
    print(f"{'model':9} {'entries':>7} {'aligned':>7} {'cost $':>8} {'s/entry':>7} {'EN words':>8}")
    for k, r in sorted(rows.items(), key=lambda x: x[1]["cost"]):
        print(f"{k:9} {r['n']:7d} {r['ok']:7d} {r['cost']:8.4f} {r['secs'] / r['n']:7.0f} {r['words']:8d}")


def side(entry: str) -> None:
    paras = paragraphs(entry)
    runs = {}
    for f in sorted(OUT.glob(f"*__{entry}.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d["n_answers"] == d["n_paras"]:  # skip truncated runs
            runs[f.stem.split("__")[0]] = d["english"]
    lines = [f"# {ENTRIES[entry]}: all models, paragraph by paragraph\n"]
    for i, p in enumerate(paras):
        lines.append(f"## ¶{i + 1}\n\n> {p}\n")
        for k, en in runs.items():
            lines.append(f"**{k}:** {en[i] if i < len(en) else '(missing)'}\n")
    (OUT / f"side_{entry}.md").write_text("\n".join(lines), encoding="utf-8")
    print(OUT / f"side_{entry}.md")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    if sys.argv[1] == "run":
        names = sys.argv[2:] or list(MODELS)
        with ThreadPoolExecutor(14) as ex:
            for line in ex.map(lambda a: one(*a), [(n, e) for n in names for e in ENTRIES]):
                print(line, flush=True)
    elif sys.argv[1] == "side":
        side(sys.argv[2])
    else:
        table()
