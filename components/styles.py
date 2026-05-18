"""
components/styles.py — Global CSS injection + theme system for BullzIQ.

Usage:
    inject_css(get_theme())    # in every page, before any st.* UI call
    # Theme auto-switches by browser-local time:
    # 07:00-18:59 -> Light - Sky Glass
    # 19:00-06:59 -> Dark - Petrol

Themes are applied via CSS custom properties injected into the page.
"""

from __future__ import annotations
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components

# ── Theme definitions ──────────────────────────────────────────────────────────
# Each theme: bg, bg2 (card), bg3 (hover/input), text, muted, border, accent,
#             accent2, positive, negative, tab_active, sidebar_bg

THEME_CONFIGS: dict[str, dict] = {
    "Dark (Default)": {
        "bg":       "#0d1117",
        "bg2":      "#161b22",
        "bg3":      "#21262d",
        "text":     "#e6edf3",
        "muted":    "#8b949e",
        "border":   "#30363d",
        "accent":   "#e10600",
        "accent2":  "#58a6ff",
        "pos":      "#3fb950",
        "neg":      "#f85149",
        "tab":      "#e10600",
        "sidebar":  "#0d1117",
    },
    "Light": {
        "bg":       "#ffffff",
        "bg2":      "#f6f8fa",
        "bg3":      "#eaeef2",
        "text":     "#24292e",
        "muted":    "#586069",
        "border":   "#d0d7de",
        "accent":   "#cf0500",
        "accent2":  "#0366d6",
        "pos":      "#196c2e",
        "neg":      "#cf222e",
        "tab":      "#cf0500",
        "sidebar":  "#f6f8fa",
    },
    "Midnight Navy": {
        "bg":       "#0a0e1a",
        "bg2":      "#111827",
        "bg3":      "#1a2332",
        "text":     "#cdd9e5",
        "muted":    "#7990a8",
        "border":   "#2d4059",
        "accent":   "#4d9de0",
        "accent2":  "#f0a500",
        "pos":      "#22c55e",
        "neg":      "#ef4444",
        "tab":      "#4d9de0",
        "sidebar":  "#080c15",
    },
    "Forest Green": {
        "bg":       "#0b1a0e",
        "bg2":      "#142212",
        "bg3":      "#1e2e1c",
        "text":     "#d4edda",
        "muted":    "#7aab7a",
        "border":   "#2d4a2d",
        "accent":   "#3fb950",
        "accent2":  "#f0a500",
        "pos":      "#2ea043",
        "neg":      "#f85149",
        "tab":      "#3fb950",
        "sidebar":  "#091408",
    },
    "Slate Pro": {
        "bg":       "#13171f",
        "bg2":      "#1c2128",
        "bg3":      "#252b34",
        "text":     "#cdd9e5",
        "muted":    "#848d97",
        "border":   "#373e47",
        "accent":   "#6cb6ff",
        "accent2":  "#e36414",
        "pos":      "#57ab5a",
        "neg":      "#e5534b",
        "tab":      "#6cb6ff",
        "sidebar":  "#0e1116",
    },
    "Crimson & Black": {
        "bg":       "#0a0808",
        "bg2":      "#180f0f",
        "bg3":      "#231515",
        "text":     "#f0e0e0",
        "muted":    "#a67474",
        "border":   "#3a1a1a",
        "accent":   "#e10600",
        "accent2":  "#f0a500",
        "pos":      "#4caf50",
        "neg":      "#ff6b6b",
        "tab":      "#e10600",
        "sidebar":  "#080505",
    },
    "Ocean Teal": {
        "bg":       "#071a1a",
        "bg2":      "#0d2222",
        "bg3":      "#122e2e",
        "text":     "#ccf0f0",
        "muted":    "#5fa8a8",
        "border":   "#1a4040",
        "accent":   "#14b8a6",
        "accent2":  "#f59e0b",
        "pos":      "#10b981",
        "neg":      "#f43f5e",
        "tab":      "#14b8a6",
        "sidebar":  "#050f0f",
    },
    "Royal Purple": {
        "bg":       "#0e0a1a",
        "bg2":      "#160f2a",
        "bg3":      "#1e1538",
        "text":     "#ddd6fe",
        "muted":    "#9478cc",
        "border":   "#312a6b",
        "accent":   "#a855f7",
        "accent2":  "#ec4899",
        "pos":      "#a3e635",
        "neg":      "#f43f5e",
        "tab":      "#a855f7",
        "sidebar":  "#09071a",
    },
    "Ember": {
        "bg":       "#120a00",
        "bg2":      "#1e1200",
        "bg3":      "#2a1b00",
        "text":     "#fde8c8",
        "muted":    "#c8965a",
        "border":   "#4a2e00",
        "accent":   "#f59e0b",
        "accent2":  "#ef4444",
        "pos":      "#84cc16",
        "neg":      "#f43f5e",
        "tab":      "#f59e0b",
        "sidebar":  "#0a0600",
    },
    "Arctic Light": {
        "bg":       "#f0f6ff",
        "bg2":      "#ffffff",
        "bg3":      "#dce8f5",
        "text":     "#0d1a2e",
        "muted":    "#4a6880",
        "border":   "#b0c8e0",
        "accent":   "#0284c7",
        "accent2":  "#e10600",
        "pos":      "#15803d",
        "neg":      "#dc2626",
        "tab":      "#0284c7",
        "sidebar":  "#e0ecf8",
    },
    "Graphite": {
        "bg":       "#111111",
        "bg2":      "#1c1c1c",
        "bg3":      "#262626",
        "text":     "#e0e0e0",
        "muted":    "#888888",
        "border":   "#333333",
        "accent":   "#6366f1",
        "accent2":  "#34d399",
        "pos":      "#34d399",
        "neg":      "#f87171",
        "tab":      "#6366f1",
        "sidebar":  "#0d0d0d",
    },
    "Solarized Dark": {
        "bg":       "#002b36",
        "bg2":      "#073642",
        "bg3":      "#094050",
        "text":     "#93a1a1",
        "muted":    "#586e75",
        "border":   "#0f4d5e",
        "accent":   "#268bd2",
        "accent2":  "#cb4b16",
        "pos":      "#859900",
        "neg":      "#dc322f",
        "tab":      "#268bd2",
        "sidebar":  "#00212b",
    },
    "Dark - Obsidian": {
        "bg":       "#0b0b10",
        "bg2":      "#14141b",
        "bg3":      "#1e1f29",
        "text":     "#eceff4",
        "muted":    "#9aa3b2",
        "border":   "#2c2f3a",
        "accent":   "#ff6b35",
        "accent2":  "#4cc9f0",
        "pos":      "#2dc653",
        "neg":      "#ff5d73",
        "tab":      "#ff6b35",
        "sidebar":  "#07070c",
    },
    "Dark - Cobalt": {
        "bg":       "#0a1020",
        "bg2":      "#121a2e",
        "bg3":      "#1a2740",
        "text":     "#e2e9f5",
        "muted":    "#8ea1bf",
        "border":   "#2d3f5f",
        "accent":   "#3a86ff",
        "accent2":  "#ffbe0b",
        "pos":      "#22c55e",
        "neg":      "#ef476f",
        "tab":      "#3a86ff",
        "sidebar":  "#070d1a",
    },
    "Dark - Espresso": {
        "bg":       "#120d0a",
        "bg2":      "#1d1511",
        "bg3":      "#2a1f19",
        "text":     "#f3e9df",
        "muted":    "#b59f8d",
        "border":   "#453328",
        "accent":   "#c97b63",
        "accent2":  "#ffd166",
        "pos":      "#80ed99",
        "neg":      "#ff7b7b",
        "tab":      "#c97b63",
        "sidebar":  "#0d0907",
    },
    "Dark - Petrol": {
        "bg":       "#071418",
        "bg2":      "#0f2026",
        "bg3":      "#183039",
        "text":     "#d8edf2",
        "muted":    "#7ba7b2",
        "border":   "#28505c",
        "accent":   "#00b4d8",
        "accent2":  "#f77f00",
        "pos":      "#2ec4b6",
        "neg":      "#ef476f",
        "tab":      "#00b4d8",
        "sidebar":  "#051015",
    },
    "Dark - Iron": {
        "bg":       "#101317",
        "bg2":      "#1a1f25",
        "bg3":      "#242b33",
        "text":     "#e5e7eb",
        "muted":    "#9ca3af",
        "border":   "#3a444f",
        "accent":   "#f59e0b",
        "accent2":  "#60a5fa",
        "pos":      "#34d399",
        "neg":      "#f87171",
        "tab":      "#f59e0b",
        "sidebar":  "#0b0e12",
    },
    "Dark - Plum Smoke": {
        "bg":       "#120f1a",
        "bg2":      "#1c1628",
        "bg3":      "#2a2038",
        "text":     "#e8ddff",
        "muted":    "#a796c8",
        "border":   "#43365a",
        "accent":   "#c77dff",
        "accent2":  "#ffd166",
        "pos":      "#80ed99",
        "neg":      "#ff758f",
        "tab":      "#c77dff",
        "sidebar":  "#0d0a14",
    },
    "Dark - Matrix": {
        "bg":       "#071107",
        "bg2":      "#0f1b0f",
        "bg3":      "#172817",
        "text":     "#c8facc",
        "muted":    "#7fbf88",
        "border":   "#2f5235",
        "accent":   "#39d353",
        "accent2":  "#f4d35e",
        "pos":      "#39d353",
        "neg":      "#ff6b6b",
        "tab":      "#39d353",
        "sidebar":  "#050d05",
    },
    "Dark - Ruby Night": {
        "bg":       "#14090b",
        "bg2":      "#220f13",
        "bg3":      "#33171d",
        "text":     "#f8e7ea",
        "muted":    "#c4979f",
        "border":   "#5a2f37",
        "accent":   "#e11d48",
        "accent2":  "#60a5fa",
        "pos":      "#4ade80",
        "neg":      "#fb7185",
        "tab":      "#e11d48",
        "sidebar":  "#0e0608",
    },
    "Dark - Neon Arcade": {
        "bg":       "#0a0a16",
        "bg2":      "#131327",
        "bg3":      "#1e1e3a",
        "text":     "#e7e7ff",
        "muted":    "#9ca3d9",
        "border":   "#32325a",
        "accent":   "#00f5d4",
        "accent2":  "#f15bb5",
        "pos":      "#80ed99",
        "neg":      "#ff4d6d",
        "tab":      "#00f5d4",
        "sidebar":  "#070711",
    },
    "Dark - Charcoal Mint": {
        "bg":       "#0f1314",
        "bg2":      "#182022",
        "bg3":      "#222d30",
        "text":     "#dff7f2",
        "muted":    "#8eb8af",
        "border":   "#355257",
        "accent":   "#2dd4bf",
        "accent2":  "#f59e0b",
        "pos":      "#34d399",
        "neg":      "#f87171",
        "tab":      "#2dd4bf",
        "sidebar":  "#0b0f10",
    },
    "Light - Ivory": {
        "bg":       "#fffdf8",
        "bg2":      "#fffaf0",
        "bg3":      "#f4eee0",
        "text":     "#2b2a27",
        "muted":    "#6d675c",
        "border":   "#d9d1bf",
        "accent":   "#b45309",
        "accent2":  "#0ea5e9",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#b45309",
        "sidebar":  "#f8f2e6",
    },
    "Light - Sky Glass": {
        "bg":       "#f6fbff",
        "bg2":      "#ffffff",
        "bg3":      "#e8f2fb",
        "text":     "#1f3347",
        "muted":    "#607a95",
        "border":   "#c5d9ed",
        "accent":   "#0284c7",
        "accent2":  "#f97316",
        "pos":      "#15803d",
        "neg":      "#dc2626",
        "tab":      "#0284c7",
        "sidebar":  "#ecf5ff",
    },
    "Light - Sandstone": {
        "bg":       "#fbf8f3",
        "bg2":      "#ffffff",
        "bg3":      "#efe7db",
        "text":     "#32281f",
        "muted":    "#7a6958",
        "border":   "#d8c8b4",
        "accent":   "#c2410c",
        "accent2":  "#0d9488",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#c2410c",
        "sidebar":  "#f4ede3",
    },
    "Light - Rose Paper": {
        "bg":       "#fff6f8",
        "bg2":      "#ffffff",
        "bg3":      "#fde8ee",
        "text":     "#3c2430",
        "muted":    "#8a6272",
        "border":   "#eab8cb",
        "accent":   "#db2777",
        "accent2":  "#2563eb",
        "pos":      "#15803d",
        "neg":      "#dc2626",
        "tab":      "#db2777",
        "sidebar":  "#fdeff4",
    },
    "Light - Mint Cream": {
        "bg":       "#f4fff9",
        "bg2":      "#ffffff",
        "bg3":      "#e3f6ec",
        "text":     "#1f3b2d",
        "muted":    "#5f8a76",
        "border":   "#bfe2cf",
        "accent":   "#059669",
        "accent2":  "#2563eb",
        "pos":      "#15803d",
        "neg":      "#dc2626",
        "tab":      "#059669",
        "sidebar":  "#eafff2",
    },
    "Light - Citrus": {
        "bg":       "#fffef2",
        "bg2":      "#ffffff",
        "bg3":      "#f8f2cc",
        "text":     "#3a3518",
        "muted":    "#7f7340",
        "border":   "#e1d89a",
        "accent":   "#ca8a04",
        "accent2":  "#0284c7",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#ca8a04",
        "sidebar":  "#faf7df",
    },
    "Light - Lavender Mist": {
        "bg":       "#faf8ff",
        "bg2":      "#ffffff",
        "bg3":      "#ede9fe",
        "text":     "#2f2a44",
        "muted":    "#6f6697",
        "border":   "#d3c8f3",
        "accent":   "#7c3aed",
        "accent2":  "#f59e0b",
        "pos":      "#15803d",
        "neg":      "#dc2626",
        "tab":      "#7c3aed",
        "sidebar":  "#f1ecff",
    },
    "Light - Coral Reef": {
        "bg":       "#fff8f6",
        "bg2":      "#ffffff",
        "bg3":      "#ffe5df",
        "text":     "#3d2722",
        "muted":    "#8d6459",
        "border":   "#f0b9aa",
        "accent":   "#ea580c",
        "accent2":  "#0284c7",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#ea580c",
        "sidebar":  "#fff0eb",
    },
    "Light - Ice Blue": {
        "bg":       "#f7fcff",
        "bg2":      "#ffffff",
        "bg3":      "#e5f3fb",
        "text":     "#1b3444",
        "muted":    "#5f7f90",
        "border":   "#c3ddeb",
        "accent":   "#0369a1",
        "accent2":  "#f97316",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#0369a1",
        "sidebar":  "#edf7fd",
    },
    "Light - Monochrome": {
        "bg":       "#fafafa",
        "bg2":      "#ffffff",
        "bg3":      "#efefef",
        "text":     "#202124",
        "muted":    "#5f6368",
        "border":   "#d5d7db",
        "accent":   "#111827",
        "accent2":  "#2563eb",
        "pos":      "#166534",
        "neg":      "#b91c1c",
        "tab":      "#111827",
        "sidebar":  "#f3f4f6",
    },
}

