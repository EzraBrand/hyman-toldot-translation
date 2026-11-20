"""Translate the extracted Hyman entries with Gemini 4 Argon (effort low), chosen in translate_test.py (20-Nov-2026).
  py -3.13 translate.py [LETTER] [--limit N] [--workers 8]   -> data/en/<pageid>.json  (resumable; skips done chunks)
  py -3.13 translate.py --cost                               -> total cost so far
Paragraphs go out as a numbered JSON list, in chunks of up to CHUNK Hebrew characters. A chunk whose answer does not
have the right number of strings is retried once, then left out (the entry is reported as incomplete).
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
EN = ROOT / "data" / "en"
KEY_FILE = Path(os.environ.get("OPENROUTER_KEY_FILE", ROOT.parent / "bochart-hierozoicon.txt"))
MODEL, EFFORT = "google/gemini-4-argon", "low"
CHUNK = 6000
MIN_CHARS = 40
sys.path.insert(0, str(ROOT))
from translate_test import PROMPT  # noqa: E402  (same prompt as the test)


def entries(letter: str | None):
    for line in (ROOT / "data" / "entries.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["chars"] >= MIN_CHARS and (not letter or r["letter"] == letter):
            yield r


def chunks(paras: list[str]) -> list[tuple[int, int]]:
    out, start, size = [], 0, 0
    for i, p in enumerate(paras):
        if size and size + len(p) > CHUNK:
            out.append((start, i)); start, size = i, 0
        size += len(p)
    out.append((start, len(paras)))
    return out


def call(prompt: str) -> tuple[str, float, float]:
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    body = {"model": MODEL, "max_tokens": 24000, "reasoning": {"effort": EFFORT}, "usage": {"include": True},
            "messages": [{"role": "user", "content": prompt}]}
    for attempt in range(4):
        t = time.time()
        try:
            r = requests.post("https://openrouter.ai/api/v1/chat/completions",
                              headers={"Authorization": "Bearer " + key}, json=body, timeout=900)
            d = r.json()
            if r.ok and "error" not in d:
                return d["choices"][0]["message"]["content"] or "", time.time() - t, (d.get("usage") or {}).get("cost") or 0.0
            msg = f"HTTP {r.status_code}: {str(d.get('error', d))[:200]}"
            if r.status_code == 402:
                raise RuntimeError("KEY BALANCE: " + msg)
        except RuntimeError:
            raise
        except Exception as e:
            msg = str(e)
        print(f"  retry {attempt + 1}: {msg}", flush=True)
        time.sleep(20 * (attempt + 1))
    raise RuntimeError(msg)


def do_chunk(entry: dict, a: int, b: int) -> tuple[list[str] | None, float, float]:
    paras = entry["paras"][a:b]
    name = re.sub(r"^## ", "", entry["paras"][0]) if entry["paras"][0].startswith("## ") else entry["name"]
    prompt = PROMPT.format(entry=name, n=len(paras),
                           paras=json.dumps([[i + 1, p] for i, p in enumerate(paras)], ensure_ascii=False))
    cost = secs = 0.0
    for _ in range(2):
        text, s, c = call(prompt)
        cost += c; secs += s
        m = re.search(r"\[.*\]", text, re.S)
        try:
            en = json.loads(m.group()) if m else None
        except Exception:
            en = None
        if isinstance(en, list) and len(en) == len(paras) and all(isinstance(x, str) for x in en):
            return en, cost, secs
    return None, cost, secs


def do_entry(entry: dict) -> str:
    out = EN / f"{entry['pageid']}.json"
    d = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"pageid": entry["pageid"], "chunks": {}}
    if d.get("paras_hash") != hash_paras(entry):
        d = {"pageid": entry["pageid"], "chunks": {}}
    d.update(model=MODEL, effort=EFFORT, title=entry["title"], paras_hash=hash_paras(entry))
    spent = 0.0
    for a, b in chunks(entry["paras"]):
        k = f"{a}-{b}"
        if k in d["chunks"]:
            continue
        en, cost, secs = do_chunk(entry, a, b)
        spent += cost
        d.setdefault("cost", 0.0); d["cost"] += cost
        if en is not None:
            d["chunks"][k] = en
        out.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    n = len(chunks(entry["paras"]))
    done = sum(1 for a, b in chunks(entry["paras"]) if f"{a}-{b}" in d["chunks"])
    return f"{entry['letter']} {entry['name']}: {done}/{n} chunks, ${spent:.4f}" + ("" if done == n else "  INCOMPLETE")


def hash_paras(entry: dict) -> str:
    import hashlib
    return hashlib.sha256("\n".join(entry["paras"]).encode()).hexdigest()[:16]


def english(pageid: int, n_paras: int) -> list[str | None]:
    """English paragraphs in order (None where a chunk failed)."""
    f = EN / f"{pageid}.json"
    out: list[str | None] = [None] * n_paras
    if f.exists():
        for k, en in json.loads(f.read_text(encoding="utf-8"))["chunks"].items():
            a, b = map(int, k.split("-"))
            out[a:b] = en
    return out


def main():
    EN.mkdir(parents=True, exist_ok=True)
    if "--cost" in sys.argv:
        files = list(EN.glob("*.json"))
        print(f"{len(files)} entries, ${sum(json.loads(f.read_text(encoding='utf-8')).get('cost', 0) for f in files):.4f}")
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8
    letter = args[0] if args and not args[0].isdigit() else None
    todo = list(entries(letter))[:limit]
    print(f"{len(todo)} entries, {sum(e['chars'] for e in todo):,} Hebrew characters, model {MODEL}", flush=True)
    t, total = time.time(), 0
    with ThreadPoolExecutor(workers) as ex:
        futs = [ex.submit(do_entry, e) for e in todo]
        for i, f in enumerate(as_completed(futs), 1):
            try:
                line = f.result()
            except Exception as e:
                line = f"FAILED {e}"
                if "KEY BALANCE" in str(e):
                    print(line, flush=True); ex.shutdown(cancel_futures=True); break
            print(f"{i}/{len(todo)} {line}", flush=True)
    print(f"finished in {time.time() - t:.0f} s", flush=True)


if __name__ == "__main__":
    main()
