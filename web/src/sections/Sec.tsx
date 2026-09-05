import type { ReactNode } from "react";
import { Reveal } from "../components/Reveal";
import { Boot } from "../components/Skeleton";

/**
 * One section of the page. A section the analysis had nothing for is not rendered at
 * all, rather than left as an empty heading.
 *
 * A titled section is an editorial spread rather than a centred column: on a wide
 * screen the heading sits in a sticky rail down the left and the content takes the rest
 * of the width. Narrow screens stack the two, which is what the page always did. The
 * content reveals on the way in, once, and is plain markup under reduced motion.
 */
export function Sec({
  id,
  title,
  order,
  skeleton,
  when = true,
  className,
  children,
}: {
  id?: string;
  title?: string;
  order: number;
  skeleton: ReactNode;
  when?: boolean;
  className?: string;
  children: ReactNode;
}) {
  if (!when) return null;
  return (
    <section id={id} className={className}>
      <div className={["wrap", title && "spread"].filter(Boolean).join(" ")}>
        {title && (
          <div className="sec-rail">
            <h2 className="sec">{title}</h2>
          </div>
        )}
        <Reveal className="sec-body">
          <Boot order={order} skeleton={skeleton}>
            {children}
          </Boot>
        </Reveal>
      </div>
    </section>
  );
}
