"""Re-translate the paragraphs that numcheck.py flagged, with the number rule now in the prompt (20-Nov-2026).
  py -3.13 fixflags.py      -> replaces those paragraphs in data/en/<pageid>.json (old text kept under "fixes")
Each paragraph goes alone, with the entry name. The new English is kept only if it has no more unexplained numbers
than the old one.
"""
import csv
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from numcheck import english_numbers, hebrew_values  # noqa: E402
from translate import EN, do_chunk  # noqa: E402


def unexplained(he: str, en: str) -> int:
    hv = hebrew_values(he)
    return sum(1 for v, _ in english_numbers(en) if v not in hv)


def fix(entry: dict, j: int) -> str:
    f = EN / f"{entry['pageid']}.json"
    d = json.loads(f.read_text(encoding="utf-8"))
    key = next(k for k in d["chunks"] if int(k.split("-")[0]) <= j < int(k.split("-")[1]))
    a = int(key.split("-")[0])
    old = d["chunks"][key][j - a]
    sub = dict(entry, paras=entry["paras"][j:j + 1])
    sub["paras"] = [entry["paras"][0]] + sub["paras"] if entry["paras"][0].startswith("## ") and j else sub["paras"]
    en, cost, _ = do_chunk(sub, 0, len(sub["paras"]))
    if en is None:
        return f"{entry['name']} ¶{j}: no answer, ${cost:.4f}"
    new = en[-1]
    n_old, n_new = unexplained(entry["paras"][j], old), unexplained(entry["paras"][j], new)
    return_line = f"{entry['name']} ¶{j}: {n_old} -> {n_new} unexplained, ${cost:.4f}"
    if n_new <= n_old:
        d = json.loads(f.read_text(encoding="utf-8"))  # re-read: another worker may have fixed this entry
        d["chunks"][key][j - a] = new
        d.setdefault("fixes", []).append({"para": j, "old": old, "new": new, "why": "numcheck 20-Nov-2026"})
        d["cost"] = d.get("cost", 0) + cost
        f.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
        return return_line + " (kept)"
    return return_line + " (old kept)"


def main():
    rows = {json.loads(l)["pageid"]: json.loads(l) for l in (ROOT / "data" / "entries.jsonl").open(encoding="utf-8")}
    flags = sorted({(int(x["pageid"]), int(x["para"])) for x in
                    csv.DictReader((ROOT / "data" / "numcheck.tsv").open(encoding="utf-8-sig"), delimiter="\t")})
    by_entry = {}
    for pid, j in flags:
        by_entry.setdefault(pid, []).append(j)
    print(f"{len(flags)} paragraphs in {len(by_entry)} entries", flush=True)

    def run_entry(pid):  # one entry at a time per worker, so file writes do not collide
        return [fix(rows[pid], j) for j in by_entry[pid]]

    with ThreadPoolExecutor(8) as ex:
        for lines in ex.map(run_entry, by_entry):
            for line in lines:
                print(line, flush=True)


if __name__ == "__main__":
    main()
