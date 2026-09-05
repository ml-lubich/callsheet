import { useEffect, useMemo, useRef } from "react";
import { Skeleton } from "../components/Skeleton";
import { figureFor, registeredFigureIds } from "../figures";
import { reduceMotion } from "../lib/jump";

/** Elements that are worth drawing as a stroke rather than fading in. */
const STROKED = "path, line, polyline";
const FILLED = "text, rect, circle, ellipse, polygon, image";

interface Piece {
  id: string;
  html: string;
  /** A drawn figure rather than a lead-in or a bridge. Only these count against a cap. */
  figure: boolean;
}

/** The fragment split into its top-level nodes, so a single figure can be swapped out. */
export function splitFragment(html: string): Piece[] {
  if (typeof DOMParser === "undefined" || !html.trim()) return [];
  const doc = new DOMParser().parseFromString(`<body>${html}</body>`, "text/html");
  return [...doc.body.children].map((el, i) => ({
    id: el.id || `piece-${i}`,
    html: el.outerHTML,
    figure: el.tagName === "FIGURE",
  }));
}

/**
 * A mode's figure cap, applied the way the vanilla template applies it: the first `cap`
 * figures survive and the rest are dropped. The prose between them is not a figure and
 * is not counted.
 */
export function capFigures(pieces: Piece[], cap?: number): Piece[] {
  if (typeof cap !== "number" || cap < 0) return pieces;
  let seen = 0;
  return pieces.filter((p) => !p.figure || ++seen <= cap);
}

/** How a figure is driven: once, on the way in, or continuously by scroll position. */
export type Driver = "reveal" | "scroll";

/**
 * The figure's own progress across the viewport, 0 just below it to 1 once it has been
 * read. Deliberately not motion's `useScroll`: these elements are injected HTML, not
 * React children, so there is no ref to hand it.
 */
function scrollProgressOf(el: Element): number {
  const box = el.getBoundingClientRect();
  const h = window.innerHeight || 1;
  const run = box.height + h * 0.5;
  return Math.max(0, Math.min(1, (h - box.top) / (run || 1)));
}

/**
 * Draws the figures on. Generic over whatever SVG the fragment happens to contain:
 * strokes sweep from nothing to their full length, then the text and fills come up
 * behind them. Hand-authored figures animate with no edits of their own.
 *
 * `reveal` runs the draw once when the figure is scrolled to. `scroll` ties the same
 * draw to scroll position, so the reader can run it backwards.
 */
function useDrawOn(ref: React.RefObject<HTMLDivElement | null>, driver: Driver) {
  useEffect(() => {
    const root = ref.current;
    if (!root || reduceMotion() || typeof IntersectionObserver === "undefined") return;

    const figures = [...root.querySelectorAll<HTMLElement>("figure, .dg")];
    const prepared = figures.filter((fig) => {
      let marked = 0;
      fig.querySelectorAll<SVGGeometryElement>(STROKED).forEach((el, i) => {
        const len = typeof el.getTotalLength === "function" ? el.getTotalLength() : 0;
        if (!len || len > 6000) return;
        el.setAttribute("data-draw", "");
        el.style.setProperty("--dash", `${len.toFixed(1)}`);
        el.style.setProperty("--wait", `${Math.min(0.5, i * 0.02)}s`);
        marked++;
      });
      fig.querySelectorAll<SVGElement>(FILLED).forEach((el, i) => {
        el.setAttribute("data-fade", "");
        el.style.setProperty("--wait", `${0.25 + Math.min(0.5, i * 0.012)}s`);
        marked++;
      });
      if (marked) fig.classList.add("dg-draw");
      return marked > 0;
    });

    if (driver === "scroll") {
      prepared.forEach((f) => f.classList.add("dg-scrubbed"));
      let raf = 0;
      const paint = () => {
        raf = 0;
        for (const fig of prepared) {
          fig.style.setProperty("--p", scrollProgressOf(fig).toFixed(3));
        }
      };
      const onScroll = () => {
        if (!raf) raf = requestAnimationFrame(paint);
      };
      paint();
      window.addEventListener("scroll", onScroll, { passive: true });
      window.addEventListener("resize", onScroll, { passive: true });
      return () => {
        cancelAnimationFrame(raf);
        window.removeEventListener("scroll", onScroll);
        window.removeEventListener("resize", onScroll);
      };
    }

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (!e.isIntersecting) continue;
          e.target.classList.add("dg-drawn");
          io.unobserve(e.target);
        }
      },
      { rootMargin: "0px 0px -12% 0px" },
    );
    prepared.forEach((f) => io.observe(f));
    // a figure must never be left half-drawn because no observation was ever delivered
    const giveUp = setTimeout(() => prepared.forEach((f) => f.classList.add("dg-drawn")), 1500);
    return () => {
      io.disconnect();
      clearTimeout(giveUp);
    };
  }, [ref, driver]);
}

export function FiguresSkeleton() {
  return (
    <div className="sk-grid" style={{ gap: 28 }}>
      <Skeleton h={13} w="72%" />
      <Skeleton h={172} />
      <Skeleton h={172} />
    </div>
  );
}

/**
 * The diagrams. Hand-authored SVG arrives as one fragment; a project that would rather
 * draw a figure in React registers a component under that figure's id and it takes the
 * fragment figure's place. Registered ids the fragment does not have are appended.
 */
export function Figures({
  fragment,
  driver = "reveal",
  cap,
}: {
  fragment: string;
  /** "reveal" draws each figure once on the way in; "scroll" ties the draw to scroll. */
  driver?: Driver;
  /** A mode may cap the figure set. Extra figures are dropped, not hidden. */
  cap?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const all = useMemo(() => splitFragment(fragment), [fragment]);
  const pieces = useMemo(() => capFigures(all, cap), [all, cap]);
  useDrawOn(ref, driver);

  const present = new Set(pieces.map((p) => p.id));
  const extra = registeredFigureIds().filter((id) => !present.has(id));

  return (
    <div className="dg-wrap" ref={ref}>
      {pieces.map((piece) => {
        const Override = figureFor(piece.id);
        if (Override) return <Override key={piece.id} id={piece.id} />;
        return (
          <div
            key={piece.id}
            className="dg-slot"
            dangerouslySetInnerHTML={{ __html: piece.html }}
          />
        );
      })}
      {extra.map((id) => {
        const Extra = figureFor(id)!;
        return <Extra key={id} id={id} />;
      })}
    </div>
  );
}
