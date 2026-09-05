/**
 * The glyph library: small SVG parts figures are assembled from. Every one of them
 * draws in currentColor and CSS variables only, so a glyph inherits its figure's pen
 * and works in both themes without a second definition.
 */
import type { ReactNode } from "react";
import { CountUp } from "../components/CountUp";
import { type Pen, penClassName } from "./pen";

export type { Pen };
export { penClassName };

const SOFT = "var(--ink-soft)";
const GRID = "var(--grid)";

/** Shared frame: a titled svg that scales to its container and never overflows it. */
function Frame({
  w,
  h,
  title,
  className,
  pen,
  children,
}: {
  w: number;
  h: number;
  title: string;
  className?: string;
  pen?: Pen;
  children: ReactNode;
}) {
  return (
    <svg
      className={penClassName(pen, className)}
      viewBox={`0 0 ${w} ${h}`}
      role="img"
      aria-label={title}
      preserveAspectRatio="xMinYMid meet"
      style={{ display: "block", width: "100%", height: "auto", maxWidth: w }}
    >
      <title>{title}</title>
      {children}
    </svg>
  );
}

/* ------------------------------------------------------------------ ScaleBar */

/**
 * A score on a bar. `bounded` fills a 0–1 track, `unbounded` runs off the end behind a
 * ≫ overflow mark, and `own` labels the track with the range it is actually drawn on.
 */
export function ScaleBar({
  value,
  label,
  kind = "bounded",
  min = 0,
  max = 1,
  pen = "neutral",
  width = 320,
}: {
  value: number;
  label?: string;
  kind?: "bounded" | "unbounded" | "own";
  min?: number;
  max?: number;
  pen?: Pen;
  width?: number;
}) {
  const H = label ? 46 : 26;
  const y = label ? 28 : 10;
  const track = kind === "unbounded" ? width - 34 : width - 2;
  const span = max - min || 1;
  const fill = Math.max(0, Math.min(1, (value - min) / span)) * track;
  const over = kind === "unbounded" && value > max;
  return (
    <Frame w={width} h={H} pen={pen} title={`${label ? label + ": " : ""}${value}`} className="gl-scale">
      {label && (
        <text className="gl-lab" x={1} y={14} fill={SOFT}>
          {label}
        </text>
      )}
      <rect x={1} y={y} width={track} height={8} fill="none" stroke={GRID} />
      <rect x={1} y={y} width={fill.toFixed(1)} height={8} fill="currentColor" />
      <line x1={1 + fill} y1={y - 4} x2={1 + fill} y2={y + 12} stroke="currentColor" strokeWidth={1.4} />
      {over && (
        <text className="gl-lab" x={width - 26} y={y + 9} fill="currentColor">
          &#8811;
        </text>
      )}
      {kind === "own" && (
        <>
          <text className="gl-tick" x={1} y={y + 21} fill={SOFT}>
            {min}
          </text>
          <text className="gl-tick" x={track} y={y + 21} fill={SOFT} textAnchor="end">
            {max}
          </text>
        </>
      )}
    </Frame>
  );
}

/* ------------------------------------------------------------------ FieldRow */

/** One field of a record: never filled, filled, or filled and backed by a citation. */
export function FieldRow({
  label,
  state = "empty",
  fill = 0.68,
  pen = "neutral",
  width = 300,
}: {
  label: string;
  state?: "empty" | "filled" | "cited";
  fill?: number;
  pen?: Pen;
  width?: number;
}) {
  const barX = 116;
  const barW = width - barX - (state === "cited" ? 18 : 2);
  return (
    <Frame w={width} h={22} pen={pen} title={`${label} — ${state}`} className="gl-field">
      <text className="gl-lab" x={0} y={14} fill={SOFT}>
        {label}
      </text>
      {state === "empty" ? (
        <rect x={barX} y={6} width={barW} height={9} fill="none" stroke={GRID} strokeDasharray="3 3" />
      ) : (
        <>
          <rect x={barX} y={6} width={barW} height={9} fill="none" stroke={GRID} />
          <rect x={barX} y={6} width={(barW * Math.min(1, fill)).toFixed(1)} height={9} fill="currentColor" />
        </>
      )}
      {state === "cited" && <circle cx={width - 7} cy={10.5} r={3.5} fill="currentColor" />}
    </Frame>
  );
}

/* ------------------------------------------------------------------ DocGlyph */

