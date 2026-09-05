/**
 * Build-time data. The vite plugin in vite.config.ts reads content.json, turns.json,
 * metrics.json and the optional diagrams fragment out of CALLGEN_WORK and serves them
 * as `virtual:callgen-data`, so nothing here is fetched at runtime.
 */
import { CONTENT, TURNS, METRICS, DIAGRAMS } from "virtual:callgen-data";
import { deck } from "./lib/deck";
import type { Content, Deck, Metrics, Turn } from "./types";

export const DECK: Deck = deck(
  CONTENT as Content,
  TURNS as Turn[],
  METRICS as Metrics,
  DIAGRAMS,
);

export { deck };
export { CONTENT, TURNS, METRICS, DIAGRAMS };
