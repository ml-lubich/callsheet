import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { Figures, splitFragment } from "../sections/Figures";
import { clearFigures, registerFigure } from "../figures";

const FRAGMENT = `
<div class="dg-lead">Two figures, in order.</div>
<figure class="dg" id="dg-first"><figcaption>hand-drawn first</figcaption></figure>
<figure class="dg" id="dg-second"><figcaption>hand-drawn second</figcaption></figure>
`;

afterEach(clearFigures);

describe("figures", () => {
  it("splits the fragment into its top-level nodes, keyed by figure id", () => {
    expect(splitFragment(FRAGMENT).map((p) => p.id)).toEqual([
      "piece-0",
      "dg-first",
      "dg-second",
    ]);
  });

  it("renders the hand-authored fragment as it stands", () => {
    render(<Figures fragment={FRAGMENT} />);
    expect(screen.getByText("hand-drawn first")).toBeInTheDocument();
    expect(screen.getByText("hand-drawn second")).toBeInTheDocument();
  });

  it("lets a registered component take a fragment figure's place", () => {
    registerFigure("dg-second", ({ id }) => <figure id={id}>drawn in react</figure>);
    render(<Figures fragment={FRAGMENT} />);
    expect(screen.getByText("drawn in react")).toBeInTheDocument();
    expect(screen.queryByText("hand-drawn second")).not.toBeInTheDocument();
    expect(screen.getByText("hand-drawn first")).toBeInTheDocument();
  });

  it("appends a registered figure the fragment does not have", () => {
    registerFigure("dg-extra", () => <figure>an extra figure</figure>);
    render(<Figures fragment={FRAGMENT} />);
    expect(screen.getByText("an extra figure")).toBeInTheDocument();
    expect(screen.getByText("hand-drawn second")).toBeInTheDocument();
  });
});
