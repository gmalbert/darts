import { useState, useMemo } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { Tabs } from "../components/controls/Tabs";
import { BettingOracleFooter } from "../components/legal/Footer";
import { formatAmericanOdds, formatTime, natFlag } from "../utils/formatters";
import type { Pick, Match, SteamEvent, ModelRecord, BulkEloEntry, YearlyStats, EraStats, Player } from "../types";

export default function HomePage() {
  const [minEdge, setMinEdge] = useState(1);
  const [sortBy, setSortBy] = useState<"edge" | "time" | "confidence">("edge");
  const [days, setDays] = useState(7);
  const [expandedReasoning, setExpandedReasoning] = useState<Record<number, boolean>>({});
  const [eloPlayers, setEloPlayers] = useState<string[]>([]);

  const modelRecord = useApi<ModelRecord>(() => api.modelRecord(30), []);
  const picks = useApi<Pick[]>(() => api.picks(0), []);
  const matches = useApi<Match[]>(() => api.matches({ upcoming: true, days }), [days]);
  const odds = useApi(() => api.odds(), []);
  const steamEvents = useApi<SteamEvent[]>(() => api.steam(24), []);
  const yearlyStats = useApi<YearlyStats[]>(() => api.yearlyStats(), []);
  const eraStats = useApi<EraStats[]>(() => api.eraPerformance(), []);
  const eloHistory = useApi<BulkEloEntry[]>(() => api.eloHistoryBulk(), []);
  const players = useApi<Player[]>(() => api.players(), []);

  const filteredPicks = useMemo(() => {
    if (!picks.data) return [];
    let p = picks.data.filter((pk) => pk.edge_pct >= minEdge);
    if (sortBy === "edge") p = [...p].sort((a, b) => b.edge_pct - a.edge_pct);
    else if (sortBy === "time") p = [...p].sort((a, b) => (a.match_date ?? "").localeCompare(b.match_date ?? ""));
    else if (sortBy === "confidence") {
      const order = { HIGH: 3, MED: 2, LOW: 1 };
      p = [...p].sort((a, b) => (order[b.confidence as keyof typeof order] ?? 0) - (order[a.confidence as keyof typeof order] ?? 0));
    }
    return p;
  }, [picks.data, minEdge, sortBy]);

  const bestEdge = useMemo(() => {
    if (!picks.data || picks.data.length === 0) return null;
    return Math.max(...picks.data.map((p) => p.edge_pct));
  }, [picks.data]);

  const mergedSchedule = useMemo(() => {
    if (!matches.data || !odds.data) return [];
    const oddsMap = new Map(odds.data.map((o) => [o.match_id, o]));
    return matches.data.map((m) => ({ ...m, odds: oddsMap.get(m.match_id) ?? null }));
  }, [matches.data, odds.data]);

  const groupedSchedule = useMemo(() => {
    const groups: Record<string, typeof mergedSchedule> = {};
    for (const m of mergedSchedule) {
      if (!groups[m.tournament]) groups[m.tournament] = [];
      groups[m.tournament].push(m);
    }
    return groups;
  }, [mergedSchedule]);

  const eloPlayerNames = useMemo(() => {
    if (!eloHistory.data) return [];
    const names = new Map<number, string>();
    for (const e of eloHistory.data) {
      if (!names.has(e.player_id)) names.set(e.player_id, e.player_name);
    }
    const sorted = [...names.entries()].sort((a, b) => a[1].localeCompare(b[1]));
    return sorted.map(([id, name]) => ({ id, name }));
  }, [eloHistory.data]);

  const selectedEloNames = useMemo(() => {
    if (eloPlayers.length > 0) return eloPlayers;
    return eloPlayerNames.slice(0, 5).map((p) => p.name);
  }, [eloPlayers, eloPlayerNames]);

  const eloChartData = useMemo(() => {
    const hist = eloHistory.data;
    if (!hist) return [];
    return selectedEloNames
      .map((name) => {
        const entries = hist
          .filter((e) => e.player_name === name)
          .sort((a, b) => a.recorded_at.localeCompare(b.recorded_at));
        return { name, entries };
      })
      .filter((g) => g.entries.length > 0);
  }, [eloHistory.data, selectedEloNames]);

  const lineColors = ["#0284c7", "#f97316", "#15803d", "#dc2626", "#8b5cf6", "#ec4899", "#14b8a6", "#f59e0b", "#6366f1", "#ef4444", "#06b6d4", "#84cc16"];

  const edgeDistribution = useMemo(() => {
    if (!picks.data || picks.data.length === 0) return [];
    const bins = Array.from({ length: 10 }, (_, i) => ({ label: `${i * 1}%–${(i + 1) * 1}%`, count: 0 }));
    for (const p of picks.data) {
      const idx = Math.min(Math.floor(p.edge_pct), 9);
      if (idx >= 0) bins[idx].count++;
    }
    return bins;
  }, [picks.data]);

  const maxBinCount = useMemo(() => Math.max(1, ...edgeDistribution.map((b) => b.count)), [edgeDistribution]);

  const mr = modelRecord.data;

  function toggleReasoning(id: number) {
    setExpandedReasoning((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function getEdgeBadgeClass(edge: number) {
    if (edge >= 4) return "badge-edge-high";
    if (edge >= 2) return "badge-edge-med";
    if (edge > 0) return "badge-edge-low";
    return "badge-edge-none";
  }

  function getEdgeLabel(edge: number) {
    if (edge > 0) return `+${edge.toFixed(1)}% Edge`;
    return `${edge.toFixed(1)}% Edge`;
  }

  function getConfBadgeClass(conf: string) {
    if (conf === "HIGH") return "badge-conf-high";
    if (conf === "MED") return "badge-conf-med";
    return "badge-conf-low";
  }

  const top12Players = useMemo(() => {
    if (!players.data) return [];
    return [...players.data]
      .sort((a, b) => a.name.localeCompare(b.name))
      .slice(0, 12);
  }, [players.data]);

  const tabs = [
    { key: "picks", label: "Today's Picks", icon: "\uD83C\uDFAF" },
    { key: "schedule", label: "Schedule", icon: "\uD83D\uDCC5" },
    { key: "steam", label: "Steam Moves", icon: "\uD83D\uDD25" },
    { key: "model", label: "Model Info", icon: "\uD83D\uDCCA" },
    { key: "history", label: "Historical", icon: "\uD83D\uDCC8" },
  ];

  return (
    <>
      <div className="page-header">
        <img src="/logo.png" alt="BullzIQ" className="logo-hero" style={{ width: 200 }} />
      </div>
      <hr className="divider" />

      <div className="metrics-row">
        <div className="metric-card">
          <div className="label">30-Day Record</div>
          <div className="value">{mr ? `${mr.wins}–${mr.losses}` : "—"}</div>
          <div className="delta">{mr ? `${(mr.win_rate * 100).toFixed(1)}% win rate` : ""}</div>
        </div>
        <div className="metric-card">
          <div className="label">Model ROI (30d)</div>
          <div className="value">{mr ? `+${mr.roi_pct.toFixed(1)}%` : "—"}</div>
          <div className="delta">vs. flat bet</div>
        </div>
        <div className="metric-card">
          <div className="label">Active Picks Today</div>
          <div className="value">{picks.data ? picks.data.length : "—"}</div>
          <div className="delta">all matches</div>
        </div>
        <div className="metric-card">
          <div className="label">Best Edge Today</div>
          <div className="value">{bestEdge !== null ? (bestEdge > 0 ? `+${bestEdge.toFixed(1)}%` : `${bestEdge.toFixed(1)}%`) : "—"}</div>
          <div className="delta">vs. DraftKings line</div>
        </div>
      </div>

      <hr className="divider" />

      <Tabs tabs={tabs}>
        <div key="picks">
          <h3>Today&apos;s Model Picks</h3>
          <div className="grid-2-1" style={{ marginBottom: 16 }}>
            <div>
              <label>Minimum edge %</label>
              <input
                type="range"
                min={0}
                max={8}
                step={0.5}
                value={minEdge}
                onChange={(e) => setMinEdge(parseFloat(e.target.value))}
              />
              <div style={{ fontSize: "0.8rem", color: "var(--biq-muted)", marginTop: 2 }}>
                {minEdge.toFixed(1)}%
              </div>
            </div>
            <div>
              <label>Sort by</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)}>
                <option value="edge">Edge %</option>
                <option value="time">Match time</option>
                <option value="confidence">Confidence</option>
              </select>
            </div>
          </div>

          {filteredPicks.length === 0 ? (
            <div className="empty-state">
              No picks meet the current edge filter. Lower the slider to see more.
            </div>
          ) : (
            filteredPicks.map((pk) => (
              <div key={pk.pick_id} className="card">
                <div className="grid-3-1">
                  <div>
                    <strong>{pk.player1}</strong> vs <strong>{pk.player2}</strong>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginTop: 2 }}>
                      {pk.tournament} · {pk.round} · {formatTime(pk.match_date)}
                    </div>
                  </div>
                  <div style={{ textAlign: "right", display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 4 }}>
                    <span className={`badge ${getEdgeBadgeClass(pk.edge_pct)}`}>
                      {getEdgeLabel(pk.edge_pct)}
                    </span>
                    <span className={`badge ${getConfBadgeClass(pk.confidence)}`} style={{ border: "none", padding: "3px 0", fontSize: "0.78rem" }}>
                      ● {pk.confidence}
                    </span>
                  </div>
                </div>
                <hr className="divider" />
                <div className="metrics-row" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 0 }}>
                  <div className="metric-card">
                    <div className="label">Pick</div>
                    <div className="value" style={{ fontSize: "1rem" }}>{pk.pick}</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">DK Odds</div>
                    <div className="value" style={{ fontSize: "1rem" }}>{formatAmericanOdds(pk.dk_odds)}</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">Model Prob</div>
                    <div className="value" style={{ fontSize: "1rem" }}>{(pk.model_prob * 100).toFixed(1)}%</div>
                  </div>
                  <div className="metric-card">
                    <div className="label">DK Implied</div>
                    <div className="value" style={{ fontSize: "1rem" }}>{(pk.dk_implied * 100).toFixed(1)}%</div>
                  </div>
                </div>
                {pk.reasoning && (
                  <div style={{ marginTop: 12 }}>
                    <button
                      onClick={() => toggleReasoning(pk.pick_id)}
                      style={{
                        background: "none",
                        border: "none",
                        color: "var(--biq-accent)",
                        cursor: "pointer",
                        fontSize: "0.85rem",
                        padding: 0,
                        fontFamily: "inherit",
                      }}
                    >
                      {expandedReasoning[pk.pick_id] ? "▾ Hide reasoning" : "▸ Show reasoning"}
                    </button>
                    {expandedReasoning[pk.pick_id] && (
                      <div className="info-box" style={{ marginTop: 6 }}>
                        {pk.reasoning}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        <div key="schedule">
          <h3>Upcoming PDC Matches (DraftKings covered)</h3>
          <div style={{ marginBottom: 16, maxWidth: 300 }}>
            <label>Days ahead</label>
            <input
              type="range"
              min={1}
              max={14}
              step={1}
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
            />
            <div style={{ fontSize: "0.8rem", color: "var(--biq-muted)", marginTop: 2 }}>
              {days} days
            </div>
          </div>

          {matches.loading ? (
            <div className="empty-state">Loading schedule…</div>
          ) : mergedSchedule.length === 0 ? (
            <div className="empty-state">No upcoming matches in the database.</div>
          ) : (
            Object.entries(groupedSchedule).map(([tournament, tMatches]) => (
              <div key={tournament} style={{ marginBottom: 20 }}>
                <h4 style={{ marginBottom: 8 }}>{tournament}</h4>
                {tMatches.map((m) => (
                  <div key={m.match_id} className="card">
                    <div style={{ display: "grid", gridTemplateColumns: "2fr 1.5fr 0.3fr 1.5fr 1.5fr", alignItems: "center", gap: 8 }}>
                      <div>
                        <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>{formatTime(m.match_date)}</div>
                        <div style={{ color: "var(--biq-muted)", fontSize: "0.78rem" }}>{m.round}</div>
                      </div>
                      <div><strong>{m.player1}</strong></div>
                      <div style={{ textAlign: "center", color: "var(--biq-muted)" }}>vs</div>
                      <div><strong>{m.player2}</strong></div>
                      <div>
                        {m.odds ? (
                          <div>
                            <span style={{ color: "var(--biq-accent2)", fontWeight: 700, fontSize: "1.05rem" }}>
                              {formatAmericanOdds(m.odds.p1_odds)} / {formatAmericanOdds(m.odds.p2_odds)}
                            </span>
                          </div>
                        ) : (
                          <span style={{ color: "var(--biq-muted)", fontSize: "0.85rem" }}>Lines not open yet</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ))
          )}
        </div>

        <div key="steam">
          <h3>🔥 Steam Moves — Significant Line Movement</h3>
          <p style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginBottom: 16 }}>
            Flagged when implied probability shifts ≥3pp within 30 minutes.
          </p>

          {steamEvents.loading ? (
            <div className="empty-state">Loading steam events…</div>
          ) : !steamEvents.data || steamEvents.data.length === 0 ? (
            <div className="empty-state">No steam moves detected in the last 24 hours.</div>
          ) : (
            steamEvents.data.map((ev, idx) => (
              <div key={idx} className="card">
                <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr 1fr", alignItems: "center", gap: 16 }}>
                  <div>
                    <strong>{ev.player1} vs {ev.player2}</strong>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginTop: 2 }}>{ev.tournament}</div>
                  </div>
                  <div>
                    <span className="badge badge-steam">
                      {ev.shift_pct > 0 ? "▲" : "▼"} STEAM: {ev.player_steamed}
                    </span>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem", marginTop: 4 }}>
                      {formatAmericanOdds(ev.opening_odds)} → {formatAmericanOdds(ev.current_odds)} ({ev.shift_pct > 0 ? "+" : ""}{ev.shift_pct}pp)
                    </div>
                  </div>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem", textAlign: "right" }}>
                    {formatTime(ev.detected_at)}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        <div key="model">
          <h3>How the Model Works</h3>
          <div className="grid-2" style={{ alignItems: "start" }}>
            <div>
              <div className="card">
                <h4>Elo Rating System</h4>
                <p style={{ fontSize: "0.9rem", lineHeight: 1.6, marginTop: 8 }}>
                  Every player starts with a base Elo rating. After each match, ratings update using
                  a K-factor system calibrated for darts. Higher-rated players gain less from beating
                  lower-rated opponents and lose more from upsets.
                </p>
              </div>
              <div className="card">
                <h4>Match Predictor</h4>
                <p style={{ fontSize: "0.9rem", lineHeight: 1.6, marginTop: 8 }}>
                  The model converts Elo differentials into win probabilities using a logistic function.
                  Format adjustments (best-of legs) are applied to account for match length — longer
                  formats slightly favor the stronger player.
                </p>
              </div>
              <div className="card">
                <h4>Edge Calculation</h4>
                <p style={{ fontSize: "0.9rem", lineHeight: 1.6, marginTop: 8 }}>
                  The model compares its predicted win probability against the DraftKings implied
                  probability. When the model probability exceeds the implied probability by a
                  meaningful margin, that gap is flagged as an edge.
                </p>
              </div>
            </div>
            <div>
              <div className="card">
                <h4>30-Day Performance Summary</h4>
                {mr ? (
                  <div className="table-wrap">
                    <table>
                      <tbody>
                        <tr><td style={{ fontWeight: 600 }}>Record</td><td>{mr.wins}–{mr.losses} ({mr.days} days)</td></tr>
                        <tr><td style={{ fontWeight: 600 }}>Win Rate</td><td>{(mr.win_rate * 100).toFixed(1)}%</td></tr>
                        <tr><td style={{ fontWeight: 600 }}>ROI</td><td>+{mr.roi_pct.toFixed(1)}%</td></tr>
                        <tr><td style={{ fontWeight: 600 }}>Avg Edge</td><td>+{mr.avg_edge.toFixed(1)}%</td></tr>
                        <tr><td style={{ fontWeight: 600 }}>Brier Score</td><td>{mr.brier_score.toFixed(3)}</td></tr>
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="empty-state">Loading performance data…</div>
                )}
              </div>

              <div className="info-box" style={{ marginBottom: 16 }}>
                <strong>Brier Score</strong> measures prediction accuracy on a 0–1 scale where 0 is perfect.
                A score of 0.25 is equivalent to random guessing. Lower is better.
              </div>

              {edgeDistribution.length > 0 && (
                <div className="card">
                  <h4 style={{ marginBottom: 12 }}>Edge Distribution — Active Picks</h4>
                  <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 200, padding: "0 8px" }}>
                    {edgeDistribution.map((bin, i) => (
                      <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                        <div style={{ fontSize: "0.7rem", color: "var(--biq-muted)", marginBottom: 2 }}>{bin.count || ""}</div>
                        <div
                          style={{
                            width: "100%",
                            height: `${(bin.count / maxBinCount) * 180}px`,
                            background: "var(--biq-accent2)",
                            borderRadius: "3px 3px 0 0",
                            minHeight: bin.count > 0 ? 4 : 0,
                          }}
                        />
                      </div>
                    ))}
                  </div>
                  <div style={{ display: "flex", gap: 4, padding: "4px 8px 0" }}>
                    {edgeDistribution.map((bin, i) => (
                      <div key={i} style={{ flex: 1, textAlign: "center", fontSize: "0.65rem", color: "var(--biq-muted)" }}>
                        {bin.label}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <div key="history">
          <h3>📈 Historical Model Performance (2015–Present)</h3>
          <p style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginBottom: 20 }}>
            Tracking model performance across years and eras of professional darts.
          </p>

          <h4>Elo Rating Trajectories</h4>
          <div style={{ marginBottom: 12, maxWidth: 600 }}>
            <label>Select players</label>
            <select
              multiple
              value={selectedEloNames}
              onChange={(e) => setEloPlayers(Array.from(e.target.selectedOptions, (o) => o.value))}
              style={{ height: 140 }}
            >
              {eloPlayerNames.map((p) => (
                <option key={p.id} value={p.name}>{p.name}</option>
              ))}
            </select>
          </div>

          {eloChartData.length > 0 ? (
            <div className="card" style={{ overflow: "hidden" }}>
              <svg viewBox="0 0 900 380" style={{ width: "100%", height: 380 }}>
                {(() => {
                  const allPoints = eloChartData.flatMap((g) => g.entries);
                  const minTime = allPoints.reduce((m, p) => Math.min(m, new Date(p.recorded_at).getTime()), Infinity);
                  const maxTime = allPoints.reduce((m, p) => Math.max(m, new Date(p.recorded_at).getTime()), -Infinity);
                  const minElo = allPoints.reduce((m, p) => Math.min(m, p.elo), Infinity);
                  const maxElo = allPoints.reduce((m, p) => Math.max(m, p.elo), -Infinity);
                  const pad = { top: 20, right: 20, bottom: 40, left: 60 };
                  const w = 900 - pad.left - pad.right;
                  const h = 380 - pad.top - pad.bottom;
                  const eloRange = maxElo - minElo || 1;
                  const timeRange = maxTime - minTime || 1;

                  function x(t: number) { return pad.left + ((t - minTime) / timeRange) * w; }
                  function y(e: number) { return pad.top + h - ((e - minElo) / eloRange) * h; }

                  const tickCount = 5;
                  const eloTicks = Array.from({ length: tickCount }, (_, i) => minElo + (eloRange / (tickCount - 1)) * i);

                  return (
                    <>
                      {eloTicks.map((e, i) => (
                        <g key={i}>
                          <line x1={pad.left} y1={y(e)} x2={900 - pad.right} y2={y(e)} stroke="#e5e7eb" strokeWidth={1} />
                          <text x={pad.left - 8} y={y(e) + 4} textAnchor="end" fontSize={11} fill="#607a95">
                            {Math.round(e)}
                          </text>
                        </g>
                      ))}
                      {eloChartData.map((g, gi) => {
                        const points = g.entries.map((e) => `${x(new Date(e.recorded_at).getTime()).toFixed(1)},${y(e.elo).toFixed(1)}`).join(" ");
                        return (
                          <g key={gi}>
                            <polyline points={points} fill="none" stroke={lineColors[gi % lineColors.length]} strokeWidth={2} />
                            <text
                              x={x(new Date(g.entries[g.entries.length - 1].recorded_at).getTime()) + 4}
                              y={y(g.entries[g.entries.length - 1].elo) - 6}
                              fontSize={10}
                              fill={lineColors[gi % lineColors.length]}
                              fontWeight={600}
                            >
                              {g.name}
                            </text>
                          </g>
                        );
                      })}
                    </>
                  );
                })()}
              </svg>
            </div>
          ) : (
            <div className="empty-state">Select players to view Elo trajectories.</div>
          )}

          <hr className="divider" />

          <h4>Year-by-Year Match Volume &amp; Model Accuracy</h4>
          {yearlyStats.data && yearlyStats.data.length > 0 ? (() => {
            const ysData = yearlyStats.data!;
            const maxMatches = Math.max(...ysData.map((y) => y.total_matches));
            return (<>
              <div className="card" style={{ marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "flex-end", gap: 6, height: 200, padding: "0 8px" }}>
                  {ysData.map((ys, i) => {
                    return (
                      <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}>
                        <div style={{ fontSize: "0.7rem", color: "var(--biq-muted)", marginBottom: 2 }}>{ys.total_matches}</div>
                        <div
                          style={{
                            width: "100%",
                            height: `${(ys.total_matches / maxMatches) * 180}px`,
                            background: "var(--biq-accent2)",
                            borderRadius: "3px 3px 0 0",
                            minHeight: 4,
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
                <div style={{ display: "flex", gap: 6, padding: "4px 8px 0" }}>
                  {ysData.map((ys, i) => (
                    <div key={i} style={{ flex: 1, textAlign: "center", fontSize: "0.75rem", color: "var(--biq-muted)" }}>
                      {ys.year}
                    </div>
                  ))}
                </div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Year</th><th>Matches</th></tr>
                  </thead>
                  <tbody>
                    {ysData.map((ys) => (
                      <tr key={ys.year}>
                        <td>{ys.year}</td>
                        <td>{ys.total_matches}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
            );
          })() : (
            <div className="empty-state">No yearly statistics available.</div>
          )}

          <hr className="divider" />

          <h4>Era Performance — Top Win Rates by Period</h4>
          {eraStats.data && eraStats.data.length > 0 ? (
            <div className="card">
              {(() => {
                const eras = [...new Set(eraStats.data!.map((e) => e.era))];
                const eraColors: Record<number, string[]> = {
                  0: ["#0284c7", "#38bdf8", "#bae6fd"],
                  1: ["#f97316", "#fb923c", "#fed7aa"],
                  2: ["#15803d", "#4ade80", "#bbf7d0"],
                  3: ["#dc2626", "#f87171", "#fecaca"],
                  4: ["#8b5cf6", "#a78bfa", "#ddd6fe"],
                };
                return eras.map((era, ei) => {
                  const eraEntries = eraStats.data!.filter((e) => e.era === era).sort((a, b) => b.win_rate - a.win_rate);
                  const maxRate = Math.max(...eraEntries.map((e) => e.win_rate));
                  const colors = eraColors[ei % Object.keys(eraColors).length];
                  return (
                    <div key={era} style={{ marginBottom: 20 }}>
                      <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--biq-text)", marginBottom: 8 }}>{era}</div>
                      <div style={{ display: "flex", alignItems: "flex-end", gap: 8, height: 120, padding: "0 4px" }}>
                        {eraEntries.slice(0, 8).map((entry, i) => (
                          <div key={i} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", minWidth: 40 }}>
                            <div style={{ fontSize: "0.65rem", color: "var(--biq-muted)", marginBottom: 2 }}>
                              {(entry.win_rate * 100).toFixed(0)}%
                            </div>
                            <div
                              style={{
                                width: "100%",
                                height: `${(entry.win_rate / (maxRate || 1)) * 100}px`,
                                background: colors[i % colors.length],
                                borderRadius: "3px 3px 0 0",
                                minHeight: 4,
                              }}
                            />
                            <div
                              style={{
                                fontSize: "0.6rem",
                                color: "var(--biq-muted)",
                                marginTop: 4,
                                textAlign: "center",
                                lineHeight: 1.2,
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                                maxWidth: 80,
                              }}
                              title={entry.player_name}
                            >
                              {entry.player_name}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                });
              })()}
            </div>
          ) : (
            <div className="empty-state">No era performance data available.</div>
          )}
        </div>
      </Tabs>

      <BettingOracleFooter />
    </>
  );
}
