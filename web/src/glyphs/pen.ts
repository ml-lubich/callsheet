export type Pen = "a" | "b" | "neutral";

/**
 * Every glyph paints with currentColor; the pen only sets what currentColor is, so a
 * glyph dropped into a figure inherits the palette in both themes with no overrides.
 */
export function penClassName(pen: Pen = "neutral", extra?: string): string {
  return ["gl", `pen-${pen}`, extra].filter(Boolean).join(" ");
}
