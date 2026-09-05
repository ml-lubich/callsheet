import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { Transcript } from "../sections/Transcript";
import { jump } from "../lib/jump";
import { DECK } from "./fixture";

async function open() {
  const user = userEvent.setup();
  render(<Transcript deck={DECK} />);
  await user.click(screen.getByRole("button", { name: /read the transcript/i }));
  return user;
}

describe("transcript", () => {
  beforeEach(() => {
    location.hash = "";
  });

  it("is shut until asked for, and says how many turns are inside", () => {
    render(<Transcript deck={DECK} />);
    expect(screen.getByRole("button", { name: /3 turns/ })).toHaveAttribute(
      "aria-expanded",
      "false",
    );
    expect(screen.queryByText(/nothing else to add/)).not.toBeInTheDocument();
  });

  it("searches across a spacing difference and highlights the hit", async () => {
    const user = await open();
    await user.type(screen.getByLabelText(/search the transcript/i), "deepseek");
    // both the spaced and the spaceless spelling answer to it
    expect(screen.getByText("2 of 3 turns shown")).toBeInTheDocument();
    expect(screen.getByText("deep seek").tagName).toBe("MARK");
    expect(screen.getByText("deepseek").tagName).toBe("MARK");
  });

  it("finds the spaceless spelling from a spaced query", async () => {
    const user = await open();
    await user.type(screen.getByLabelText(/search the transcript/i), "deep seek");
    expect(screen.getByText("2 of 3 turns shown")).toBeInTheDocument();
    expect(screen.getByText("deepseek").tagName).toBe("MARK");
  });

  it("filters by speaker", async () => {
    const user = await open();
    await user.click(screen.getByRole("button", { name: "Bo Listener" }));
    expect(screen.getByText("1 of 3 turns shown")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "All" }));
    expect(screen.getByText("3 of 3 turns shown")).toBeInTheDocument();
  });

  it("opens itself and clears the filter when something jumps into it", async () => {
    const user = await open();
    await user.click(screen.getByRole("button", { name: "Bo Listener" }));
    expect(screen.getByText("1 of 3 turns shown")).toBeInTheDocument();
    jump(2);
    await waitFor(() => expect(screen.getByText("3 of 3 turns shown")).toBeInTheDocument());
    expect(document.getElementById("t-2")).not.toBeNull();
  });

  it("opens on a deep link to a turn", async () => {
    location.hash = "#t-1";
    render(<Transcript deck={DECK} />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /read the transcript/i })).toHaveAttribute(
        "aria-expanded",
        "true",
      ),
    );
    expect(document.getElementById("t-1")).not.toBeNull();
  });
});
