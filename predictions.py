"""
predictions.py — BullzIQ entry point with st.navigation().

Run with: streamlit run predictions.py
"""

from __future__ import annotations
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ── Page config — called ONCE here; sub-pages must NOT call set_page_config ───
st.set_page_config(
    page_title="BullzIQ — PDC Darts Analytics",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Bootstrap DB (creates + seeds on first run) ───────────────────────────────
from db.seed import ensure_seeded
ensure_seeded()

# ── Shared components ─────────────────────────────────────────────────────────
from components.styles import (
    inject_css, get_theme, render_theme_picker,
    format_american_odds, edge_badge_html, confidence_badge_html,
)
from components.disclaimers import (
    rg_banner, affiliate_disclosure, model_disclaimer, dk_cta, page_footer,
)
from db.queries import (
    get_active_picks, get_upcoming_matches, get_recent_steam_events,
    get_model_record, get_current_odds,
)

LOGO_PATH = Path("data_files/logo.png")


# ── Card render helpers (defined before use) ──────────────────────────────────

def _render_pick_card(row: pd.Series) -> None:
    edge = row.get("edge_pct", 0)
    conf = row.get("confidence", "low")
    odds_str = format_american_odds(int(row.get("dk_odds", 0)))
    model_pct = round(row.get("model_prob", 0) * 100, 1)
    dk_pct = round(row.get("dk_implied", 0) * 100, 1)
    pick_name = row.get("pick", "")
    p1 = row.get("player1", "")
    p2 = row.get("player2", "")
    tourn = row.get("tournament", "")
    rnd = row.get("round", "")
    match_dt = row.get("match_date")
    time_str = match_dt.strftime("%I:%M %p") if pd.notna(match_dt) else ""
    reasoning = row.get("reasoning", "")

    with st.container(border=True):
        left_col, right_col = st.columns([3, 1])
        with left_col:
            st.markdown(
                f"**{p1}** vs **{p2}**  \n"
                f"<span style='color:var(--biq-muted); font-size:0.85rem;'>"
                f"{tourn} · {rnd} · {time_str}</span>",
                unsafe_allow_html=True,
            )
        with right_col:
            st.markdown(
                edge_badge_html(edge) + "&nbsp;&nbsp;" + confidence_badge_html(conf),
                unsafe_allow_html=True,
            )
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Pick", pick_name)
        with m2:
            st.metric("DK Odds", odds_str)
        with m3:
            st.metric("Model Prob", f"{model_pct}%")
        with m4:
            st.metric("DK Implied", f"{dk_pct}%")
        with st.expander("📖 Reasoning"):
            st.write(reasoning)
            dk_cta(int(row.get("dk_odds", 0)), f"{p1} vs {p2}")


def _render_schedule_row(row: pd.Series) -> None:
    dt = row.get("match_date")
    time_str = dt.strftime("%a %b %d · %I:%M %p") if pd.notna(dt) else "TBD"
    p1 = row.get("player1", "")
    p2 = row.get("player2", "")
    p1_odds = row.get("p1_odds")
    p2_odds = row.get("p2_odds")
    rnd = row.get("round", "")

    with st.container(border=True):
        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 0.3, 1.5, 1.5])
        with c1:
            st.markdown(
                f"<span style='color:var(--biq-muted); font-size:0.8rem;'>{time_str}</span><br>"
                f"<span style='font-size:0.78rem; color:var(--biq-muted);'>{rnd}</span>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(f"**{p1}**")
        with c3:
            st.markdown(
                "<div style='text-align:center; color:var(--biq-muted);'>vs</div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(f"**{p2}**")
        with c5:
            if pd.notna(p1_odds) and pd.notna(p2_odds):
                o1 = format_american_odds(int(p1_odds))
                o2 = format_american_odds(int(p2_odds))
                st.markdown(
                    f"<span style='color:var(--biq-accent2);'>{o1}</span> / "
                    f"<span style='color:var(--biq-accent2);'>{o2}</span>",
                    unsafe_allow_html=True,
                )


def _render_steam_row(row: pd.Series) -> None:
    direction = row.get("player_steamed", "")
    shift = row.get("shift_pct", 0)
    open_odds = format_american_odds(int(row.get("opening_odds", 0)))
    curr_odds = format_american_odds(int(row.get("current_odds", 0)))
    p1 = row.get("player1", "")
    p2 = row.get("player2", "")
    tourn = row.get("tournament", "")
    detected = row.get("detected_at")
    when_str = detected.strftime("%H:%M") if pd.notna(detected) else ""

    arrow = "▲" if shift > 0 else "▼"
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            st.markdown(
                f"**{p1} vs {p2}**  \n"
                f"<span style='color:var(--biq-muted); font-size:0.82rem;'>{tourn}</span>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<span class="steam-badge">{arrow} STEAM: {direction}</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<span style='color:var(--biq-muted); font-size:0.82rem;'>"
                f"{open_odds} → {curr_odds} "
                f"({'+' if shift > 0 else ''}{shift:.1f}pp)</span>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f"<span style='color:var(--biq-muted); font-size:0.8rem;'>{when_str}</span>",
                unsafe_allow_html=True,
            )


# ── Home page function ────────────────────────────────────────────────────────

def home_page() -> None:
    inject_css(get_theme())

    # Sidebar — logo + theme picker only
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=180)
        render_theme_picker()

    # Header — no logo, just title + tagline
    st.markdown(
        "<h1 style='font-size:2.2rem; font-weight:800; margin-bottom:2px;'>"
        "🎯 BullzIQ</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:var(--biq-muted); font-size:0.95rem; margin-top:0;'>"
        "Model-driven picks &nbsp;·&nbsp; Elo ratings &nbsp;·&nbsp; "
        "Live odds &nbsp;·&nbsp; PDC darts on DraftKings"
        "</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    # Top metrics row
    record = get_model_record(days=30)
    picks_df = get_active_picks(min_edge=0.0)
    picks_today = len(picks_df) if not picks_df.empty else 0
    best_edge = round(picks_df["edge_pct"].max(), 1) if not picks_df.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        win_pct = round(record["win_rate"] * 100, 1)
        st.metric("30-Day Record", f"{record['wins']}–{record['losses']}", f"{win_pct}% win rate")
    with c2:
        st.metric("Model ROI (30d)", f"+{record['roi_pct']}%", "vs. flat bet")
    with c3:
        st.metric("Active Picks Today", picks_today, "all matches")
    with c4:
        best_str = f"+{best_edge}%" if best_edge > 0 else f"{best_edge}%"
        st.metric("Best Edge Today", best_str, "vs. DraftKings line")

    st.divider()

    # Main tabs
    tab_picks, tab_schedule, tab_steam, tab_model, tab_history = st.tabs(
        ["🎯 Today's Picks", "📅 Schedule", "🔥 Steam Moves", "📊 Model Info", "📈 Historical"]
    )

    # ── TAB 1: TODAY'S PICKS ──────────────────────────────────────────────────
    with tab_picks:
        st.markdown("### Today's Model Picks")
        col_filter, col_sort = st.columns([2, 1])
        with col_filter:
            min_edge = st.slider(
                "Minimum edge %", 0.0, 8.0, 1.0, 0.5,
                help="Filter picks by minimum edge over DraftKings implied probability.",
            )
        with col_sort:
            sort_by = st.selectbox("Sort by", ["Edge %", "Match time", "Confidence"])

        filtered = get_active_picks(min_edge=min_edge)
        if filtered.empty:
            st.info("No picks meet the current edge filter. Lower the slider to see more.")
        else:
            if sort_by == "Match time":
                filtered = filtered.sort_values("match_date")
            elif sort_by == "Confidence":
                conf_order = {"high": 0, "medium": 1, "low": 2}
                filtered["conf_rank"] = filtered["confidence"].map(conf_order)
                filtered = filtered.sort_values("conf_rank")
            model_disclaimer(inline=True)
            st.markdown("")
            for _, row in filtered.iterrows():
                _render_pick_card(row)

    # ── TAB 2: SCHEDULE ───────────────────────────────────────────────────────
    with tab_schedule:
        st.markdown("### Upcoming PDC Matches (DraftKings covered)")
        days_ahead = st.slider("Days ahead", 1, 14, 7, key="sched_days")
        sched_df = get_upcoming_matches(days=days_ahead)
        odds_df = get_current_odds()

        if sched_df.empty:
            st.info("No upcoming matches in the database.")
        else:
            if not odds_df.empty:
                sched_df = sched_df.merge(
                    odds_df[["match_id", "p1_odds", "p2_odds"]],
                    on="match_id", how="left",
                )
            for tourn_name, group in sched_df.groupby("tournament"):
                st.markdown(f"#### {tourn_name}")
                for _, row in group.iterrows():
                    _render_schedule_row(row)
                st.markdown("")

    # ── TAB 3: STEAM MOVES ────────────────────────────────────────────────────
    with tab_steam:
        st.markdown("### 🔥 Steam Moves — Significant Line Movement")
        st.caption("Flagged when implied probability shifts ≥3pp within 30 minutes.")
        steam_df = get_recent_steam_events(hours=24)
        if steam_df.empty:
            st.info("No steam moves detected in the last 24 hours.")
        else:
            for _, row in steam_df.iterrows():
                _render_steam_row(row)

    # ── TAB 4: MODEL INFO ─────────────────────────────────────────────────────
    with tab_model:
        st.markdown("### How the Model Works")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                """
                #### Elo Rating System
                The base layer is a DartsElo model trained on PDC match history
                from **2015 to present**. Key adjustments:
                - **Tournament K-multipliers** — World Championship matches move
                  ratings 1.5× more than floor events.
                - **Margin of victory** — Winning 7–1 vs 7–6 has different impact.
                - **Format length** — Longer formats amplify the skill gap.

                #### Match Predictor
                A calibrated logistic regression adds feature signals on top of Elo:
                - Recent form (last 20 matches)
                - 3-dart average and checkout % differential
                - Head-to-head record (last 10 meetings)
                - Tournament-specific win rates
                - Ranking differential

                #### Edge Calculation
                Edge % = (Model Probability − DK Implied Probability) × 100.
                Picks with positive edge suggest the model sees value vs. the book.
                """,
            )
        with col_b:
            st.markdown("#### 30-Day Performance Summary")
            record30 = get_model_record(30)
            perf_data = {
                "Metric": ["Record", "Win Rate", "ROI", "Avg Edge", "Brier Score"],
                "Value": [
                    f"{record30['wins']}–{record30['losses']}",
                    f"{round(record30['win_rate'] * 100, 1)}%",
                    f"+{record30['roi_pct']}%",
                    f"+{record30['avg_edge']}%",
                    str(record30['brier_score']),
                ],
            }
            st.dataframe(pd.DataFrame(perf_data), hide_index=True, use_container_width=True)
            st.info(
                "**Brier Score**: Calibration metric (0 = perfect, 1 = worst). "
                "Industry benchmark for well-calibrated models ≈ 0.22."
            )
            picks_chart = get_active_picks(min_edge=-10.0)
            if not picks_chart.empty:
                fig_h = go.Figure(go.Histogram(
                    x=picks_chart["edge_pct"], nbinsx=20,
                    marker_color="#e10600", opacity=0.8,
                ))
                fig_h.update_layout(
                    title="Current Pick Edge Distribution",
                    xaxis_title="Edge %", yaxis_title="Count",
                    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)", height=260,
                    margin=dict(l=10, r=10, t=40, b=30),
                )
                st.plotly_chart(fig_h, use_container_width=True)

    # ── TAB 5: HISTORICAL ────────────────────────────────────────────────────
    with tab_history:
        _render_history_tab()

    page_footer()


