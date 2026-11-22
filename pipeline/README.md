# Hyman, Toldot Tannaim ve-Amoraim: model test for translation (20-Nov-2026)

This file records the model test that chose Gemini 4 Argon. The full pipeline that uses it (`fetch_wikisource.py`,
`extract.py`, `translate.py`, `build_site.py`) and the current status are described in the main README of
[hyman-toldot-translation](https://github.com/openseforim/hyman#readme). Paths below such as
`source/` and `out/` are in the local working folder, not in the repository.

Source: Hebrew Wikisource, two entries of letter Alef (text taken through the parse API, abbreviation tooltips removed,
SHA-256 checked against the browser copy):

- `source/abba-stam.he.txt`: R' Abba (stam), 3,482 characters, 12 paragraphs. A reviewed translation of this entry is
  already in `..\hyman-toldot\r-abba-stam.html` (02-Nov-2026), used as the reference.
- `source/abba-bar-zavda.he.txt`: R' Abba bar Zavda, 4,253 characters, 21 paragraphs. New.

Script: `translate_test.py` (OpenRouter, key `..\bochart-hierozoicon.txt`). One call per entry; paragraphs go out as a
numbered JSON list. Outputs in `out/`; side-by-side files `out/side_abba-stam.md`, `out/side_abba-bar-zavda.md`.

## Cost and speed (both entries together, 7,735 Hebrew characters)

| Model | Cost | Seconds per entry | Complete |
|---|---|---|---|
| Gemini 3.8 Flash (low) | $0.022 | 17 | 2/2 |
| GPT-6.1 Sol (low) | $0.058 | 27 | 2/2 |
| Gemini 4 Argon (low) | $0.058 | 36 | 2/2 |
| Sonnet 5.5 (low) | $0.080 | 21 | 2/2 |
| Opus 5.5 (low) | $0.164 | 28 | 2/2 |
| Haiku 5.5 (default) | $0.017 | 66 | 1/2 (reasoning used all 20k tokens) |
| Gemini 3.8 Flash (high) | $0.148 | 101 | 1/2 (same) |

Test total: about $0.55.

## Accuracy (read by hand)

R' Abba (stam) is easy: all complete runs get the hard points (530 of the Seleucid era, "Rav is a Tanna and may
dispute", Buber note 9, Yerushalmi Berakhot 4:1 28b, Shitah Mekubbetzet). Haiku has 520 for 530.

R' Abba bar Zavda separates the models:

| Point | Flash | Argon | GPT | Sonnet | Opus |
|---|---|---|---|---|---|
| Megillah 5b "לא כך היה מעשה" = "the incident was not so" | question (wrong) | right | question (wrong) | question (wrong) | right |
| יבמות ס"פו = Yerushalmi Yevamot end of ch. 6 | right | "Yevamot 65b" (wrong) | right | no "Yerushalmi" | right |
| אי זכאי הוה לי מקמייתא (children from the first wife) | right | right | right | wrong | right |
| Shekalim end ch. 2 "חכים רבי לרב" | right | right | right | garbled | right |
| קידושין פ"ז הי"ב (Yerushalmi Kiddushin has 4 chapters) | passed silently | flags it, proposes 3:12 | passed silently | passed silently | marks [?] |
| אסא ביני חילפי (myrtle among willows/reeds) | "thorns" (wrong) | willows | reeds | "thorns" (wrong) | reeds |
| ויק"ר פלו־ו = Lev. Rabbah 36:6 | right | right | right | right | "30:6" (wrong) |
| יבמות פ"ג: = Yevamot 83b | right | right | right | "3b" (wrong) | right |
| תרסג' = 663 Seleucid (352 CE) | right, adds 352 CE | right, "Seleucid" | right (no era) | "4063 [303 CE]" (wrong) | "4663 [?]" (wrong) |
| ד"א / ריב"ב in Yerushalmi Taanit 4:6 | "another matter" / Yehoshua ben Betheira | R' Elazar / Yoḥanan ben Beroka | R' Elazar / Yoḥanan ben Beroka | "R' Abba" / Yehuda ben Bava [?] | "another version" / Yoḥanan ben Beroka |

Errors on the 10 points: Argon 1, GPT 2, Flash 3, Opus 2 (+1 flag), Sonnet 6+.

## Result

- **Use Gemini 4 Argon (effort low)** for the main run: fewest errors, the only model that found Hyman's own wrong
  reference (Kiddushin 7:12), and $0.0075 per 1,000 Hebrew characters, about a third of Opus's price.
- **Gemini 3.8 Flash** is the cheap option ($0.0028 per 1,000 characters, 17 s an entry) with lexical slips in the
  quoted Aramaic; good for a first pass or a long tail of short entries.
- Do not use high effort or Haiku: they spend the token budget on reasoning and cut the answer.
- The Anthropic models (Sonnet, Opus) are not better on this text and cost more; Sonnet makes the most errors.

Not done: the house format of `..\hyman-toldot` (summary, quote blocks with Hebrew first); that is a second step after
the translation. A second reader for the Aramaic quotes (Argon + GPT and compare) would catch most of the remaining
slips at about $0.015 per 1,000 characters for the pair.
