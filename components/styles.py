"""
components/styles.py — Global CSS injection + theme system for BullzIQ.

Usage:
    inject_css(get_theme())    # in every page, before any st.* UI call
    render_theme_picker()       # in sidebar block

Themes are applied via CSS custom properties injected into the page.
"""

from __future__ import annotations
import streamlit as st

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
}

DEFAULT_THEME = "Dark (Default)"


def get_theme() -> str:
    """Return the active theme name from session state."""
    return st.session_state.get("biq_theme", DEFAULT_THEME)


def render_theme_picker() -> None:
    """Render the theme selector dropdown in the sidebar."""
    theme_names = list(THEME_CONFIGS.keys())
    current = get_theme()
    idx = theme_names.index(current) if current in theme_names else 0
    st.sidebar.selectbox(
        "Theme",
        theme_names,
        index=idx,
        key="biq_theme",
        help="Choose a colour scheme for the app.",
    )


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
    if theme_name is None:
        theme_name = get_theme()
    cfg = THEME_CONFIGS.get(theme_name, THEME_CONFIGS[DEFAULT_THEME])
    st.markdown(_build_theme_css(cfg), unsafe_allow_html=True)


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
