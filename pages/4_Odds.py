"""
pages/4_Odds.py — Live odds tracker, line movement, steam detection.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import inject_css, get_theme, chart_style, themed_dataframe, format_american_odds
from components.disclaimers import page_footer, dk_cta
from db.queries import (
    get_current_odds,
    get_upcoming_matches,
    get_odds_history,
    get_recent_steam_events,
)

inject_css(get_theme())
chart = chart_style()

st.markdown("## 📊 Odds Tracker")
st.caption("Live DraftKings moneylines, line movement, and steam detection for PDC events.")
st.divider()

tab_current, tab_movement, tab_steam = st.tabs(
    ["💰 Current Lines", "📈 Line Movement", "🔥 Steam Moves"]
)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — CURRENT LINES
# ════════════════════════════════════════════════════════════════════════════════
with tab_current:
    st.markdown("### Current DraftKings Lines")

    odds_df = get_current_odds()
    upcoming_df = get_upcoming_matches(days=7)

    if odds_df.empty:
        if upcoming_df.empty:
            st.info("No upcoming fixtures found in the next 7 days.")
        else:
            st.info(
                f"{len(upcoming_df)} upcoming fixture(s) found, but DraftKings moneylines are not posted yet."
            )
            st.caption("Odds will appear automatically when the sportsbook opens markets.")
    else:
        # Filter by tournament
        tourns = ["All"] + sorted(odds_df["tournament"].dropna().unique().tolist())
        sel_tourn = st.selectbox("Tournament", tourns, key="odds_tourn")

        display_df = odds_df.copy()
        if sel_tourn != "All":
            display_df = display_df[display_df["tournament"] == sel_tourn]

        for _, row in display_df.iterrows():
            p1 = row.get("player1", "")
            p2 = row.get("player2", "")
            p1_odds = row.get("p1_odds")
            p2_odds = row.get("p2_odds")
            p1_impl = row.get("p1_implied", 0)
            p2_impl = row.get("p2_implied", 0)
            tourn = row.get("tournament", "")
            dt = row.get("match_date")
            time_str = dt.strftime("%a %b %d, %I:%M %p") if pd.notna(dt) else "TBD"
            upd = row.get("updated")
            upd_str = upd.strftime("%H:%M") if pd.notna(upd) else ""

            with st.container(border=True):
                hdr, upd_col = st.columns([5, 1])
                with hdr:
                    st.markdown(
                        f"<span style='font-size:0.82rem; color:var(--biq-muted);'>{tourn} · {time_str}</span>",
                        unsafe_allow_html=True,
                    )
                with upd_col:
                    st.markdown(
                        f"<span style='font-size:0.75rem; color:var(--biq-muted);'>Updated {upd_str}</span>",
                        unsafe_allow_html=True,
                    )

                c_p1, c_odds, c_p2 = st.columns([3, 2, 3])
                with c_p1:
                    o1 = format_american_odds(int(p1_odds)) if pd.notna(p1_odds) else "—"
                    impl1 = round(p1_impl * 100, 1) if pd.notna(p1_impl) else 0
                    clr = "var(--biq-pos)" if pd.notna(p1_odds) and int(p1_odds) > 0 else "var(--biq-neg)"
                    st.markdown(
                        f"**{p1}**  \n"
                        f"<span style='color:{clr}; font-size:1.3rem; font-weight:700;'>{o1}</span>  "
                        f"<span style='color:var(--biq-muted); font-size:0.8rem;'>({impl1}% implied)</span>",
                        unsafe_allow_html=True,
                    )
                with c_odds:
                    # Probability bar
                    if pd.notna(p1_impl) and pd.notna(p2_impl):
                        total_impl = p1_impl + p2_impl
                        p1_pct = p1_impl / total_impl * 100 if total_impl > 0 else 50
                        bar_html = (
                            f"<div style='display:flex; height:8px; border-radius:4px; overflow:hidden; margin:20px 0;'>"
                            f"<div style='width:{p1_pct:.0f}%; background:var(--biq-accent);'></div>"
                            f"<div style='width:{100-p1_pct:.0f}%; background:var(--biq-accent2);'></div>"
                            f"</div>"
                            f"<div style='display:flex; justify-content:space-between; font-size:0.75rem; color:var(--biq-muted);'>"
                            f"<span>{p1_pct:.0f}%</span><span>{100-p1_pct:.0f}%</span>"
                            f"</div>"
                        )
                        st.markdown(bar_html, unsafe_allow_html=True)
                with c_p2:
                    o2 = format_american_odds(int(p2_odds)) if pd.notna(p2_odds) else "—"
                    impl2 = round(p2_impl * 100, 1) if pd.notna(p2_impl) else 0
                    clr = "var(--biq-pos)" if pd.notna(p2_odds) and int(p2_odds) > 0 else "var(--biq-neg)"
                    st.markdown(
                        f"**{p2}**  \n"
                        f"<span style='color:{clr}; font-size:1.3rem; font-weight:700;'>{o2}</span>  "
                        f"<span style='color:var(--biq-muted); font-size:0.8rem;'>({impl2}% implied)</span>",
                        unsafe_allow_html=True,
                    )

        st.divider()
        st.caption("Odds data sourced from DraftKings. Refresh page for latest lines.")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — LINE MOVEMENT
# ════════════════════════════════════════════════════════════════════════════════
with tab_movement:
    st.markdown("### Odds Line Movement Chart")
    st.caption("Track how DraftKings implied probabilities shift over time for each match.")

    upcoming_mv = get_upcoming_matches(days=7)

    if upcoming_mv.empty:
        st.info("No upcoming matches available.")
    else:
        upcoming_mv["label"] = (
            upcoming_mv["player1"] + " vs " + upcoming_mv["player2"]
            + " — " + upcoming_mv["tournament"]
        )
        labels = upcoming_mv["label"].tolist()
        sel = st.selectbox("Select match", labels, key="mv_match")
        sel_row = upcoming_mv[upcoming_mv["label"] == sel].iloc[0]
        match_id = int(sel_row["match_id"])
        p1 = sel_row["player1"]
        p2 = sel_row["player2"]

        odds_hist = get_odds_history(match_id)

        if odds_hist.empty:
            st.info("No odds history available for this match.")
        else:
            # Main implied probability chart
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p1_implied"] * 100,
                name=p1,
                mode="lines+markers",
                line=dict(color=chart["accent"], width=2.5),
                marker=dict(size=7, symbol="circle"),
                fill="tozeroy",
                fillcolor="rgba(0,0,0,0)",
            ))
            fig.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p2_implied"] * 100,
                name=p2,
                mode="lines+markers",
                line=dict(color=chart["accent2"], width=2.5),
                marker=dict(size=7, symbol="circle"),
                fill="tozeroy",
                fillcolor="rgba(0,0,0,0)",
            ))
            fig.add_hline(
                y=50, line_dash="dash", line_color=chart["grid"],
                annotation_text="50%", annotation_position="right",
            )
            fig.update_layout(
                title=f"Implied Probability: {p1} vs {p2}",
                xaxis_title="Snapshot Time",
                yaxis_title="Implied Probability (%)",
                template=chart["template"],
                paper_bgcolor=chart["paper_bgcolor"],
                plot_bgcolor=chart["plot_bgcolor"],
                font=dict(color=chart["text"]),
                height=400,
                margin=dict(l=10, r=10, t=50, b=50),
                legend=dict(orientation="h", y=-0.2),
                yaxis=dict(range=[0, 100], ticksuffix="%", gridcolor=chart["grid"]),
                xaxis=dict(gridcolor=chart["grid"]),
            )
            st.plotly_chart(fig, width="stretch")

            # American odds movement
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p1_odds"],
                name=f"{p1} (ML)",
                mode="lines+markers",
                line=dict(color=chart["accent"], width=2),
                marker=dict(size=6),
            ))
            fig2.add_trace(go.Scatter(
                x=odds_hist["time"],
                y=odds_hist["p2_odds"],
                name=f"{p2} (ML)",
                mode="lines+markers",
                line=dict(color=chart["accent2"], width=2),
                marker=dict(size=6),
            ))
            fig2.add_hline(y=0, line_dash="dot", line_color=chart["grid"])
            fig2.update_layout(
                title="American Moneyline Movement",
                xaxis_title="Snapshot Time",
                yaxis_title="American Odds",
                template=chart["template"],
                paper_bgcolor=chart["paper_bgcolor"],
                plot_bgcolor=chart["plot_bgcolor"],
                font=dict(color=chart["text"]),
                height=300,
                margin=dict(l=10, r=10, t=50, b=50),
                legend=dict(orientation="h", y=-0.25),
                yaxis=dict(gridcolor=chart["grid"]),
                xaxis=dict(gridcolor=chart["grid"]),
            )
            st.plotly_chart(fig2, width="stretch")

            # Movement summary table
            st.markdown("#### Movement Summary")
            opening = odds_hist.iloc[0]
            latest = odds_hist.iloc[-1]
            mv_data = {
                "": [p1, p2],
                "Opening Odds": [
                    format_american_odds(int(opening["p1_odds"])),
                    format_american_odds(int(opening["p2_odds"])),
                ],
                "Current Odds": [
                    format_american_odds(int(latest["p1_odds"])),
                    format_american_odds(int(latest["p2_odds"])),
                ],
                "Open Implied": [
                    f"{round(opening['p1_implied']*100,1)}%",
                    f"{round(opening['p2_implied']*100,1)}%",
                ],
                "Current Implied": [
                    f"{round(latest['p1_implied']*100,1)}%",
                    f"{round(latest['p2_implied']*100,1)}%",
                ],
                "Shift (pp)": [
                    f"{round((latest['p1_implied'] - opening['p1_implied'])*100, 2):+.2f}",
                    f"{round((latest['p2_implied'] - opening['p2_implied'])*100, 2):+.2f}",
                ],
            }
            themed_dataframe(pd.DataFrame(mv_data), hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — STEAM MOVES
# ════════════════════════════════════════════════════════════════════════════════
with tab_steam:
    st.markdown("### 🔥 Steam Moves")
    st.caption(
        "Steam = significant sharp-money line movement. "
        "Flagged when implied probability shifts ≥3 percentage points within 30 minutes."
    )

    hours_back = st.slider("Look-back window (hours)", 1, 48, 24, key="steam_hours")
    steam_df = get_recent_steam_events(hours=hours_back)

    if steam_df.empty:
        st.info(f"No steam moves detected in the last {hours_back} hours.")
    else:
        st.success(f"**{len(steam_df)} steam move(s) detected** in the last {hours_back} hours.")

        for _, row in steam_df.iterrows():
            direction = row.get("player_steamed", "")
            shift = row.get("shift_pct", 0)
            open_o = format_american_odds(int(row.get("opening_odds", 0)))
            curr_o = format_american_odds(int(row.get("current_odds", 0)))
            p1 = row.get("player1", "")
            p2 = row.get("player2", "")
            tourn = row.get("tournament", "")
            detected = row.get("detected_at")
            dt_str = detected.strftime("%b %d, %H:%M") if pd.notna(detected) else ""
            arrow = "▲" if shift > 0 else "▼"
            intensity = "🔴🔴🔴" if abs(shift) >= 5 else ("🔴🔴" if abs(shift) >= 3 else "🔴")

            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1.5])
                with c1:
                    st.markdown(
                        f"**{p1} vs {p2}**  \n"
                        f"<span style='color:var(--biq-muted); font-size:0.82rem;'>{tourn}</span>",
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f'<span class="steam-badge">{arrow} STEAM on {direction}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<span style='color:var(--biq-muted); font-size:0.8rem;'>"
                        f"Shift: {'+' if shift > 0 else ''}{shift:.1f}pp</span>",
                        unsafe_allow_html=True,
                    )
                with c3:
                    st.markdown(
                        f"<span style='color:var(--biq-muted); font-size:0.82rem;'>Open → Current</span><br>"
                        f"<span style='font-weight:700;'>{open_o} → {curr_o}</span>",
                        unsafe_allow_html=True,
                    )
                with c4:
                    st.markdown(
                        f"{intensity}<br>"
                        f"<span style='color:var(--biq-muted); font-size:0.8rem;'>{dt_str}</span>",
                        unsafe_allow_html=True,
                    )

        st.info(
            "**What does steam mean for your bet?** When sharp money hits a line and the book "
            "moves it quickly, that movement signals new information. A steam move in the same "
            "direction as a BullzIQ model pick increases confidence. A steam move against a "
            "pick is a warning sign to reassess."
        )

page_footer()
