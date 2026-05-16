"""
pages/3_Tournaments.py — Tournament hubs, prize money, DK availability.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import inject_css, get_theme, render_theme_picker
from components.disclaimers import page_footer
from db.queries import get_all_tournaments, get_tournament_results

inject_css(get_theme())

with st.sidebar:
    render_theme_picker()

st.markdown("## 🏆 Tournament Hub")
st.caption("PDC events covered on DraftKings — formats, prize money, and results.")
st.divider()

tournaments = get_all_tournaments()

if not tournaments:
    st.warning("No tournament data. Ensure the database is seeded.")
    st.stop()

df_tourns = pd.DataFrame(tournaments)

# ── Summary metrics ───────────────────────────────────────────────────────────
tm1, tm2, tm3, tm4 = st.columns(4)
with tm1:
    st.metric("DK-Covered Tournaments", len(df_tourns[df_tourns["dk_covered"] == True]))
with tm2:
    major_count = len(df_tourns[df_tourns["prestige_tier"] == 1])
    st.metric("Major Events", major_count)
with tm3:
    total_prize = df_tourns["prize_fund"].sum()
    st.metric("Total Prize Pool", f"£{total_prize:,.0f}")
with tm4:
    st.metric("Active Years Coverage", "2000–2026")

st.divider()

# ── Tournament grid ────────────────────────────────────────────────────────────
tab_grid, tab_detail = st.tabs(["🗂️ All Tournaments", "📊 Tournament Detail"])

with tab_grid:
    st.markdown("### All PDC Tournaments")

    tier_filter = st.radio(
        "Filter by tier",
        ["All", "Majors (Tier 1)", "Ranking (Tier 2)"],
        horizontal=True,
    )

    filtered_tourns = tournaments
    if tier_filter == "Majors (Tier 1)":
        filtered_tourns = [t for t in tournaments if t["prestige_tier"] == 1]
    elif tier_filter == "Ranking (Tier 2)":
        filtered_tourns = [t for t in tournaments if t["prestige_tier"] == 2]

    for i, t in enumerate(filtered_tourns):
        tier = t.get("prestige_tier", 2)
        border_color = "#e10600" if tier == 1 else "#f0a500"
        dk_badge = "✅ DK" if t.get("dk_covered") else "❌"
        prize = t.get("prize_fund", 0)
        prize_str = f"£{prize:,}" if prize else "—"

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 2, 1.5, 1.5])
            with c1:
                tier_label = "🏅 MAJOR" if tier == 1 else "🎯 RANKING"
                st.markdown(
                    f"**{t['name']}**  \n"
                    f"<span style='color:#8b949e; font-size:0.8rem;'>{tier_label} · {t.get('typical_month', '—')}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"<span style='color:#8b949e; font-size:0.82rem;'>{t.get('format_desc', '—')}</span>",
                    unsafe_allow_html=True,
                )
            with c3:
                st.markdown(
                    f"<span style='color:#f0a500; font-weight:700;'>{prize_str}</span>",
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f"<span style='font-size:0.9rem;'>{dk_badge}</span>",
                    unsafe_allow_html=True,
                )

    # Prize fund bar chart
    st.markdown("#### Prize Fund Comparison")
    df_prize = pd.DataFrame(filtered_tourns).sort_values("prize_fund", ascending=True)
    fig_prize = go.Figure()
    fig_prize.add_trace(go.Bar(
        y=df_prize["name"],
        x=df_prize["prize_fund"],
        orientation="h",
        marker_color=["#e10600" if t == 1 else "#f0a500" for t in df_prize["prestige_tier"]],
        text=df_prize["prize_fund"].apply(lambda x: f"£{x:,}"),
        textposition="outside",
    ))
    fig_prize.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        height=380,
        margin=dict(l=10, r=100, t=20, b=20),
        xaxis=dict(showgrid=True, gridcolor="#21262d", title="Prize Fund (£)"),
        yaxis=dict(showgrid=False),
    )
    st.plotly_chart(fig_prize, use_container_width=True)


with tab_detail:
    st.markdown("### Tournament Results")

    tourn_names = [t["name"] for t in tournaments]
    sel_tourn = st.selectbox("Select tournament", tourn_names, key="tourn_detail")
    sel_tourn_obj = next((t for t in tournaments if t["name"] == sel_tourn), None)

    if sel_tourn_obj:
        st.markdown(
            f"**Format:** {sel_tourn_obj.get('format_desc', '—')}  \n"
            f"**Prize Fund:** £{sel_tourn_obj.get('prize_fund', 0):,}  \n"
            f"**Typical Month:** {sel_tourn_obj.get('typical_month', '—')}",
        )
        st.divider()

        results_df = get_tournament_results(sel_tourn_obj["id"], limit=100)

        if results_df.empty:
            st.info("No results logged for this tournament yet.")
        else:
            results_df["date"] = pd.to_datetime(results_df["date"]).dt.strftime("%b %d, %Y")
            st.dataframe(
                results_df[["date", "round", "player1", "score", "player2", "winner"]].rename(columns={
                    "date": "Date", "round": "Round",
                    "player1": "Player 1", "score": "Score",
                    "player2": "Player 2", "winner": "Winner",
                }),
                hide_index=True,
                use_container_width=True,
                height=500,
            )

            # Win count bar chart from these results
            st.markdown("#### Most Wins in This Tournament")
            win_counts = results_df["winner"].value_counts().head(10).reset_index()
            win_counts.columns = ["player", "wins"]
            fig_wins = go.Figure(go.Bar(
                x=win_counts["wins"],
                y=win_counts["player"],
                orientation="h",
                marker_color="#e10600",
            ))
            fig_wins.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0d1117",
                plot_bgcolor="#161b22",
                height=300,
                margin=dict(l=10, r=20, t=20, b=20),
                xaxis=dict(showgrid=True, gridcolor="#21262d", title="Match Wins"),
                yaxis=dict(showgrid=False, autorange="reversed"),
            )
            st.plotly_chart(fig_wins, use_container_width=True)

page_footer()
