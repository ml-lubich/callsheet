import { useScroll, useTransform, type MotionValue } from "motion/react";
import { type ReactNode, useEffect, useRef, useState } from "react";
import { reduceMotion } from "../lib/jump";

/**
 * The three scroll primitives the page is built on. Everything scroll-driven goes
 * through one of them, so there is one place that knows how progress is measured and
 * one place that knows to sit still under reduced motion.
 */

/** 0 as the element's top reaches the bottom of the viewport, 1 as its bottom leaves the top. */
export function useScrollProgress(ref: React.RefObject<HTMLElement | null>): MotionValue<number> {
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  return scrollYProgress;
}

/** The same progress as a plain number, for callers that render rather than animate. */
export function useScrollValue(ref: React.RefObject<HTMLElement | null>): number {
  const progress = useScrollProgress(ref);
  const [value, setValue] = useState(0);
  useEffect(() => progress.on("change", setValue), [progress]);
  return value;
}

/**
 * A runway with a child pinned inside it. The child stays put while `runwayVh` of page
 * scrolls past, which is how a figure gets to hold still and be read.
 */
export function Pinned({
  runwayVh = 140,
  top = 88,
  className,
  children,
}: {
  runwayVh?: number;
  top?: number;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={className} style={{ minHeight: `${runwayVh}vh` }}>
      <div className="sticky" style={{ top }}>
        {children}
      </div>
    </div>
  );
}

/**
 * Hands its child the 0..1 progress of its own box across the viewport. Under reduced
 * motion the child is handed 1 once and never moves — the finished state, immediately.
 */
export function Scrub({
  from = 0,
  to = 1,
  className,
  children,
}: {
  /** Progress at which the mapped value should read 0. */
  from?: number;
  /** Progress at which it should read 1. */
  to?: number;
  className?: string;
  children: (progress: number) => ReactNode;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const still = reduceMotion();
  const raw = useScrollProgress(ref);
  const mapped = useTransform(raw, [from, to], [0, 1], { clamp: true });
  const [value, setValue] = useState(still ? 1 : 0);

  useEffect(() => {
    if (still) return;
    setValue(mapped.get());
    return mapped.on("change", setValue);
  }, [mapped, still]);

  return (
    <div ref={ref} className={className}>
      {children(still ? 1 : value)}
    </div>
  );
}
