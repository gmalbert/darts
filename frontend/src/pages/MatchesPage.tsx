import { useState, useMemo } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { TabPanel } from "../components/controls/Tabs";
import { BettingOracleFooter } from "../components/legal/Footer";
import { formatAmericanOdds, formatDateTime, natFlag } from "../utils/formatters";
import type { Match, MatchDetail, OddsEntry, OddsHistoryEntry, H2HResult } from "../types";

export default function MatchesPage() {
  const [activeTab, setActiveTab] = useState("upcoming");
  const [days, setDays] = useState(7);
  const [filterTournament, setFilterTournament] = useState("All");
  const [filterPlayer, setFilterPlayer] = useState("All");
  const [selectedMatchId, setSelectedMatchId] = useState<number | null>(null);

  const { data: upcomingMatches } = useApi(() => api.matches({ upcoming: true, days }), [days]);
  const { data: recentMatches } = useApi(() => api.matches({ limit: 100 }), []);
  const { data: oddsList } = useApi(() => api.odds(), []);
  const { data: allUpcoming } = useApi(() => api.matches({ upcoming: true, days: 14 }), []);

  const { data: matchDetail } = useApi<MatchDetail | null>(
    () => selectedMatchId ? api.match(selectedMatchId) : Promise.resolve(null),
    [selectedMatchId]
  );
  const { data: oddsHistory } = useApi<OddsHistoryEntry[] | null>(
    () => selectedMatchId ? api.oddsHistory(selectedMatchId) : Promise.resolve(null),
    [selectedMatchId]
  );

  const { data: h2hData } = useApi<H2HResult | null>(
    () => matchDetail ? api.h2h(matchDetail.player1_id, matchDetail.player2_id) : Promise.resolve(null),
    [matchDetail]
  );

  const oddsMap = useMemo(() => {
    const m = new Map<number, OddsEntry>();
    (oddsList ?? []).forEach((o: OddsEntry) => m.set(o.match_id, o));
    return m;
  }, [oddsList]);

  const groupedUpcoming = useMemo(() => {
    const groups: Record<string, Match[]> = {};
    (upcomingMatches ?? []).forEach((m: Match) => {
      if (!groups[m.tournament]) groups[m.tournament] = [];
      groups[m.tournament].push(m);
    });
    return groups;
  }, [upcomingMatches]);

  const tournaments = useMemo(() => {
    const set = new Set<string>();
    (recentMatches ?? []).forEach((m: any) => set.add(m.tournament));
    return Array.from(set);
  }, [recentMatches]);

  const players = useMemo(() => {
    const set = new Set<string>();
    (recentMatches ?? []).forEach((m: any) => {
      set.add(m.player1);
      set.add(m.player2);
    });
    return Array.from(set);
  }, [recentMatches]);

  const filteredRecent = useMemo(() => {
    return (recentMatches ?? []).filter((m: any) => {
      if (filterTournament !== "All" && m.tournament !== filterTournament) return false;
      if (filterPlayer !== "All" && m.player1 !== filterPlayer && m.player2 !== filterPlayer)
        return false;
      return true;
    });
  }, [recentMatches, filterTournament, filterPlayer]);

  const tabDefs = [
    { key: "upcoming", label: "Upcoming", icon: "📅" },
    { key: "results", label: "Recent Results", icon: "📋" },
    { key: "detail", label: "Match Detail", icon: "🔍" },
  ];

  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1rem" }}>
      <div className="page-header">
        <h2>BullzIQ Match Center</h2>
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

      <TabPanel tabKey="upcoming" active={activeTab}>
        <h3>Upcoming PDC Fixtures</h3>
        <div className="card" style={{ marginBottom: "1rem", padding: "1rem" }}>
          <label style={{ fontSize: "0.85rem" }}>
            Show matches over next{" "}
            <strong>{days}</strong> day{days !== 1 && "s"}
            <input
              type="range"
              min={1}
              max={14}
              value={days}
              onChange={(e) => setDays(Number(e.target.value))}
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
        </div>
        {(!upcomingMatches || upcomingMatches.length === 0) ? (
          <div className="empty-state">No upcoming matches in the database.</div>
        ) : (
          Object.entries(groupedUpcoming).map(([tournament, matches]) => (
            <div key={tournament} style={{ marginBottom: "1.5rem" }}>
              <h4>{tournament}</h4>
              {matches.map((m: Match) => {
                const odds = oddsMap.get(m.match_id);
                const bo = (m.legs_to_win ?? 6) * 2 - 1;
                return (
                  <div className="card" key={m.match_id} style={{ marginBottom: 8 }}>
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "2fr 2.5fr 0.3fr 2.5fr 2fr 1.5fr",
                        alignItems: "center",
                        gap: 8,
                      }}
                    >
                      <div>
                        <div style={{ color: "#888", fontSize: "0.82rem" }}>
                          {formatDateTime(m.match_date)}
                        </div>
                        <div style={{ color: "#888", fontSize: "0.75rem" }}>
                          {m.round || "TBD"}
                        </div>
                      </div>
                      <div>
                        <span>{natFlag(m.p1_nationality)}</span> <strong>{m.player1}</strong>
                        {odds && (
                          <div style={{ color: "#888", fontSize: "0.82rem" }}>
                            {(odds.p1_implied * 100).toFixed(1)}% implied
                          </div>
                        )}
                      </div>
                      <div style={{ textAlign: "center", color: "#888" }}>vs</div>
                      <div>
                        <span>{natFlag(m.p2_nationality)}</span> <strong>{m.player2}</strong>
                        {odds && (
                          <div style={{ color: "#888", fontSize: "0.82rem" }}>
                            {(odds.p2_implied * 100).toFixed(1)}% implied
                          </div>
                        )}
                      </div>
                      <div style={{ fontWeight: 700 }}>
                        {odds ? (
                          <span>
                            <span className={odds.p1_odds > 0 ? "odds-positive" : "odds-negative"}>
                              {formatAmericanOdds(odds.p1_odds)}
                            </span>
                            {" / "}
                            <span className={odds.p2_odds > 0 ? "odds-positive" : "odds-negative"}>
                              {formatAmericanOdds(odds.p2_odds)}
                            </span>
                          </span>
                        ) : (
                          <span style={{ color: "#888" }}>Lines not open yet</span>
                        )}
                      </div>
                      <div style={{ color: "var(--accent2, #e040fb)", fontSize: "0.78rem" }}>
                        BO{bo}
                      </div>
                    </div>
                  </div>
                );
              })}
              <div style={{ height: "1.5rem" }} />
            </div>
          ))
        )}
      </TabPanel>

      <TabPanel tabKey="results" active={activeTab}>
        <h3>Recent Results</h3>
        <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
          <select
            className="card"
            value={filterTournament}
            onChange={(e) => setFilterTournament(e.target.value)}
            style={{ padding: "6px 12px", borderRadius: 6 }}
          >
            <option value="All">All</option>
            {tournaments.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          <select
            className="card"
            value={filterPlayer}
            onChange={(e) => setFilterPlayer(e.target.value)}
            style={{ padding: "6px 12px", borderRadius: 6 }}
          >
            <option value="All">All</option>
            {players.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>
        {filteredRecent.length === 0 ? (
          <div className="empty-state">No results in the database.</div>
        ) : (
          <div className="table-wrap" style={{ maxHeight: 550, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Tournament</th>
                  <th>Round</th>
                  <th>Player 1</th>
                  <th>Score</th>
                  <th>Player 2</th>
                  <th>Winner</th>
                </tr>
              </thead>
              <tbody>
                {filteredRecent.map((m: any) => (
                  <tr key={m.match_id}>
                    <td>
                      {new Date(m.date).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </td>
                    <td>{m.tournament}</td>
                    <td>{m.round}</td>
                    <td>{m.player1}</td>
                    <td style={{ fontWeight: 700, textAlign: "center" }}>{m.score}</td>
                    <td>{m.player2}</td>
                    <td style={{ fontWeight: 700 }}>{m.winner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TabPanel>

      <TabPanel tabKey="detail" active={activeTab}>
        <h3>Match Detail — Odds Movement</h3>
        <div className="card" style={{ marginBottom: 16, padding: "0.75rem 1rem" }}>
          <label style={{ fontSize: "0.85rem" }}>
            Select a match{" "}
            <select
              value={selectedMatchId ?? ""}
              onChange={(e) => setSelectedMatchId(Number(e.target.value) || null)}
              style={{ padding: "4px 8px", borderRadius: 6, marginLeft: 8 }}
            >
              <option value="">-- select --</option>
              {(allUpcoming ?? []).map((m: Match) => (
                <option key={m.match_id} value={m.match_id}>
                  {m.player1} vs {m.player2} ({m.tournament})
                </option>
              ))}
            </select>
          </label>
        </div>

        {!selectedMatchId && (
          <div className="empty-state">No upcoming matches available for detail view.</div>
        )}

        {matchDetail && (
          <div>
            <h4>{matchDetail.player1} vs {matchDetail.player2}</h4>
            <div style={{ color: "#888", marginBottom: 12 }}>
              {matchDetail.tournament} · {matchDetail.round}
            </div>

            <div className="card" style={{ marginBottom: 16 }}>
              <div className="metrics-row">
                <div className="metric-card">
                  <div className="label">{matchDetail.player1} Score</div>
                  <div className="value">{matchDetail.score1}</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player2} Score</div>
                  <div className="value">{matchDetail.score2}</div>
                </div>
                <div className="metric-card">
                  <div className="label">Legs to Win</div>
                  <div className="value">{matchDetail.legs_to_win}</div>
                </div>
                {matchDetail.winner && (
                  <div className="metric-card">
                    <div className="label">Winner</div>
                    <div className="value">{matchDetail.winner}</div>
                  </div>
                )}
              </div>
            </div>

            <div className="card" style={{ marginBottom: 16 }}>
              <div className="metrics-row">
                <div className="metric-card">
                  <div className="label">{matchDetail.player1} Avg</div>
                  <div className="value">{matchDetail.avg_p1?.toFixed(1)}</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player2} Avg</div>
                  <div className="value">{matchDetail.avg_p2?.toFixed(1)}</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player1} Checkout %</div>
                  <div className="value">{matchDetail.checkout_pct_p1?.toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player2} Checkout %</div>
                  <div className="value">{matchDetail.checkout_pct_p2?.toFixed(1)}%</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player1} 180s</div>
                  <div className="value">{matchDetail.legs_180_p1}</div>
                </div>
                <div className="metric-card">
                  <div className="label">{matchDetail.player2} 180s</div>
                  <div className="value">{matchDetail.legs_180_p2}</div>
                </div>
              </div>
            </div>

            <div className="divider" />

            {oddsHistory && oddsHistory.length > 0 ? (
              <>
                <div className="table-wrap" style={{ marginBottom: 16 }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>{matchDetail.player1} Implied %</th>
                        <th>{matchDetail.player2} Implied %</th>
                      </tr>
                    </thead>
                    <tbody>
                      {oddsHistory.map((h: OddsHistoryEntry, i: number) => (
                        <tr key={i}>
                          <td>{formatDateTime(h.time)}</td>
                          <td>{(h.p1_implied * 100).toFixed(1)}%</td>
                          <td>{(h.p2_implied * 100).toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <h4>Line Movement Summary</h4>
                <div className="card">
                  <div className="metrics-row">
                    {oddsHistory.length >= 2 && (
                      <>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player1} — Open</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[0].p1_odds)}</div>
                        </div>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player1} — Current</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[oddsHistory.length - 1].p1_odds)}</div>
                          <div className="delta">
                            {oddsHistory[oddsHistory.length - 1].p1_odds - oddsHistory[0].p1_odds > 0 ? "+" : ""}
                            {oddsHistory[oddsHistory.length - 1].p1_odds - oddsHistory[0].p1_odds}
                          </div>
                        </div>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player2} — Open</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[0].p2_odds)}</div>
                        </div>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player2} — Current</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[oddsHistory.length - 1].p2_odds)}</div>
                          <div className="delta">
                            {oddsHistory[oddsHistory.length - 1].p2_odds - oddsHistory[0].p2_odds > 0 ? "+" : ""}
                            {oddsHistory[oddsHistory.length - 1].p2_odds - oddsHistory[0].p2_odds}
                          </div>
                        </div>
                      </>
                    )}
                    {oddsHistory.length === 1 && (
                      <>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player1} Odds</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[0].p1_odds)}</div>
                        </div>
                        <div className="metric-card">
                          <div className="label">{matchDetail.player2} Odds</div>
                          <div className="value">{formatAmericanOdds(oddsHistory[0].p2_odds)}</div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </>
            ) : (
              <div className="info-box" style={{ marginBottom: 16 }}>
                No odds history available for this match.
              </div>
            )}

            <div className="divider" />

            <h4>Historical Head-to-Head</h4>
            {h2hData && h2hData.matches && h2hData.matches.length > 0 ? (
              <>
                <div className="card" style={{ marginBottom: 16 }}>
                  <div className="metrics-row">
                    <div className="metric-card">
                      <div className="label">{matchDetail.player1} Wins</div>
                      <div className="value">{h2hData.p1_wins}</div>
                    </div>
                    <div className="metric-card">
                      <div className="label">Total</div>
                      <div className="value">{h2hData.p1_wins + h2hData.p2_wins}</div>
                    </div>
                    <div className="metric-card">
                      <div className="label">{matchDetail.player2} Wins</div>
                      <div className="value">{h2hData.p2_wins}</div>
                    </div>
                  </div>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Winner</th>
                      </tr>
                    </thead>
                    <tbody>
                      {h2hData.matches.map((h, i) => {
                        const winnerName =
                          h.winner_id === matchDetail.player1_id
                            ? matchDetail.player1
                            : matchDetail.player2;
                        return (
                          <tr key={i}>
                            <td>{formatDateTime(h.date)}</td>
                            <td style={{ fontWeight: 700, textAlign: "center" }}>{h.score}</td>
                            <td style={{ fontWeight: 700 }}>{winnerName}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <div className="empty-state">No previous meetings found.</div>
            )}
          </div>
        )}
      </TabPanel>

      <div className="page-footer" style={{ marginTop: 24 }}>
        <BettingOracleFooter />
      </div>
    </div>
  );
}