import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { SpeakerKey } from "../components/SpeakerKey";
import { deck } from "../lib/deck";
import { Reader, chapters } from "../sections/Transcript";
import type { Act, Content } from "../types";
import { CONTENT, METRICS, TURNS } from "./fixture";

const ACTS: Act[] = [
  { n: 1, title: "The opening", span: "0:00-0:40", start_s: 0, end_s: 40, summary: "one" },
  { n: 2, title: "The turn", span: "0:40-2:00", start_s: 40, end_s: 120, summary: "two" },
];

const WITH_ACTS: Content = {
  ...CONTENT,
  acts: ACTS,
  meta: {
    ...CONTENT.meta,
    participants: [
      { key: "A", name: "Ada Speaker", role: "Analyst" },
      { key: "B", name: "Bo Listener", role: "Reviewer" },
    ],
  },
};

const DECK = deck(WITH_ACTS, TURNS, METRICS, "");

describe("cutting the turns into chapters", () => {
  it("gives each act the turns spoken after it started", () => {
    const cut = chapters(ACTS, TURNS);
    expect(cut.map((c) => [c.n, c.turns.map((t) => t.i)])).toEqual([
      [1, [0]],
      [2, [1, 2]],
    ]);
  });

  it("puts a turn spoken before the first act into it rather than stranding it", () => {
    const late = [{ ...ACTS[0], start_s: 30 }];
    expect(chapters(late, TURNS)[0].turns.map((t) => t.i)).toEqual([0, 1, 2]);
  });

  it("drops an act nobody spoke during", () => {
    const empty: Act = { ...ACTS[1], n: 3, start_s: 900, end_s: 1000, title: "Silence" };
    expect(chapters([...ACTS, empty], TURNS).map((c) => c.n)).toEqual([1, 2]);
  });

  it("reads a call with no acts as one chapter", () => {
    expect(chapters([], TURNS)).toEqual([
      { n: 0, title: "The call", start_s: 0, turns: TURNS },
    ]);
  });
});

describe("the reader", () => {
  beforeEach(() => {
    location.hash = "";
  });

  it("puts a chapter rail beside the turns, one entry per act", () => {
    render(<Reader deck={DECK} />);
    const rail = screen.getByRole("navigation", { name: "Chapters" });
    expect(rail.textContent).toContain("The opening");
    expect(rail.textContent).toContain("The turn");
  });

  it("keeps every chapter shut until it is asked for", () => {
    render(<Reader deck={DECK} />);
    for (const b of screen.getAllByRole("button", { expanded: false })) {
      expect(b).toHaveAttribute("aria-expanded", "false");
    }
    expect(screen.queryByText(/nothing else to add/)).not.toBeInTheDocument();
  });

  it("opens one chapter without opening the others", async () => {
    const user = userEvent.setup();
    render(<Reader deck={DECK} />);
    await user.click(screen.getByRole("button", { name: /2\. The turn/ }));
    expect(screen.getByText(/nothing else to add/)).toBeInTheDocument();
    expect(screen.queryByText(/before friday/)).not.toBeInTheDocument();
  });

  it("opens every chapter that has a hit while a search is running", async () => {
    const user = userEvent.setup();
    render(<Reader deck={DECK} />);
    await user.type(screen.getByLabelText(/search the transcript/i), "deepseek");
    expect(screen.getByText("2 of 3 turns shown")).toBeInTheDocument();
    expect(screen.getByText("deep seek").tagName).toBe("MARK");
    expect(screen.getByText("deepseek").tagName).toBe("MARK");
  });

  it("marks each hit on the scrubber so they can be found without scrolling", async () => {
    const user = userEvent.setup();
    const { container } = render(<Reader deck={DECK} />);
    expect(container.querySelectorAll(".scrub-hit")).toHaveLength(0);
    await user.type(screen.getByLabelText(/search the transcript/i), "deepseek");
    expect(container.querySelectorAll(".scrub-hit")).toHaveLength(2);
  });

  it("filters by speaker", async () => {
    const user = userEvent.setup();
    render(<Reader deck={DECK} />);
    await user.click(screen.getByRole("button", { name: "Bo Listener" }));
    expect(screen.getByText("1 of 3 turns shown")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getByText("3 of 3 turns shown")).toBeInTheDocument();
  });

  it("opens the right chapter and clears the filter for a deep link", async () => {
    location.hash = "#t-2";
    render(<Reader deck={DECK} />);
    await waitFor(() => expect(document.getElementById("t-2")).not.toBeNull());
    expect(screen.getByText("3 of 3 turns shown")).toBeInTheDocument();
    // the deep link opened chapter 2 only
    expect(screen.queryByText(/before friday/)).not.toBeInTheDocument();
  });
});

describe("the speaker key", () => {
  it("names each speaker, their role and their share of the words", () => {
    render(<SpeakerKey deck={DECK} />);
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toBe("Ada SpeakerAnalyst50%");
    expect(rows[1].textContent).toBe("Bo ListenerReviewer50%");
  });

  it("gives each speaker the pen they are drawn with everywhere else", () => {
    const { container } = render(<SpeakerKey deck={DECK} />);
    const swatches = [...container.querySelectorAll<HTMLElement>(".swatch")];
    expect(swatches.map((s) => s.style.background)).toEqual([
      "var(--pen-a)",
      "var(--pen-b)",
    ]);
  });

  it("says nothing at all when the call named nobody", () => {
    const anon = deck({ ...WITH_ACTS, meta: { ...WITH_ACTS.meta, participants: [] } }, TURNS, METRICS, "");
    const { container } = render(<SpeakerKey deck={anon} />);
    expect(container.firstChild).toBeNull();
  });
});
