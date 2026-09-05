import { useEffect, useRef, useState } from "react";
import { useOnceInView } from "../lib/inview";
import { reduceMotion } from "../lib/jump";

/**
 * A number that arrives rather than appears — 600ms, ease-out, the first time it is
 * scrolled into view, and always landing on the exact value it was given.
 */
export function CountUp({
  value,
  duration = 600,
  format = (n: number) => n.toLocaleString("en-US"),
  className,
}: {
  value: number;
  duration?: number;
  format?: (n: number) => string;
  className?: string;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const seen = useOnceInView(ref);
  const instant = reduceMotion();
  const [shown, setShown] = useState(instant ? value : 0);

  useEffect(() => {
    if (instant) {
      setShown(value);
      return;
    }
    if (!seen) return;
    let raf = 0;
    let t0 = 0;
    // the clock starts on the first frame and is read from the same source thereafter:
    // hosts that measure performance.now() and the frame timestamp from different
    // origins would otherwise finish the whole count in one frame
    const step = (now: number) => {
      if (!t0) t0 = now;
      const p = Math.min(1, (now - t0) / duration);
      // exact on the last frame, never a rounding artefact of the easing
      setShown(p >= 1 ? value : Math.round(value * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    // a host that never delivers a second frame still gets the right number
    const giveUp = setTimeout(() => setShown(value), duration + 300);
    return () => {
      cancelAnimationFrame(raf);
      clearTimeout(giveUp);
    };
  }, [seen, value, duration, instant]);

  return (
    <span ref={ref} className={className} style={{ fontVariantNumeric: "tabular-nums" }}>
      {format(shown)}
    </span>
  );
}
