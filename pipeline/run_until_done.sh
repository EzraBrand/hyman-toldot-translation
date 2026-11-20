#!/usr/bin/env bash
# Translate new entries every 10 minutes while the fetch runs; at the end build the site, commit and push hyman-toldot.
# Done = every page in list.json saved, or no new page file for 30 minutes.
set -u
cd "$(dirname "$0")"
SITE=../hyman-toldot
total() { py -3.13 -c "import json;print(len(json.load(open('data/wikisource/list.json',encoding='utf-8'))))"; }
saved() { ls data/wikisource/pages | wc -l; }
idle=0; last=$(saved)
while true; do
  echo "$(date +%H:%M) pages $(saved)/$(total)"
  py -3.13 extract.py | head -1
  out=$(py -3.13 translate.py 2>&1)
  echo "$out" | grep -E "INCOMPLETE|FAILED|KEY BALANCE|entries,|finished"
  if echo "$out" | grep -q "KEY BALANCE"; then echo "STOP: key balance"; exit 1; fi
  now=$(saved)
  if [ "$now" -ge "$(total)" ]; then echo "fetch complete"; break; fi
  if [ "$now" -eq "$last" ]; then idle=$((idle+10)); else idle=0; fi
  last=$now
  if [ "$idle" -ge 30 ]; then echo "no new pages for 30 min: stopping"; break; fi
  sleep 600
done
py -3.13 extract.py
py -3.13 translate.py | tail -3
py -3.13 translate.py --cost
py -3.13 build_site.py
cp README.md translate_test.py fetch_wikisource.py extract.py translate.py build_site.py "$SITE/pipeline/"
git add -A && git commit -qm "Fetched pages and translations" || true
cd "$SITE" && git add -A && git commit -qm "Machine translation of all transcribed entries (Gemini 4 Argon)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" && git push -q origin main && git log --oneline | head -1
echo "ALL DONE"
