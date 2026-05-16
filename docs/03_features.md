# 03 — Site Features & User Flows

## Page Map (Streamlit Pages)

```
app.py                      Home — live event banner, today's picks, top movers
pages/1_Tournaments.py      All DK-covered tournaments with schedules
pages/2_Players.py          Player index + profile browser (selectbox to drill in)
pages/3_Matches.py          Match center (pre-match analysis + live scores)
pages/4_Picks.py            Today's model picks with edge % and filter slider
pages/5_Odds.py             Live odds tracker with line movement chart
pages/6_Tools.py            Edge calculator, H2H tool, 180s over/under calc
```

Each page is a self-contained Python file. Navigation is handled by Streamlit's built-in sidebar page list.

---

## Feature 1 — Match Center (`pages/3_Matches.py`)

The most important page. Every DK-covered match needs one.

```python
# components/match_center.py
import streamlit as st
import plotly.graph_objects as go
from db.queries import get_match, get_odds_history, get_h2h_history
from models.props_model import calculate_edge

def render_match_center(match_id: int):
    match    = get_match(match_id)
    odds_hist = get_odds_history(match_id)
    h2h      = get_h2h_history(match["player1_id"], match["player2_id"])

    latest_odds = odds_hist[-1] if odds_hist else None
    model_prob  = match.get("model_prob_p1")

    if model_prob and latest_odds:
        edge = calculate_edge(model_prob, latest_odds["price"])
        if edge["has_edge"]:
            pick_name = match["player1"] if edge["edge_side"] == "p1" else match["player2"]
            st.success(
                f"**Model Pick: {pick_name}** — {edge['edge_pct']:.1f}% edge  "
                f"(Our prob: {edge['our_prob']*100:.1f}% vs DK implied: {edge['dk_implied']*100:.1f}%)"
            )

    # Stat comparison bars
    st.subheader("Key Stats")
    cols = st.columns(3)
    stats = [
        ("3-dart avg (last 20)", match["avg1_recent"], match["avg2_recent"]),
        ("Checkout %",           match["co_pct1"],      match["co_pct2"]),
        ("180s per leg",         match["rate_180_1"],   match["rate_180_2"]),
    ]
    for col, (label, v1, v2) in zip(cols, stats):
        with col:
            st.metric(f"{match['player1']}", f"{v1:.2f}")
            st.caption(label)
            st.metric(f"{match['player2']}", f"{v2:.2f}")

    # H2H history
    st.subheader(f"H2H History ({len(h2h)} meetings)")
    if h2h:
        import pandas as pd
        df = pd.DataFrame(h2h)[["year", "tournament", "round", "score1", "score2", "winner"]]
        st.dataframe(df, hide_index=True, use_container_width=True)

    # Odds movement chart
    if odds_hist:
        render_odds_chart(odds_hist, match["player1"], match["player2"])

    # 180s prop calculator embedded
    st.subheader("180s Calculator")
    render_180s_calc(
        p1_rate=match.get("rate_180_1", 0.10),
        p2_rate=match.get("rate_180_2", 0.10),
        legs_to_win=match.get("legs_to_win", 6),
    )

    st.caption(
        "21+ only where legal. Model outputs are informational, not betting advice. "
        "Gambling problem? Call 1-800-GAMBLER."
    )
```

---

## Feature 2 — Player Profile (`pages/2_Players.py`)

