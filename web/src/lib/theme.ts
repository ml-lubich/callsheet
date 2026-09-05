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

/** The theme in force: an explicit choice if one was made, otherwise the system's. */
export function currentTheme(): "light" | "dark" {
  const attr = document.documentElement.getAttribute("data-theme");
  if (attr === "light" || attr === "dark") return attr;
  return stored() ?? systemTheme();
}

export function useTheme(): { theme: "light" | "dark"; toggle: () => void } {
  const [theme, setTheme] = useState<"light" | "dark">(() =>
    typeof document === "undefined" ? "light" : currentTheme(),
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const toggle = useCallback(() => {
    setTheme((now) => {
      const next = now === "dark" ? "light" : "dark";
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch {
        /* a browser that refuses storage still gets the toggle, just not the memory */
      }
      return next;
    });
  }, []);

  return { theme, toggle };
}
