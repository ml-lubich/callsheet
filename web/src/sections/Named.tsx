import { Reveal, STAGGER } from "../components/Reveal";
import { Skeleton } from "../components/Skeleton";

export function NamedSkeleton() {
  return (
    <div className="sk-grid">
      <Skeleton h={13} w="58%" />
      <Skeleton h={38} />
    </div>
  );
}

/** What was said, not what was endorsed. */
export function Named({ tech }: { tech: string[] }) {
  const sorted = [...tech].sort((a, b) => a.toLowerCase().localeCompare(b.toLowerCase()));
  return (
    <>
      <p className="narrow dia-note">
        {sorted.length} named by one or more speakers. What was said, not what was endorsed.
      </p>
      <ul className="techlist">
        {sorted.map((t, i) => (
          <Reveal as="li" key={t} delay={Math.min(12, i) * STAGGER}>
            {t}
          </Reveal>
        ))}
      </ul>
    </>
  );
}
