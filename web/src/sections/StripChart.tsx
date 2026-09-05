import { type ReactNode, useMemo, useRef, useState } from "react";
import { Skeleton } from "../components/Skeleton";
import { keyOf, mmss, nearestTurn, penVar, stats } from "../lib/derive";
import { jump, reduceMotion } from "../lib/jump";
import type { Deck, TimelinePoint } from "../types";

/* One fixed drawing surface; the browser scales it. Numbers are the vanilla page's. */
const VW = 1600;
const VH = 300;
const X0 = 44;
const XW = 1500;
const BASE = 132;
const HALF = 112;
const TOP = 16;
const BOT = 250;
const RUL = 258;

export function tickFor(duration: number): number {
  return Math.max(60, Math.round(duration / 14 / 60) * 60);
}

export function StripChartSkeleton() {
  return (
    <div className="sk-grid">
      <Skeleton h={14} w="42%" />
      <Skeleton h={196} />
      <Skeleton h={14} w="66%" />
    </div>
  );
}

export function StripChart({ deck, terrain }: { deck: Deck; terrain?: ReactNode }) {
  const { metrics, turns, keys, names, duration } = deck;
  const timeline = metrics.timeline ?? [];
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<TimelinePoint | null>(null);

  const derived = useMemo(() => stats(deck, metrics), [deck, metrics]);
  const tick = tickFor(duration);
  const xOf = (s: number) => X0 + (s / duration) * XW;
  const maxWords = timeline.reduce((m, t) => Math.max(m, t.words), 1) || 1;

  const ticks = useMemo(() => {
    const out: number[] = [];
    for (let s = 0; s <= duration; s += tick) out.push(s);
    return out;
  }, [duration, tick]);

  const bars = useMemo(
    () =>
      timeline.map((t, i) => {
        const key = keyOf(deck, t.spk);
        const up = keys.indexOf(key) !== 1;
        const next = timeline[i + 1];
        const gap = next ? (xOf(next.s) - xOf(t.s)) * 0.72 : 4;
        const w = Math.min(11, Math.max(2.2, gap));
        const h = Math.max(1.2, (t.words / maxWords) * HALF);
        return { t, i, x: xOf(t.s) - w / 2, y: up ? BASE - h : BASE, w, h, fill: penVar(keys, key) };
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [timeline, keys, maxWords, duration],
  );

  function readAt(clientX: number) {
    const svg = svgRef.current;
    if (!svg || !timeline.length) return;
    const box = svg.getBoundingClientRect();
    const sec = (((clientX - box.left) / box.width) * VW - X0) / XW * duration;
    let best = timeline[0];
    let bd = Infinity;
    for (const t of timeline) {
      const d = Math.abs(t.s - sec);
      if (d < bd) {
        bd = d;
        best = t;
      }
    }
    setHover(best);
  }

  return (
    <>
      <div className="chart-head">
        <div className="legend">
          {keys.map((k, i) => (
            <span key={k}>
              <i className="swatch" style={{ background: penVar(keys, k) }} />
              {names[k] || k}
              {i === 1 ? " below" : " above"}
            </span>
          ))}
        </div>
        <div className="readout" aria-live="polite">
          {hover ? (
            <>
              <span className="num">{hover.ts}</span> <span className="dim">/</span> {hover.spk}{" "}
              <span className="dim">/</span> <span className="num">{hover.words}</span> words
            </>
          ) : (
            <span className="dim">Hover the chart for turn detail</span>
          )}
        </div>
      </div>

      <div className="chart-scroll">
        <div className="chart-inner">
          <svg
            ref={svgRef}
            viewBox={`0 0 ${VW} ${VH}`}
            role="img"
            aria-label="Turn-by-turn word counts across elapsed time"
            onMouseMove={(e) => readAt(e.clientX)}
            onMouseLeave={() => setHover(null)}
            onTouchMove={(e) => e.touches[0] && readAt(e.touches[0].clientX)}
          >
            <defs>
              <linearGradient id="cs-trail" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--pen-a)" stopOpacity=".07" />
                <stop offset="50%" stopColor="var(--pen-a)" stopOpacity="0" />
                <stop offset="50%" stopColor="var(--pen-b)" stopOpacity="0" />
                <stop offset="100%" stopColor="var(--pen-b)" stopOpacity=".07" />
              </linearGradient>
              <clipPath id="cs-sweep">
                <rect
                  className={reduceMotion() ? undefined : "cs-sweep"}
                  x="0"
                  y="0"
                  width={VW}
                  height={VH}
                />
              </clipPath>
            </defs>

            <rect x={X0} y={TOP} width={XW} height={BOT - TOP} fill="url(#cs-trail)" />
            {ticks.map((s) => (
              <line
                key={`g${s}`}
                x1={xOf(s)}
                y1={TOP}
                x2={xOf(s)}
                y2={BOT}
                stroke="var(--grid)"
                strokeWidth={1}
              />
            ))}
            <line x1={X0} y1={BASE} x2={X0 + XW} y2={BASE} stroke="var(--ink-soft)" strokeWidth={1} />

            <g clipPath="url(#cs-sweep)">
              {bars.map((b) => (
                <rect
                  key={b.i}
                  className="bar"
                  x={b.x}
                  y={b.y}
                  width={b.w}
                  height={b.h}
                  fill={b.fill}
                  onClick={() => jump(nearestTurn(turns, b.t.s))}
                >
                  <title>{`${b.t.ts}  ${b.t.spk}  ${b.t.words} words`}</title>
                </rect>
              ))}
            </g>

            <line
              x1={hover ? xOf(hover.s) : 0}
              x2={hover ? xOf(hover.s) : 0}
              y1={TOP}
              y2={BOT}
              stroke="var(--ink-soft)"
              strokeWidth={1}
              strokeDasharray="3 4"
              opacity={hover ? 1 : 0}
            />

            <line x1={X0} y1={RUL} x2={X0 + XW} y2={RUL} stroke="var(--grid)" strokeWidth={1} />
            {ticks.map((s) => (
              <g key={`r${s}`}>
                <line x1={xOf(s)} y1={RUL} x2={xOf(s)} y2={RUL + 9} stroke="var(--grid)" strokeWidth={1} />
                <text x={xOf(s)} y={RUL + 30} fontSize={19} fill="var(--ink-soft)" textAnchor="middle">
                  {mmss(s)}
                </text>
              </g>
            ))}
          </svg>
        </div>
      </div>

      {derived && (
        <p className="stats">
          {derived.turns} turns &nbsp;·&nbsp;{" "}
          {derived.shares.map((s) => `${s.name} ${s.percent}%`).join(" / ")} of words &nbsp;·&nbsp;
          longest turn {derived.longest.words} words at {derived.longest.ts} &nbsp;·&nbsp; median
          turn {derived.medianWords} words
          {derived.estimatedTiming ? " · timing estimated from word counts" : ""}
        </p>
      )}

      {terrain}
    </>
  );
}
