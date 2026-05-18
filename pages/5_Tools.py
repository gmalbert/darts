"""
pages/5_Tools.py — Interactive analytics tools:
  - Edge Calculator
  - H2H Comparison Tool
  - 180s Probability Calculator
  - Format Variance Explainer
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import inject_css, get_theme, chart_style, themed_dataframe, format_american_odds
from components.disclaimers import page_footer
from db.queries import get_all_players, get_player_by_name, get_h2h
from models.props_model import (
    prob_180s_over, prob_180s_under, expected_180s_in_match,
    calculate_edge, format_adjusted_probability,
)
from models.elo import DartsElo

inject_css(get_theme())
chart = chart_style()

st.markdown("## 🔧 Analytics Tools")
st.caption("Interactive calculators for edge, props, and format analysis.")
st.divider()

tab_edge, tab_180s, tab_format, tab_parlay = st.tabs(
    ["💰 Edge Calculator", "🎯 180s Calculator", "📐 Format Variance", "🔗 Parlay Edge"]
)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — EDGE CALCULATOR
# ════════════════════════════════════════════════════════════════════════════════
with tab_edge:
    st.markdown("### 💰 Betting Edge Calculator")
    st.markdown(
        "Enter your estimated win probability and the DraftKings odds to calculate edge. "
        "**Edge > 0** means the model sees value."
    )

    all_players = get_all_players()
    player_names = [p["name"] for p in all_players]
    player_elo_map = {p["name"]: p["elo"] for p in all_players}

    col_input, col_result = st.columns([1, 1])

    with col_input:
        st.markdown("#### Method 1 — Elo-Based")
        p1_elo_sel = st.selectbox("Player 1 (favourite)", player_names, key="edge_p1")
        p2_elo_sel = st.selectbox("Player 2 (underdog)", player_names,
                                   index=min(1, len(player_names)-1), key="edge_p2")
        legs_elo = st.selectbox("Legs to win", [5, 6, 7, 8, 10], index=1, key="edge_legs")
        dk_odds_elo = st.number_input("DK Odds for Player 1 (e.g. -140 or +110)",
                                       value=-150, step=5, key="edge_dk")

        if p1_elo_sel != p2_elo_sel:
            elo1 = player_elo_map.get(p1_elo_sel, 1500)
            elo2 = player_elo_map.get(p2_elo_sel, 1500)
            elo_obj = DartsElo()
            elo_obj.ratings[p1_elo_sel] = elo1
            elo_obj.ratings[p2_elo_sel] = elo2
            base_prob = elo_obj.win_probability(p1_elo_sel, p2_elo_sel)
            adj_prob = format_adjusted_probability(base_prob, legs_elo)
            edge_result = calculate_edge(adj_prob, dk_odds_elo)

            with col_result:
                st.markdown("#### Result")
                r1, r2 = st.columns(2)
                with r1:
                    st.metric("Model Probability", f"{round(adj_prob*100,1)}%")
                    st.metric("DK Implied Prob", f"{round(edge_result['dk_implied']*100,1)}%")
                with r2:
                    edge = edge_result["edge_pct"]
                    edge_color = "var(--biq-pos)" if edge > 0 else "var(--biq-neg)"
                    st.markdown(
                        f"<div style='text-align:center; padding:16px; background:var(--biq-bg2); "
                        f"border:1px solid {edge_color}; border-radius:8px;'>"
                        f"<div style='font-size:2.2rem; font-weight:700; color:{edge_color};'>"
                        f"{'+' if edge > 0 else ''}{edge:.2f}%</div>"
                        f"<div style='color:var(--biq-muted);'>EDGE</div>"
                        f"<div style='font-size:1.2rem; color:{edge_color};'>{edge_result['grade']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.metric(
                        "EV (per $100 bet)",
                        f"${edge_result['expected_value']:+.2f}",
                        delta=f"Grade {edge_result['grade']}",
                    )

                st.markdown("#### Elo Context")
                st.markdown(
                    f"- **{p1_elo_sel} Elo:** {elo1:.0f}  \n"
                    f"- **{p2_elo_sel} Elo:** {elo2:.0f}  \n"
                    f"- **Raw Elo Win Prob:** {round(base_prob*100,1)}%  \n"
                    f"- **Format-Adjusted Prob:** {round(adj_prob*100,1)}%  \n"
                    f"- **Fair Odds:** {format_american_odds(DartsElo.to_american_odds(adj_prob))}"
                )

    st.divider()

    with st.expander("📖 How to use this tool"):
        st.markdown(
            """
            1. Select the two players from the dropdown.
            2. Choose the match format (legs to win).
            3. Enter the DraftKings moneyline odds for Player 1.
            4. The tool calculates:
               - **Model probability** — derived from Elo ratings, adjusted for format length.
               - **DK implied probability** — what DraftKings is pricing.
               - **Edge %** — the gap between model and book. Positive edge = value.
               - **EV (Expected Value)** — expected profit per $100 bet at flat stake.
               - **Grade** — A (≥5%), B (≥3%), C (≥1.5%), D (<1.5%).
            
            ⚠️ This is a model estimate, not a guaranteed bet. Always gamble responsibly.
            """,
        )

    st.markdown("#### Manual Entry")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        manual_prob = st.number_input("Your win probability (%)", min_value=1.0, max_value=99.0,
                                       value=55.0, step=0.5, key="manual_prob")
    with col_m2:
        manual_odds = st.number_input("DraftKings odds", value=-120, step=5, key="manual_odds")
    with col_m3:
        if st.button("Calculate", key="manual_calc"):
            res = calculate_edge(manual_prob / 100, manual_odds)
            edge = res["edge_pct"]
            clr = "var(--biq-pos)" if edge > 0 else "var(--biq-neg)"
            st.markdown(
                f"**Edge:** <span style='color:{clr}; font-weight:700;'>{edge:+.2f}%</span>  \n"
                f"**EV:** ${res['expected_value']:+.2f} per $100  \n"
                f"**Grade:** {res['grade']}",
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — 180s CALCULATOR
# ════════════════════════════════════════════════════════════════════════════════
with tab_180s:
    st.markdown("### 🎯 180s Probability Calculator")
    st.markdown(
        "Uses a Poisson distribution model to estimate the probability of a player "
        "hitting over/under a 180s prop line."
    )

    all_players_180 = get_all_players()
    pnames_180 = [p["name"] for p in all_players_180]
    p180_map = {p["name"]: p.get("avg_180s_per_leg", 0.10) for p in all_players_180}

    col_180_input, col_180_result = st.columns([1, 1])

    with col_180_input:
        sel_player_180 = st.selectbox("Select player", pnames_180, key="p180_player")
        legs_to_win_180 = st.slider("Legs to win (match format)", 3, 10, 6, key="p180_legs")
        line_180 = st.number_input("180s line (over/under)", min_value=0.5, max_value=20.0,
                                    value=3.5, step=0.5, key="p180_line")
        dk_over_odds = st.number_input("DK odds for OVER", value=-115, step=5, key="p180_over_dk")
        dk_under_odds = st.number_input("DK odds for UNDER", value=-115, step=5, key="p180_under_dk")

        avg_per_leg = p180_map.get(sel_player_180, 0.10)

        # Allow user override
        avg_override = st.number_input(
            f"Override {sel_player_180}'s avg 180s/leg",
            value=round(avg_per_leg, 3),
            min_value=0.01,
            max_value=0.50,
            step=0.005,
            format="%.3f",
            key="p180_override",
        )

    with col_180_result:
        expected = expected_180s_in_match(avg_override, legs_to_win_180)
        prob_over = prob_180s_over(expected, line_180)
        prob_under = prob_180s_under(expected, line_180)
        edge_over = calculate_edge(prob_over, dk_over_odds)
        edge_under = calculate_edge(prob_under, dk_under_odds)

        st.markdown("#### Results")
        rc1, rc2 = st.columns(2)
        with rc1:
            st.metric("Expected 180s", f"{expected:.2f}")
            over_clr = "var(--biq-pos)" if edge_over["edge_pct"] > 0 else "var(--biq-neg)"
            st.markdown(
                f"<div style='background:var(--biq-bg2); border:1px solid {over_clr}; "
                f"border-radius:8px; padding:12px; text-align:center; margin:4px 0;'>"
                f"<div style='color:var(--biq-muted); font-size:0.78rem;'>OVER {line_180:.1f}</div>"
                f"<div style='font-size:1.5rem; font-weight:700; color:var(--biq-text);'>"
                f"{round(prob_over*100,1)}%</div>"
                f"<div style='color:{over_clr}; font-size:0.9rem; font-weight:700;'>"
                f"Edge: {edge_over['edge_pct']:+.2f}% ({edge_over['grade']})</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
        with rc2:
            st.metric("Model (Poisson μ)", f"λ={expected:.2f}")
            under_clr = "var(--biq-pos)" if edge_under["edge_pct"] > 0 else "var(--biq-neg)"
            st.markdown(
                f"<div style='background:var(--biq-bg2); border:1px solid {under_clr}; "
                f"border-radius:8px; padding:12px; text-align:center; margin:4px 0;'>"
                f"<div style='color:var(--biq-muted); font-size:0.78rem;'>UNDER {line_180:.1f}</div>"
                f"<div style='font-size:1.5rem; font-weight:700; color:var(--biq-text);'>"
                f"{round(prob_under*100,1)}%</div>"
                f"<div style='color:{under_clr}; font-size:0.9rem; font-weight:700;'>"
                f"Edge: {edge_under['edge_pct']:+.2f}% ({edge_under['grade']})</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # Poisson distribution chart
        import math
        try:
            from scipy.stats import poisson
            k_vals = list(range(0, int(expected * 3) + 2))
            probs = [poisson.pmf(k, expected) for k in k_vals]
            colors = [chart["accent"] if k > line_180 else chart["accent2"] for k in k_vals]

            fig_poisson = go.Figure()
            fig_poisson.add_trace(go.Bar(
                x=k_vals,
                y=[p * 100 for p in probs],
                marker_color=colors,
                name="P(X=k)",
            ))
            fig_poisson.add_vline(
                x=line_180, line_dash="dash", line_color=chart["accent2"],
                annotation_text=f"Line: {line_180}", annotation_position="top",
            )
            fig_poisson.update_layout(
                title=f"Poisson Distribution — {sel_player_180} 180s",
                xaxis_title="Number of 180s",
                yaxis_title="Probability (%)",
                template=chart["template"],
                paper_bgcolor=chart["paper_bgcolor"],
                plot_bgcolor=chart["plot_bgcolor"],
                font=dict(color=chart["text"]),
                height=280,
                margin=dict(l=10, r=10, t=50, b=30),
                showlegend=False,
            )
            st.plotly_chart(fig_poisson, width="stretch")
        except ImportError:
            st.info("Install scipy for the probability chart.")

    st.info(
        "**Poisson model**: λ (expected 180s) = avg_180s_per_leg × expected_legs, "
        "where expected_legs ≈ legs_to_win × 1.6. The bar chart shows P(X=k) for each "
        "180s count — blue = under line, red = over line."
    )


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — FORMAT VARIANCE
# ════════════════════════════════════════════════════════════════════════════════
with tab_format:
    st.markdown("### 📐 Format Variance Explainer")
    st.markdown(
        "Shorter PDC formats (fewer legs) compress win probabilities toward 50%, "
        "giving underdogs better value. Adjust the sliders to explore."
    )

    col_fv1, col_fv2 = st.columns(2)

    with col_fv1:
        base_prob_fv = st.slider(
            "Base win probability for stronger player (%)",
            min_value=50.0, max_value=90.0, value=65.0, step=0.5,
            key="fv_base",
        )
        legs_options = [3, 4, 5, 6, 7, 8, 10]
        format_results = []
        for legs in legs_options:
            adj = format_adjusted_probability(base_prob_fv / 100, legs)
            format_results.append({
                "legs_to_win": legs,
                "format": f"Best of {legs*2-1}",
                "adjusted_prob": round(adj * 100, 1),
                "upset_rate": round((1 - adj) * 100, 1),
            })

        df_fv = pd.DataFrame(format_results)

        fig_fv = go.Figure()
        fig_fv.add_trace(go.Scatter(
            x=df_fv["format"],
            y=df_fv["adjusted_prob"],
            name="Favourite Win %",
            mode="lines+markers",
            line=dict(color=chart["accent"], width=2.5),
            marker=dict(size=8),
        ))
        fig_fv.add_trace(go.Scatter(
            x=df_fv["format"],
            y=df_fv["upset_rate"],
            name="Underdog Win %",
            mode="lines+markers",
            line=dict(color=chart["accent2"], width=2.5),
            marker=dict(size=8),
        ))
        fig_fv.add_hline(y=50, line_dash="dot", line_color=chart["grid"])
        fig_fv.update_layout(
            title=f"Format Impact (Base: {base_prob_fv:.0f}% favourite)",
            xaxis_title="Format",
            yaxis_title="Win Probability (%)",
            template=chart["template"],
            paper_bgcolor=chart["paper_bgcolor"],
            plot_bgcolor=chart["plot_bgcolor"],
            font=dict(color=chart["text"]),
            height=320,
            margin=dict(l=10, r=10, t=50, b=50),
            legend=dict(orientation="h", y=-0.25),
            xaxis=dict(gridcolor=chart["grid"]),
            yaxis=dict(gridcolor=chart["grid"]),
        )
        st.plotly_chart(fig_fv, width="stretch")

    with col_fv2:
        st.markdown("#### Format Reference Table")
        themed_dataframe(
            df_fv.rename(columns={
                "format": "Format",
                "adjusted_prob": "Fav Win %",
                "upset_rate": "Underdog %",
            })[["Format", "Fav Win %", "Underdog %"]],
            hide_index=True,
            width="stretch",
        )

        st.markdown("")
        st.info(
            "**Key takeaway**: In a Best of 5 (legs to win = 3) match, a player with "
            "65% base probability wins ~60% of the time. In a Best of 19 (legs to win = 10), "
            "that same player wins ~72%. Shorter formats = more variance = better underdog value."
        )

        st.markdown("#### PDC Tournament Formats")
        format_ref = pd.DataFrame([
            {"Tournament": "PDC World Championship (Final)", "Format": "Best of 13 sets"},
            {"Tournament": "Premier League", "Format": "Best of 11 legs"},
            {"Tournament": "World Matchplay (Final)", "Format": "Best of 31 legs"},
            {"Tournament": "Grand Slam (Final)", "Format": "Best of 19 legs"},
            {"Tournament": "UK Open (Final)", "Format": "Best of 11 legs"},
            {"Tournament": "World Grand Prix (sets)", "Format": "Best of 5 sets (3-leg)"},
            {"Tournament": "PC Finals (Final)", "Format": "Best of 21 legs"},
        ])
        themed_dataframe(format_ref, hide_index=True, width="stretch")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — PARLAY EDGE
# ════════════════════════════════════════════════════════════════════════════════
with tab_parlay:
    st.markdown("### 🔗 Parlay Edge Calculator")
    st.markdown(
        "Add up to 4 individual bets to calculate combined parlay probability and edge."
    )

    num_legs = st.number_input("Number of parlay legs", min_value=2, max_value=4, value=2, step=1)

    leg_data = []
    cols = st.columns(int(num_legs))

    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**Leg {i+1}**")
            prob_i = st.number_input(
                f"Model prob (%) — Leg {i+1}",
                min_value=1.0, max_value=99.0, value=55.0,
                step=0.5, key=f"parlay_prob_{i}",
            )
            odds_i = st.number_input(
                f"DK odds — Leg {i+1}",
                value=-130, step=5, key=f"parlay_odds_{i}",
            )
            leg_data.append((prob_i / 100, odds_i))

    if leg_data:
        combined_model_prob = 1.0
        combined_implied_prob = 1.0
        combined_decimal = 1.0

        for prob, odds in leg_data:
            if odds < 0:
                dk_impl = (-odds) / (-odds + 100)
                decimal = 1 + 100 / (-odds)
            else:
                dk_impl = 100 / (odds + 100)
                decimal = 1 + odds / 100
            combined_model_prob *= prob
            combined_implied_prob *= dk_impl
            combined_decimal *= decimal

        parlay_edge = (combined_model_prob - combined_implied_prob) * 100
        ev_100 = combined_model_prob * ((combined_decimal - 1) * 100) - (1 - combined_model_prob) * 100

        st.divider()
        pm1, pm2, pm3, pm4 = st.columns(4)
        with pm1:
            st.metric("Parlay Model Prob", f"{round(combined_model_prob*100,2)}%")
        with pm2:
            st.metric("DK Implied Prob", f"{round(combined_implied_prob*100,2)}%")
        with pm3:
            edge_clr = "normal" if parlay_edge > 0 else "inverse"
            st.metric("Parlay Edge", f"{parlay_edge:+.2f}%", delta_color=edge_clr)
        with pm4:
            st.metric("EV per $100", f"${ev_100:+.2f}")

        st.info(
            "⚠️ Parlays multiply both your potential payout and the book's edge. "
            "Even if each individual leg has positive edge, the combined parlay edge "
            "decreases significantly. Use with caution."
        )
page_footer()
