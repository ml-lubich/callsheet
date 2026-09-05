import { describe, expect, it } from "vitest";
import { matches, ranges, segments } from "../lib/search";

describe("spacing-tolerant search", () => {
  it("finds a spaced phrase from a spaceless query", () => {
    expect(matches("look at deep seek before friday", "deepseek")).toBe(true);
  });

  it("finds a spaceless word from a spaced query", () => {
    expect(matches("deepseek is the one", "deep seek")).toBe(true);
  });

  it("still refuses a word that is not there", () => {
    expect(matches("deepseek is the one", "shallow")).toBe(false);
  });

  it("treats an empty query as no filter at all", () => {
    expect(matches("anything", "   ")).toBe(true);
    expect(ranges("anything", "  ")).toEqual([]);
  });

  it("highlights the real text a spaceless query matched", () => {
    const parts = segments("look at deep seek now", "deepseek");
    expect(parts.filter((p) => p.hit).map((p) => p.text)).toEqual(["deep seek"]);
    expect(parts.map((p) => p.text).join("")).toBe("look at deep seek now");
  });

  it("highlights every occurrence", () => {
    const hits = segments("ada then ada again", "ada").filter((p) => p.hit);
    expect(hits).toHaveLength(2);
  });

  it("ignores case", () => {
    expect(matches("DeepSeek", "deepseek")).toBe(true);
  });
});
