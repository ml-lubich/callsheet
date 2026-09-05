/**
 * One place the whole page can say "show me turn 12". The transcript owns the how —
 * it may need to open itself and clear a filter first — so it registers the handler
 * and everything else just calls jump().
 */
type Handler = (index: number) => void;

let handler: Handler | null = null;

export function onJump(h: Handler): () => void {
  handler = h;
  return () => {
    if (handler === h) handler = null;
  };
}

export function jump(index: number): void {
  handler?.(index);
}

export function reduceMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}
