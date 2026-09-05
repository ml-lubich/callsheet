import { describe, expect, it } from "vitest";
import { DEFAULT_SECTIONS, shapeOf } from "../lib/mode";
import { capFigures, splitFragment } from "../sections/Figures";

const FRAGMENT = `
<div class="dg-lead">lead</div>
<figure id="f1"></figure>
<p class="dg-bridge">bridge</p>
<figure id="f2"></figure>
<figure id="f3"></figure>
`;

describe("the shape a mode asks for", () => {
  it("draws everything, in the pipeline's order, when there is no mode block", () => {
    const shape = shapeOf({});
    expect(shape.sections).toEqual([...DEFAULT_SECTIONS]);
    expect(shape.transcript).toBe("collapsed");
    expect(shape.figures).toBeUndefined();
  });

  it("keeps the mode's own order rather than the default one", () => {
    const shape = shapeOf({
      _mode: { name: "formal", sections: ["strip", "abstract", "evidence", "figures"] },
    });
    expect(shape.sections).toEqual([
      "strip",
      "abstract",
      "evidence",
      "figures",
      "transcript",
    ]);
  });

  it("drops the sections the mode did not ask for", () => {
    const shape = shapeOf({ _mode: { sections: ["abstract", "numbers"], transcript: "omit" } });
    expect(shape.sections).toEqual(["abstract", "numbers"]);
    expect(shape.sections).not.toContain("acts");
  });

  it("omits the transcript entirely when the mode says so", () => {
    expect(shapeOf({ _mode: { transcript: "omit" } }).sections).not.toContain("transcript");
  });

  it("appends the transcript once, wherever the mode listed it", () => {
    const shape = shapeOf({ _mode: { sections: ["transcript", "abstract"], transcript: "open" } });
    expect(shape.sections).toEqual(["abstract", "transcript"]);
    expect(shape.transcript).toBe("open");
  });

  it("carries the figure cap through, and only when it is a number", () => {
    expect(shapeOf({ _mode: { figures: 1 } }).figures).toBe(1);
    expect(shapeOf({ _mode: { figures: 0 } }).figures).toBe(0);
    expect(shapeOf({ _mode: {} }).figures).toBeUndefined();
  });

  it("ignores a section id this page has never heard of", () => {
    const shape = shapeOf({ _mode: { sections: ["abstract", "hologram"] } });
    expect(shape.sections).toEqual(["abstract", "transcript"]);
  });

  it("falls back to the full page rather than rendering nothing", () => {
    expect(shapeOf({ _mode: { sections: [] } }).sections).toEqual([...DEFAULT_SECTIONS]);
  });
});

describe("the mode's figure cap", () => {
  it("keeps the first n figures and drops the rest", () => {
    const kept = capFigures(splitFragment(FRAGMENT), 2).map((p) => p.id);
    expect(kept).toEqual(["piece-0", "f1", "piece-2", "f2"]);
  });

  it("counts figures only — the lead-in and the bridges are not capped away", () => {
    const kept = capFigures(splitFragment(FRAGMENT), 0);
    expect(kept.map((p) => p.id)).toEqual(["piece-0", "piece-2"]);
  });

  it("leaves the fragment alone when there is no cap", () => {
    expect(capFigures(splitFragment(FRAGMENT)).length).toBe(5);
  });
});

describe("collapsed sections", () => {
  it("reads _mode.collapsed and keeps only known section ids", async () => {
    const { shapeOf } = await import("../lib/mode");
    const shape = shapeOf({ _mode: { collapsed: ["evidence", "signals", "not-a-section"] } } as never);
    expect(shape.collapsed).toEqual(["evidence", "signals"]);
  });
  it("collapses nothing when the mode says nothing", async () => {
    const { shapeOf } = await import("../lib/mode");
    expect(shapeOf({} as never).collapsed).toEqual([]);
  });
});