/** A document: folded corner, three lines of text, and an optional processing badge. */
export function DocGlyph({
  badge,
  label,
  pen = "neutral",
  width = 84,
}: {
  badge?: string;
  label?: string;
  pen?: Pen;
  width?: number;
}) {
  const H = label ? 112 : 96;
  return (
    <Frame w={width} h={H} pen={pen} title={label || badge || "document"} className="gl-doc">
      <path
        d="M6 6 h44 l20 20 v58 h-64 z"
        fill="var(--paper-2)"
        stroke="currentColor"
        strokeWidth={1.2}
      />
      <path d="M50 6 v20 h20" fill="none" stroke="currentColor" strokeWidth={1.2} />
      {[42, 54, 66].map((y, i) => (
        <line key={y} x1={16} y1={y} x2={i === 2 ? 44 : 60} y2={y} stroke={SOFT} strokeWidth={1.4} />
      ))}
      {badge && (
        <>
          <rect x={12} y={72} width={34} height={13} fill="currentColor" />
          <text className="gl-badge" x={29} y={81.5} textAnchor="middle" fill="var(--paper)">
            {badge}
          </text>
        </>
      )}
      {label && (
        <text className="gl-lab" x={6} y={104} fill={SOFT}>
          {label}
        </text>
      )}
    </Frame>
  );
}

/* --------------------------------------------------------------- PersonGlyph */

/** A person. Head, shoulders, an optional name beneath. */
export function PersonGlyph({
  label,
  pen = "neutral",
  width = 64,
}: {
  label?: string;
  pen?: Pen;
  width?: number;
}) {
  const H = label ? 76 : 58;
  return (
    <Frame w={width} h={H} pen={pen} title={label || "participant"} className="gl-person">
      <circle cx={32} cy={17} r={11} fill="none" stroke="currentColor" strokeWidth={1.4} />
      <path
        d="M11 52 a21 21 0 0 1 42 0"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.4}
      />
      {label && (
        <text className="gl-lab" x={32} y={68} textAnchor="middle" fill={SOFT}>
          {label}
        </text>
      )}
    </Frame>
  );
}

/* ----------------------------------------------------------------- GateChain */

/** n gates on a line: the shape a decision graph makes when every step can stop it. */
export function GateChain({
  n = 3,
  labels = [],
  passed = n,
  pen = "neutral",
  width = 360,
}: {
  n?: number;
  labels?: string[];
  passed?: number;
  pen?: Pen;
  width?: number;
}) {
  const H = labels.length ? 56 : 34;
  const step = (width - 32) / Math.max(1, n - 1 || 1);
  const cy = 17;
  const at = (i: number) => (n === 1 ? width / 2 : 16 + i * step);
  return (
    <Frame w={width} h={H} pen={pen} title={`${n} gates, ${passed} passed`} className="gl-gates">
      <line x1={at(0)} y1={cy} x2={at(n - 1)} y2={cy} stroke={GRID} strokeWidth={1.2} />
      {Array.from({ length: n }, (_, i) => {
        const x = at(i);
        const on = i < passed;
        return (
          <g key={i}>
            <path
              d={`M${x} ${cy - 9} L${x + 9} ${cy} L${x} ${cy + 9} L${x - 9} ${cy} Z`}
              fill={on ? "currentColor" : "var(--paper-2)"}
              stroke="currentColor"
              strokeWidth={1.2}
            />
            {labels[i] && (
              <text className="gl-lab" x={x} y={cy + 30} textAnchor="middle" fill={SOFT}>
                {labels[i]}
              </text>
            )}
          </g>
        );
      })}
    </Frame>
  );
}

/* ------------------------------------------------------------------- Cascade */

/** An escalation that steps down: each stage lower and narrower than the one before. */
export function Cascade({
  steps,
  pen = "neutral",
  width = 340,
}: {
  steps: string[];
  pen?: Pen;
  width?: number;
}) {
  const drop = 26;
  const H = steps.length * drop + 14;
  const run = (width - 8) / Math.max(1, steps.length);
  return (
    <Frame w={width} h={H} pen={pen} title={steps.join(" → ")} className="gl-cascade">
      {steps.map((s, i) => {
        const y = 12 + i * drop;
        const x = 4 + i * (run * 0.34);
        return (
          <g key={s + i}>
            <line x1={x} y1={y} x2={x + run * 0.62} y2={y} stroke="currentColor" strokeWidth={1.6} />
            {i < steps.length - 1 && (
              <line
                x1={x + run * 0.62}
                y1={y}
                x2={x + run * 0.62}
                y2={y + drop}
                stroke={GRID}
                strokeWidth={1.2}
                strokeDasharray="2 3"
              />
            )}
            <text className="gl-lab" x={x} y={y - 6} fill={SOFT}>
              {s}
            </text>
          </g>
        );
      })}
    </Frame>
  );
}

