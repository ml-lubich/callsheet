import { Reveal, STAGGER } from "../components/Reveal";
import { TimeLink } from "../components/TimeLink";
import type { Content, Turn } from "../types";

export function Friction({
  tensions = [],
  diarization = [],
  turns,
}: {
  tensions?: NonNullable<Content["tensions"]>;
  diarization?: NonNullable<Content["diarization"]>;
  turns: Turn[];
}) {
  return (
    <>
      <ul className="rows">
        {tensions.map((t, i) => (
          <Reveal as="li" key={`${t.s}-${i}`} delay={i * STAGGER}>
            <TimeLink ts={t.ts} s={t.s} turns={turns} />
            <div>{t.note}</div>
          </Reveal>
        ))}
      </ul>
      {diarization.length > 0 && (
        <div className="dia-block">
          <h3 className="subhead">Diarization drift</h3>
          <p className="dia-note">
            Speakers were separated by voice, not by identity, and labels are least reliable at
            turn boundaries. Read the moments below as label drift, not as things said.
          </p>
          <ul className="rows">
            {diarization.map((d, i) => (
              <Reveal as="li" key={`${d.s}-${i}`} delay={i * STAGGER}>
                <TimeLink ts={d.ts} s={d.s} turns={turns} />
                <div>{d.why}</div>
              </Reveal>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
