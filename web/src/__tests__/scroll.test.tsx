import { render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Pinned, Scrub } from "../components/Scroll";
import { Figures } from "../sections/Figures";

const FRAGMENT = `<figure class="dg" id="dg-one"><svg><path d="M0 0 L10 10"/><text>hi</text></svg></figure>`;

function reducedMotion(on: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: on && query.includes("prefers-reduced-motion"),
    media: query,
    onchange: null,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent: () => false,
  }));
}

afterEach(() => reducedMotion(false));

describe("Pinned", () => {
  it("gives its child a runway to stay still inside", () => {
    const { container } = render(
      <Pinned runwayVh={200} top={64}>
        <p>held</p>
      </Pinned>,
    );
    const runway = container.firstElementChild as HTMLElement;
    expect(runway.style.minHeight).toBe("200vh");
    const stuck = runway.firstElementChild as HTMLElement;
    expect(stuck.className).toBe("sticky");
    expect(stuck.style.top).toBe("64px");
  });
});

describe("Scrub", () => {
  it("starts its child at the beginning of the run", () => {
    const { container } = render(<Scrub>{(p) => <span>{p.toFixed(2)}</span>}</Scrub>);
    expect(container.textContent).toBe("0.00");
  });

  it("hands the finished state straight over under reduced motion", () => {
    reducedMotion(true);
    const { container } = render(<Scrub>{(p) => <span>{p.toFixed(2)}</span>}</Scrub>);
    expect(container.textContent).toBe("1.00");
  });
});

describe("the figure driver", () => {
  it("draws each figure once on the way in by default", () => {
    const { container } = render(<Figures fragment={FRAGMENT} />);
    const fig = container.querySelector("#dg-one")!;
    expect(fig.classList.contains("dg-draw")).toBe(true);
    expect(fig.classList.contains("dg-scrubbed")).toBe(false);
    // the stubbed observer reports "on screen" immediately
    expect(fig.classList.contains("dg-drawn")).toBe(true);
  });

  it('ties the draw to scroll position when asked for driver="scroll"', () => {
    const { container } = render(<Figures fragment={FRAGMENT} driver="scroll" />);
    const fig = container.querySelector<HTMLElement>("#dg-one")!;
    expect(fig.classList.contains("dg-scrubbed")).toBe(true);
    expect(fig.classList.contains("dg-drawn")).toBe(false);
    expect(fig.style.getPropertyValue("--p")).not.toBe("");
  });

  it("leaves the figures alone entirely under reduced motion", () => {
    reducedMotion(true);
    const { container } = render(<Figures fragment={FRAGMENT} />);
    expect(container.querySelector("#dg-one")!.className).toBe("dg");
  });
});
