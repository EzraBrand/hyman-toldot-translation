# Hyman, *Toldot Tannaim ve-Amoraim*: sample English translation

**A sample / test.** English translation of two entries from Aaron Hyman, *Toldot Tannaim ve-Amoraim* (London, 1910), a biographical dictionary of the Tannaim and Amoraim. The Hebrew text is from [Hebrew Wikisource](https://he.wikisource.org/wiki/%D7%AA%D7%95%D7%9C%D7%93%D7%95%D7%AA_%D7%AA%D7%A0%D7%90%D7%99%D7%9D_%D7%95%D7%90%D7%9E%D7%95%D7%A8%D7%90%D7%99%D7%9D).

Site: https://ezrabrand.github.io/hyman-toldot-translation/

| Entry | Page | Note |
|---|---|---|
| R' Abba (stam) | [r-abba-stam.html](https://ezrabrand.github.io/hyman-toldot-translation/r-abba-stam.html) | Short entry; complete |
| R' Yoḥanan | [r-yohanan.html](https://ezrabrand.github.io/hyman-toldot-translation/r-yohanan.html) | Long entry; only pp. 236–240 of pp. 236–255 are transcribed on Wikisource |

## Machine translation of all entries (from 20-Nov-2026)

[`mt/`](https://ezrabrand.github.io/hyman-toldot-translation/mt/): every entry transcribed on Wikisource, translated
paragraph by paragraph with Gemini 4 Argon (via OpenRouter) and shown next to the Hebrew. Not reviewed. Code in
[`pipeline/`](pipeline/): `fetch_wikisource.py` (API, 20 entries per parse call), `extract.py` (clean paragraphs, book
order), `translate.py` (Argon, resumable), `build_site.py` (pages). The model test of 20-Nov-2026 (7 models, 2 entries)
is in [`pipeline/README.md`](pipeline/README.md).

## Pipeline of the reviewed entries

1. Take the Hebrew entry from Wikisource.
2. Translate it into English, with abbreviations written out.
3. Add a summary (and tables where useful) at the top.
4. Set each quoted source as a quote block: Hebrew first, with punctuation that matches the English, then the English, then the reference.

Conventions: text in (parentheses) is Hyman's; text in [square brackets], shown in gray, is the translator's. The translations were made with Claude.

## Related projects

- [lewysohn-zoologie](https://github.com/EzraBrand/lewysohn-zoologie): Lewysohn, *Die Zoologie des Talmuds* (1858), OCR and translation
- [talmud-zoology-factcheck](https://github.com/EzraBrand/talmud-zoology-factcheck): zoological claims of the Talmud checked against modern zoology
- [low-flora](https://github.com/EzraBrand/low-flora): Löw, *Die Flora der Juden*, OCR and translation pilot
- [bochart-hierozoicon](https://github.com/EzraBrand/bochart-hierozoicon): Bochart, *Hierozoicon*, pilot on the shafan
- [abba-to-zebedee](https://github.com/EzraBrand/abba-to-zebedee): naming conventions in the Mishnah, Talmud and Midrash

## License

Translations and code: [MIT](LICENSE). Hyman's 1910 Hebrew text is in the public domain.
