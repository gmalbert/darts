export interface ThemeTokens {
  bg: string;
  bg2: string;
  bg3: string;
  text: string;
  muted: string;
  border: string;
  accent: string;
  accent2: string;
  pos: string;
  neg: string;
  tab: string;
  sidebar: string;
}

export const DAY_THEME: ThemeTokens = {
  bg: "#f6fbff",
  bg2: "#ffffff",
  bg3: "#e8f2fb",
  text: "#1f3347",
  muted: "#607a95",
  border: "#c5d9ed",
  accent: "#0284c7",
  accent2: "#f97316",
  pos: "#15803d",
  neg: "#dc2626",
  tab: "#0284c7",
  sidebar: "#ecf5ff",
};

export const NIGHT_THEME: ThemeTokens = {
  bg: "#071418",
  bg2: "#0f2026",
  bg3: "#183039",
  text: "#d8edf2",
  muted: "#7ba7b2",
  border: "#28505c",
  accent: "#00b4d8",
  accent2: "#f77f00",
  pos: "#2ec4b6",
  neg: "#ef476f",
  tab: "#00b4d8",
  sidebar: "#051015",
};

export function isDayTheme(theme: ThemeTokens): boolean {
  return theme === DAY_THEME;
}

export function getPlotlyTemplate(theme: ThemeTokens): "plotly_dark" | "plotly_white" {
  return isDayTheme(theme) ? "plotly_white" : "plotly_dark";
}

export function getPlotlyColors(theme: ThemeTokens) {
  return {
    template: getPlotlyTemplate(theme),
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    grid: theme.border,
    text: theme.text,
    muted: theme.muted,
    accent: theme.accent,
    accent2: theme.accent2,
    pos: theme.pos,
    neg: theme.neg,
  };
}
