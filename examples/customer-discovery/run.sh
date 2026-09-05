#!/usr/bin/env bash
# The whole pipeline on the shipped transcript, including the hold-out. The
# agent fan-out is stood in for by the expected/ files, so this runs offline and
# produces the same page every time. See ../agents/ for the real fan-out.
set -euo pipefail
cd "$(dirname "$0")"
CALLSHEET=${CALLSHEET:-callsheet}

rm -rf work out sealed sealed.sha256
mkdir -p out sealed

"$CALLSHEET" parse transcript.txt -o work
"$CALLSHEET" chunk work/turns.json -n 3 -o work --metrics work/metrics.json

# Seal the other analyst's write-up BEFORE any analysis happens. After this it
# is read-only and hashed, and nothing in the build may open it.
cp other-analyst.html sealed/
"$CALLSHEET" seal sealed

# In a real run an agent writes each of these; here they are shipped alongside.
cp expected/content.json work/content.json
cp expected/diagrams.html out/diagrams.html

"$CALLSHEET" lint-diagrams out/diagrams.html --turns work/turns.json
"$CALLSHEET" build --content work/content.json --turns work/turns.json \
                   --metrics work/metrics.json --diagrams out/diagrams.html \
                   -o out/index.html

# Only now, with the artifact final, is the seal opened and overlap measured.
"$CALLSHEET" compare out/index.html sealed
echo "wrote $(pwd)/out/index.html"