/* ------------------------------------------------------------- MagnitudeBar */

/** One bar against a shared maximum, for the comparisons that only work at scale. */
export function MagnitudeBar({
  label,
  value,
  max,
  display,
  pen = "neutral",
  width = 420,
}: {
  label: string;
  value: number;
  max: number;
  display?: string;
  pen?: Pen;
  width?: number;
}) {
  const barW = Math.max(1.5, (Math.max(0, value) / (max || 1)) * (width - 132));
  return (
    <Frame w={width} h={34} pen={pen} title={`${label}: ${display ?? value}`} className="gl-mag">
      <text className="gl-lab" x={0} y={13} fill={SOFT}>
        {label}
      </text>
      <rect x={0} y={19} width={barW.toFixed(1)} height={11} fill="currentColor" />
      <text className="gl-val" x={barW + 8} y={29} fill="var(--ink)">
        {display ?? value.toLocaleString("en-US")}
      </text>
    </Frame>
  );
}

/* ---------------------------------------------------------------- BigNumber */

/** A figure set large enough to be read across the room, with its unit and its caption. */
export function BigNumber({
  value,
  unit,
  caption,
  display,
  pen = "neutral",
}: {
  value: number;
  unit?: string;
  caption?: string;
  display?: string;
  pen?: Pen;
}) {
  return (
    <div className={penClassName(pen, "gl-big")}>
      <div className="gl-big-v">
        {display ? <span>{display}</span> : <CountUp value={value} />}
        {unit && <span className="gl-big-u">{unit}</span>}
      </div>
      {caption && <div className="gl-big-c">{caption}</div>}
    </div>
  );
}

/* ------------------------------------------------------------------- Compare */

/** Two inputs meeting at a node — the point where a comparison actually happens. */
export function Compare({
  left,
  right,
  out,
  pen = "neutral",
  width = 320,
}: {
  left: string;
  right: string;
  out?: string;
  pen?: Pen;
  width?: number;
}) {
  const cx = width / 2;
  return (
    <Frame w={width} h={92} pen={pen} title={`${left} compared with ${right}`} className="gl-compare">
      <text className="gl-lab" x={0} y={20} fill={SOFT}>
        {left}
      </text>
      <text className="gl-lab" x={width} y={20} textAnchor="end" fill={SOFT}>
        {right}
      </text>
      <path d={`M14 28 C14 50 ${cx - 24} 40 ${cx - 14} 46`} fill="none" stroke="currentColor" strokeWidth={1.3} />
      <path
        d={`M${width - 14} 28 C${width - 14} 50 ${cx + 24} 40 ${cx + 14} 46`}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.3}
      />
      <circle cx={cx} cy={46} r={11} fill="var(--paper-2)" stroke="currentColor" strokeWidth={1.3} />
      <line x1={cx - 6} y1={46} x2={cx + 6} y2={46} stroke="currentColor" strokeWidth={1.3} />
      <line x1={cx} y1={40} x2={cx} y2={52} stroke="currentColor" strokeWidth={1.3} />
      {out && (
        <>
          <line x1={cx} y1={57} x2={cx} y2={70} stroke={GRID} strokeWidth={1.2} />
          <text className="gl-lab" x={cx} y={84} textAnchor="middle" fill="var(--ink)">
            {out}
          </text>
        </>
      )}
    </Frame>
  );
}

/* --------------------------------------------------------------------- Route */

/** One source fanning out to the places it ends up. */
export function Route({
  from,
  to,
  pen = "neutral",
  width = 380,
}: {
  from: string;
  to: string[];
  pen?: Pen;
  width?: number;
}) {
  const gap = 26;
  const H = Math.max(70, to.length * gap + 18);
  const cy = H / 2;
  const x0 = 6;
  const x1 = 138;
  const x2 = 168;
  return (
    <Frame w={width} h={H} pen={pen} title={`${from} to ${to.join(", ")}`} className="gl-route">
      <text className="gl-lab" x={x0} y={cy + 4} fill="var(--ink)">
        {from}
      </text>
      <circle cx={x1} cy={cy} r={4} fill="currentColor" />
      {to.map((t, i) => {
        const y = 14 + i * gap + 4;
        return (
          <g key={t + i}>
            <path
              d={`M${x1 + 4} ${cy} C${x1 + 22} ${cy} ${x2 - 20} ${y} ${x2} ${y}`}
              fill="none"
              stroke="currentColor"
              strokeWidth={1.2}
            />
            <text className="gl-lab" x={x2 + 8} y={y + 4} fill={SOFT}>
              {t}
            </text>
          </g>
        );
      })}
    </Frame>
  );
}
