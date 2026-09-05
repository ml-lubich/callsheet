import { CountUp } from "../components/CountUp";
import { Boot, Skeleton } from "../components/Skeleton";
import { SpeakerKey } from "../components/SpeakerKey";
import { useTheme } from "../lib/theme";
import type { Deck } from "../types";

function Cells({ meta }: { meta: Deck["content"]["meta"] }) {
  const cells: [string, string | number][] = [
    ["Date", meta.date ?? ""],
    ["Duration", meta.duration_label ?? ""],
    ["Turns", meta.turns ?? ""],
    ["Words", meta.words ?? ""],
    ...(meta.extra ?? []),
  ].filter(([, v]) => v !== "" && v != null) as [string, string | number][];

  return (
    <dl className="metastrip">
      {cells.map(([label, value]) => (
        <div className="cell" key={label}>
          <dt>{label}</dt>
          <dd>{typeof value === "number" ? <CountUp value={value} /> : value}</dd>
        </div>
      ))}
    </dl>
  );
}

export function Plate({ deck }: { deck: Deck }) {
  const meta = deck.content.meta;
  const { theme, toggle } = useTheme();

  return (
    <header className="wrap plate">
      <div className="plate-top">
        <span className="rule-word">{meta.kind || "Call record"}</span>
        <button
          type="button"
          className="tbtn"
          onClick={toggle}
          aria-label="Toggle light and dark theme"
        >
          {theme === "dark" ? "Light" : "Dark"}
        </button>
      </div>
      <Boot
        order={0}
        skeleton={
          <div className="sk-grid">
            <Skeleton h={54} w="72%" />
            <Skeleton h={22} w="46%" />
            <Skeleton h={62} mt={18} />
          </div>
        }
      >
        <h1>{meta.title}</h1>
        {meta.subtitle && <p className="sub">{meta.subtitle}</p>}
        <Cells meta={meta} />
        <SpeakerKey deck={deck} />
      </Boot>
    </header>
  );
}
