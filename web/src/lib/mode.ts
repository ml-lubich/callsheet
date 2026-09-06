import type { Content, ModeBlock } from "../types";

/**
 * The output mode, as `src/callgen/modes.py` wrote it into content.json. A mode
 * decides three things and nothing else: which sections appear and in what order, how
 * the transcript is shown, and how many figures survive. It never decides what is true,
 * so nothing here edits a fact — it only drops and reorders whole sections.
 */

export type TranscriptMode = "open" | "collapsed" | "omit";

export type { ModeBlock };

/** Every section the page can draw, in the order it draws them when no mode says otherwise. */
export const DEFAULT_SECTIONS = [
  "strip",
  "abstract",
  "highlights",
  "figures",
  "acts",
  "threads",
  "evidence",
  "signals",
  "numbers",
  "tech",
  "friction",
  "quotes",
  "fit",
  "next",
  "transcript",
] as const;

/**
 * The mode this build was rendered for, as the CLI passed it through the environment and
 * index.html stamped on <html>. It is a label: the shape itself comes from content.json's
 * _mode block, which knows the sections, and that block wins wherever both have a name.
 */
export function buildMode(): string | null {
  if (typeof document === "undefined") return null;
  return document.documentElement.getAttribute("data-mode") || null;
}

export interface Shape {
  name: string;
  sections: string[];
  transcript: TranscriptMode;
  /** undefined means no cap. */
  figures?: number;
  /** Section ids the page renders collapsed by default. */
  collapsed: string[];
}

/**
 * The shape the page should take. Unknown section ids are dropped rather than trusted,
 * so a mode from a newer pipeline cannot make this page render an empty heading.
 */
export function shapeOf(content: Pick<Content, "_mode">): Shape {
  const block = content._mode ?? {};
  const known = new Set<string>(DEFAULT_SECTIONS);
  const asked = Array.isArray(block.sections) ? block.sections.filter((s) => known.has(s)) : null;
  const transcript: TranscriptMode =
    block.transcript === "open" || block.transcript === "omit" ? block.transcript : "collapsed";

  const sections = (asked?.length ? asked : [...DEFAULT_SECTIONS]).filter(
    (s) => s !== "transcript",
  );
  if (transcript !== "omit") sections.push("transcript");

  const collapsed = Array.isArray(block.collapsed)
    ? block.collapsed.filter((s) => known.has(s))
    : [];

  return {
    name: block.name || buildMode() || "professional",
    sections,
    transcript,
    collapsed,
    figures: typeof block.figures === "number" && block.figures >= 0 ? block.figures : undefined,
  };
}