def _render_history_tab() -> None:
    """Historical performance analytics — Elo trajectories + yearly breakdown."""
    from db.queries import get_all_players, get_elo_history, get_yearly_stats

    st.markdown("### 📈 Historical Model Performance (2015–Present)")
    st.caption(
        "Elo ratings and performance metrics built from 10+ years of PDC match data."
    )

    # ── Elo Trajectories ─────────────────────────────────────────────────────
    st.markdown("#### Elo Rating Trajectories")
    all_players = get_all_players()
    player_names = [p["name"] for p in all_players[:12]]  # top 12 for selector

    selected_players = st.multiselect(
        "Select players to compare",
        player_names,
        default=player_names[:5],
        key="hist_players",
    )

    if selected_players:
        fig_elo = go.Figure()
        palette = [
            "#e10600", "#58a6ff", "#3fb950", "#f0a500", "#a855f7",
            "#14b8a6", "#ec4899", "#f59e0b", "#6366f1", "#34d399",
            "#f87171", "#facc15",
        ]
        for i, pname in enumerate(selected_players):
            p_data = next((p for p in all_players if p["name"] == pname), None)
            if not p_data:
                continue
            elo_hist = get_elo_history(p_data["id"])
            if elo_hist.empty:
                continue
            df_elo = pd.DataFrame(elo_hist)
            df_elo["recorded_at"] = pd.to_datetime(df_elo["recorded_at"])
            df_elo = df_elo.sort_values("recorded_at")
            fig_elo.add_trace(go.Scatter(
                x=df_elo["recorded_at"],
                y=df_elo["elo"],
                name=pname,
                mode="lines",
                line=dict(color=palette[i % len(palette)], width=2),
            ))

        fig_elo.update_layout(
            xaxis_title="Date",
            yaxis_title="Elo Rating",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=380,
            margin=dict(l=10, r=10, t=20, b=40),
            legend=dict(orientation="h", y=-0.25),
        )
        st.plotly_chart(fig_elo, use_container_width=True)
    else:
        st.info("Select at least one player above to display Elo trajectories.")

    st.divider()

    # ── Year-by-year breakdown ────────────────────────────────────────────────
    st.markdown("#### Year-by-Year Match Volume & Model Accuracy")
    yearly = get_yearly_stats()

    if not yearly.empty:
        col_chart, col_table = st.columns([3, 2])
        with col_chart:
            fig_yr = go.Figure()
            fig_yr.add_trace(go.Bar(
                x=yearly["year"].astype(str),
                y=yearly["total_matches"],
                name="Total Matches",
                marker_color="#58a6ff",
                opacity=0.8,
            ))
            if "avg_elo_spread" in yearly.columns:
                fig_yr.add_trace(go.Scatter(
                    x=yearly["year"].astype(str),
                    y=yearly["avg_elo_spread"],
                    name="Avg Elo Spread",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color="#e10600", width=2),
                    marker=dict(size=6),
                ))
                fig_yr.update_layout(
                    yaxis2=dict(
                        title="Avg Elo Spread",
                        overlaying="y", side="right",
                        showgrid=False,
                    ),
                )

            fig_yr.update_layout(
                xaxis_title="Year",
                yaxis_title="Matches",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                margin=dict(l=10, r=10, t=20, b=40),
                barmode="group",
                legend=dict(orientation="h", y=-0.3),
            )
            st.plotly_chart(fig_yr, use_container_width=True)

        with col_table:
            display_cols = ["year", "total_matches"]
            if "avg_elo_spread" in yearly.columns:
                display_cols.append("avg_elo_spread")
            st.dataframe(
                yearly[display_cols].rename(columns={
                    "year": "Year",
                    "total_matches": "Matches",
                    "avg_elo_spread": "Avg Elo Δ",
                }),
                hide_index=True,
                use_container_width=True,
            )
    else:
        st.info("Seed the database to see historical breakdown.")

    st.divider()

    # ── Top performers by era ─────────────────────────────────────────────────
    st.markdown("#### Era Performance — Top Win Rates by Period")
    from db.queries import get_era_performance
    era_df = get_era_performance()
    if not era_df.empty:
        fig_era = go.Figure()
        eras = era_df["era"].unique()
        palette2 = ["#e10600", "#58a6ff", "#3fb950"]
        for j, era in enumerate(eras):
            sub = era_df[era_df["era"] == era].head(8)
            fig_era.add_trace(go.Bar(
                name=era,
                x=sub["player_name"],
                y=sub["win_rate"],
                marker_color=palette2[j % 3],
                opacity=0.85,
            ))
        fig_era.update_layout(
            barmode="group",
            xaxis_title="Player",
            yaxis_title="Win Rate",
            yaxis_tickformat=".0%",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
            margin=dict(l=10, r=10, t=20, b=80),
            legend=dict(title="Era", orientation="h", y=-0.4),
        )
        st.plotly_chart(fig_era, use_container_width=True)
    else:
        st.info("No era data available yet.")


# ── Navigation setup ──────────────────────────────────────────────────────────

pg = st.navigation(
    {
        "": [
            st.Page(home_page, title="Predictions", icon="🎯", default=True),
        ],
        "Analytics": [
            st.Page("pages/1_Players.py",     title="Players",     icon="👤"),
            st.Page("pages/2_Matches.py",     title="Matches",     icon="🎮"),
            st.Page("pages/3_Tournaments.py", title="Tournaments", icon="🏆"),
            st.Page("pages/4_Odds.py",        title="Odds",        icon="📊"),
            st.Page("pages/5_Tools.py",       title="Tools",       icon="🔧"),
        ],
    }
)
pg.run()
