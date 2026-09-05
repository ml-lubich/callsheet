#!/usr/bin/env bash
# The whole pipeline on the shipped transcript. The agent fan-out is stood in
# for by the expected/ files, so this runs offline and produces the same page
# every time. See ../agents/ for the real fan-out.
set -euo pipefail
cd "$(dirname "$0")"
CALLGEN=${CALLGEN:-callgen}

rm -rf work out
mkdir -p out

"$CALLGEN" parse transcript.txt -o work
"$CALLGEN" chunk work/turns.json -n 3 -o work --metrics work/metrics.json

# In a real run an agent writes each of these; here they are shipped alongside.
cp expected/content.json work/content.json
cp expected/diagrams.html out/diagrams.html

"$CALLGEN" lint-prose work/content.json
"$CALLGEN" lint-diagrams out/diagrams.html --turns work/turns.json
"$CALLGEN" build --content work/content.json --turns work/turns.json \
                   --metrics work/metrics.json --diagrams out/diagrams.html \
                   -o out/index.html
echo "wrote $(pwd)/out/index.html"
