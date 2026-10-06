import { useState, useEffect } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { BettingOracleFooter } from "../components/legal/Footer";
import { PoissonDistChart } from "../components/charts/PoissonDistChart";
import { formatAmericanOdds } from "../utils/formatters";
import { calculateEdge, formatAdjustedProbability, prob180sOver, prob180sUnder, expected180sInMatch } from "../utils/calculators";
import type { Player } from "../types";

function edgeBadgeClass(edge: number): string {
  if (edge >= 5) return "badge badge-edge-high";
  if (edge >= 3) return "badge badge-edge-med";
  if (edge >= 1.5) return "badge badge-edge-low";
  return "badge badge-edge-none";
}

export default function ToolsPage() {
  const { data: players } = useApi(() => api.players(), []);

  const [activeTab, setActiveTab] = useState("edge");

  const [p1Id, setP1Id] = useState("");
  const [p2Id, setP2Id] = useState("");
  const [legs, setLegs] = useState(6);
  const [dkOdds, setDkOdds] = useState(-150);

  const [mProb, setMProb] = useState(55);
  const [mOdds, setMOdds] = useState(-120);
  const [mResult, setMResult] = useState<{ model_prob: number; dk_implied: number; edge_pct: number; expected_value: number; grade: string } | null>(null);

  const [s180Player, setS180Player] = useState("");
  const [s180Legs, setS180Legs] = useState(6);
  const [s180Line, setS180Line] = useState(3.5);
  const [s180OverOdds, setS180OverOdds] = useState(-115);
  const [s180UnderOdds, setS180UnderOdds] = useState(-115);
  const [s180AvgOverride, setS180AvgOverride] = useState(0.1);
  const [s180Result, setS180Result] = useState<{ expected_180s: number; prob_over: number; prob_under: number } | null>(null);
  const [s180OverEdge, setS180OverEdge] = useState<{ edge_pct: number; expected_value: number; grade: string } | null>(null);
  const [s180UnderEdge, setS180UnderEdge] = useState<{ edge_pct: number; expected_value: number; grade: string } | null>(null);

  const [fvBase, setFvBase] = useState(65);

  const [numLegs, setNumLegs] = useState(2);
  const [lp1, setLp1] = useState(55);
  const [lo1, setLo1] = useState(-130);
  const [lp2, setLp2] = useState(55);
  const [lo2, setLo2] = useState(-130);
  const [lp3, setLp3] = useState(55);
  const [lo3, setLo3] = useState(-130);
  const [lp4, setLp4] = useState(55);
  const [lo4, setLo4] = useState(-130);
  const [parlayResult, setParlayResult] = useState<{ combined_model_prob: number; combined_implied_prob: number; combined_decimal_odds: number; edge_pct: number; ev_per_100: number } | null>(null);

  const p1 = players?.find((p) => p.id === Number(p1Id));
  const p2 = players?.find((p) => p.id === Number(p2Id));

  useEffect(() => {
    if (!p1 || !p2 || p1.id === p2.id) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const eloRes = await api.calcEloProb(p1.elo, p2.elo);
        const fmtRes = await api.calcFormatAdjust(eloRes.prob_a, legs);
        const edgeRes = await api.calcEdge(fmtRes.adjusted_prob, dkOdds);
        if (!cancelled) {
          setEloP1(p1.elo);
          setEloP2(p2.elo);
          setEloRawProb(eloRes.prob_a);
          setEloFmtProb(fmtRes.adjusted_prob);
          setEloFairOdds(eloRes.fair_odds_a);
          setEResult(edgeRes);
          setEEdge(edgeRes.edge_pct);
        }
      } catch {
        if (!cancelled) setEResult(null);
      }
    })();
    return () => { cancelled = true; };
  }, [p1, p2, legs, dkOdds]);

  const [eResult, setEResult] = useState<{ model_prob: number; dk_implied: number; edge_pct: number; expected_value: number; grade: string } | null>(null);
  const [eEdge, setEEdge] = useState(0);
  const [eloP1, setEloP1] = useState(0);
  const [eloP2, setEloP2] = useState(0);
  const [eloRawProb, setEloRawProb] = useState(0);
  const [eloFmtProb, setEloFmtProb] = useState(0);
  const [eloFairOdds, setEloFairOdds] = useState(0);

  function handleManualCalc() {
    setMResult(calculateEdge(mProb / 100, mOdds));
  }

  // Sync the override to the player's actual avg when a player is selected.
  // Streamlit shows the player's real avg_180s_per_leg in the override field by default.
  useEffect(() => {
    if (!s180Player || !players) return;
    const pl = players.find((p) => p.id === Number(s180Player));
    if (!pl) return;
    setS180AvgOverride(pl.avg_180s_per_leg ?? 0.1);
  }, [s180Player, players]);

  useEffect(() => {
    if (!s180Player || !players) return;
    const pl = players.find((p) => p.id === Number(s180Player));
    if (!pl) return;
    const avg = s180AvgOverride || pl.avg_180s_per_leg || 0.1;
    const expected = expected180sInMatch(avg, s180Legs);
    const pOver = prob180sOver(expected, s180Line);
    const pUnder = prob180sUnder(expected, s180Line);
    setS180Result({ expected_180s: expected, prob_over: pOver, prob_under: pUnder });
    setS180OverEdge(calculateEdge(pOver, s180OverOdds));
    setS180UnderEdge(calculateEdge(pUnder, s180UnderOdds));
  }, [s180Player, s180Legs, s180Line, s180OverOdds, s180UnderOdds, s180AvgOverride, players]);

  useEffect(() => {
    const legsData: Array<{ prob: number; odds: number }> = [];
    const probs = [lp1, lp2, lp3, lp4];
    const odds = [lo1, lo2, lo3, lo4];
    for (let i = 0; i < numLegs; i++) {
      legsData.push({ prob: probs[i] / 100, odds: odds[i] });
    }
    api.calcParlay(legsData).then(setParlayResult).catch(() => setParlayResult(null));
  }, [numLegs, lp1, lo1, lp2, lo2, lp3, lo3, lp4, lo4]);

  const fvFormats = [3, 4, 5, 6, 7, 8, 10];
  const fvLabels: Record<number, string> = { 3: "Bo5", 4: "Bo7", 5: "Bo9", 6: "Bo11", 7: "Bo13", 8: "Bo15", 10: "Bo19" };
  const fvData = fvFormats.map((l) => ({
    legs: l,
    label: fvLabels[l],
    fav: formatAdjustedProbability(fvBase / 100, l) * 100,
  }));

  const maxFav = Math.max(...fvData.map((d) => d.fav));

  const s180Mu = s180Result?.expected_180s ?? 1;
  const s180PlayerObj = players?.find((p) => p.id === Number(s180Player));

  const tournamentFormats = [
    { name: "World Championship", format: "Bo5 / Bo7 / Bo9 / Bo11 / Bo13", legs: "3-7 to 6-7" },
    { name: "Premier League", format: "Bo11", legs: "6 legs" },
    { name: "World Matchplay", format: "Bo11 / Bo19 / Bo21", legs: "6-10 to 11-10" },
    { name: "World Grand Prix", format: "Bo5 / Bo7 / Bo9 / Bo11", legs: "3-6 to 6-6" },
    { name: "Grand Slam of Darts", format: "Bo9 / Bo11 / Bo15 / Bo19", legs: "5-10 to 10-10" },
    { name: "Players Championship Finals", format: "Bo7 / Bo9 / Bo11 / Bo15", legs: "4-10 to 8-8" },
    { name: "Masters", format: "Bo11", legs: "6 legs" },
  ];

  const tabDefs = [
    { key: "edge", label: "Edge Calculator", icon: "\uD83D\uDCB0" },
    { key: "180s", label: "180s Calculator", icon: "\uD83C\uDFAF" },
    { key: "format", label: "Format Variance", icon: "\uD83D\uDCD0" },
    { key: "parlay", label: "Parlay Edge", icon: "\uD83D\uDD17" },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="page-header">
        <h2>BullzIQ Analytics Tools</h2>
        <div className="caption">Calculators, models, and edge analysis for darts betting</div>
      </div>

      <div className="tabs">
        {tabDefs.map((t) => (
          <button
            key={t.key}
            className={`tab${t.key === activeTab ? " active" : ""}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {activeTab === "edge" && (
        <div>
          <h3>Betting Edge Calculator</h3>
          <p style={{ marginBottom: 16 }}>
            Enter your estimated win probability and the DraftKings odds to calculate edge.{" "}
            <strong>Edge &gt; 0</strong> means the model sees value.
          </p>

          <div className="grid-2">
            <div className="card">
              <div style={{ marginBottom: 12 }}>
                <label>Player 1 (favourite)</label>
                <select value={p1Id} onChange={(e) => setP1Id(e.target.value)}>
                  <option value="">-- select player --</option>
                  {players?.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>Player 2 (underdog)</label>
                <select value={p2Id} onChange={(e) => setP2Id(e.target.value)}>
                  <option value="">-- select player --</option>
                  {players?.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>Legs to win</label>
                <select value={legs} onChange={(e) => setLegs(Number(e.target.value))}>
                  {[5, 6, 7, 8, 10].map((l) => (
                    <option key={l} value={l}>{l}</option>
                  ))}
                </select>
              </div>
              <div>
                <label>DK Odds for Player 1 (e.g. -140 or +110)</label>
                <input
                  type="number"
                  value={dkOdds}
                  step={5}
                  onChange={(e) => setDkOdds(Number(e.target.value))}
                />
              </div>
            </div>

            {p1 && p2 && p1.id !== p2.id && eResult ? (
              <div>
                <div className="metrics-row" style={{ gridTemplateColumns: "1fr 1fr" }}>
                  <div className="metric-card">
                    <div className="label">Model Probability</div>
                    <div className="value">{(eResult.model_prob * 100).toFixed(1)}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">DK Implied Probability</div>
                    <div className="value">{(eResult.dk_implied * 100).toFixed(1)}%</div>
                  </div>
                </div>

                <div className="card" style={{ textAlign: "center", padding: "20px 16px" }}>
                  <div className="label" style={{ marginBottom: 8 }}>Edge</div>
                  <div style={{ fontSize: "2.2rem", fontWeight: 700, color: eEdge > 0 ? "var(--biq-pos)" : eEdge < 0 ? "var(--biq-neg)" : "var(--biq-muted)" }}>
                    {eEdge > 0 ? "+" : ""}{eEdge.toFixed(2)}%
                  </div>
                  <span className={edgeBadgeClass(eEdge)} style={{ marginTop: 8, display: "inline-block" }}>
                    Grade {eResult.grade}
                  </span>
                </div>

                <div className="metrics-row" style={{ gridTemplateColumns: "1fr", marginTop: 8 }}>
                  <div className="metric-card">
                    <div className="label">Expected Value (per $100)</div>
                    <div className="value" style={{ color: eResult.expected_value > 0 ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                      ${eResult.expected_value.toFixed(2)}
                    </div>
                  </div>
                </div>

                <div className="card" style={{ marginTop: 8 }}>
                  <div className="label" style={{ marginBottom: 8 }}>Elo Context</div>
                  <ul style={{ margin: 0, paddingLeft: 20, fontSize: "0.88rem", lineHeight: 1.8 }}>
                    <li>{p1.name} Elo: <strong>{eloP1}</strong></li>
                    <li>{p2.name} Elo: <strong>{eloP2}</strong></li>
                    <li>Raw Elo Win Probability: <strong>{(eloRawProb * 100).toFixed(1)}%</strong></li>
                    <li>Format-Adjusted Probability: <strong>{(eloFmtProb * 100).toFixed(1)}%</strong></li>
                    <li>Fair Odds: <strong>{formatAmericanOdds(eloFairOdds)}</strong></li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="empty-state">
                {p1 && p2 && p1.id === p2.id
                  ? "Please select two different players."
                  : "Select both players to see results."}
              </div>
            )}
          </div>

          <hr className="divider" />

          <div className="info-box" style={{ marginBottom: 16 }}>
            <strong>How to use this tool</strong>
            <ol style={{ margin: "8px 0 0", paddingLeft: 20 }}>
              <li>Select two players from the database. The model will automatically calculate their Elo-based win probability.</li>
              <li>Choose the match format (legs to win) to adjust for format variance.</li>
              <li>Enter the current DraftKings odds for the favourite. The model compares its probability against the implied odds.</li>
              <li>A positive edge means the model sees value — the probability exceeds what the odds imply.</li>
            </ol>
            <div style={{ marginTop: 10 }}>
              <strong>Grade Legend:</strong>{" "}
              <span className="badge badge-edge-high">A (&ge;5%)</span>{" "}
              <span className="badge badge-edge-med">B (&ge;3%)</span>{" "}
              <span className="badge badge-edge-low">C (&ge;1.5%)</span>{" "}
              <span className="badge badge-edge-none">D (&lt;1.5%)</span>
            </div>
          </div>

          <h4>Manual Entry</h4>
          <div className="grid-3" style={{ marginTop: 8 }}>
            <div className="card">
              <label>Your win probability (%)</label>
              <input
                type="number"
                min={1}
                max={99}
                step={0.5}
                value={mProb}
                onChange={(e) => setMProb(Number(e.target.value))}
              />
            </div>
            <div className="card">
              <label>DraftKings odds</label>
              <input
                type="number"
                step={5}
                value={mOdds}
                onChange={(e) => setMOdds(Number(e.target.value))}
              />
            </div>
            <div className="card" style={{ display: "flex", alignItems: "flex-end" }}>
              <button className="btn-primary" onClick={handleManualCalc} style={{ width: "100%" }}>
                Calculate
              </button>
            </div>
          </div>
          {mResult && (
            <div className="card" style={{ marginTop: 8 }}>
              <div className="metrics-row" style={{ gridTemplateColumns: "1fr 1fr 1fr 1fr" }}>
                <div className="metric-card">
                  <div className="label">Model Prob</div>
                  <div className="value">{(mResult.model_prob * 100).toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">DK Implied</div>
                  <div className="value">{(mResult.dk_implied * 100).toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">Edge</div>
                  <div className="value" style={{ color: mResult.edge_pct > 0 ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                    {mResult.edge_pct > 0 ? "+" : ""}{mResult.edge_pct.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-card">
                  <div className="label">EV per $100</div>
                  <div className="value" style={{ color: mResult.expected_value > 0 ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                    ${mResult.expected_value.toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "180s" && (
        <div>
          <h3>180s Probability Calculator</h3>
          <p style={{ marginBottom: 16 }}>
            Uses a Poisson model based on the player&apos;s historical 180s per leg to estimate over/under probabilities for a given line.
          </p>

          <div className="grid-2">
            <div className="card">
              <div style={{ marginBottom: 12 }}>
                <label>Select player</label>
                <select value={s180Player} onChange={(e) => setS180Player(e.target.value)}>
                  <option value="">-- select player --</option>
                  {players?.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>Legs to win (match format): <strong>{s180Legs}</strong></label>
                <input
                  type="range"
                  min={3}
                  max={10}
                  value={s180Legs}
                  onChange={(e) => setS180Legs(Number(e.target.value))}
                  style={{ width: "100%", marginTop: 4 }}
                />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>180s line (over/under)</label>
                <input
                  type="number"
                  min={0.5}
                  max={20}
                  step={0.5}
                  value={s180Line}
                  onChange={(e) => setS180Line(Number(e.target.value))}
                />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>DK odds for OVER</label>
                <input
                  type="number"
                  step={5}
                  value={s180OverOdds}
                  onChange={(e) => setS180OverOdds(Number(e.target.value))}
                />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label>DK odds for UNDER</label>
                <input
                  type="number"
                  step={5}
                  value={s180UnderOdds}
                  onChange={(e) => setS180UnderOdds(Number(e.target.value))}
                />
              </div>
              <div>
                <label>Override avg 180s/leg (0.01–0.50)</label>
                <input
                  type="number"
                  min={0.01}
                  max={0.5}
                  step={0.005}
                  value={s180AvgOverride}
                  onChange={(e) => setS180AvgOverride(Number(e.target.value))}
                />
              </div>
            </div>

            {s180Result && s180OverEdge && s180UnderEdge ? (
              <div>
                <div className="metrics-row" style={{ gridTemplateColumns: "1fr" }}>
                  <div className="metric-card">
                    <div className="label">Expected 180s in Match</div>
                    <div className="value">{s180Result.expected_180s.toFixed(2)}</div>
                  </div>
                </div>

                <div className="grid-2" style={{ marginTop: 8 }}>
                  <div className="card" style={{ textAlign: "center" }}>
                    <div className="label">OVER {s180Line}</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 700, margin: "8px 0" }}>
                      {(s180Result.prob_over * 100).toFixed(1)}%
                    </div>
                    <span className={edgeBadgeClass(s180OverEdge.edge_pct)}>
                      Edge {s180OverEdge.edge_pct > 0 ? "+" : ""}{s180OverEdge.edge_pct.toFixed(2)}% ({s180OverEdge.grade})
                    </span>
                  </div>
                  <div className="card" style={{ textAlign: "center" }}>
                    <div className="label">UNDER {s180Line}</div>
                    <div style={{ fontSize: "1.8rem", fontWeight: 700, margin: "8px 0" }}>
                      {(s180Result.prob_under * 100).toFixed(1)}%
                    </div>
                    <span className={edgeBadgeClass(s180UnderEdge.edge_pct)}>
                      Edge {s180UnderEdge.edge_pct > 0 ? "+" : ""}{s180UnderEdge.edge_pct.toFixed(2)}% ({s180UnderEdge.grade})
                    </span>
                  </div>
                </div>

                <div className="card" style={{ marginTop: 12 }}>
                  <PoissonDistChart
                    mu={s180Mu}
                    line={s180Line}
                    playerName={s180PlayerObj?.name ?? ""}
                  />
                </div>

                <div className="info-box" style={{ marginTop: 8 }}>
                  The Poisson model estimates the probability of each possible 180 count based on the player&apos;s average 180s per leg and expected total legs in the match. Shorter matches produce wider variance.
                </div>
              </div>
            ) : (
              <div className="empty-state">Select a player to see 180s probabilities.</div>
            )}
          </div>
        </div>
      )}

      {activeTab === "format" && (
        <div>
          <h3>Format Variance Explainer</h3>
          <p style={{ marginBottom: 16 }}>
            Shorter formats increase variance and give underdogs a better chance. Adjust the base win probability to see how different match formats shift the balance.
          </p>

          <div className="grid-2">
            <div>
              <div className="card">
                <label>Base win probability for stronger player: <strong>{fvBase}%</strong></label>
                <input
                  type="range"
                  min={50}
                  max={90}
                  step={0.5}
                  value={fvBase}
                  onChange={(e) => setFvBase(Number(e.target.value))}
                  style={{ width: "100%", marginTop: 4 }}
                />
              </div>

              <div className="card" style={{ marginTop: 12 }}>
                <div className="label" style={{ marginBottom: 12 }}>Favourite Win % by Format</div>
                {fvData.map((d) => (
                  <div key={d.legs} style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
                    <div style={{ width: 50, fontSize: "0.82rem", fontWeight: 600, flexShrink: 0 }}>{d.label}</div>
                    <div style={{ flex: 1, height: 18, background: "var(--biq-bg3)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ width: `${maxFav > 0 ? (d.fav / maxFav) * 100 : 0}%`, height: "100%", background: "var(--biq-accent)", borderRadius: 4, transition: "width 0.3s" }} />
                    </div>
                    <div style={{ width: 60, textAlign: "right", fontSize: "0.85rem", fontWeight: 600, marginLeft: 8 }}>{d.fav.toFixed(1)}%</div>
                  </div>
                ))}
                <div style={{ marginTop: 6 }}>
                  <div style={{ display: "flex", alignItems: "center", marginBottom: 6 }}>
                    <div style={{ width: 50, fontSize: "0.82rem", fontWeight: 600, flexShrink: 0, color: "var(--biq-muted)" }}>Underdog</div>
                    <div style={{ flex: 1, height: 18, background: "var(--biq-bg3)", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ width: `${maxFav > 0 ? ((100 - fvData[fvData.length - 1].fav) / maxFav) * 100 : 0}%`, height: "100%", background: "var(--biq-accent2)", borderRadius: 4, transition: "width 0.3s" }} />
                    </div>
                    <div style={{ width: 60, textAlign: "right", fontSize: "0.85rem", fontWeight: 600, marginLeft: 8, color: "var(--biq-accent2)" }}>{(100 - fvData[fvData.length - 1].fav).toFixed(1)}%</div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <div className="card">
                <div className="label" style={{ marginBottom: 8 }}>Format Reference Table</div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Format</th>
                        <th>Fav Win %</th>
                        <th>Underdog %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {fvData.map((d) => (
                        <tr key={d.legs}>
                          <td style={{ fontWeight: 600 }}>{d.label}</td>
                          <td>{d.fav.toFixed(1)}%</td>
                          <td>{(100 - d.fav).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="info-box" style={{ marginTop: 12 }}>
                <strong>Key Takeaway:</strong> Moving from a Bo11 to a Bo5 reduces the favourite&apos;s win probability by ~{(formatAdjustedProbability(fvBase / 100, 6) * 100 - formatAdjustedProbability(fvBase / 100, 3) * 100).toFixed(1)} percentage points. This is why upsets are more common in shorter tournament formats.
              </div>

              <div className="card" style={{ marginTop: 12 }}>
                <div className="label" style={{ marginBottom: 8 }}>PDC Tournament Formats</div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Tournament</th>
                        <th>Format</th>
                        <th>Legs</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tournamentFormats.map((tf) => (
                        <tr key={tf.name}>
                          <td style={{ fontWeight: 600 }}>{tf.name}</td>
                          <td>{tf.format}</td>
                          <td>{tf.legs}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === "parlay" && (
        <div>
          <h3>Parlay Edge Calculator</h3>
          <p style={{ marginBottom: 16 }}>
            Combine multiple legs into a parlay to see the combined edge and expected value. Each leg&apos;s model probability is multiplied together, and compared against the combined DraftKings implied probability.
          </p>

          <div className="card" style={{ marginBottom: 12, maxWidth: 300 }}>
            <label>Number of parlay legs</label>
            <input
              type="number"
              min={2}
              max={4}
              step={1}
              value={numLegs}
              onChange={(e) => setNumLegs(Number(e.target.value))}
            />
          </div>

          <div className="grid-2" style={{ gridTemplateColumns: numLegs <= 2 ? "1fr 1fr" : "repeat(2, 1fr)" }}>
            {Array.from({ length: numLegs }, (_, i) => {
              const prob = [lp1, lp2, lp3, lp4][i];
              const odds = [lo1, lo2, lo3, lo4][i];
              const setProb = [setLp1, setLp2, setLp3, setLp4][i];
              const setOdds = [setLo1, setLo2, setLo3, setLo4][i];
              return (
                <div className="card" key={i}>
                  <div style={{ fontWeight: 700, marginBottom: 10 }}>Leg {i + 1}</div>
                  <div style={{ marginBottom: 10 }}>
                    <label>Model probability (%)</label>
                    <input
                      type="number"
                      min={1}
                      max={99}
                      step={0.5}
                      value={prob}
                      onChange={(e) => setProb(Number(e.target.value))}
                    />
                  </div>
                  <div>
                    <label>DK odds</label>
                    <input
                      type="number"
                      step={5}
                      value={odds}
                      onChange={(e) => setOdds(Number(e.target.value))}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          <hr className="divider" />

          {parlayResult && (
            <div>
              <div className="metrics-row">
                <div className="metric-card">
                  <div className="label">Parlay Model Prob</div>
                  <div className="value">{(parlayResult.combined_model_prob * 100).toFixed(2)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">DK Implied Prob</div>
                  <div className="value">{(parlayResult.combined_implied_prob * 100).toFixed(2)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">Parlay Edge</div>
                  <div className="value" style={{ color: parlayResult.edge_pct > 0 ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                    {parlayResult.edge_pct > 0 ? "+" : ""}{parlayResult.edge_pct.toFixed(2)}%
                  </div>
                </div>
                <div className="metric-card">
                  <div className="label">EV per $100</div>
                  <div className="value" style={{ color: parlayResult.ev_per_100 > 0 ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                    ${parlayResult.ev_per_100.toFixed(2)}
                  </div>
                </div>
              </div>

              <div className="info-box" style={{ marginTop: 8 }}>
                <strong>Parlay Warning:</strong> Parlays compound the house edge across all legs. Even with a positive edge on individual legs, the combined implied probability increases the bookmaker&apos;s advantage. Use this tool to identify parlays where the model edge outweighs the compounding effect.
              </div>
            </div>
          )}
        </div>
      )}

      <div className="page-footer" style={{ marginTop: 24 }}>
        <BettingOracleFooter />
      </div>
    </div>
  );
}
