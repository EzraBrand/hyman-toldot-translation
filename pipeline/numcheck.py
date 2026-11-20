"""Free check: every number in the English must come from a number in the Hebrew paragraph (20-Nov-2026).
  py -3.13 numcheck.py            -> data/numcheck.tsv + summary
Hebrew numbers are mostly letters (עג' = 73, תרסג' = 663, כתובות כז. = 27a), so each short Hebrew word that is a valid
gematria (letters in falling order, טו/טז allowed) gives candidate values, also after stripping prefixes such as
ב/כ/ו/ל/ש/ס/ר/פ/ה ("ספ"ו" -> 6). Digits in the Hebrew count too. English numbers inside [brackets] are the translator's
(era conversions etc.) and are skipped. An English number that no Hebrew word can give is flagged.
"""
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from translate import MIN_CHARS, english  # noqa: E402

VAL = dict(zip("אבגדהוזחטיכלמנסעפצקרשת", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]))
FINAL = str.maketrans("ךםןףץ", "כמנפצ")
PREFIX = "בכולשמדהספרע"


def gematria(s: str) -> int | None:
    s = s.translate(FINAL)
    if not s or any(c not in VAL for c in s) or len(s) > 5:
        return None
    vals = [VAL[c] for c in s]
    if s.endswith(("טו", "טז")):
        vals = vals[:-2] + [9]  # 15 and 16 are written טו / טז, not יה / יו
    if any(a < b for a, b in zip(vals, vals[1:])):
        return None
    return sum(VAL[c] for c in s)


def hebrew_values(he: str) -> set[int]:
    out = {int(x) for x in re.findall(r"\d+", he)}
    words = re.findall(r"[א-ת\"'״׳]+", he)
    for a, b in zip(words, words[1:]):  # a year with a thousands letter: ה'תרפ"ח, ג'תתקל"ה
        a1, b1 = re.sub(r"[\"'״׳]", "", a), re.sub(r"[\"'״׳]", "", b)
        if len(a1) == 1 and a1 in VAL and VAL[a1] < 10 and gematria(b1):
            out.add(VAL[a1] * 1000 + gematria(b1))
    for w in re.findall(r"[א-ת]'[א-ת\"'״׳]+", he):  # the same written as one word: ה'תרפח
        g = gematria(re.sub(r"[\"'״׳]", "", w[2:]))
        if g and w[0] in VAL and VAL[w[0]] < 10:
            out.add(VAL[w[0]] * 1000 + g)
    for m in re.finditer(r"([א-ט])['\"]?\s*(?:אלפים|אלף|א)['\"]?\s+([א-ת\"'״׳]+)", he):  # ד' אלפים קי"ז, ד"א קלב
        g = gematria(re.sub(r"[\"'״׳]", "", m.group(2)))
        if g:
            out.add(VAL[m.group(1)] * 1000 + g)
    for w in words:
        letters = re.sub(r"[\"'״׳]", "", w)
        for i in range(len(letters)):  # every suffix, so prefixes like ב / ס"פ / ר"פ fall away
            if i and letters[i - 1] not in PREFIX and i > 3:
                break
            v = gematria(letters[i:])
            if v:
                out.add(v)
                if v >= 400:  # a year written without the thousands (תרסג = [5]663 or Seleucid 663)
                    out |= {v + 5000, v + 4000, v + 3000}
    return out


def is_raw_ocr(he: str) -> bool:
    """Uncorrected OCR on Wikisource: many bidi control marks (columns interleaved, letters confused)."""
    return len(re.findall("[‪-‮]", he)) * 100 >= 5 * max(1, len(he))


def english_numbers(en: str) -> list[tuple[int, str]]:
    en = re.sub(r"\[[^\]]*\]", " ", en)  # translator's additions
    out = []
    for m in re.finditer(r"(?<![\w.])(\d{1,5})(?:st|nd|rd|th)?(?![\d])", en):
        out.append((int(m.group(1)), en[max(0, m.start() - 50):m.end() + 30].replace("\n", " ")))
    return out


def main():
    rows = [json.loads(l) for l in (ROOT / "data" / "entries.jsonl").open(encoding="utf-8")]
    flags, n_paras, n_nums = [], 0, 0
    for r in rows:
        if r["chars"] < MIN_CHARS:
            continue
        en = english(r["pageid"], len(r["paras"]))
        for j, (he, e) in enumerate(zip(r["paras"], en)):
            if not e:
                continue
            if is_raw_ocr(he):
                continue
            n_paras += 1
            hv = hebrew_values(he)
            for v, ctx in english_numbers(e):
                n_nums += 1
                if v not in hv:
                    flags.append((r["pageid"], r["letter"], r["name"], j, v, ctx))
    with (ROOT / "data" / "numcheck.tsv").open("w", encoding="utf-8-sig") as f:
        f.write("pageid\tletter\tentry\tpara\tnumber\tcontext\n")
        for fl in flags:
            f.write("\t".join(str(x) for x in fl) + "\n")
    print(f"{n_paras:,} paragraphs, {n_nums:,} English numbers, {len(flags)} flagged in "
          f"{len({(f[0], f[3]) for f in flags})} paragraphs of {len({f[0] for f in flags})} entries -> data/numcheck.tsv")


if __name__ == "__main__":
    main()
