import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { Sec } from "../sections/Sec";
import { SpeakerChip, initials } from "../components/SpeakerKey";
import { shapeOf } from "../lib/mode";
import { THEME_KEY, useTheme } from "../lib/theme";
import { Plate } from "../sections/Plate";
import { DECK } from "./fixture";

/* restored by hand rather than with unstubAllGlobals, which would also take away the
   IntersectionObserver and storage the shared setup put there */
const realMatchMedia = window.matchMedia;

/** jsdom answers every media query with "no"; this one answers reduce with "yes". */
function preferReducedMotion() {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query.includes("prefers-reduced-motion"),
    media: query,
    onchange: null,
    addListener() {},
    removeListener() {},
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent: () => false,
  }));
}

describe("Sec", () => {
  afterEach(() => vi.stubGlobal("matchMedia", realMatchMedia));

  it("reveals its content on the way in", () => {
    const { container } = render(
      <Sec order={1} title="Threads" skeleton={null}>
        <p>the body</p>
      </Sec>,
    );
    const body = container.querySelector(".sec-body");
    expect(body).not.toBeNull();
    expect(body!.classList.contains("rv")).toBe(true);
  });

  it("puts a titled section's heading in its own rail", () => {
    const { container } = render(
      <Sec order={1} title="Threads" skeleton={null}>
        <p>the body</p>
      </Sec>,
    );
    expect(container.querySelector(".wrap.spread")).not.toBeNull();
    expect(container.querySelector(".sec-rail .sec")?.textContent).toBe("Threads");
  });

  it("hands a reduced-motion reader plain markup with no entrance to wait on", () => {
    preferReducedMotion();
    const { container } = render(
      <Sec order={1} title="Threads" skeleton={null}>
        <p>the body</p>
      </Sec>,
    );
    const body = container.querySelector(".sec-body");
    expect(body).not.toBeNull();
    expect(body!.classList.contains("rv")).toBe(false);
    expect(screen.getByText("the body")).toBeInTheDocument();
  });
});

describe("SpeakerChip", () => {
  it("gives each speaker their initials in their own pen", () => {
    const { container } = render(
      <>
        <SpeakerChip keys={["A", "B"]} spk="A" name="Ada Speaker" />
        <SpeakerChip keys={["A", "B"]} spk="B" name="Bo Listener" />
        <SpeakerChip keys={["A", "B"]} spk="C" name="Cy Guest" />
      </>,
    );
    const chips = [...container.querySelectorAll(".chip")];
    expect(chips.map((c) => c.querySelector(".chip-i")?.textContent)).toEqual([
      "AS",
      "BL",
      "CG",
    ]);
    expect(chips.map((c) => c.className)).toEqual(["chip p0", "chip p1", "chip pn"]);
    expect(chips[0].querySelector(".chip-n")?.textContent).toBe("Ada Speaker");
  });
});

/** The toggle the plate would render, so a pinned build's no-op can still be clicked. */
function ThemeProbe() {
  const { theme, toggle } = useTheme();
  return (
    <button type="button" onClick={toggle}>
      {theme}
    </button>
  );
}

describe("a build pinned to one theme", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.removeAttribute("data-theme-pin");
  });

  it("takes the pinned theme and offers nothing to toggle", () => {
    document.documentElement.setAttribute("data-theme-pin", "dark");
    render(<Plate deck={DECK} />);
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(
      screen.queryByRole("button", { name: /toggle light and dark/i }),
    ).not.toBeInTheDocument();
  });

  it("keeps the toggle when the build left the theme on auto", () => {
    render(<Plate deck={DECK} />);
    expect(screen.getByRole("button", { name: /toggle light and dark/i })).toBeInTheDocument();
  });
});

describe("the wordmark", () => {
  it("names the product once, beside the kind of record", () => {
    const { container } = render(<Plate deck={DECK} />);
    expect(container.querySelector(".masthead .brand")?.textContent).toBe("Callgen");
    expect(container.querySelector(".masthead .rule-word")?.textContent).toBe("Call record");
  });
});

describe("a pinned theme cannot be toggled away", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.removeAttribute("data-theme-pin");
  });

  it("ignores the toggle and remembers nothing", async () => {
    document.documentElement.setAttribute("data-theme-pin", "dark");
    const user = userEvent.setup();
    render(<ThemeProbe />);
    await user.click(screen.getByRole("button"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(screen.getByRole("button").textContent).toBe("dark");
    expect(localStorage.getItem(THEME_KEY)).toBeNull();
  });

  it("still flips an auto build", async () => {
    const user = userEvent.setup();
    render(<ThemeProbe />);
    await user.click(screen.getByRole("button"));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(localStorage.getItem(THEME_KEY)).toBe("dark");
  });
});

describe("initials", () => {
  it("takes the first letter of each of the first two words", () => {
    expect(initials("Ada Speaker")).toBe("AS");
    expect(initials("Ana Maria Silva")).toBe("AM");
  });

  it("gives one letter for a one-word name", () => {
    expect(initials("Ada")).toBe("A");
  });

  it("falls back to a placeholder rather than throwing on nothing at all", () => {
    expect(initials("")).toBe("?");
    expect(initials("   ")).toBe("?");
    expect(initials(undefined as unknown as string)).toBe("?");
  });
});

describe("the mode the build was rendered for", () => {
  afterEach(() => document.documentElement.removeAttribute("data-mode"));

  it("reads the name the build stamped on the document", () => {
    document.documentElement.setAttribute("data-mode", "summarized");
    expect(shapeOf({}).name).toBe("summarized");
  });

  it("lets the content's own mode block win over the build's label", () => {
    document.documentElement.setAttribute("data-mode", "summarized");
    expect(shapeOf({ _mode: { name: "forensic" } }).name).toBe("forensic");
  });

  it("falls back to professional when neither says", () => {
    expect(shapeOf({}).name).toBe("professional");
  });
});
