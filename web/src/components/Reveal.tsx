import { createElement, type ReactNode, useRef } from "react";
import { useOnceInView } from "../lib/inview";
import { reduceMotion } from "../lib/jump";

/**
 * The one in-section stagger, in seconds. Every list on the page steps its rows by
 * this, so the whole document has a single rhythm rather than one per section.
 */
export const STAGGER = 0.04;

/**
 * Opacity and eight pixels of rise, once, on the way in. Nothing bounces and nothing
 * moves once it has landed. Under reduced motion the element is simply there.
 *
 * Deliberately a CSS animation triggered by a class rather than a JavaScript one: an
 * animation that gates visibility must not depend on frames being delivered. Between
 * that and `useOnceInView`'s give-up timer, no element on this page can be left at
 * opacity 0 by an entrance that never started.
 */
export function Reveal({
  children,
  delay = 0,
  as = "div",
  className,
}: {
  children: ReactNode;
  delay?: number;
  as?: "div" | "section" | "li" | "article" | "tr" | "p";
  className?: string;
}) {
  const ref = useRef<HTMLElement>(null);
  const seen = useOnceInView(ref);

  if (reduceMotion()) {
    return createElement(as, { className }, children);
  }

  return createElement(
    as,
    {
      ref,
      className: [className, "rv", seen && "rv-in"].filter(Boolean).join(" "),
      style: delay ? ({ "--rv-wait": `${delay.toFixed(3)}s` } as React.CSSProperties) : undefined,
    },
    children,
  );
}
