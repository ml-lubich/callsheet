#!/usr/bin/env bash
# The whole pipeline on the shipped transcript. The agent fan-out is stood in
# for by the expected/ files, so this runs offline and produces the same page
# every time. See ../agents/ for the real fan-out.
set -euo pipefail
cd "$(dirname "$0")"
CALLSHEET=${CALLSHEET:-callsheet}

rm -rf work out
mkdir -p out

"$CALLSHEET" parse transcript.txt -o work
"$CALLSHEET" chunk work/turns.json -n 3 -o work --metrics work/metrics.json

# In a real run an agent writes each of these; here they are shipped alongside.
cp expected/content.json work/content.json
cp expected/diagrams.html out/diagrams.html

"$CALLSHEET" lint-prose work/content.json
"$CALLSHEET" lint-diagrams out/diagrams.html --turns work/turns.json
"$CALLSHEET" build --content work/content.json --turns work/turns.json \
                   --metrics work/metrics.json --diagrams out/diagrams.html \
                   -o out/index.html
echo "wrote $(pwd)/out/index.html"
