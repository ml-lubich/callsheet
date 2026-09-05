import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Collapsible } from "../components/Collapsible";
import { Scrubber } from "../components/Scrubber";
import { SpeakerChip, SpeakerKey } from "../components/SpeakerKey";
import { penClass } from "../lib/derive";
import { onJump, reduceMotion } from "../lib/jump";
import type { TranscriptMode } from "../lib/mode";
import { matches, segments } from "../lib/search";
import type { Act, Deck, Turn } from "../types";

const DEEP_LINK = /^#t-\d+$/;

export interface Chapter {
  n: number;
  title: string;
  span?: string;
  start_s: number;
  turns: Turn[];
}

/**
 * The turns, cut at the act boundaries. A turn belongs to the last act that had started
 * by the time it was spoken; anything before the first act joins it rather than being
 * stranded in a chapter of its own. A call with no acts is one chapter.
 */
export function chapters(acts: Act[], turns: Turn[]): Chapter[] {
  if (!acts.length) {
    return turns.length ? [{ n: 0, title: "The call", start_s: 0, turns }] : [];
  }
  const out: Chapter[] = acts.map((a) => ({
    n: a.n,
    title: a.title,
    span: a.span,
    start_s: a.start_s,
    turns: [],
  }));
  for (const t of turns) {
    let at = 0;
    for (let i = 0; i < acts.length; i++) if (acts[i].start_s <= t.s) at = i;
    out[at].turns.push(t);
  }
  return out.filter((c) => c.turns.length > 0);
}

function Body({ text, query }: { text: string; query: string }) {
  const parts = useMemo(() => segments(text, query), [text, query]);
  return (
    <p>
      {parts.map((p, i) => (p.hit ? <mark key={i}>{p.text}</mark> : <span key={i}>{p.text}</span>))}
    </p>
  );
}

/**
 * Which stretch of the call is on screen, in seconds. Turn offsets are measured once per
 * layout and searched on scroll, so the reader can be dragged around without a hundred
 * getBoundingClientRect calls a frame.
 */
function useVisibleSpan(deps: unknown[]): [number, number] | null {
  const [span, setSpan] = useState<[number, number] | null>(null);
  const marks = useRef<{ s: number; top: number }[]>([]);

  const measure = useCallback(() => {
    marks.current = [...document.querySelectorAll<HTMLElement>("[data-turn-s]")]
      .map((el) => ({
        s: Number(el.dataset.turnS),
        top: el.getBoundingClientRect().top + window.scrollY,
      }))
      .sort((a, b) => a.top - b.top);
  }, []);

  const read = useCallback(() => {
    const all = marks.current;
    if (!all.length) return setSpan(null);
    const top = window.scrollY;
    const bottom = top + window.innerHeight;
    const inside = all.filter((m) => m.top >= top && m.top <= bottom);
    if (inside.length) return setSpan([inside[0].s, inside[inside.length - 1].s]);
    // between two turns: the one just above the fold stands for the whole viewport
    const above = all.filter((m) => m.top < top);
    const at = above.length ? above[above.length - 1].s : all[0].s;
    setSpan([at, at]);
  }, []);

  useLayoutEffect(() => {
    measure();
    read();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(() => ((raf = 0), read()));
    };
    const onResize = () => {
      measure();
      read();
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onResize);
    };
  }, [measure, read]);

  return span;
}

/** The chapter rail's highlight: the last chapter heading to have crossed the top. */
function useCurrentChapter(chapterNumbers: number[]): number | null {
  const [current, setCurrent] = useState<number | null>(chapterNumbers[0] ?? null);
  useEffect(() => {
    if (typeof IntersectionObserver === "undefined") return;
    const seen = new Set<number>();
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          const n = Number((e.target as HTMLElement).dataset.chapter);
          if (e.isIntersecting) seen.add(n);
          else seen.delete(n);
        }
        if (seen.size) setCurrent(Math.min(...seen));
      },
      { rootMargin: "-20% 0px -60% 0px" },
    );
    document.querySelectorAll("[data-chapter]").forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [chapterNumbers.join(",")]);
  return current;
}

/**
 * The whole call, read rather than listed: a chapter rail down the side, the turns cut
 * into acts that open one at a time, and a miniature of the strip chart pinned above
 * them showing where in the call the reader currently is. Every timestamp elsewhere on
 * the page links in here, so it also has to be able to open the right chapter, clear
 * whatever filter was left behind, and scroll to the turn.
 */
