import { useCallback, useEffect, useState } from "react";

export const THEME_KEY = "cs-theme";

function stored(): "light" | "dark" | null {
  try {
    const v = localStorage.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

function systemTheme(): "light" | "dark" {
  return typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

/**
 * A build may pin the page to one theme. The CLI passes that through the environment,
 * the build writes it into the inline script in index.html, and that script stamps it on
 * <html> before the first paint — so the pin is a fact about the document by the time
 * any of this runs, and there is nothing here to keep in sync with it.
 */
export function pinnedTheme(): "light" | "dark" | null {
  if (typeof document === "undefined") return null;
  const pin = document.documentElement.getAttribute("data-theme-pin");
  return pin === "light" || pin === "dark" ? pin : null;
}

/** The theme in force: the pin, then an explicit choice, then the system's. */
export function currentTheme(): "light" | "dark" {
  const pin = pinnedTheme();
  if (pin) return pin;
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  return stored() ?? systemTheme();
}

export function useTheme(): { theme: "light" | "dark"; toggle: () => void; pinned: boolean } {
  const pin = pinnedTheme();
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    typeof document === "undefined" ? "light" : currentTheme(),
  );

  const effective = pin ?? theme;

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", effective);
  }, [effective]);

  const toggle = useCallback(() => {
    if (pin) return; // a pinned build has nothing to toggle, and no choice to remember
    setTheme((now) => {
      const next = now === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch {
        /* a browser that refuses storage still gets the toggle, just not the memory */
      }
      return next;
    });
  }, [pin]);

  return { theme: effective, toggle, pinned: pin != null };
}
