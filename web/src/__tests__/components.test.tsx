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
