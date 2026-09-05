/** The shape of the JSON the Python pipeline writes. Mirrors src/callgen/schema.py. */

export type Stamp = { ts: string; s: number };

export interface Participant {
  key: string;
  name: string;
  role?: string;
}

export interface Meta {
  title: string;
  subtitle?: string;
  kind?: string;
  date?: string;
  duration_label?: string;
  duration_s?: number;
  turns?: number;
  words?: number;
  extra?: [string, string | number][];
  participants: Participant[];
}

export interface Act extends Partial<Stamp> {
  n: number;
  title: string;
  span: string;
  start_s: number;
  end_s: number;
  summary: string;
  turning_point?: Stamp & { text: string };
}

export interface Thread {
  name: string;
  what: string;
  why_it_matters: string;
  marks?: Stamp[];
}

export type Strength = "strong" | "medium" | "weak";

export interface Content {
  meta: Meta;
  /** The output mode the build was shaped by. See lib/mode.ts. */
  _mode?: {
    name?: string;
    sections?: string[];
    figures?: number;
    transcript?: "open" | "collapsed" | "omit";
    collapsed?: string[];
  };
  /** `summarized` mode folds threads, signals and tensions into this one short list. */
  highlights?: string[];
  abstract?: string;
  /** Optional one-line finding, rendered above the abstract when the analysis supplies one. */
  /** The stance the analysis commits to, with the case each way and the one open question. */
  verdict?: {
    position: string;
    for: string[];
    against: string[];
    decides_it: string;
  };
  acts: Act[];
  threads?: Thread[];
  /** Optional "where it lands" rows: what changed, and for whom. */
  lands?: (Partial<Stamp> & { observation: string; transfers_to: string })[];
  evidence?: (Stamp & { claim: string; evidence: string; strength: Strength })[];
  signals?: (Stamp & { signal: string })[];
  numbers?: (Stamp & { value: string; means: string })[];
  quotes?: (Stamp & { speaker: string; text: string })[];
  tensions?: (Stamp & { note: string })[];
  diarization?: (Stamp & { why: string })[];
  next_steps?: (Stamp & { commitment: string })[];
  tech?: string[];
  fit?: {
    aligned_on?: string[];
    unresolved?: string[];
    risks?: { who: string; note: string }[];
  };
}

export interface Turn {
  i: number;
  ts: string;
  s: number;
  spk: string;
  name?: string;
  w: number;
  t: string;
}

export interface TimelinePoint {
  ts: string;
  s: number;
  spk: string;
  words: number;
}

export interface Metrics {
  duration_s: number;
  turns: number;
  estimated_timing?: boolean;
  speakers: Record<string, { words: number; turns: number }>;
  timeline: TimelinePoint[];
}

/** Everything the page needs, resolved once and passed down as props. */
export interface Deck {
  content: Content;
  turns: Turn[];
  metrics: Metrics;
  diagrams: string;
  /** participant keys, in the order the pens are assigned */
  keys: string[];
  /** participant key -> display name */
  names: Record<string, string>;
  duration: number;
}
