import { useEffect, useRef, useState, type ReactNode } from "react";
import { motion, useScroll, useTransform, type MotionValue } from "motion/react";
import { reduceMotion } from "../lib/jump";
import {
  resolveScrollStackVariant,
  shouldUseCompactScrollStackViewport,
} from "../lib/scroll-stack-layout";

/**
 * ScrollStack — cards that pin below the top of the viewport and stack as the reader
 * scrolls, each one settling back and dimming a touch as the next arrives. Scroll is
 * the only input.
 *
 * Only wide, mouse-driven, motion-ok desktops get the stack. Phones, tablets, coarse
 * pointers, reduced-motion and low-core devices render `items` inside a plain element
 * with `compactClassName` — pass the layout those readers already had and the change
 * is a no-op for them.
 *
 * ponytail: the variant is measured in an effect, so the first paint is always the
 * compact column and wide desktops swap to the stack after mount. Upgrade to a
 * CSS-only container query if that ever stops being good enough.
 */

export type ScrollStackItem = { key: string; node: ReactNode };

type ScrollStackProps = {
  items: ScrollStackItem[];
  /** Classes for the compact/column root — pass the old layout's classes for a no-op. */
  compactClassName?: string;
  /** Classes for the stack root. */
  className?: string;
  /** Classes for the moving card itself; pass "" when the card carries its own chrome. */
  cardClassName?: string;
  /** Distance from the viewport top where cards pin (px). */
  stickyTop?: number;
  /** Extra offset per card so the stack peeks (px). */
  stackOffset?: number;
  /** Scroll runway allocated per card (vh). */
  scrollPerCard?: number;
};

const TOP_CLEARANCE_PX = 112;

/**
 * The signals are read straight from the platform on every measurement rather than
 * through framer's cached hook: the routing function is the whole safety story here,
 * and it deserves the live answer.
 */
function useCompactViewport(): boolean | null {
  const [compact, setCompact] = useState<boolean | null>(null);

  useEffect(() => {
    const mq = (query: string) =>
      typeof window.matchMedia === "function" && window.matchMedia(query).matches;
    const compute = () =>
      setCompact(
        shouldUseCompactScrollStackViewport({
          innerWidth: window.innerWidth,
          pointerCoarse: mq("(pointer: coarse)"),
          hoverNone: mq("(hover: none)"),
          maxTouchPoints: navigator.maxTouchPoints ?? 0,
          prefersReducedMotion: reduceMotion(),
          hardwareConcurrency: navigator.hardwareConcurrency,
        }),
      );
    compute();
    window.addEventListener("resize", compute, { passive: true });
    return () => window.removeEventListener("resize", compute);
  }, []);

  return compact;
}

export function ScrollStack({
  items,
  compactClassName,
  className,
  cardClassName = "stack-card",
  stickyTop = TOP_CLEARANCE_PX,
  stackOffset = 18,
  scrollPerCard = 62,
}: ScrollStackProps) {
  const compact = useCompactViewport();
  const variant = resolveScrollStackVariant(undefined, compact ?? true);

  if (variant !== "stack") {
    return (
      <div data-variant={variant} className={compactClassName}>
        {items.map((item) => (
          <div key={item.key}>{item.node}</div>
        ))}
      </div>
    );
  }

  return (
    <StackRoot
      items={items}
      className={className}
      cardClassName={cardClassName}
      stickyTop={stickyTop}
      stackOffset={stackOffset}
      scrollPerCard={scrollPerCard}
    />
  );
}

type StackRootProps = Required<
  Pick<ScrollStackProps, "items" | "cardClassName" | "stickyTop" | "stackOffset" | "scrollPerCard">
> &
  Pick<ScrollStackProps, "className">;

/** Owns the scroll container ref, so `useScroll` only ever runs with a mounted target. */
function StackRoot({
  items,
  className,
  cardClassName,
  stickyTop,
  stackOffset,
  scrollPerCard,
}: StackRootProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end end"],
  });

  return (
    <div ref={containerRef} data-variant="stack" className={className}>
      {items.map((item, i) => (
        <StackCard
          key={item.key}
          index={i}
          count={items.length}
          progress={scrollYProgress}
          cardClassName={cardClassName}
          stickyTop={stickyTop + i * stackOffset}
          runwayVh={scrollPerCard}
        >
          {item.node}
        </StackCard>
      ))}
    </div>
  );
}

type StackCardProps = {
  index: number;
  count: number;
  progress: MotionValue<number>;
  cardClassName: string;
  stickyTop: number;
  runwayVh: number;
  children: ReactNode;
};

function StackCard({
  index,
  count,
  progress,
  cardClassName,
  stickyTop,
  runwayVh,
  children,
}: StackCardProps) {
  // Card i is "covered" while card i+1 travels in: that slice of the runway.
  const coverStart = (index + 1) / count;
  const coverEnd = Math.min(1, (index + 2) / count);
  const isLast = index === count - 1;
  const scale = useTransform(progress, [coverStart, coverEnd], isLast ? [1, 1] : [1, 0.94]);
  const opacity = useTransform(progress, [coverStart, coverEnd], isLast ? [1, 1] : [1, 0.72]);

  return (
    <div
      data-scroll-stack-card
      className="sticky"
      style={{ top: stickyTop, minHeight: `${runwayVh}vh` }}
    >
      <motion.div style={{ scale, opacity, transformOrigin: "50% 0%" }} className={cardClassName}>
        {children}
      </motion.div>
    </div>
  );
}
