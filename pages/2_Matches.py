"""
pages/2_Matches.py — Match center: upcoming fixtures, recent results, match detail.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import inject_css, get_theme, chart_style, themed_dataframe, nat_flag, format_american_odds
from components.disclaimers import page_footer
from db.queries import (
    get_upcoming_matches,
    get_recent_results,
    get_current_odds,
    get_odds_history,
    get_all_players,
    get_player_by_name,
    get_h2h,
)

inject_css(get_theme())
chart = chart_style()

st.markdown("## 🎮 Match Center")
st.caption("Upcoming fixtures, live odds, match statistics, and historical results.")
st.divider()

tab_upcoming, tab_results, tab_detail = st.tabs(["📅 Upcoming", "📋 Recent Results", "🔍 Match Detail"])


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — UPCOMING MATCHES
# ════════════════════════════════════════════════════════════════════════════════
with tab_upcoming:
    st.markdown("### Upcoming PDC Fixtures")

    days = st.slider("Show matches over next N days", 1, 14, 7, key="upcoming_days")
    upcoming = get_upcoming_matches(days=days)
    odds_df = get_current_odds()

    if upcoming.empty:
        st.info("No upcoming matches in the database.")
    else:
        if not odds_df.empty:
            upcoming = upcoming.merge(
                odds_df[["match_id", "p1_odds", "p2_odds", "p1_implied", "p2_implied"]],
                on="match_id", how="left",
            )

        for tourn_name, group in upcoming.groupby("tournament"):
            st.markdown(f"#### {tourn_name}")

            for _, row in group.iterrows():
                with st.container(border=True):
                    dt = row.get("match_date")
                    time_str = dt.strftime("%a %b %d, %I:%M %p") if pd.notna(dt) else "TBD"
                    p1 = row.get("player1", "")
                    p2 = row.get("player2", "")
                    rnd = row.get("round")
                    rnd_str = rnd.strip() if isinstance(rnd, str) and rnd.strip() else "TBD"
                    legs = row.get("legs_to_win", 6)
                    p1_odds = row.get("p1_odds")
                    p2_odds = row.get("p2_odds")
                    p1_impl = row.get("p1_implied")
                    p2_impl = row.get("p2_implied")

                    c_time, c_p1, c_vs, c_p2, c_odds, c_format = st.columns([2, 2.5, 0.3, 2.5, 2, 1.5])

                    with c_time:
                        st.markdown(
                            f"<span style='color:var(--biq-muted); font-size:0.82rem;'>{time_str}</span><br>"
                            f"<span style='font-size:0.75rem; color:var(--biq-muted);'>{rnd_str}</span>",
                            unsafe_allow_html=True,
                        )
                    with c_p1:
                        p1_data = get_player_by_name(p1)
                        flag1 = nat_flag(p1_data.get("nationality", "") if p1_data else "")
                        st.markdown(f"{flag1} **{p1}**")
                        if p1_impl:
                            st.markdown(
                                f"<span style='color:var(--biq-muted); font-size:0.78rem;'>{round(p1_impl*100,1)}% implied</span>",
                                unsafe_allow_html=True,
                            )
                    with c_vs:
                        st.markdown("<div style='text-align:center; margin-top:8px; color:var(--biq-muted);'>vs</div>",
                                    unsafe_allow_html=True)
                    with c_p2:
                        p2_data = get_player_by_name(p2)
                        flag2 = nat_flag(p2_data.get("nationality", "") if p2_data else "")
                        st.markdown(f"{flag2} **{p2}**")
                        if p2_impl:
                            st.markdown(
                                f"<span style='color:var(--biq-muted); font-size:0.78rem;'>{round(p2_impl*100,1)}% implied</span>",
                                unsafe_allow_html=True,
                            )
                    with c_odds:
                        if pd.notna(p1_odds) and pd.notna(p2_odds):
                            o1 = format_american_odds(int(p1_odds))
                            o2 = format_american_odds(int(p2_odds))
                            clr1 = "var(--biq-pos)" if int(p1_odds) > 0 else "var(--biq-neg)"
                            clr2 = "var(--biq-pos)" if int(p2_odds) > 0 else "var(--biq-neg)"
                            st.markdown(
                                f"<span style='color:{clr1}; font-weight:700;'>{o1}</span>  "
                                f"<span style='color:var(--biq-muted);'>/</span>  "
                                f"<span style='color:{clr2}; font-weight:700;'>{o2}</span>",
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown("<span style='color:var(--biq-muted);'>Lines not open yet</span>",
                                        unsafe_allow_html=True)
                    with c_format:
                        st.markdown(
                            f"<span style='color:var(--biq-accent2); font-size:0.78rem;'>BO{legs*2-1}</span>",
                            unsafe_allow_html=True,
                        )

            st.markdown("")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — RECENT RESULTS
# ════════════════════════════════════════════════════════════════════════════════
with tab_results:
    st.markdown("### Recent Results")

    results_df = get_recent_results(limit=100)

    if results_df.empty:
        st.info("No results in the database.")
    else:
        # Filters
        col_tf, col_pf = st.columns(2)
        with col_tf:
            all_tourns = ["All"] + sorted(results_df["tournament"].unique().tolist())
            tourn_filter = st.selectbox("Filter by tournament", all_tourns, key="res_tourn")
        with col_pf:
            all_players_res = set(results_df["player1"].tolist() + results_df["player2"].tolist())
            player_filter = st.selectbox("Filter by player", ["All"] + sorted(all_players_res), key="res_player")

        filtered = results_df.copy()
        if tourn_filter != "All":
            filtered = filtered[filtered["tournament"] == tourn_filter]
        if player_filter != "All":
            filtered = filtered[
                (filtered["player1"] == player_filter) | (filtered["player2"] == player_filter)
            ]

        # Format for display
        filtered["date"] = pd.to_datetime(filtered["date"]).dt.strftime("%b %d, %Y")
        display_cols = ["date", "tournament", "round", "player1", "score", "player2", "winner"]
        themed_dataframe(
            filtered[display_cols].rename(columns={
                "date": "Date", "tournament": "Tournament", "round": "Round",
                "player1": "Player 1", "score": "Score", "player2": "Player 2",
                "winner": "Winner",
            }),
            hide_index=True,
            use_container_width=True,
            height=550,
        )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — MATCH DETAIL (odds movement for a selected upcoming match)
# ════════════════════════════════════════════════════════════════════════════════
with tab_detail:
    st.markdown("### Match Detail — Odds Movement")

    upcoming_detail = get_upcoming_matches(days=14)

    if upcoming_detail.empty:
        st.info("No upcoming matches available for detail view.")
    else:
        upcoming_detail["label"] = (
            upcoming_detail["player1"]
            + " vs "
            + upcoming_detail["player2"]
            + " — "
            + upcoming_detail["tournament"]
        )
        match_labels = upcoming_detail["label"].tolist()
        sel_label = st.selectbox("Select a match", match_labels, key="detail_match")

        sel_row = upcoming_detail[upcoming_detail["label"] == sel_label].iloc[0]
        match_id = int(sel_row["match_id"])
        p1 = sel_row["player1"]
        p2 = sel_row["player2"]

        odds_hist = get_odds_history(match_id)

        # ── Match header ──────────────────────────────────────────────────────
        st.markdown(f"#### {p1} vs {p2}")
        round_val = sel_row.get("round") if hasattr(sel_row, "get") else sel_row["round"]
        round_str = round_val.strip() if isinstance(round_val, str) and round_val.strip() else "TBD"
        st.caption(f"{sel_row['tournament']} · {round_str}")

        if not odds_hist.empty:
            # ── Odds movement chart ───────────────────────────────────────────
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p1_implied"] * 100,
                name=p1,
                mode="lines+markers",
                line=dict(color=chart["accent"], width=2),
                marker=dict(size=6),
            ))
            fig.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p2_implied"] * 100,
                name=p2,
                mode="lines+markers",
                line=dict(color=chart["accent2"], width=2),
                marker=dict(size=6),
            ))
            fig.add_hline(
                y=50, line_dash="dot", line_color=chart["grid"],
                annotation_text="50% line", annotation_position="bottom right",
            )
            fig.update_layout(
                title="DraftKings Implied Probability — 3-Hour Window",
                xaxis_title="Time",
                yaxis_title="Implied Probability (%)",
                template=chart["template"],
                paper_bgcolor=chart["paper_bgcolor"],
                plot_bgcolor=chart["plot_bgcolor"],
                font=dict(color=chart["text"]),
                height=380,
                margin=dict(l=10, r=10, t=50, b=40),
                legend=dict(orientation="h", y=-0.15),
                yaxis=dict(range=[0, 100], ticksuffix="%", gridcolor=chart["grid"]),
                xaxis=dict(gridcolor=chart["grid"]),
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Current odds detail ───────────────────────────────────────────
            latest = odds_hist.iloc[-1]
            opening = odds_hist.iloc[0]
            st.markdown("#### Line Movement Summary")
            sm1, sm2, sm3, sm4 = st.columns(4)
            with sm1:
                st.metric(
                    f"{p1} — Open",
                    format_american_odds(int(opening["p1_odds"])),
                )
            with sm2:
                st.metric(
                    f"{p1} — Current",
                    format_american_odds(int(latest["p1_odds"])),
                    delta=f"{int(latest['p1_odds']) - int(opening['p1_odds'])}",
                )
            with sm3:
                st.metric(
                    f"{p2} — Open",
                    format_american_odds(int(opening["p2_odds"])),
                )
            with sm4:
                st.metric(
                    f"{p2} — Current",
                    format_american_odds(int(latest["p2_odds"])),
                    delta=f"{int(latest['p2_odds']) - int(opening['p2_odds'])}",
                )
        else:
            st.info("No odds history available for this match.")

        # ── H2H preview ───────────────────────────────────────────────────────
        st.markdown("#### Historical Head-to-Head")
        from db.queries import get_player_by_name as gpbn
        p1_obj = gpbn(p1)
        p2_obj = gpbn(p2)
        if p1_obj and p2_obj:
            h2h_df = get_h2h(p1_obj["id"], p2_obj["id"])
            if h2h_df.empty:
                st.info("No previous meetings found.")
            else:
                p1_w = h2h_df.attrs.get("p1_wins", 0)
                p2_w = h2h_df.attrs.get("p2_wins", 0)
                hw1, hw2, hw3 = st.columns(3)
                with hw1:
                    st.metric(f"{p1} Wins", p1_w)
                with hw2:
                    st.metric("Total Meetings", p1_w + p2_w)
                with hw3:
                    st.metric(f"{p2} Wins", p2_w)

                themed_dataframe(
                    h2h_df[["date", "score", "winner_id"]].head(10),
                    hide_index=True,
                    use_container_width=True,
                )

page_footer()
