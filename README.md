# Hyman, *Toldot Tannaim ve-Amoraim*: English translation

English translation of Aaron Hyman, *Toldot Tannaim ve-Amoraim* (London, 1910), a biographical dictionary of the
Tannaim and Amoraim. The Hebrew text is from
[Hebrew Wikisource](https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%9C%D7%93%D7%95%D7%AA_%D7%AA%D7%A0%D7%90%D7%99%D7%9D_%D7%95%D7%90%D7%9E%D7%95%D7%A8%D7%90%D7%99%D7%9D).

Site: https://openseforim.org/hyman/

The project has two parts:

1. **Machine translation of all entries** ([`mt/`](https://openseforim.org/hyman/mt/)),
   **complete as of 20-Nov-2026**: all 1,889 entries that are transcribed on Wikisource (about 285,000 Hebrew words),
   translated paragraph by paragraph with Gemini 4 Argon and shown next to the Hebrew, for $13.55 in all.
   **Not reviewed.** Wikisource has no entries yet for the letters Mem, Ayin and Pe, and only 18 for Yod; rerunning
   the pipeline adds new entries when they are transcribed.
2. **Reviewed sample entries** (02-Nov-2026): two entries translated with Claude and checked, with a summary at the top
   and each quoted source as a quote block.

## Status

<!-- status:start -->
As of 22-Nov-2026 21:08 (Israel time).

- Wikisource pages fetched: 2,242 of 2,242 (entry pages plus 22 letter index pages).
- Entries with an English page: **1,889**. Translation cost (including the number-check re-translation): $13.55.

| Letter | Entries fetched | With text | Translated | Hebrew characters |
|---|---|---|---|---|
| Alef (א) | 727 | 626 | 626 | 593,976 |
| Bet (ב) | 256 | 205 | 205 | 85,065 |
| Gimel (ג) | 63 | 55 | 55 | 55,664 |
| Dalet (ד) | 67 | 59 | 59 | 32,127 |
| He (ה) | 115 | 105 | 105 | 104,144 |
| Vav (ו) | 5 | 4 | 4 | 517 |
| Zayin (ז) | 100 | 90 | 90 | 67,853 |
| Ḥet (ח) | 353 | 315 | 315 | 184,050 |
| Tet (ט) | 39 | 36 | 36 | 20,453 |
| Yod (י) | 18 | 17 | 17 | 21,673 |
| Kaf (כ) | 39 | 36 | 36 | 25,031 |
| Lamed (ל) | 10 | 6 | 6 | 9,281 |
| Nun (נ) | 8 | 6 | 6 | 654 |
| Samekh (ס) | 73 | 60 | 60 | 25,635 |
| Tsadi (צ) | 9 | 7 | 7 | 904 |
| Qof (ק) | 39 | 26 | 26 | 7,132 |
| Resh (ר) | 185 | 137 | 137 | 152,736 |
| Shin (ש) | 45 | 39 | 39 | 65,832 |
| Tav (ת) | 66 | 60 | 60 | 18,673 |
<!-- status:end -->

## Machine translation: how it is made

Code in [`pipeline/`](pipeline/):

| Step | Script | What it does |
|---|---|---|
| 1 | `fetch_wikisource.py` | Downloads every entry page under the book's Wikisource prefix through the MediaWiki API. The entry pages only transclude the scan pages, so it asks the API to render them: 20 entries per `action=parse` call, 3 s apart (the anonymous API returns HTTP 429 at about 5 calls a second). Resumable. |
| 2 | `extract.py` | Turns the rendered HTML into clean Hebrew paragraphs (abbreviation tooltips and page markers removed) and puts the entries in book order, from the letter index pages. |
| 3 | `translate.py` | Sends each entry to Gemini 4 Argon (effort low, via OpenRouter) as a numbered JSON list of paragraphs, in chunks of up to 6,000 characters, and checks that one English paragraph comes back for each Hebrew one. Resumable. |
| 4 | `numcheck.py`, `fixflags.py` | Free check: every number in the English (pages, chapters, years, ages) must come from a number in the Hebrew paragraph (Hebrew letter numerals are decoded). On 20-Nov-2026 it flagged 128 numbers in 125 paragraphs; those paragraphs were translated again with a stricter rule (Hyman's numbers exactly, any correction only in brackets), $0.49, leaving 47 flags, mostly numbers the check cannot decode. The rest are listed in [`pipeline/numcheck_remaining.tsv`](pipeline/numcheck_remaining.tsv) for review. Paragraphs whose Hebrew on Wikisource is raw, uncorrected OCR (92 paragraphs, mainly in the entries on Resh Lakish and Rav Sheshet) are skipped and marked on the site. |
| 5 | `build_site.py` | Writes `mt/index.html` (all entries by letter, with a filter) and one page per entry: English and Hebrew side by side, with links to Wikisource, the scan page, and the previous and next entries. |

The translation prompt asks for every abbreviation to be written out, standard English references (Berakhot 49a,
Yerushalmi Shabbat 1:2), Hyman's own (parentheses) kept, and the translator's additions in [square brackets], shown in
gray on the site.

**Why Gemini 4 Argon.** On 20-Nov-2026 seven models translated two entries (R' Abba (stam) and R' Abba bar Zavda), and
the results were checked by hand on ten hard points. Argon made the fewest errors (1 of 10) and was the only model that
noticed one of Hyman's own wrong references; it costs about a third of Claude Opus 5.5. Gemini 3.8 Flash is cheaper
with more slips in the Aramaic; Claude Sonnet 5.5 and Opus 5.5 made errors in dates (era of the year) and references.
Details: [`pipeline/README.md`](pipeline/README.md).

**Known limits.** The English is not reviewed. Expect wrong expansions of ambiguous abbreviations, wrong forms of rare
names, and errors that Hyman's own text carries. In a few entries (Resh Lakish, Rav Sheshet and some others in volume II) the Wikisource text is raw OCR with the two columns mixed; those paragraphs carry a warning. Short "see entry X" cross-references have no page; entries that
Wikisource has not transcribed yet (scan only) are listed in gray.

## Reviewed sample entries

| Entry | Page | Note |
|---|---|---|
| R' Abba (stam) | [r-abba-stam.html](https://openseforim.org/hyman/r-abba-stam.html) | Short entry; complete |
| R' Yoḥanan | [r-yohanan.html](https://openseforim.org/hyman/r-yohanan.html) | Long entry; only pp. 236–240 of pp. 236–255 are transcribed on Wikisource |

How they were made:

1. Take the Hebrew entry from Wikisource.
2. Translate it into English, with abbreviations written out.
3. Add a summary (and tables where useful) at the top.
4. Set each quoted source as a quote block: Hebrew first, with punctuation that matches the English, then the English, then the reference.

Conventions: text in (parentheses) is Hyman's; text in [square brackets], shown in gray, is the translator's. The translations were made with Claude.

## Related projects

- [lewysohn-zoologie](https://github.com/openseforim/lewysohn): Lewysohn, *Die Zoologie des Talmuds* (1858), OCR and translation
- [talmud-zoology-factcheck](https://github.com/EzraBrand/talmud-zoology-factcheck): zoological claims of the Talmud checked against modern zoology
- [low-flora](https://github.com/openseforim/loew): Löw, *Die Flora der Juden*, OCR and translation pilot
- [bochart-hierozoicon](https://github.com/openseforim/bochart): Bochart, *Hierozoicon*, pilot on the shafan
- [abba-to-zebedee](https://github.com/EzraBrand/abba-to-zebedee): naming conventions in the Mishnah, Talmud and Midrash

## License

Translations: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) (see `LICENSE-TEXT`). Code: [MIT](LICENSE). Hyman's 1910 Hebrew text is in the public domain.
