import type { Content } from "../types";

/**
 * The output mode, as `src/callgen/modes.py` wrote it into content.json. A mode
 * decides three things and nothing else: which sections appear and in what order, how
 * the transcript is shown, and how many figures survive. It never decides what is true,
 * so nothing here edits a fact — it only drops and reorders whole sections.
 */

export type TranscriptMode = "open" | "collapsed" | "omit";

export interface ModeBlock {
  name?: string;
  sections?: string[];
  figures?: number;
  transcript?: TranscriptMode;
}

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

export interface Shape {
  sections: string[];
  transcript: TranscriptMode;
  /** undefined means no cap. */
  figures?: number;
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

  return {
    sections,
    transcript,
    figures: typeof block.figures === "number" && block.figures >= 0 ? block.figures : undefined,
  };
}