export function Reader({ deck }: { deck: Deck }) {
  const { turns, keys, names, content } = deck;
  const [query, setQuery] = useState("");
  const [speaker, setSpeaker] = useState("");
  const [flash, setFlash] = useState<number | null>(null);
  const [open, setOpen] = useState<Set<number>>(new Set());

  const cut = useMemo(() => chapters(content.acts ?? [], turns), [content.acts, turns]);
  const filtering = Boolean(query.trim() || speaker);
  const keep = useCallback(
    (t: Turn) => (!speaker || t.spk === speaker) && matches(t.t, query),
    [speaker, query],
  );

  const shown = useMemo(
    () => cut.map((c) => ({ ...c, turns: c.turns.filter(keep) })).filter((c) => c.turns.length),
    [cut, keep],
  );
  const total = shown.reduce((n, c) => n + c.turns.length, 0);

  // while a filter is on, every chapter with a hit is open: a closed reader full of
  // matches reads as no matches at all
  const isOpen = (n: number) => filtering || open.has(n);
  const toggle = (n: number, next: boolean) =>
    setOpen((now) => {
      const copy = new Set(now);
      if (next) copy.add(n);
      else copy.delete(n);
      return copy;
    });

  const chapterOf = useCallback(
    (index: number) => cut.find((c) => c.turns.some((t) => t.i === index))?.n,
    [cut],
  );

  const goTo = useCallback(
    (index: number) => {
      setQuery("");
      setSpeaker("");
      setFlash(index);
      const chapter = chapterOf(index);
      if (chapter != null) setOpen((now) => new Set(now).add(chapter));
      const scroll = () =>
        document.getElementById(`t-${index}`)?.scrollIntoView({
          block: "center",
          behavior: reduceMotion() ? "auto" : "smooth",
        });
      // two frames: the chapter has to have opened before it can be scrolled to
      requestAnimationFrame(() => requestAnimationFrame(scroll));
      setTimeout(() => setFlash(null), 1400);
    },
    [chapterOf],
  );

  useEffect(() => onJump(goTo), [goTo]);

  useEffect(() => {
    const fromHash = () => {
      if (DEEP_LINK.test(location.hash)) goTo(Number(location.hash.slice(3)));
    };
    fromHash();
    window.addEventListener("hashchange", fromHash);
    return () => window.removeEventListener("hashchange", fromHash);
  }, [goTo]);

  /** Drag or click the scrubber: the nearest turn that is actually on the page. */
  const seek = useCallback(
    (seconds: number) => {
      let best: Turn | null = null;
      for (const c of shown) {
        for (const t of c.turns) {
          if (!best || Math.abs(t.s - seconds) < Math.abs(best.s - seconds)) best = t;
        }
      }
      if (!best) return;
      const chapter = chapterOf(best.i);
      if (chapter != null && !isOpen(chapter)) toggle(chapter, true);
      const id = `t-${best.i}`;
      requestAnimationFrame(() =>
        document.getElementById(id)?.scrollIntoView({ block: "center", behavior: "auto" }),
      );
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [shown, chapterOf, filtering, open],
  );

  const openKey = shown.map((c) => `${c.n}:${isOpen(c.n) ? 1 : 0}`).join(",");
  const span = useVisibleSpan([openKey, total]);
  const current = useCurrentChapter(shown.map((c) => c.n));
  const hits = useMemo(
    () => (query.trim() ? shown.flatMap((c) => c.turns.map((t) => t.s)) : []),
    [query, shown],
  );

  return (
    <div className="reader">
      <nav className="rail" aria-label="Chapters">
        <ol>
          {shown.map((c) => (
            <li key={c.n}>
              <button
                type="button"
                className={current === c.n ? "on" : undefined}
                aria-current={current === c.n ? "true" : undefined}
                onClick={() => {
                  toggle(c.n, true);
                  requestAnimationFrame(() =>
                    document
                      .getElementById(`ch-${c.n}`)
                      ?.scrollIntoView({ block: "start", behavior: "smooth" }),
                  );
                }}
              >
                <span className="rail-n">{c.n || "·"}</span>
                <span className="rail-t">{c.title}</span>
              </button>
            </li>
          ))}
        </ol>
      </nav>

      <div className="reader-main">
        <SpeakerKey deck={deck} className="reader-key" />

        <div className="reader-tools">
          <input
            className="search"
            type="search"
            value={query}
            placeholder="Search the transcript"
            aria-label="Search the transcript"
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="filters" role="group" aria-label="Filter by speaker">
            <button type="button" aria-pressed={speaker === ""} onClick={() => setSpeaker("")}>
              All
            </button>
            {keys.map((k) => (
              <button
                key={k}
                type="button"
                aria-pressed={speaker === k}
                onClick={() => setSpeaker(k)}
              >
                {names[k] || k}
              </button>
            ))}
          </div>
        </div>

        <div className="reader-pin">
          <Scrubber deck={deck} hits={hits} window={span} onSeek={seek} />
          <p className="tcount">
            {total} of {turns.length} turns shown
          </p>
        </div>

        {shown.map((c) => (
          <div className="chapter" key={c.n} id={`ch-${c.n}`} data-chapter={c.n}>
            <Collapsible
              label={c.n ? `${c.n}. ${c.title}` : c.title}
              meta={`${c.turns.length} turns${c.span ? ` · ${c.span}` : ""}`}
              open={isOpen(c.n)}
              onOpenChange={(next) => toggle(c.n, next)}
            >
              {c.turns.map((t) => (
                <article
                  key={t.i}
                  id={`t-${t.i}`}
                  data-turn-s={t.s}
                  className={`turn ${penClass(keys, t.spk)}${flash === t.i ? " flash" : ""}`}
                >
                  <div className="head">
                    <SpeakerChip
                      keys={keys}
                      spk={t.spk}
                      name={names[t.spk] || t.name || t.spk}
                    />
                    <span className="ts">{t.ts}</span>
                    <span className="ts">{t.w} words</span>
                  </div>
                  <Body text={t.t} query={query} />
                </article>
              ))}
            </Collapsible>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * The transcript as the mode asked for it. `open` puts the reader on the page; the
 * default shuts it behind one more click, because it is the longest thing here and the
 * least often wanted. `omit` never reaches this component.
 */
export function Transcript({ deck, mode = "collapsed" }: { deck: Deck; mode?: TranscriptMode }) {
  const [open, setOpen] = useState(
    () => mode === "open" || (typeof location !== "undefined" && DEEP_LINK.test(location.hash)),
  );

  useEffect(() => {
    const check = () => DEEP_LINK.test(location.hash) && setOpen(true);
    check();
    window.addEventListener("hashchange", check);
    return () => window.removeEventListener("hashchange", check);
  }, []);

  if (mode === "open") return <Reader deck={deck} />;

  return (
    <Collapsible
      label="Read the transcript"
      meta={`${deck.turns.length} turns`}
      open={open}
      onOpenChange={setOpen}
    >
      <Reader deck={deck} />
    </Collapsible>
  );
}
