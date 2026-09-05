import { deck } from "../lib/deck";
import type { Content, Metrics, Turn } from "../types";

/** A three-turn call, small enough that every derived number can be checked by hand. */
export const CONTENT: Content = {
  meta: {
    title: "A short call",
    kind: "Call record",
    duration_s: 120,
    turns: 3,
    words: 40,
    participants: [
      { key: "A", name: "Ada Speaker" },
      { key: "B", name: "Bo Listener" },
    ],
  },
  abstract: "Two people, three turns.",
  acts: [
    {
      n: 1,
      title: "The only act",
      span: "00:00:00-00:02:00",
      start_s: 0,
      end_s: 120,
      summary: "It happened.",
    },
  ],
};

export const TURNS: Turn[] = [
  { i: 0, ts: "00:00:00", s: 0, spk: "A", w: 10, t: "we should look at deep seek before friday" },
  { i: 1, ts: "00:00:40", s: 40, spk: "B", w: 20, t: "deepseek is the one i meant" },
  { i: 2, ts: "00:01:20", s: 80, spk: "A", w: 10, t: "agreed, nothing else to add" },
];

export const METRICS: Metrics = {
  duration_s: 120,
  turns: 3,
  estimated_timing: false,
  speakers: {
    "Ada Speaker": { words: 20, turns: 2 },
    "Bo Listener": { words: 20, turns: 1 },
  },
  timeline: [
    { ts: "00:00:00", s: 0, spk: "Ada Speaker", words: 10 },
    { ts: "00:00:40", s: 40, spk: "Bo Listener", words: 20 },
    { ts: "00:01:20", s: 80, spk: "Ada Speaker", words: 10 },
  ],
};

export const DECK = deck(CONTENT, TURNS, METRICS, "");
