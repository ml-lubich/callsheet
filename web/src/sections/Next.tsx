import { Reveal, STAGGER } from "../components/Reveal";
import { TimeLink } from "../components/TimeLink";
import type { Content, Turn } from "../types";

export function Next({
  steps,
  turns,
}: {
  steps: NonNullable<Content["next_steps"]>;
  turns: Turn[];
}) {
  return (
    <ul className="steps">
      {steps.map((n, i) => (
        <Reveal as="li" key={`${n.s}-${i}`} delay={i * STAGGER}>
          <TimeLink ts={n.ts} s={n.s} turns={turns} />
          <div>{n.commitment}</div>
        </Reveal>
      ))}
    </ul>
  );
}
