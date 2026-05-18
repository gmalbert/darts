# 04 — Design System

## Design Direction

**Aesthetic**: Dark, data-dense, editorial. Think Bloomberg Terminal meets FiveThirtyEight — serious numbers presented with confidence. Avoid generic sportsbook green/gold. Use deep navy + electric amber as primary palette. The site should feel like a quant built it, not a marketing team.

---

## Streamlit Theme (`.streamlit/config.toml`)

```toml
[theme]
base                     = "dark"
primaryColor             = "#f0a500"    # amber — darts bullseye gold
backgroundColor          = "#0d1117"   # near-black, not pure black
secondaryBackgroundColor = "#161b22"   # card/panel surface
textColor                = "#e6edf3"   # near-white primary text
font                     = "sans serif"
```

---

## Color Reference

| Token | Hex | Use |
|-------|-----|-----|
| Amber (primary) | `#f0a500` | Picks, edge highlights, key metrics |
| Amber dim | `#7d5600` | Muted amber backgrounds |
| Blue | `#58a6ff` | Links, secondary player color in charts |
| Edge positive | `#3fb950` | Positive edge values |
| Edge negative | `#f85149` | Negative edge / value warnings |
| Steam | `#f0a500` | Line movement alerts |
| Text primary | `#e6edf3` | Main content |
| Text secondary | `#8b949e` | Labels, captions |
| Text muted | `#484f58` | De-emphasized text |
| Surface | `#161b22` | Card / container background |
| Surface 2 | `#21262d` | Elevated surface |
| Border | `#30363d` | Subtle borders |

Use these in `st.markdown()` with inline styles or a custom CSS block injected via `st.html()` / `st.markdown("<style>...<style>", unsafe_allow_html=True)`.

---

## Custom CSS Injection

Inject a global stylesheet once in `app.py`:

```python
# app.py
import streamlit as st

def inject_styles():
    st.markdown("""
    <style>
    /* Monospace for odds and probabilities */
    .odds-value { font-family: 'JetBrains Mono', monospace; }

    /* Positive / negative edge colors */
    .edge-pos { color: #3fb950; font-weight: 600; }
    .edge-neg { color: #f85149; font-weight: 600; }
    .edge-neutral { color: #8b949e; }

    /* Steam badge */
    .steam-badge {
        background: #7d5600;
        color: #f0a500;
        border: 1px solid #f0a500;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Stat label — small uppercase */
    .stat-label {
        font-size: 0.6875rem;
        font-weight: 500;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #8b949e;
    }

    /* Hide Streamlit default menu/footer for cleaner look */
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)
```

---

## Layout Patterns

### Full-width data pages (Match Center, Picks)
```python
st.set_page_config(layout="wide")
```

### Stat columns (4-up for key metrics)
```python
c1, c2, c3, c4 = st.columns(4)
c1.metric("3-dart avg", "96.5")
c2.metric("Checkout %", "42.3%")
c3.metric("180s/leg",   "0.123")
c4.metric("Elo",        "1847")
```

### Head-to-head comparison
```python
def stat_bar(label: str, v1: float, v2: float, p1: str, p2: str, fmt: str = ".2f"):
    total = v1 + v2 or 1
    p1_pct = v1 / total * 100
    winner = p1 if v1 > v2 else p2
    cols = st.columns([3, 6, 3])
    cols[0].write(f"**{format(v1, fmt)}**" if v1 >= v2 else format(v1, fmt))
    cols[1].progress(int(p1_pct), text=label)
    cols[2].write(f"**{format(v2, fmt)}**" if v2 > v1 else format(v2, fmt))
```

### Container with border (Streamlit 1.30+)
```python
with st.container(border=True):
    st.write("Match card content here")
```

### Expander for secondary info
```python
with st.expander("Why this pick?"):
    for reason in pick["reasoning"]:
        st.write(f"- {reason}")
```

---

## Chart Style (Plotly)

All charts use `template="plotly_dark"` to match the dark theme, with amber as the primary series color:

```python
import plotly.express as px

def elo_chart(df):
    fig = px.line(
        df, x="recorded_at", y="rating",
        title="Elo Rating History",
        template="plotly_dark",
        color_discrete_sequence=["#f0a500"],
    )
    fig.update_layout(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        xaxis=dict(gridcolor="#30363d"),
        yaxis=dict(gridcolor="#30363d"),
        margin=dict(l=0, r=0, t=40, b=0),
    )
    st.plotly_chart(fig, width="stretch")
```

For H2H / odds movement (two series):
```python
color_discrete_sequence=["#f0a500", "#58a6ff"]   # amber = P1, blue = P2
```

---

## Typography Guidelines

- **Numbers / odds / probabilities**: use `st.code()` inline, or inject the `odds-value` CSS class via markdown — monospace reads better for data
- **Labels**: use `st.caption()` for secondary context below metrics
- **Warnings / alerts**: use `st.warning()` (steam moves), `st.success()` (model picks), `st.info()` (neutral)
- **Disclaimers**: always use `st.caption()` — keeps it visible but de-emphasized

---

## Page Header Pattern

```python
st.title("🎯 Darts Analytics")
st.caption("Model-driven picks and stats for DraftKings-covered PDC tournaments.")
st.divider()
```

## Responsible Gambling Footer Pattern

Include on every page that shows picks or odds:

```python
st.divider()
st.caption(
    "21+ only. Must be located in a jurisdiction where sports betting is legal. "
    "Model outputs are for informational purposes only — not betting advice. "
    "Gambling problem? Call 1-800-522-4700 or visit [ncpgambling.org](https://ncpgambling.org)."
)
```