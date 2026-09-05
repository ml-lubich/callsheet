import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useRef } from "react";
import { useOnceInView } from "../lib/inview";

type Cb = (entries: { isIntersecting: boolean }[]) => void;

function Probe() {
  const ref = useRef<HTMLDivElement>(null);
  const seen = useOnceInView(ref);
  return <div ref={ref} data-seen={seen ? "yes" : "no"} />;
}

/** An observer the test drives by hand: `report` is what the browser would call. */
function fakeObserver() {
  const state: { report: Cb | null } = { report: null };
  class IO {
    constructor(cb: Cb) {
      state.report = cb;
    }
    observe() {}
    disconnect() {}
  }
  vi.stubGlobal("IntersectionObserver", IO);
  return state;
}

describe("useOnceInView", () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("waits for the reader when the observer says the element is not yet visible", () => {
    const io = fakeObserver();
    const { container } = render(<Probe />);
    act(() => io.report!([{ isIntersecting: false }]));
    act(() => vi.advanceTimersByTime(5000));
    expect(container.firstElementChild!.getAttribute("data-seen")).toBe("no");
    act(() => io.report!([{ isIntersecting: true }]));
    expect(container.firstElementChild!.getAttribute("data-seen")).toBe("yes");
  });

  it("gives up and shows the element when the observer never reports", () => {
    fakeObserver();
    const { container } = render(<Probe />);
    expect(container.firstElementChild!.getAttribute("data-seen")).toBe("no");
    act(() => vi.advanceTimersByTime(1300));
    expect(container.firstElementChild!.getAttribute("data-seen")).toBe("yes");
  });
});
