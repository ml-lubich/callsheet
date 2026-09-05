import { useState } from "react";
import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";
import { TimeLink } from "../components/TimeLink";
import type { Content, Strength, Turn } from "../types";

const RANK: Record<Strength, number> = { strong: 3, medium: 2, weak: 1 };

export function EvidenceSkeleton() {
  return (
    <div className="sk-grid">
      {[0, 1, 2, 3].map((i) => (
        <Skeleton h={34} key={i} />
      ))}
    </div>
  );
}

function Pips({ strength }: { strength: Strength }) {
  const n = RANK[strength] ?? 1;
  return (
    <span className="pips">
      {[1, 2, 3].map((i) => (
        <i key={i} className={i <= n ? "on" : undefined} />
      ))}
      <span className="lab">{strength}</span>
    </span>
  );
}

export function Evidence({
  rows,
  turns,
}: {
  rows: NonNullable<Content["evidence"]>;
  turns: Turn[];
}) {
  const [dir, setDir] = useState(0);
  const sorted =
    dir === 0
      ? rows
      : [...rows].sort((a, b) => dir * ((RANK[a.strength] ?? 0) - (RANK[b.strength] ?? 0)));

  return (
    <div className="tscroll">
      <table>
        <thead>
          <tr>
            <th scope="col">Time</th>
            <th scope="col">Claim</th>
            <th scope="col">How it is backed</th>
            <th
              scope="col"
              className="sortable"
              tabIndex={0}
              role="button"
              onClick={() => setDir((d) => (d >= 0 ? -1 : 1))}
              onKeyDown={(e) =>
                (e.key === "Enter" || e.key === " ") && setDir((d) => (d >= 0 ? -1 : 1))
              }
            >
              Strength <span className="arrow">{dir === 0 ? "" : dir > 0 ? "↑" : "↓"}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => (
            <Reveal as="tr" key={`${r.s}-${r.claim}`} delay={i * STAGGER}>
              <td>
                <TimeLink ts={r.ts} s={r.s} turns={turns} />
              </td>
              <td>{r.claim}</td>
              <td>{r.evidence}</td>
              <td>
                <Pips strength={r.strength} />
              </td>
            </Reveal>
          ))}
        </tbody>
      </table>
    </div>
  );
}
