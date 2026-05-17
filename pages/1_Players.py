"""
pages/1_Players.py — Player profiles, Elo rankings, H2H.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import inject_css, get_theme, chart_style, themed_dataframe, nat_flag, format_american_odds
from components.disclaimers import page_footer
from db.queries import (
    get_all_players,
    get_player_by_name,
    get_player_stats_cache,
    get_elo_history,
    get_player_match_history,
    get_h2h,
)


def _num(v, default: float = 0.0) -> float:
    """Safe numeric conversion for DB values that may be None/empty."""
    n = pd.to_numeric(v, errors="coerce")
    if pd.isna(n):
        return default
    return float(n)


inject_css(get_theme())
chart = chart_style()

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("## 🎯 Player Profiles & Rankings")
st.caption("PDC player Elo ratings, career stats, form, and head-to-head records.")
st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_rankings, tab_profile, tab_h2h = st.tabs(["🏆 Rankings", "👤 Player Profile", "⚔️ Head-to-Head"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — RANKINGS
# ════════════════════════════════════════════════════════════════════════════════
with tab_rankings:
    st.markdown("### BullzIQ Elo Rankings")

    players = get_all_players()
    if not players:
        st.warning("No player data. Ensure the database is seeded.")
        st.stop()

    df = pd.DataFrame(players)
    df["rank"] = range(1, len(df) + 1)
    df["flag"] = df["nationality"].apply(nat_flag)
    df["win_rate_pct"] = (pd.to_numeric(df["win_rate_last20"], errors="coerce") * 100).round(1).fillna(0).astype(str) + "%"
    df["checkout_pct_fmt"] = (pd.to_numeric(df["checkout_pct"], errors="coerce") * 100).round(1).fillna(0).astype(str) + "%"
    df["elo_fmt"] = pd.to_numeric(df["elo"], errors="coerce").fillna(1500).round(0).astype(int)

    # Elo bar chart — top 16
    top16 = df.head(16)
    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(
        y=top16["name"][::-1],
        x=top16["elo_fmt"][::-1],
        orientation="h",
        marker_color=chart["accent"],
        text=top16["elo_fmt"][::-1],
        textposition="outside",
    ))
    fig_rank.update_layout(
        template=chart["template"],
        paper_bgcolor=chart["paper_bgcolor"],
        plot_bgcolor=chart["plot_bgcolor"],
        font=dict(color=chart["text"]),
        height=520,
        margin=dict(l=10, r=60, t=20, b=10),
        xaxis=dict(showgrid=True, gridcolor=chart["grid"], title="Elo Rating"),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    # Full rankings table
    st.markdown("#### Full Rankings Table")
    display_cols = {
        "rank": "Rank",
        "flag": "🏳",
        "name": "Player",
        "nickname": "Nickname",
        "elo_fmt": "Elo",
        "avg_3dart": "3-Dart Avg",
        "checkout_pct_fmt": "Checkout %",
        "win_rate_pct": "Win Rate (L20)",
        "pdc_ranking": "PDC Rank",
    }
    themed_dataframe(
        df[list(display_cols.keys())].rename(columns=display_cols),
        hide_index=True,
        use_container_width=True,
        height=500,
    )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — PLAYER PROFILE
# ════════════════════════════════════════════════════════════════════════════════
with tab_profile:
    players_list = get_all_players()
    player_names = [p["name"] for p in players_list]

    selected_player = st.selectbox("Select a player", player_names, key="profile_select")
    player = get_player_by_name(selected_player)

    if not player:
        st.warning("Player not found.")
        st.stop()

    stats = get_player_stats_cache(player["id"])
    elo_hist = get_elo_history(player["id"])
    match_hist = get_player_match_history(player["id"], limit=20)

    # ── Header ──────────────────────────────────────────────────────────────────
    col_hdr, col_meta = st.columns([1, 3])
    with col_hdr:
        flag = nat_flag(player.get("nationality", ""))
        st.markdown(
            f"<div style='text-align:center; font-size:4rem;'>{flag}</div>"
            f"<div style='text-align:center; font-size:1.5rem; font-weight:700;'>{player['name']}</div>"
            f"<div style='text-align:center; color:var(--biq-muted);'>\"{player.get('nickname', '')}\"</div>",
            unsafe_allow_html=True,
        )
    with col_meta:
        mc1, mc2, mc3, mc4 = st.columns(4)
        with mc1:
            st.metric("Elo Rating", f"{int(player.get('elo', 1500)):,}")
        with mc2:
            st.metric("PDC Ranking", f"#{player.get('pdc_ranking', '—')}")
        with mc3:
            avg = _num(player.get("avg_3dart"), default=float("nan"))
            st.metric("3-Dart Avg", f"{avg:.2f}" if pd.notna(avg) else "—")
        with mc4:
            co = _num(player.get("checkout_pct"), default=float("nan"))
            st.metric("Checkout %", f"{co*100:.1f}%" if pd.notna(co) else "—")

    st.divider()

    # ── Elo chart ────────────────────────────────────────────────────────────────
    st.markdown("#### Elo Rating History")
    if not elo_hist.empty:
        fig_elo = go.Figure()
        fig_elo.add_trace(go.Scatter(
            x=elo_hist["recorded_at"],
            y=elo_hist["elo"],
            mode="lines",
            line=dict(color=chart["accent"], width=2),
            fill="tozeroy",
            fillcolor="rgba(0, 0, 0, 0)",
            name="Elo",
        ))
        # 1500 reference line
        fig_elo.add_hline(
            y=1500, line_dash="dot", line_color=chart["grid"],
            annotation_text="Baseline 1500", annotation_position="bottom right",
        )
        fig_elo.update_layout(
            template=chart["template"],
            paper_bgcolor=chart["paper_bgcolor"],
            plot_bgcolor=chart["plot_bgcolor"],
            font=dict(color=chart["text"]),
            height=300,
            margin=dict(l=10, r=10, t=10, b=30),
            xaxis=dict(showgrid=True, gridcolor=chart["grid"]),
            yaxis=dict(showgrid=True, gridcolor=chart["grid"], title="Elo"),
            showlegend=False,
        )
        st.plotly_chart(fig_elo, use_container_width=True)
    else:
        st.info("No Elo history available for this player.")

    # ── Stats detail ─────────────────────────────────────────────────────────────
    if stats:
        st.markdown("#### Detailed Stats")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            st.metric("Win Rate (L20)", f"{round(_num(stats.get('win_rate_last20')) * 100, 1)}%")
            st.metric("PL Win Rate", f"{round(_num(stats.get('win_rate_premier_league')) * 100, 1)}%")
        with sc2:
            st.metric("3-Dart Avg (L10)", f"{_num(stats.get('avg_3dart_last10')):.2f}")
            st.metric("Checkout % (L10)", f"{round(_num(stats.get('checkout_pct_last10')) * 100, 1)}%")
        with sc3:
            st.metric("Avg 180s/Match (L10)", f"{_num(stats.get('avg_180s_last10')):.2f}")
            streak = stats.get("form_streak", "—")
            streak_colored = "".join(
                f"<span style='color:{'var(--biq-pos)' if c == 'W' else 'var(--biq-neg)'};'>{c}</span>"
                for c in streak
            )
            st.markdown(
                f"**Form (last 5):** {streak_colored}",
                unsafe_allow_html=True,
            )

    # ── Recent matches ────────────────────────────────────────────────────────────
    st.markdown("#### Recent Matches (Last 20)")
    if not match_hist.empty:
        match_hist["result_colored"] = match_hist["result"].apply(
            lambda r: f"🟢 {r}" if r == "W" else f"🔴 {r}"
        )
        display = match_hist[["date", "opponent", "score", "result_colored", "avg", "checkout_pct", "180s"]].copy()
        display.columns = ["Date", "Opponent", "Score", "Result", "Avg", "Checkout%", "180s"]
        if "Avg" in display.columns:
            display["Avg"] = pd.to_numeric(display["Avg"], errors="coerce").round(2)
        if "Checkout%" in display.columns:
            display["Checkout%"] = (pd.to_numeric(display["Checkout%"], errors="coerce") * 100).round(1)
            display["Checkout%"] = display["Checkout%"].fillna(0).astype(str) + "%"
        themed_dataframe(display, hide_index=True, use_container_width=True)
    else:
        st.info("No match history available.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — HEAD-TO-HEAD
# ════════════════════════════════════════════════════════════════════════════════
with tab_h2h:
    st.markdown("### Head-to-Head Comparison")

    all_players = get_all_players()
    player_names = [p["name"] for p in all_players]

    col_p1, _, col_p2 = st.columns([2, 0.5, 2])
    with col_p1:
        p1_sel = st.selectbox("Player 1", player_names, index=0, key="h2h_p1")
    with _:
        st.markdown("<div style='text-align:center; margin-top:28px; font-size:1.4rem;'>vs</div>",
                    unsafe_allow_html=True)
    with col_p2:
        default_p2 = 1 if len(player_names) > 1 else 0
        p2_sel = st.selectbox("Player 2", player_names, index=default_p2, key="h2h_p2")

    if p1_sel == p2_sel:
        st.warning("Select two different players.")
    else:
        p1_data = get_player_by_name(p1_sel)
        p2_data = get_player_by_name(p2_sel)

        if p1_data and p2_data:
            # ── Stat comparison cards ────────────────────────────────────────────
            st.markdown("#### Stat Comparison")
            s1, _, s2 = st.columns([5, 0.5, 5])

            def _stat_bar(label: str, v1: float, v2: float, fmt: str = "{:.2f}") -> None:
                total = v1 + v2 if (v1 + v2) > 0 else 1
                pct1 = v1 / total
                pct2 = v2 / total
                with s1:
                    st.markdown(
                        f"<div style='text-align:right;'>{fmt.format(v1)}</div>",
                        unsafe_allow_html=True,
                    )
                with _:
                    st.markdown(
                        f"<div style='text-align:center; color:var(--biq-muted); font-size:0.75rem;'>{label}</div>",
                        unsafe_allow_html=True,
                    )
                with s2:
                    st.markdown(
                        f"<div style='text-align:left;'>{fmt.format(v2)}</div>",
                        unsafe_allow_html=True,
                    )

            # Player name headers
            with s1:
                flag1 = nat_flag(p1_data.get("nationality", ""))
                st.markdown(f"<h4 style='text-align:right;'>{flag1} {p1_sel}</h4>", unsafe_allow_html=True)
            with s2:
                flag2 = nat_flag(p2_data.get("nationality", ""))
                st.markdown(f"<h4>{flag2} {p2_sel}</h4>", unsafe_allow_html=True)

            _stat_bar("Elo Rating", p1_data.get("elo", 1500), p2_data.get("elo", 1500), "{:.0f}")
            _stat_bar("3-Dart Avg", p1_data.get("avg_3dart", 0), p2_data.get("avg_3dart", 0))
            _stat_bar(
                "Checkout %",
                p1_data.get("checkout_pct", 0) * 100,
                p2_data.get("checkout_pct", 0) * 100,
                "{:.1f}%",
            )
            _stat_bar(
                "180s/Leg",
                p1_data.get("avg_180s_per_leg", 0),
                p2_data.get("avg_180s_per_leg", 0),
                "{:.3f}",
            )

            # ── H2H history ──────────────────────────────────────────────────────
            st.markdown("#### Historical H2H Record")
            h2h_df = get_h2h(p1_data["id"], p2_data["id"])

            if h2h_df.empty:
                st.info("No head-to-head matches found between these two players.")
            else:
                p1_wins = h2h_df.attrs.get("p1_wins", 0)
                p2_wins = h2h_df.attrs.get("p2_wins", 0)
                total = p1_wins + p2_wins

                hw1, hw2, hw3 = st.columns(3)
                with hw1:
                    st.metric(f"{p1_sel} Wins", p1_wins, f"{round(p1_wins/total*100)}%" if total else "")
                with hw2:
                    st.metric("Total Meetings", total)
                with hw3:
                    st.metric(f"{p2_sel} Wins", p2_wins, f"{round(p2_wins/total*100)}%" if total else "")

                # Wins over time bar chart
                h2h_df["winner_name"] = h2h_df["winner_id"].apply(
                    lambda wid: p1_sel if wid == p1_data["id"] else p2_sel
                )
                h2h_df["color"] = h2h_df["winner_name"].apply(
                    lambda n: chart["accent"] if n == p1_sel else chart["accent2"]
                )

                themed_dataframe(
                    h2h_df[["date", "score", "winner_name", "avg_p1", "avg_p2"]].rename(columns={
                        "date": "Date", "score": "Score", "winner_name": "Winner",
                        "avg_p1": f"Avg {p1_sel}", "avg_p2": f"Avg {p2_sel}",
                    }),
                    hide_index=True,
                    use_container_width=True,
                )

page_footer()
