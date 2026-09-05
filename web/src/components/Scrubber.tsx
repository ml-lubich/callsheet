import { useCallback, useRef } from "react";
import { keyOf, penVar } from "../lib/derive";
import type { Deck, TimelinePoint } from "../types";

const VW = 1000;
const VH = 44;
const MID = 22;

/**
 * The strip chart again, an inch high, pinned above the transcript. It is the reader's
 * position indicator and its jump control at once: the lit window is the stretch of the
 * call currently on screen, the ticks below are where the search matched, and a click or
 * a drag anywhere on it moves the reader to that minute.
 */
export function Scrubber({
  deck,
  hits,
  window: win,
  onSeek,
}: {
  deck: Deck;
  /** Seconds at which the current search matched, drawn as ticks. */
  hits: number[];
  /** The [from, to] seconds currently on screen, or null when nothing is rendered. */
  window: [number, number] | null;
  onSeek: (seconds: number) => void;
}) {
  const ref = useRef<SVGSVGElement>(null);
  const dragging = useRef(false);
  const { metrics, keys, duration } = deck;
  const timeline: TimelinePoint[] = metrics.timeline ?? [];
  const max = timeline.reduce((m, t) => Math.max(m, t.words), 1) || 1;
  const x = (s: number) => (s / (duration || 1)) * VW;

  const seekFrom = useCallback(
    (clientX: number) => {
      const box = ref.current?.getBoundingClientRect();
      if (!box || !box.width) return;
      const fraction = Math.max(0, Math.min(1, (clientX - box.left) / box.width));
      onSeek(fraction * duration);
    },
    [duration, onSeek],
  );

  return (
    <svg
      ref={ref}
      className="scrubber"
      viewBox={`0 0 ${VW} ${VH}`}
      preserveAspectRatio="none"
      role="slider"
      tabIndex={0}
      aria-label="Position in the call"
      aria-valuemin={0}
      aria-valuemax={Math.round(duration)}
      aria-valuenow={Math.round(win ? win[0] : 0)}
      onPointerDown={(e) => {
        dragging.current = true;
        e.currentTarget.setPointerCapture(e.pointerId);
        seekFrom(e.clientX);
      }}
      onPointerMove={(e) => dragging.current && seekFrom(e.clientX)}
      onPointerUp={() => (dragging.current = false)}
      onPointerCancel={() => (dragging.current = false)}
      onKeyDown={(e) => {
        const step = duration / 20;
        if (e.key === "ArrowRight") onSeek(Math.min(duration, (win?.[0] ?? 0) + step));
        if (e.key === "ArrowLeft") onSeek(Math.max(0, (win?.[0] ?? 0) - step));
      }}
    >
      {win && (
        <rect
          className="scrub-win"
          x={x(win[0])}
          width={Math.max(4, x(win[1]) - x(win[0]))}
          y={0}
          height={VH}
        />
      )}
      {timeline.map((t, i) => {
        const key = keyOf(deck, t.spk);
        const up = keys.indexOf(key) !== 1;
        const h = Math.max(0.8, (t.words / max) * 16);
        return (
          <rect
            key={i}
            x={x(t.s)}
            y={up ? MID - h : MID}
            width={1.6}
            height={h}
            fill={penVar(keys, key)}
            opacity={0.85}
          />
        );
      })}
      <line x1={0} y1={MID} x2={VW} y2={MID} stroke="var(--grid)" strokeWidth={0.7} />
      {hits.map((s, i) => (
        <rect key={`h${i}`} className="scrub-hit" x={x(s)} y={VH - 8} width={1.6} height={8} />
      ))}
    </svg>
  );
}
