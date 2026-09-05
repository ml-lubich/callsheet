import { useEffect, useState } from "react";

/**
 * True once the element has been seen, and true for good after that.
 *
 * The whole page hangs its entrance off this, so it fails open in every direction: no
 * IntersectionObserver means true immediately, and an observer that never delivers —
 * a print run, a screenshot renderer, an embedded webview that never paints a frame —
 * gives up after `GIVE_UP_MS` and shows the content anyway. Nothing on this page is
 * ever permanently invisible because an animation did not start.
 */
const GIVE_UP_MS = 1200;

export function useOnceInView<T extends Element>(
  ref: React.RefObject<T | null>,
  rootMargin = "0px 0px -10% 0px",
): boolean {
  const [seen, setSeen] = useState(() => typeof IntersectionObserver === "undefined");

  useEffect(() => {
    if (seen || !ref.current) return;
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) setSeen(true);
      },
      { rootMargin },
    );
    io.observe(ref.current);
    const giveUp = setTimeout(() => setSeen(true), GIVE_UP_MS);
    return () => {
      io.disconnect();
      clearTimeout(giveUp);
    };
  }, [ref, seen, rootMargin]);

  return seen;
}
