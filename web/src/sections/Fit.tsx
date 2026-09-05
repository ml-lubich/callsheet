import { Reveal, STAGGER } from "../components/Reveal";
import type { Content } from "../types";

export function Fit({ fit }: { fit: NonNullable<Content["fit"]> }) {
  const aligned = fit.aligned_on ?? [];
  const unresolved = fit.unresolved ?? [];
  const risks = fit.risks ?? [];
  return (
    <>
      <div className="fitgrid">
        {aligned.length > 0 && (
          <div>
            <h3 className="subhead">Aligned on</h3>
            <ul className="bullets">
              {aligned.map((x, i) => (
                <Reveal as="li" key={x} delay={i * STAGGER}>
                  {x}
                </Reveal>
              ))}
            </ul>
          </div>
        )}
        {unresolved.length > 0 && (
          <div>
            <h3 className="subhead">Unresolved</h3>
            <ul className="bullets">
              {unresolved.map((x, i) => (
                <Reveal as="li" key={x} delay={i * STAGGER}>
                  {x}
                </Reveal>
              ))}
            </ul>
          </div>
        )}
      </div>
      {risks.length > 0 && (
        <div className="risks">
          {risks.map((r, i) => (
            <Reveal key={r.who + i} className="risk" delay={i * STAGGER}>
              <h4>Risk for {r.who}</h4>
              <p>{r.note}</p>
            </Reveal>
          ))}
        </div>
      )}
    </>
  );
}
