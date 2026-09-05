import type { ReactNode } from "react";
import { Boot } from "../components/Skeleton";

/**
 * One section of the page. A section the analysis had nothing for is not rendered at
 * all, rather than left as an empty heading.
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
      <div className="wrap">
        {title && <h2 className="sec">{title}</h2>}
        <Boot order={order} skeleton={skeleton}>
          {children}
        </Boot>
      </div>
    </section>
  );
}
