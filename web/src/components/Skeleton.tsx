import { type ReactNode, useEffect, useState } from "react";
import { reduceMotion } from "../lib/jump";

/** A shimmering block standing in for a piece of content that has not arrived yet. */
export function Skeleton({
  w = "100%",
  h = 16,
  mt = 0,
}: {
  w?: string | number;
  h?: string | number;
  mt?: number;
}) {
  return (
    <span
      className="sk"
      aria-hidden="true"
      style={{ width: w, height: h, marginTop: mt || undefined }}
    />
  );
}

/** n stacked lines of body text, the last one short, the way a paragraph really ends. */
export function SkeletonLines({ n = 3, w = "100%" }: { n?: number; w?: string }) {
  return (
    <span className="sk-lines" style={{ maxWidth: w }} aria-hidden="true">
      {Array.from({ length: n }, (_, i) => (
        <Skeleton key={i} h={13} w={i === n - 1 ? "62%" : "100%"} />
      ))}
    </span>
  );
}

/**
 * The page composes itself top to bottom: each section shows its own skeleton until
 * its turn comes round, roughly 900ms for the whole run. Reduced motion skips it
 * entirely and renders the finished page on the first paint.
 */
export function Boot({
  order,
  skeleton,
  children,
}: {
  order: number;
  skeleton: ReactNode;
  children: ReactNode;
}) {
  const instant = reduceMotion();
  const [ready, setReady] = useState(instant);
  const delay = Math.min(900, 120 + order * 70);

  useEffect(() => {
    if (instant) return;
    const t = setTimeout(() => setReady(true), delay);
    return () => clearTimeout(t);
  }, [delay, instant]);

  if (!ready) return <div className="booting">{skeleton}</div>;
  return <div className={instant ? undefined : "booted"}>{children}</div>;
}