```python
# components/player_profile.py
import streamlit as st
import plotly.express as px
from db.queries import get_player, get_player_stats, get_elo_history, get_recent_matches

def render_player_profile(slug: str):
    player     = get_player(slug)
    stats      = get_player_stats(player["id"])
    elo_hist   = get_elo_history(player["id"])
    recent     = get_recent_matches(player["id"], limit=20)

    if not player:
        st.error("Player not found.")
        return

    # Header
    col1, col2 = st.columns([1, 3])
    with col1:
        st.metric("Elo Rating", f"{stats['elo']:.0f}", delta=f"#{stats['elo_rank']} ranked")
    with col2:
        st.subheader(f"{player['name']} — \"{player.get('nickname', '')}\"")
        st.caption(f"{player.get('nationality', '')} · PDC Tour")

    # Stat cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Career avg", f"{stats['career_avg']:.2f}")
    c2.metric("Checkout %", f"{stats['checkout_pct']*100:.1f}%")
    c3.metric("180s/leg",   f"{stats['avg_180s_per_leg']:.3f}")
    c4.metric("DK win rate", f"{stats['dk_win_rate']*100:.1f}%")

    # Elo history chart
    import pandas as pd
    df_elo = pd.DataFrame(elo_hist)
    fig = px.line(df_elo, x="recorded_at", y="rating",
                  title="Elo Rating History", template="plotly_dark",
                  color_discrete_sequence=["#f0a500"])
    fig.update_layout(xaxis_title="", yaxis_title="Elo")
    st.plotly_chart(fig, use_container_width=True)

    # Recent matches table
    st.subheader("Last 20 Matches")
    df_m = pd.DataFrame(recent)[["match_date", "tournament", "round", "opponent", "score", "result"]]
    st.dataframe(df_m, hide_index=True, use_container_width=True)
```

---

## Feature 3 — Picks Feed (`pages/4_Picks.py`)

```python
# pages/4_Picks.py
import streamlit as st
from db.queries import get_todays_picks

st.set_page_config(page_title="Today's Picks | Darts Analytics", layout="wide")
st.title("Today's Model Picks")
st.caption(
    ":orange[Model output only. Not betting advice.] "
    "21+ only where legal. Gambling problem? Call 1-800-GAMBLER."
)

min_edge = st.slider("Minimum edge %", 0, 10, 2) / 100
market   = st.selectbox("Market", ["All", "H2H", "180s Over", "180s Under"])

picks = get_todays_picks(min_edge=min_edge, market=None if market == "All" else market)

if not picks:
    st.info("No picks meet the threshold today.")
    st.stop()

for pick in picks:
    conf_color = "green" if pick["edge_pct"] >= 5 else ("orange" if pick["edge_pct"] >= 2 else "gray")
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 2])
        c1.write(f"**{pick['pick']}** to beat **{pick['opponent']}**")
        c1.caption(f"{pick['tournament']} · {pick['round']}")
        c2.metric("DK Odds",  f"{pick['dk_odds']:+d}")
        c3.metric("Our Prob", f"{pick['our_prob']*100:.1f}%")
        c4.metric("Edge", f":{conf_color}[{pick['edge_pct']:.1f}%]")

        with st.expander("Why this pick?"):
            for reason in pick["reasoning"]:
                st.write(f"- {reason}")
```

---

## Feature 4 — Odds Movement Chart (`components/odds_chart.py`)

```python
# components/odds_chart.py
import streamlit as st
import plotly.graph_objects as go

def render_odds_chart(snapshots: list[dict], p1_name: str, p2_name: str):
    times  = [s["snapshot_time"] for s in snapshots]
    p1_imp = [s["p1_implied"] * 100 for s in snapshots]
    p2_imp = [s["p2_implied"] * 100 for s in snapshots]

    opening = p1_imp[0]
    current = p1_imp[-1]
    shift   = current - opening

    if abs(shift) >= 3:
        direction = p1_name if shift > 0 else p2_name
        st.warning(f"🔥 Steam move detected: {direction} moved {abs(shift):.1f}pp implied")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=times, y=p1_imp, name=p1_name, line=dict(color="#f0a500")))
    fig.add_trace(go.Scatter(x=times, y=p2_imp, name=p2_name, line=dict(color="#58a6ff")))
    fig.add_hline(y=50, line_dash="dash", line_color="#8b949e")
    fig.update_layout(
        title="Line Movement",
        template="plotly_dark",
        xaxis_title="",
        yaxis_title="Implied Win %",
        yaxis=dict(range=[0, 100]),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Opening: {opening:.1f}% → Current: {current:.1f}% ({shift:+.1f}pp)")
```

