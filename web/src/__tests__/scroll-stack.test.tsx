/**
 * The ScrollStack contract, ported from the reference implementation: a phone gets the
 * caller's own column and nothing sticky, a wide desktop gets the sticky stack, and
 * reduced motion overrides the width.
 */
import { render, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ScrollStack } from "../components/ScrollStack";

const items = [
  { key: "a", node: <article>Card A</article> },
  { key: "b", node: <article>Card B</article> },
  { key: "c", node: <article>Card C</article> },
];

function setViewport(opts: {
  innerWidth: number;
  maxTouchPoints?: number;
  hardwareConcurrency?: number;
  coarse?: boolean;
  hoverNone?: boolean;
  reducedMotion?: boolean;
}) {
  Object.defineProperty(window, "innerWidth", { configurable: true, value: opts.innerWidth });
  Object.defineProperty(navigator, "maxTouchPoints", {
    configurable: true,
    value: opts.maxTouchPoints ?? 0,
  });
  Object.defineProperty(navigator, "hardwareConcurrency", {
    configurable: true,
    value: opts.hardwareConcurrency ?? 8,
  });
  window.matchMedia = ((query: string) =>
    ({
      matches:
        (query.includes("pointer: coarse") && !!opts.coarse) ||
        (query.includes("hover: none") && !!opts.hoverNone) ||
        (query.includes("prefers-reduced-motion") && !!opts.reducedMotion),
      media: query,
      addEventListener() {},
      removeEventListener() {},
      addListener() {},
      removeListener() {},
      onchange: null,
      dispatchEvent: () => false,
    }) as MediaQueryList) as typeof window.matchMedia;
}

afterEach(() => setViewport({ innerWidth: 1024 }));

describe("ScrollStack", () => {
  it("renders every card in the compact column on a phone-class viewport", async () => {
    setViewport({ innerWidth: 390, maxTouchPoints: 5, coarse: true, hoverNone: true });
    const { container, getByText } = render(<ScrollStack items={items} />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("compact"),
    );
    expect(getByText("Card A")).toBeInTheDocument();
    expect(getByText("Card C")).toBeInTheDocument();
    expect(container.querySelector(".sticky")).toBeNull();
  });

  it("uses the sticky stack on a wide mouse-driven desktop", async () => {
    setViewport({ innerWidth: 1600 });
    const { container } = render(<ScrollStack items={items} />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("stack"),
    );
    const cards = container.querySelectorAll("[data-scroll-stack-card]");
    expect(cards.length).toBe(3);
    for (const card of Array.from(cards)) {
      expect(card.className).toMatch(/\bsticky\b/);
    }
  });

  it("falls back to the column when the user prefers reduced motion, even on desktop", async () => {
    setViewport({ innerWidth: 1600, reducedMotion: true });
    const { container } = render(<ScrollStack items={items} />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("compact"),
    );
    expect(container.querySelector(".sticky")).toBeNull();
  });

  it("passes the compact classes through so the column matches the old layout exactly", async () => {
    setViewport({ innerWidth: 390, maxTouchPoints: 5, coarse: true, hoverNone: true });
    const { container } = render(<ScrollStack items={items} compactClassName="actlist" />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("compact"),
    );
    expect(container.firstElementChild?.className).toBe("actlist");
  });

  it("pins each card one stack offset lower than the one before it", async () => {
    setViewport({ innerWidth: 1600 });
    const { container } = render(<ScrollStack items={items} stickyTop={112} stackOffset={18} />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("stack"),
    );
    const tops = [...container.querySelectorAll<HTMLElement>("[data-scroll-stack-card]")].map(
      (el) => el.style.top,
    );
    expect(tops).toEqual(["112px", "130px", "148px"]);
  });

  it("gives every card a scroll runway of its own", async () => {
    setViewport({ innerWidth: 1600 });
    const { container } = render(<ScrollStack items={items} scrollPerCard={62} />);
    await waitFor(() =>
      expect(container.firstElementChild?.getAttribute("data-variant")).toBe("stack"),
    );
    for (const el of container.querySelectorAll<HTMLElement>("[data-scroll-stack-card]")) {
      expect(el.style.minHeight).toBe("62vh");
    }
  });
});
