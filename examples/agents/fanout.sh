#!/usr/bin/env bash
#
# The callsheet fan-out, run for real against the Claude Code CLI.
#
#   ./fanout.sh ../product-review/transcript.txt
#
# N segment analysts and one whole-call reader run in parallel; then the
# synthesizer, the diagram author, the page build and the adversarial verifier
# run in sequence. Every stage is a separate `claude -p` invocation, so every
# stage starts in a fresh context — which is decoration for the analysts and the
# entire point for the verifier.
#
# Each role's prompt lives in prompts/ and is read, not inlined, so the prompts
# can be reviewed and edited without touching this script.

set -euo pipefail

# ── the cheap/strong split — change it here and nowhere else ────────────────
ANALYST_MODEL=${ANALYST_MODEL:-claude-sonnet-5}    # N of these, one per chunk
READER_MODEL=${READER_MODEL:-claude-opus-5}        # one, and it sees everything
SYNTH_MODEL=${SYNTH_MODEL:-claude-opus-5}
DIAGRAM_MODEL=${DIAGRAM_MODEL:-claude-opus-5}
VERIFIER_MODEL=${VERIFIER_MODEL:-claude-opus-5}

CLAUDE=${CLAUDE:-claude}
CALLSHEET=${CALLSHEET:-callsheet}
PYTHON=${PYTHON:-python3}
N=${N:-4}                                          # segment analysts
WORK=${WORK:-work}
OUT=${OUT:-out}

HERE=$(cd "$(dirname "$0")" && pwd)

die() { echo "fanout: $*" >&2; exit 1; }

# The only failure worth special-casing: a stage that returned nothing. Say which.
produced() {
  [ -s "$2" ] || die "stage '$1' produced no $2 — rerun that stage alone and read what the model said"
}

# Build one prompt: the role file, then each context file under a named heading.
ask() {
  local role=$1 model=$2 out=$3; shift 3
  local prompt f
  prompt=$(cat "$role")
  for f in "$@"; do
    [ -s "$f" ] || die "cannot build the prompt for $(basename "$role" .md): $f is missing or empty"
    prompt+=$'\n\n--- '$(basename "$f")$' ---\n'
    prompt+=$(cat "$f")
  done
  "$CLAUDE" -p "$prompt" --model "$model" > "$out"
}

# Models are asked for JSON only and mostly comply; a stray fence is not a reason
# to lose the run.
unfence() { sed -i.bak -e '/^[[:space:]]*```/d' "$1" && rm -f "$1.bak"; }

TRANSCRIPT=${1:-}
[ -n "$TRANSCRIPT" ] || die "usage: $(basename "$0") TRANSCRIPT   (env: N, WORK, OUT, *_MODEL)"
[ -f "$TRANSCRIPT" ] || die "no such transcript: $TRANSCRIPT"
command -v "$CLAUDE" >/dev/null 2>&1 || die "the Claude Code CLI ($CLAUDE) is not on PATH"
command -v "$CALLSHEET" >/dev/null 2>&1 || die "callsheet ($CALLSHEET) is not on PATH — pip install -e ."

mkdir -p "$WORK" "$OUT"

# ── 1. parse and chunk (mechanical) ─────────────────────────────────────────
echo "== parse and chunk =="
"$CALLSHEET" parse "$TRANSCRIPT" -o "$WORK"
"$CALLSHEET" chunk "$WORK/turns.json" -n "$N" -o "$WORK" --metrics "$WORK/metrics.json"
produced "parse" "$WORK/turns.json"
produced "parse" "$WORK/metrics.json"

# ── 2. the fan-out: N analysts + 1 reader, all at once ──────────────────────
echo "== fan-out: $N x $ANALYST_MODEL analysts + 1 x $READER_MODEL reader =="
pids=()
for i in $(seq 1 "$N"); do
  produced "chunk" "$WORK/chunk$i.txt"
  ask "$HERE/prompts/segment-analyst.md" "$ANALYST_MODEL" "$WORK/analysis-$i.json" \
      "$WORK/chunk$i.txt" &
  pids+=("$!")
done
ask "$HERE/prompts/whole-call-reader.md" "$READER_MODEL" "$WORK/arc.json" "$TRANSCRIPT" &
pids+=("$!")

failed=0
for pid in "${pids[@]}"; do wait "$pid" || failed=1; done
[ "$failed" -eq 0 ] || die "at least one fan-out agent exited nonzero; see the files in $WORK"

for i in $(seq 1 "$N"); do
  produced "segment analyst $i" "$WORK/analysis-$i.json"
  unfence "$WORK/analysis-$i.json"
done
produced "whole-call reader" "$WORK/arc.json"
unfence "$WORK/arc.json"

# ── 3. synthesize ───────────────────────────────────────────────────────────
echo "== synthesize =="
ask "$HERE/prompts/synthesizer.md" "$SYNTH_MODEL" "$WORK/content.json" \
    "$WORK/metrics.json" "$WORK"/analysis-*.json "$WORK/arc.json"
produced "synthesizer" "$WORK/content.json"
unfence "$WORK/content.json"
"$PYTHON" -c "import json,sys;from callsheet.schema import validate;validate(json.load(open(sys.argv[1])))" \
    "$WORK/content.json"

# ── 4. draw ─────────────────────────────────────────────────────────────────
echo "== draw =="
ask "$HERE/prompts/diagram-author.md" "$DIAGRAM_MODEL" "$OUT/diagrams.html" \
    "$WORK/content.json" "$WORK/metrics.json" "$WORK/turns.json"
produced "diagram author" "$OUT/diagrams.html"
unfence "$OUT/diagrams.html"
"$CALLSHEET" lint-diagrams "$OUT/diagrams.html" --turns "$WORK/turns.json"

# ── 5. build the page (mechanical — no agent) ───────────────────────────────
echo "== build =="
"$CALLSHEET" build --content "$WORK/content.json" --turns "$WORK/turns.json" \
                   --metrics "$WORK/metrics.json" --diagrams "$OUT/diagrams.html" \
                   -o "$OUT/index.html"
produced "build" "$OUT/index.html"

# ── 6. verify, adversarially, in a context that has seen none of the above ──
echo "== verify =="
ask "$HERE/prompts/verifier.md" "$VERIFIER_MODEL" "$OUT/verification.txt" \
    "$OUT/index.html" "$WORK/turns.json"
produced "verifier" "$OUT/verification.txt"

echo
echo "artifact:     $OUT/index.html"
echo "defect list:  $OUT/verification.txt"
echo
echo "Apply every deletion the verifier found, rebuild, and run the verify stage"
echo "again in another fresh context. Two consecutive clean passes, or it is not done."
