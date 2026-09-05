import { Suspense, lazy, useMemo, useRef, type ReactNode } from "react";
import { useOnceInView } from "./lib/inview";
import { Reveal, STAGGER } from "./components/Reveal";
import { Skeleton, SkeletonLines } from "./components/Skeleton";
import { shapeOf } from "./lib/mode";
import { Collapsible } from "./components/Collapsible";
import { Abstract, AbstractSkeleton } from "./sections/Abstract";
import { Acts, ActsSkeleton } from "./sections/Acts";
import { Evidence, EvidenceSkeleton } from "./sections/Evidence";
import { Figures, FiguresSkeleton } from "./sections/Figures";
import { Fit } from "./sections/Fit";
import { Friction } from "./sections/Friction";
import { Lands } from "./sections/Lands";
import { Named, NamedSkeleton } from "./sections/Named";
import { Next } from "./sections/Next";
import { Numbers } from "./sections/Numbers";
import { Plate } from "./sections/Plate";
import { Quotes, QuotesSkeleton } from "./sections/Quotes";
import { Sec } from "./sections/Sec";
import { RowsSkeleton, Signals } from "./sections/Signals";
import { StripChart, StripChartSkeleton } from "./sections/StripChart";
import { Threads, ThreadsSkeleton } from "./sections/Threads";
import { Transcript } from "./sections/Transcript";
import { Verdict, VerdictSkeleton } from "./sections/Verdict";
import type { Deck } from "./types";

const CallTerrain = lazy(() => import("./scenes/CallTerrain"));

/**
 * The one 3D moment on the page, kept out of the way of the first paint: nothing of
 * three.js runs until the reader is nearly at it.
 */
function Terrain({ deck }: { deck: Deck }) {
  const ref = useRef<HTMLDivElement>(null);
  const near = useOnceInView(ref, "300px 0px 300px 0px");
  return (
    <div ref={ref}>
      {near && (
        <Suspense
          fallback={
            <div className="terrain">
              <Skeleton h={300} />
            </div>
          }
        >
          <CallTerrain deck={deck} />
        </Suspense>
      )}
    </div>
  );
}

interface Block {
  title?: string;
  className?: string;
  /** Row count shown on the folded header when the mode collapses this section. */
  count?: number;
  when: boolean;
  skeleton: ReactNode;
  body: ReactNode;
}

/**
 * Every section the page can draw, keyed by the id `src/callgen/modes.py` uses. The
 * mode decides which of these appear and in what order; a section the analysis had
 * nothing for is dropped whatever the mode says, rather than left as an empty heading.
 *
 * Two blocks are not the mode's to move. The verdict is the abstract's first line and
 * travels with it; where the call lands is the acts' conclusion and travels with them.
 */
