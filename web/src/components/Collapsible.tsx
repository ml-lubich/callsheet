import { type ReactNode, useCallback, useEffect, useId, useState } from "react";

/**
 * A section that stays shut until asked for. `openOnHash` lets a deep link into the
 * contents open it: landing on #t-12 must not leave the reader staring at a closed
 * transcript.
 */
export function Collapsible({
  label,
  meta,
  tools,
  openOnHash,
  defaultOpen = false,
  open: controlled,
  onOpenChange,
  children,
}: {
  label: string;
  meta?: ReactNode;
  tools?: ReactNode;
  openOnHash?: RegExp;
  defaultOpen?: boolean;
  /** Pass to drive the section from outside; omit and it keeps its own state. */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: ReactNode;
}) {
  const bodyId = useId();
  const [own, setOwn] = useState(
    () =>
      defaultOpen ||
      Boolean(openOnHash && typeof location !== "undefined" && openOnHash.test(location.hash)),
  );
  const open = controlled ?? own;

  const set = useCallback(
    (next: boolean) => {
      if (controlled === undefined) setOwn(next);
      onOpenChange?.(next);
    },
    [controlled, onOpenChange],
  );
  const show = useCallback(() => set(true), [set]);

  useEffect(() => {
    if (!openOnHash) return;
    const check = () => {
      if (openOnHash.test(location.hash)) show();
    };
    check();
    window.addEventListener("hashchange", check);
    return () => window.removeEventListener("hashchange", check);
  }, [openOnHash, show]);

  return (
    <div className="collapse">
      <div className="collapse-head">
        <button
          type="button"
          className="collapse-btn"
          aria-expanded={open}
          aria-controls={bodyId}
          onClick={() => set(!open)}
        >
          <span className="collapse-mark" aria-hidden="true">
            {open ? "−" : "+"}
          </span>
          {label}
          {meta ? <span className="collapse-meta">{meta}</span> : null}
        </button>
        {open && tools ? <div className="collapse-tools">{tools}</div> : null}
      </div>
      <div id={bodyId} hidden={!open}>
        {open ? children : null}
      </div>
    </div>
  );
}
