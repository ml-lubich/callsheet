import { nearestTurn } from "../lib/derive";
import { jump } from "../lib/jump";
import type { Turn } from "../types";

/** A timestamp that takes you to the moment it names, opening the transcript if shut. */
export function TimeLink({ ts, s, turns }: { ts: string; s?: number; turns: Turn[] }) {
  const index = nearestTurn(turns, s ?? 0);
  return (
    <a
      className="ts"
      href={`#t-${index}`}
      onClick={(e) => {
        e.preventDefault();
        jump(index);
      }}
    >
      {ts}
    </a>
  );
}
