/**
 * Scroll-stack card layout routing. Desktop gets a sticky 3D stack; phones,
 * tablets, coarse-pointer, reduced-motion and low-compute viewports get a
 * plain column with no runway and no scroll-driven transforms.
 *
 * Pure functions only — the component reads the signals from `window` and
 * `navigator`; tests feed them directly. Ported verbatim from the reference
 * implementation, thresholds included: they came from real device complaints.
 */

/** At or below this width, always use the column (phones, iPad, small laptop windows). */
export const SCROLL_STACK_COMPACT_MAX_WIDTH_PX = 1366;

/** Touch-primary devices a bit wider than the compact cap still get the column. */
export const SCROLL_STACK_TOUCH_SLATE_MAX_WIDTH_PX = 1920;

/** `hardwareConcurrency` at or below this (when reported) is treated as low compute. */
export const SCROLL_STACK_LOW_COMPUTE_CORE_MAX = 4;

export type ScrollStackViewportSignals = {
  innerWidth: number;
  pointerCoarse: boolean;
  hoverNone: boolean;
  maxTouchPoints: number;
  prefersReducedMotion: boolean;
  hardwareConcurrency: number | undefined;
};

/** True when the viewport should get the plain column instead of the sticky stack. */
export function shouldUseCompactScrollStackViewport(s: ScrollStackViewportSignals): boolean {
  const w = s.innerWidth;
  if (w <= SCROLL_STACK_COMPACT_MAX_WIDTH_PX) return true;
  if (s.prefersReducedMotion) return true;
  if (s.pointerCoarse) return true;
  if (s.maxTouchPoints > 0 && s.hoverNone) return true;
  if (s.maxTouchPoints > 0 && w <= SCROLL_STACK_TOUCH_SLATE_MAX_WIDTH_PX) return true;
  const cores = s.hardwareConcurrency;
  if (typeof cores === "number" && cores > 0 && cores <= SCROLL_STACK_LOW_COMPUTE_CORE_MAX) {
    return true;
  }
  return false;
}

export type ScrollStackRouteVariant = "grid" | "compact" | "stack";

export function resolveScrollStackVariant(
  layout: "stack" | "grid" | undefined,
  compactViewport: boolean,
): ScrollStackRouteVariant {
  if (layout === "grid") return "grid";
  if (compactViewport) return "compact";
  return "stack";
}