DEFAULT_THEME = "Dark - Petrol"
DAY_THEME = "Light - Sky Glass"
NIGHT_THEME = "Dark - Petrol"


def _is_dark_theme(theme_name: str) -> bool:
    return theme_name.startswith("Dark") or theme_name in {
        "Dark (Default)",
        "Midnight Navy",
        "Forest Green",
        "Slate Pro",
        "Crimson & Black",
        "Ocean Teal",
        "Royal Purple",
        "Ember",
        "Graphite",
        "Solarized Dark",
    }


def _sync_browser_time_mode() -> None:
    """
    Sync `biq_mode` query param from browser-local time.
    Day = 07:00-18:59 -> Sky Glass, Night = 19:00-06:59 -> Petrol.
    """
    components.html(
        """
        <script>
        (function () {
          try {
            const h = new Date().getHours();
            const mode = (h >= 7 && h < 19) ? "day" : "night";
            const u = new URL(window.parent.location.href);
            if (u.searchParams.get("biq_mode") !== mode) {
              u.searchParams.set("biq_mode", mode);
              window.parent.location.replace(u.toString());
            }
          } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )


def _theme_from_mode() -> str:
    mode = st.query_params.get("biq_mode", "")
    if isinstance(mode, list):
        mode = mode[0] if mode else ""
    if mode == "day":
        return DAY_THEME
    if mode == "night":
        return NIGHT_THEME

    # Fallback for first server render before browser script syncs param.
    return DAY_THEME if 7 <= datetime.now().hour < 19 else NIGHT_THEME


def get_theme() -> str:
    """Return active auto theme (browser-local day/night via query param)."""
    return _theme_from_mode()


def render_theme_picker() -> None:
    """Deprecated: theme picker removed in favor of browser-time auto theme."""
    return


def _build_theme_css(t: dict) -> str:
    """Generate CSS custom-property + override block for a theme dict."""
    return f"""
<style>
/* ── BullzIQ Theme ───────────────────────────────────────────────────────── */
:root {{
    --biq-bg:      {t['bg']};
    --biq-bg2:     {t['bg2']};
    --biq-bg3:     {t['bg3']};
    --biq-text:    {t['text']};
    --biq-muted:   {t['muted']};
    --biq-border:  {t['border']};
    --biq-accent:  {t['accent']};
    --biq-accent2: {t['accent2']};
    --biq-pos:     {t['pos']};
    --biq-neg:     {t['neg']};
    --biq-tab:     {t['tab']};
    --biq-sidebar: {t['sidebar']};
}}

/* App background */
.stApp, .stApp > * {{ background-color: var(--biq-bg) !important; }}
.block-container {{ background: transparent !important; max-width: 1200px; }}

/* Main text */
p, span, li,
.stMarkdown p, .stMarkdown li, .stMarkdown span,
[data-testid="stMarkdownContainer"] p {{ color: var(--biq-text) !important; }}
h1, h2, h3, h4, h5 {{ color: var(--biq-text) !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background-color: var(--biq-sidebar) !important;
    border-right: 1px solid var(--biq-border) !important;
}}
[data-testid="stSidebar"] label {{ color: var(--biq-muted) !important; font-size: 0.8rem; }}

/* Metric cards */
[data-testid="metric-container"] {{
    background: var(--biq-bg2) !important;
    border: 1px solid var(--biq-border) !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
}}
[data-testid="metric-container"] label {{
    color: var(--biq-muted) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
[data-testid="metric-container"] [data-testid="stMetricValue"] {{
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: var(--biq-text) !important;
}}

/* Horizontal rule */
hr {{ border-color: var(--biq-border) !important; }}

/* Tabs */
[data-testid="stTabs"] [role="tablist"] {{
    border-bottom: 1px solid var(--biq-border) !important;
}}
[data-testid="stTabs"] [role="tab"] {{ color: var(--biq-muted) !important; }}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {{
    color: var(--biq-tab) !important;
    border-bottom: 2px solid var(--biq-tab) !important;
    font-weight: 600 !important;
}}

/* Inputs */
[data-baseweb="input"] input,
[data-baseweb="select"] > div,
[data-baseweb="textarea"] textarea {{
    background-color: var(--biq-bg2) !important;
    color: var(--biq-text) !important;
    border-color: var(--biq-border) !important;
}}

/* Buttons */
[data-testid="baseButton-primary"] {{
    background: var(--biq-accent) !important;
    color: #ffffff !important;
    border: none !important;
}}

/* DataFrame / tables */
[data-testid="stDataFrame"],
[data-testid="stTable"] {{
    border: 1px solid var(--biq-border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}}
[data-testid="stDataFrame"] * {{
    color: var(--biq-text) !important;
}}
[data-testid="stDataFrame"] [role="grid"],
[data-testid="stDataFrame"] [role="table"],
[data-testid="stTable"] table {{
    background: var(--biq-bg2) !important;
}}

/* Plotly readability */
.js-plotly-plot .xtick text,
.js-plotly-plot .ytick text,
.js-plotly-plot .gtitle,
.js-plotly-plot .xtitle,
.js-plotly-plot .ytitle,
.js-plotly-plot .legend text,
.js-plotly-plot .annotation-text {{
    fill: var(--biq-text) !important;
}}
.js-plotly-plot .gridlayer path {{
    stroke: var(--biq-border) !important;
    stroke-opacity: 1 !important;
}}
.js-plotly-plot .modebar {{
    display: none !important;
}}

/* Hide default Streamlit chrome */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1rem; padding-bottom: 0; }}

/* ── BullzIQ component styles ──────────────────────────────────────────── */

.edge-high {{
    background: rgba(63,185,80,0.15); color: var(--biq-pos);
    border: 1px solid var(--biq-pos); border-radius: 20px;
    padding: 3px 10px; font-size: 0.78rem; font-weight: 700;
}}
.edge-med {{
    background: rgba(240,165,0,0.12); color: #f0a500;
    border: 1px solid #f0a500; border-radius: 20px;
    padding: 3px 10px; font-size: 0.78rem; font-weight: 700;
}}
.edge-low {{
    background: rgba(139,148,158,0.12); color: var(--biq-muted);
    border: 1px solid var(--biq-muted); border-radius: 20px;
    padding: 3px 10px; font-size: 0.78rem; font-weight: 600;
}}
.edge-none {{
    background: transparent; color: var(--biq-muted);
    border: 1px solid var(--biq-border); border-radius: 20px;
    padding: 3px 10px; font-size: 0.78rem;
}}
.conf-high {{ color: var(--biq-pos); font-weight: 700; }}
.conf-med  {{ color: #f0a500; font-weight: 700; }}
.conf-low  {{ color: var(--biq-muted); font-weight: 600; }}
.steam-badge {{
    background: rgba(248,81,73,0.15); color: var(--biq-neg);
    border: 1px solid var(--biq-neg); border-radius: 20px;
    padding: 3px 10px; font-size: 0.78rem; font-weight: 700;
}}
.rg-banner {{
    background: var(--biq-bg2); border-left: 3px solid var(--biq-accent);
    border-radius: 0 6px 6px 0; padding: 10px 14px;
    font-size: 0.8rem; color: var(--biq-muted); margin: 8px 0;
}}
.affiliate-notice {{
    background: transparent; border: 1px solid var(--biq-border);
    border-radius: 6px; padding: 8px 12px;
    font-size: 0.75rem; color: var(--biq-muted); margin: 4px 0;
}}
.tourn-card {{
    background: var(--biq-bg2); border: 1px solid var(--biq-border);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 12px;
}}
.tourn-tier-1 {{ border-left: 3px solid var(--biq-accent); }}
.tourn-tier-2 {{ border-left: 3px solid #f0a500; }}
.tourn-tier-3 {{ border-left: 3px solid var(--biq-accent2); }}
.odds-positive {{ color: var(--biq-pos); font-weight: 700; font-size: 1.1rem; }}
.odds-negative {{ color: var(--biq-neg); font-weight: 700; font-size: 1.1rem; }}
.odds-neutral  {{ color: var(--biq-text); font-weight: 700; font-size: 1.1rem; }}

/* Page footer */
.biq-footer {{
    margin-top: 3rem; padding: 1.4rem 1rem 1rem;
    border-top: 1px solid var(--biq-border);
    text-align: center; color: var(--biq-muted);
    font-size: 0.73rem; line-height: 1.8;
}}
.biq-footer a {{ color: var(--biq-accent2) !important; text-decoration: none; }}
</style>
"""


def inject_css(theme_name: str | None = None) -> None:
    """Inject theme CSS into the current page. Call once per page render."""
    _sync_browser_time_mode()
    if theme_name is None:
        theme_name = get_theme()
    cfg = THEME_CONFIGS.get(theme_name, THEME_CONFIGS[DEFAULT_THEME])
    st.markdown(_build_theme_css(cfg), unsafe_allow_html=True)


def theme_colors(theme_name: str | None = None) -> dict[str, str]:
    """Return resolved color tokens for the active theme."""
    if theme_name is None:
        theme_name = get_theme()
    return THEME_CONFIGS.get(theme_name, THEME_CONFIGS[DEFAULT_THEME]).copy()


def chart_style(theme_name: str | None = None) -> dict[str, str]:
    """Return Plotly-friendly style tokens for the active theme."""
    if theme_name is None:
        theme_name = get_theme()
    t = theme_colors(theme_name)
    return {
        "template": "plotly_dark" if _is_dark_theme(theme_name) else "plotly_white",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "grid": t["border"],
        "text": t["text"],
        "muted": t["muted"],
        "accent": t["accent"],
        "accent2": t["accent2"],
        "pos": t["pos"],
        "neg": t["neg"],
    }


def themed_dataframe(
    df,
    *,
    hide_index: bool = True,
    width: str = "stretch",
    height: int | None = None,
) -> None:
    """Render a dataframe with explicit theme-consistent cell colors."""
    t = theme_colors()
    data = df.data if hasattr(df, "data") else df
    table_html = data.to_html(index=not hide_index, escape=False, border=0)

    wrap_width_style = "width: 100%;" if width == "stretch" else "width: fit-content;"
    table_width_style = "width: 100%;" if width == "stretch" else "width: auto;"
    height_style = f"max-height: {height}px;" if height is not None else ""

    st.markdown(
        f"""
<style>
.biq-table-wrap {{
    {wrap_width_style}
    {height_style}
    overflow: auto;
    border: 1px solid {t['border']};
    border-radius: 10px;
    background: {t['bg2']};
}}
.biq-table-wrap table {{
    border-collapse: collapse;
    {table_width_style}
    color: {t['text']};
    background: {t['bg2']};
    font-size: 0.95rem;
}}
.biq-table-wrap thead th {{
    position: sticky;
    top: 0;
    z-index: 1;
    background: {t['bg3']};
    color: {t['text']};
    border: 1px solid {t['border']};
    text-align: left;
    padding: 8px 10px;
    font-weight: 600;
}}
.biq-table-wrap tbody td {{
    background: {t['bg2']};
    color: {t['text']};
    border: 1px solid {t['border']};
    padding: 8px 10px;
}}
.biq-table-wrap tbody tr:hover td {{
    background: {t['bg3']};
}}
</style>
<div class="biq-table-wrap">{table_html}</div>
        """,
        unsafe_allow_html=True,
    )


# ── Display helpers ────────────────────────────────────────────────────────────

def nat_flag(nat: str) -> str:
    flags = {
        "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "WAL": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "NED": "🇳🇱", "BEL": "🇧🇪", "AUS": "🇦🇺",
        "POR": "🇵🇹", "IRL": "🇮🇪", "GER": "🇩🇪",
        "USA": "🇺🇸", "NZL": "🇳🇿", "CAN": "🇨🇦",
    }
    return flags.get(nat, "🌍")


def format_american_odds(odds: int) -> str:
    if odds == 0:
        return "N/A"
    return f"+{odds}" if odds > 0 else str(odds)


def edge_badge_html(edge_pct: float) -> str:
    if edge_pct >= 4:
        cls = "edge-high"
    elif edge_pct >= 2:
        cls = "edge-med"
    elif edge_pct > 0:
        cls = "edge-low"
    else:
        cls = "edge-none"
    sign = "+" if edge_pct > 0 else ""
    return f'<span class="{cls}">{sign}{edge_pct:.1f}% Edge</span>'


def confidence_badge_html(conf: str) -> str:
    mapping = {
        "high":   ("conf-high", "● HIGH"),
        "medium": ("conf-med",  "● MED"),
        "low":    ("conf-low",  "● LOW"),
    }
    cls, label = mapping.get(conf, ("conf-low", "● LOW"))
    return f'<span class="{cls}">{label}</span>'