---

## Feature 5 — 180s Calculator (`pages/6_Tools.py`)

```python
# Inside pages/6_Tools.py
import streamlit as st
import math

def render_180s_calc(p1_rate: float = 0.12, p2_rate: float = 0.10, legs_to_win: int = 6):
    st.subheader("180s Over/Under Calculator")

    c1, c2, c3 = st.columns(3)
    p1_rate    = c1.number_input("P1 — 180s per leg", value=p1_rate, min_value=0.0, max_value=0.5, step=0.005, format="%.3f")
    p2_rate    = c2.number_input("P2 — 180s per leg", value=p2_rate, min_value=0.0, max_value=0.5, step=0.005, format="%.3f")
    legs_to_win = c3.number_input("Legs to win", value=legs_to_win, min_value=2, max_value=13, step=1)
    dk_line    = st.number_input("DraftKings total line", value=10.5, step=0.5)

    expected_legs   = legs_to_win * 1.6
    combined_lambda = (p1_rate + p2_rate) * expected_legs

    prob_over  = 1 - poisson_cdf(math.floor(dk_line), combined_lambda)
    prob_under = 1 - prob_over

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Expected 180s", f"{combined_lambda:.1f}")
    r2.metric("Prob OVER",     f"{prob_over*100:.1f}%")
    r3.metric("Fair OVER odds", to_american(prob_over))
    r4.metric("Fair UNDER odds", to_american(prob_under))

def poisson_cdf(k: int, lam: float) -> float:
    total, term = 0.0, math.exp(-lam)
    for i in range(k + 1):
        total += term
        term  *= lam / (i + 1)
    return total

def to_american(prob: float) -> str:
    if prob >= 0.5:
        return f"-{round((prob / (1 - prob)) * 100)}"
    return f"+{round(((1 - prob) / prob) * 100)}"
```

---

## Feature 6 — Tournament Hub (`pages/1_Tournaments.py`)

```python
# pages/1_Tournaments.py
import streamlit as st
import pandas as pd
from db.queries import get_tournaments, get_tournament_schedule

st.set_page_config(page_title="Tournaments | Darts Analytics", layout="wide")
st.title("DraftKings-Covered Tournaments")

tournaments = get_tournaments(dk_covered_only=True)
selected    = st.selectbox("Select tournament", [t["name"] for t in tournaments])
t           = next(x for x in tournaments if x["name"] == selected)

col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Format",   t["format"])
    st.metric("Legs/Sets to win", t.get("legs_to_win") or t.get("sets_to_win"))
    st.metric("Category", t["category"])

with col2:
    schedule = get_tournament_schedule(t["id"])
    if schedule:
        df = pd.DataFrame(schedule)
        st.dataframe(df[["match_date", "round", "player1", "player2", "score1", "score2"]],
                     hide_index=True, use_container_width=True)
    else:
        st.info("No upcoming matches found for this tournament.")
```

---

## Feature Priority Matrix (MVP vs Later)

| Feature | MVP | V2 | V3 |
|---------|-----|----|-----|
| Player profiles with Elo chart | ✓ | | |
| Match center (pre-match analysis) | ✓ | | |
| Today's picks feed | ✓ | | |
| 180s calculator tool | ✓ | | |
| Tournament hub pages | ✓ | | |
| Odds movement chart | ✓ | | |
| H2H comparison tool | ✓ | | |
| Live scores polling (during events) | | ✓ | |
| Email / push alerts for picks | | ✓ | |
| Prop model (checkout %) | | ✓ | |
| Steam move detection | | ✓ | |
| User accounts + bet tracking | | | ✓ |
| Fantasy darts integration | | | ✓ |
| In-play betting signals | | | ✓ |