function blocks(deck: Deck, figureCap?: number): Record<string, Block> {
  const c = deck.content;
  const turns = deck.turns;
  const shape = shapeOf(c);

  return {
    strip: {
      className: "chart-sec",
      when: true,
      skeleton: <StripChartSkeleton />,
      body: <StripChart deck={deck} terrain={<Terrain deck={deck} />} />,
    },
    abstract: {
      title: "Abstract",
      when: Boolean(c.abstract || c.verdict),
      skeleton: c.verdict ? <VerdictSkeleton /> : <AbstractSkeleton />,
      body: (
        <>
          {c.verdict && <Verdict verdict={c.verdict} />}
          {c.abstract && <Abstract text={c.abstract} />}
        </>
      ),
    },
    highlights: {
      title: "Highlights",
      when: (c.highlights ?? []).length > 0,
      skeleton: <SkeletonLines n={4} />,
      body: (
        <ul className="bullets narrow">
          {(c.highlights ?? []).map((h, i) => (
            <Reveal as="li" key={h} delay={i * STAGGER}>
              {h}
            </Reveal>
          ))}
        </ul>
      ),
    },
    figures: {
      title: "Diagrams",
      when: Boolean(deck.diagrams.trim()),
      skeleton: <FiguresSkeleton />,
      body: <Figures fragment={deck.diagrams} cap={figureCap} />,
    },
    acts: {
      title: "Acts",
      when: (c.acts ?? []).length > 0,
      skeleton: <ActsSkeleton />,
      body: (
        <>
          <Acts acts={c.acts} duration={deck.duration} turns={turns} />
          {(c.lands ?? []).length > 0 && (
            <div className="lands-block">
              <h3 className="subhead">Where it lands</h3>
              <Lands lands={c.lands!} turns={turns} />
            </div>
          )}
        </>
      ),
    },
    threads: {
      title: "Threads",
      when: (c.threads ?? []).length > 0,
      skeleton: <ThreadsSkeleton />,
      body: <Threads threads={c.threads!} duration={deck.duration} turns={turns} />,
    },
    evidence: {
      title: "Evidence",
      count: (c.evidence ?? []).length,
      when: (c.evidence ?? []).length > 0,
      skeleton: <EvidenceSkeleton />,
      body: <Evidence rows={c.evidence!} turns={turns} />,
    },
    signals: {
      title: "Signals",
      count: (c.signals ?? []).length,
      when: (c.signals ?? []).length > 0,
      skeleton: <RowsSkeleton n={4} />,
      body: <Signals rows={c.signals!} turns={turns} />,
    },
    numbers: {
      title: "Numbers",
      count: (c.numbers ?? []).length,
      when: (c.numbers ?? []).length > 0,
      skeleton: <RowsSkeleton n={3} />,
      body: <Numbers rows={c.numbers!} turns={turns} />,
    },
    tech: {
      title: "Named in the call",
      count: (c.tech ?? []).length,
      when: (c.tech ?? []).length > 0,
      skeleton: <NamedSkeleton />,
      body: <Named tech={c.tech!} />,
    },
    friction: {
      title: "Friction",
      count: (c.tensions ?? []).length + (c.diarization ?? []).length,
      when: (c.tensions ?? []).length > 0 || (c.diarization ?? []).length > 0,
      skeleton: <RowsSkeleton />,
      body: <Friction tensions={c.tensions} diarization={c.diarization} turns={turns} />,
    },
    quotes: {
      title: "Quotes",
      when: (c.quotes ?? []).length > 0,
      skeleton: <QuotesSkeleton />,
      body: <Quotes quotes={c.quotes!} deck={deck} turns={turns} />,
    },
    fit: {
      title: "Fit",
      when:
        (c.fit?.aligned_on ?? []).length +
          (c.fit?.unresolved ?? []).length +
          (c.fit?.risks ?? []).length >
        0,
      skeleton: <SkeletonLines n={5} />,
      body: <Fit fit={c.fit!} />,
    },
    next: {
      title: "Next",
      when: (c.next_steps ?? []).length > 0,
      skeleton: <RowsSkeleton />,
      body: <Next steps={c.next_steps!} turns={turns} />,
    },
    transcript: {
      title: "Transcript",
      when: turns.length > 0,
      skeleton: <RowsSkeleton n={2} />,
      body: <Transcript deck={deck} mode={shape.transcript} />,
    },
  };
}

/**
 * Signals and numbers are two lists of the same shape and sit side by side when the mode
 * asks for both in a row. Everything else is one section per block.
 */
function pairUp(ids: string[]): string[][] {
  const out: string[][] = [];
  for (let i = 0; i < ids.length; i++) {
    if (ids[i] === "signals" && ids[i + 1] === "numbers") {
      out.push(["signals", "numbers"]);
      i++;
    } else out.push([ids[i]]);
  }
  return out;
}

/**
 * A section the mode folds. The body is identical; only its default visibility changes,
 * so a reader who wants the 26 rows gets the 26 rows, and one who does not is not
 * handed a wall of text between two figures.
 */
function fold(folded: boolean, label: string, count: number | undefined, body: ReactNode) {
  if (!folded) return body;
  return (
    <Collapsible label={`Show ${label.toLowerCase()}`} meta={count ? `${count} rows` : undefined}>
      {body}
    </Collapsible>
  );
}

export function App({ deck }: { deck: Deck }) {
  const shape = useMemo(() => shapeOf(deck.content), [deck.content]);
  const all = useMemo(() => blocks(deck, shape.figures), [deck, shape.figures]);

  const rows = pairUp(shape.sections.filter((id) => all[id]?.when));

  return (
    <main>
      <Plate deck={deck} />
      {rows.map((row, order) => {
        if (row.length === 2) {
          const [a, b] = row.map((id) => all[id]);
          return (
            <Sec
              key={row.join("-")}
              order={order + 1}
              title="Signals & numbers"
              skeleton={<RowsSkeleton n={4} />}
            >
              {fold(
                row.every((id) => shape.collapsed.includes(id)),
                "Signals and numbers",
                (a.count ?? 0) + (b.count ?? 0),
                <div className="twoup">
                  <div>
                    <h3 className="subhead">{a.title}</h3>
                    {a.body}
                  </div>
                  <div>
                    <h3 className="subhead">{b.title}</h3>
                    {b.body}
                  </div>
                </div>,
              )}
            </Sec>
          );
        }
        const block = all[row[0]];
        return (
          <Sec
            key={row[0]}
            id={`sec-${row[0]}`}
            order={order + 1}
            title={block.title}
            className={block.className}
            skeleton={block.skeleton}
          >
            {fold(shape.collapsed.includes(row[0]), block.title ?? row[0], block.count, block.body)}
          </Sec>
        );
      })}
      <p className="colophon">
        Callgen · one file, every timestamp links to the turn it came from.
      </p>
    </main>
  );
}
