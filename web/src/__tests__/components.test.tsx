import { Lands } from "../sections/Lands";
import { Verdict } from "../sections/Verdict";
import { Abstract } from "../sections/Abstract";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { Collapsible } from "../components/Collapsible";
import { CountUp } from "../components/CountUp";
import { Plate } from "../sections/Plate";
import { THEME_KEY } from "../lib/theme";
import { DECK } from "./fixture";

describe("CountUp", () => {
  it("lands on the exact value", async () => {
    render(<CountUp value={119000} />);
    await waitFor(() => expect(screen.getByText("119,000")).toBeInTheDocument(), {
      timeout: 3000,
    });
  });

  it("counts up rather than starting at the answer", () => {
    render(<CountUp value={4242} />);
    expect(screen.queryByText("4,242")).not.toBeInTheDocument();
  });
});

describe("Collapsible", () => {
  beforeEach(() => {
    location.hash = "";
  });

  it("stays shut and hides its contents", () => {
    render(
      <Collapsible label="More">
        <p>inside</p>
      </Collapsible>,
    );
    expect(screen.queryByText("inside")).not.toBeInTheDocument();
  });

  it("opens on a deep link that matches its pattern", () => {
    location.hash = "#t-12";
    render(
      <Collapsible label="More" openOnHash={/^#t-\d+$/}>
        <p>inside</p>
      </Collapsible>,
    );
    expect(screen.getByText("inside")).toBeInTheDocument();
  });

  it("opens when the hash changes later", async () => {
    render(
      <Collapsible label="More" openOnHash={/^#t-\d+$/}>
        <p>inside</p>
      </Collapsible>,
    );
    expect(screen.queryByText("inside")).not.toBeInTheDocument();
    location.hash = "#t-3";
    window.dispatchEvent(new HashChangeEvent("hashchange"));
    await waitFor(() => expect(screen.getByText("inside")).toBeInTheDocument());
  });

  it("ignores a hash that is not its own", () => {
    location.hash = "#somewhere-else";
    render(
      <Collapsible label="More" openOnHash={/^#t-\d+$/}>
        <p>inside</p>
      </Collapsible>,
    );
    expect(screen.queryByText("inside")).not.toBeInTheDocument();
  });
});

describe("theme toggle", () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
  });

  it("flips the document and remembers the choice", async () => {
    const user = userEvent.setup();
    render(<Plate deck={DECK} />);
    await user.click(screen.getByRole("button", { name: /toggle light and dark/i }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(localStorage.getItem(THEME_KEY)).toBe("dark");
    await user.click(screen.getByRole("button", { name: /toggle light and dark/i }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
    expect(localStorage.getItem(THEME_KEY)).toBe("light");
  });
});

describe("Abstract", () => {
  it("renders each blank-line-separated paragraph as its own <p>", () => {
    const { container } = render(
      <Abstract text={"First paragraph.\n\nSecond paragraph.\n\nThird."} />,
    );
    const ps = container.querySelectorAll("p");
    expect(ps.length).toBe(3);
    expect(ps[1].textContent).toBe("Second paragraph.");
  });
  it("renders a single paragraph when there are no blank lines", () => {
    const { container } = render(<Abstract text={"One paragraph only."} />);
    expect(container.querySelectorAll("p").length).toBe(1);
  });
});

describe("Verdict", () => {
  const verdict = {
    position: "Hire on the delivery axis.",
    for: ["Release discipline shown on screen"],
    against: ["No dev, stage or prod"],
    decides_it: "Whether an hour a day is real.",
  };
  it("renders the position, both columns and what would settle it", () => {
    render(<Verdict verdict={verdict} />);
    expect(screen.getByText("Hire on the delivery axis.")).toBeTruthy();
    expect(screen.getByText("Release discipline shown on screen")).toBeTruthy();
    expect(screen.getByText("No dev, stage or prod")).toBeTruthy();
    expect(screen.getByText("Whether an hour a day is real.")).toBeTruthy();
  });
  it("colours the for column with pen b and against with pen a", () => {
    const { container } = render(<Verdict verdict={verdict} />);
    expect(container.querySelector(".verdict-for.pen-b")).toBeTruthy();
    expect(container.querySelector(".verdict-against.pen-a")).toBeTruthy();
  });
});

describe("Lands", () => {
  it("renders the observation and what it transfers to, with the timestamp", () => {
    const lands = [
      { observation: "He audits what his own agent produced.", transfers_to: "Any agent-assembled corpus.", ts: "00:23:27", s: 1407 },
    ];
    render(<Lands lands={lands} turns={[]} />);
    expect(screen.getByText("He audits what his own agent produced.")).toBeTruthy();
    expect(screen.getByText("Any agent-assembled corpus.")).toBeTruthy();
    expect(screen.getByText("00:23:27")).toBeTruthy();
  });
});
