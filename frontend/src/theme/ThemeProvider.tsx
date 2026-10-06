import { useState, useEffect, useCallback } from "react";
import { DAY_THEME, NIGHT_THEME, type ThemeTokens } from "./tokens";

function getStoredMode(): "day" | "night" {
  const params = new URLSearchParams(window.location.search);
  const urlMode = params.get("biq_mode");
  if (urlMode === "day" || urlMode === "night") return urlMode;
  try {
    const stored = localStorage.getItem("biq_mode") as "day" | "night" | null;
    if (stored === "day" || stored === "night") return stored;
  } catch {}
  const hour = new Date().getHours();
  return hour >= 7 && hour < 19 ? "day" : "night";
}

function resolveTheme(mode: "day" | "night"): ThemeTokens {
  return mode === "day" ? DAY_THEME : NIGHT_THEME;
}

export function useTheme() {
  const [mode, setMode] = useState<"day" | "night">(getStoredMode);

  useEffect(() => {
    const interval = setInterval(() => {
      const h = new Date().getHours();
      const newMode = h >= 7 && h < 19 ? "day" : "night";
      if (newMode !== mode) setMode(newMode);
    }, 60_000);
    return () => clearInterval(interval);
  }, [mode]);

  const theme = resolveTheme(mode);

  const applyToDOM = useCallback(() => {
    const r = document.documentElement.style;
    r.setProperty("--biq-bg", theme.bg);
    r.setProperty("--biq-bg2", theme.bg2);
    r.setProperty("--biq-bg3", theme.bg3);
    r.setProperty("--biq-text", theme.text);
    r.setProperty("--biq-muted", theme.muted);
    r.setProperty("--biq-border", theme.border);
    r.setProperty("--biq-accent", theme.accent);
    r.setProperty("--biq-accent2", theme.accent2);
    r.setProperty("--biq-pos", theme.pos);
    r.setProperty("--biq-neg", theme.neg);
    r.setProperty("--biq-tab", theme.tab);
    r.setProperty("--biq-sidebar", theme.sidebar);
    document.body.style.backgroundColor = theme.bg;
    document.body.style.color = theme.text;
  }, [theme]);

  useEffect(() => { applyToDOM(); }, [applyToDOM]);

  return { theme, mode, setMode };
}
