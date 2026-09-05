import { describe, expect, it } from "vitest";
import { keyOf, median, mmss, nearestTurn, penClass, stats } from "../lib/derive";
import { tickFor } from "../sections/StripChart";
import { DECK, METRICS, TURNS } from "./fixture";

describe("strip chart derivations", () => {
  it("computes shares, longest turn and median from the timeline", () => {
    const s = stats(DECK, METRICS)!;
    expect(s.turns).toBe(3);
    expect(s.shares).toEqual([
      { key: "A", name: "Ada Speaker", percent: 50 },
      { key: "B", name: "Bo Listener", percent: 50 },
    ]);
    expect(s.longest.words).toBe(20);
    expect(s.longest.ts).toBe("00:00:40");
    expect(s.medianWords).toBe(10);
    expect(s.estimatedTiming).toBe(false);
  });

  it("has nothing to say about an empty timeline", () => {
    expect(stats(DECK, { ...METRICS, timeline: [] })).toBeNull();
  });

  it("maps a timeline display name back to its participant key", () => {
    expect(keyOf(DECK, "Bo Listener")).toBe("B");
    expect(keyOf(DECK, "Someone Else")).toBe("S");
  });

  it("assigns one pen per speaker and a neutral pen to the rest", () => {
    expect(penClass(DECK.keys, "A")).toBe("p0");
    expect(penClass(DECK.keys, "B")).toBe("p1");
    expect(penClass(DECK.keys, "C")).toBe("pn");
  });

  it("finds the last turn that had started by a given second", () => {
    expect(nearestTurn(TURNS, 0)).toBe(0);
    expect(nearestTurn(TURNS, 39)).toBe(0);
    expect(nearestTurn(TURNS, 41)).toBe(1);
    expect(nearestTurn(TURNS, 9999)).toBe(2);
  });

  it("rounds the ruler to whole minutes, never below one", () => {
    expect(tickFor(120)).toBe(60);
    expect(tickFor(3385)).toBe(240);
  });

  it("formats and averages", () => {
    expect(mmss(0)).toBe("0:00");
    expect(mmss(605)).toBe("10:05");
    expect(median([3, 1, 2])).toBe(2);
    expect(median([4, 1, 2, 3])).toBe(3);
    expect(median([])).toBe(0);
  });
});
