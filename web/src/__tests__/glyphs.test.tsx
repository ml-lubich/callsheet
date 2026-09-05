import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  BigNumber,
  Cascade,
  Compare,
  DocGlyph,
  FieldRow,
  GateChain,
  MagnitudeBar,
  PersonGlyph,
  Route,
  ScaleBar,
  type Pen,
} from "../glyphs";

const cases: [string, (pen: Pen) => React.ReactElement][] = [
  ["ScaleBar", (pen) => <ScaleBar value={0.6} label="score" pen={pen} />],
  ["FieldRow", (pen) => <FieldRow label="issuer" state="cited" pen={pen} />],
  ["DocGlyph", (pen) => <DocGlyph badge="OCR" label="statement" pen={pen} />],
  ["PersonGlyph", (pen) => <PersonGlyph label="analyst" pen={pen} />],
  ["GateChain", (pen) => <GateChain n={3} labels={["a", "b", "c"]} pen={pen} />],
  ["Cascade", (pen) => <Cascade steps={["one", "two"]} pen={pen} />],
  ["MagnitudeBar", (pen) => <MagnitudeBar label="rows" value={25} max={119000} pen={pen} />],
  ["BigNumber", (pen) => <BigNumber value={119000} unit="rows" caption="of them" pen={pen} />],
  ["Compare", (pen) => <Compare left="claim" right="evidence" out="verdict" pen={pen} />],
  ["Route", (pen) => <Route from="source" to={["one", "two"]} pen={pen} />],
];

describe("glyph library", () => {
  it.each(cases)("%s carries the pen it was given", (_name, make) => {
    for (const pen of ["a", "b", "neutral"] as Pen[]) {
      const { container, unmount } = render(make(pen));
      const root = container.firstElementChild!;
      expect(root).toHaveClass("gl");
      expect(root).toHaveClass(`pen-${pen}`);
      unmount();
    }
  });

  it("defaults to the neutral pen", () => {
    const { container } = render(<ScaleBar value={0.2} />);
    expect(container.firstElementChild).toHaveClass("pen-neutral");
  });

  it("marks an unbounded scale that ran off the end", () => {
    const { container } = render(<ScaleBar value={4} max={1} kind="unbounded" />);
    expect(container.textContent).toContain("≫");
  });

  it("draws a dashed track for a field that was never filled", () => {
    const { container } = render(<FieldRow label="issuer" state="empty" />);
    expect(container.querySelector("[stroke-dasharray]")).not.toBeNull();
  });
});
