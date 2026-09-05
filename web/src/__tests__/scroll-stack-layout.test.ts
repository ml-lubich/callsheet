/**
 * Scroll-stack routing: wide desktop keeps the sticky stack; phones, tablets
 * and constrained devices get the plain column. Behaviour spec, not
 * implementation detail — ported verbatim from the reference implementation,
 * with only the test-runner import changed.
 */
import { describe, expect, it } from "vitest";
import {
  SCROLL_STACK_COMPACT_MAX_WIDTH_PX,
  SCROLL_STACK_LOW_COMPUTE_CORE_MAX,
  SCROLL_STACK_TOUCH_SLATE_MAX_WIDTH_PX,
  resolveScrollStackVariant,
  shouldUseCompactScrollStackViewport,
  type ScrollStackViewportSignals,
} from "../lib/scroll-stack-layout";

function sig(
  partial: Partial<ScrollStackViewportSignals> &
    Pick<ScrollStackViewportSignals, "innerWidth">,
): ScrollStackViewportSignals {
  return {
    pointerCoarse: false,
    hoverNone: false,
    maxTouchPoints: 0,
    prefersReducedMotion: false,
    hardwareConcurrency: 8,
    ...partial,
  };
}

describe("shouldUseCompactScrollStackViewport", () => {
  it("uses the column at iPad-class widths without relying on pointer heuristics", () => {
    expect(
      shouldUseCompactScrollStackViewport(sig({ innerWidth: SCROLL_STACK_COMPACT_MAX_WIDTH_PX })),
    ).toBe(true);
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: SCROLL_STACK_COMPACT_MAX_WIDTH_PX - 1 }),
      ),
    ).toBe(true);
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: SCROLL_STACK_COMPACT_MAX_WIDTH_PX + 1 }),
      ),
    ).toBe(false);
  });

  it("keeps the sticky stack on large desktop viewports without touch", () => {
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: SCROLL_STACK_TOUCH_SLATE_MAX_WIDTH_PX + 120, maxTouchPoints: 0 }),
      ),
    ).toBe(false);
  });

  it("prefers the column when the user asks for reduced motion", () => {
    expect(
      shouldUseCompactScrollStackViewport(sig({ innerWidth: 2000, prefersReducedMotion: true })),
    ).toBe(true);
  });

  it("prefers the column with a coarse primary pointer even when very wide", () => {
    expect(shouldUseCompactScrollStackViewport(sig({ innerWidth: 2000, pointerCoarse: true }))).toBe(
      true,
    );
  });

  it("treats touch + no-hover viewports as tablet-like", () => {
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: 2000, maxTouchPoints: 5, hoverNone: true }),
      ),
    ).toBe(true);
  });

  it("uses the column for touch slates up to the touch-slate width cap", () => {
    expect(
      shouldUseCompactScrollStackViewport(
        sig({
          innerWidth: SCROLL_STACK_TOUCH_SLATE_MAX_WIDTH_PX,
          maxTouchPoints: 5,
          hoverNone: false,
        }),
      ),
    ).toBe(true);
  });

  it("uses the column on very low core counts when reported", () => {
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: 2000, hardwareConcurrency: SCROLL_STACK_LOW_COMPUTE_CORE_MAX }),
      ),
    ).toBe(true);
    expect(
      shouldUseCompactScrollStackViewport(
        sig({ innerWidth: 2000, hardwareConcurrency: SCROLL_STACK_LOW_COMPUTE_CORE_MAX + 1 }),
      ),
    ).toBe(false);
  });
});

describe("resolveScrollStackVariant", () => {
  it("never stacks when layout is grid", () => {
    expect(resolveScrollStackVariant("grid", false)).toBe("grid");
    expect(resolveScrollStackVariant("grid", true)).toBe("grid");
  });

  it("uses the compact column when the viewport is compact", () => {
    expect(resolveScrollStackVariant(undefined, true)).toBe("compact");
    expect(resolveScrollStackVariant("stack", true)).toBe("compact");
  });

  it("uses the sticky stack only on wide non-compact viewports", () => {
    expect(resolveScrollStackVariant(undefined, false)).toBe("stack");
    expect(resolveScrollStackVariant("stack", false)).toBe("stack");
  });
});
