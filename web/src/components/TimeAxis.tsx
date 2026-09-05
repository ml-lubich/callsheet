import type { Stamp } from "../types";

/**
 * A hairline of elapsed time with the moments something happened marked on it. Ruled
 * with the same tick interval as the strip chart so the two read as one clock.
 */
export function TimeAxis({
  duration,
  marks = [],
  tick,
  onPick,
}: {
  duration: number;
  marks?: Stamp[];
  tick: number;
  onPick?: (mark: Stamp) => void;
}) {
  const ticks: number[] = [];
  for (let s = 0; s <= duration; s += tick) ticks.push(s);
  const at = (s: number) => `${((s / (duration || 1)) * 100).toFixed(3)}%`;
  return (
    <div className="mini">
      {ticks.map((s) => (
        <span key={s} className="m5" style={{ left: at(s) }} />
      ))}
      {marks.map((m, i) => (
        <i
          key={`${m.s}-${i}`}
          style={{ left: at(m.s) }}
          title={m.ts}
          onClick={onPick ? () => onPick(m) : undefined}
        />
      ))}
    </div>
  );
}
