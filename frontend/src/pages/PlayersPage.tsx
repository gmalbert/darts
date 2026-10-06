import { useState, useMemo, useEffect } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { Tabs } from "../components/controls/Tabs";
import { PlayerPicker } from "../components/controls/PlayerPicker";
import { BettingOracleFooter } from "../components/legal/Footer";
import { natFlag } from "../utils/formatters";
import type { Player, PlayerStats, EloHistoryEntry, MatchHistoryEntry, H2HResult } from "../types";

// Tabs mounts only the active panel, so this is just a plain layout wrapper.
function TabPanel({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>;
}

export default function PlayersPage() {
  const { data: players } = useApi(() => api.players(), []);
  const [activeTab, setActiveTab] = useState("rankings");
  const [selectedPlayer, setSelectedPlayer] = useState<Player | null>(null);
  const [p1, setP1] = useState<Player | null>(null);
  const [p2, setP2] = useState<Player | null>(null);

  const selectedPlayerId = selectedPlayer?.id ?? null;

  const { data: player } = useApi(
    () => selectedPlayerId ? api.player(selectedPlayerId) : Promise.resolve(null),
    [selectedPlayerId]
  );
  const { data: eloHistory } = useApi(
    () => selectedPlayerId ? api.playerEloHistory(selectedPlayerId) : Promise.resolve([]),
    [selectedPlayerId]
  );
  const { data: matchHistory } = useApi(
    () => selectedPlayerId ? api.playerMatches(selectedPlayerId, 20) : Promise.resolve([]),
    [selectedPlayerId]
  );
  const { data: h2h } = useApi(
    () => p1 && p2 && p1.id !== p2.id
      ? api.h2h(p1.id, p2.id)
      : Promise.resolve(null),
    [p1, p2]
  );

  const rankedPlayers = useMemo(() => {
    if (!players) return [];
    return [...players].sort((a, b) => b.elo - a.elo);
  }, [players]);

  const [allStats, setAllStats] = useState<Map<number, PlayerStats>>(new Map());

  useEffect(() => {
    if (!players || players.length === 0) return;
    let cancelled = false;
    const ids = players.map((p) => p.id);
    api.playerStatsBatch(ids)
      .then((statsList) => {
        if (cancelled) return;
        const map = new Map<number, PlayerStats>();
        statsList.forEach((s) => map.set(s.player_id, s));
        setAllStats(map);
      })
      .catch(() => {});
    return () => { cancelled = true; };
  }, [players]);

  // Mirror Streamlit: it reads player stats straight from the cache server-side, so derive
  // the profile from the batch cache instead of hitting /players/{id}/stats (404s when empty).
  const playerStats = selectedPlayerId ? (allStats.get(selectedPlayerId) ?? null) : null;

  // Mirror Streamlit: preselect the highest-ranked player so the profile is never empty.
  useEffect(() => {
    if (selectedPlayer || rankedPlayers.length === 0) return;
    setSelectedPlayer(rankedPlayers[0]);
  }, [rankedPlayers, selectedPlayer]);

  // Preselect both H2H slots once the roster is known.
  useEffect(() => {
    if (rankedPlayers.length < 2) return;
    setP1((cur) => cur ?? rankedPlayers[0]);
    setP2((cur) => cur ?? rankedPlayers[1]);
  }, [rankedPlayers]);

  const openProfile = (p: Player) => {
    setSelectedPlayer(p);
    setActiveTab("profile");
  };

  const tabs = [
    { key: "rankings", label: "Rankings", icon: "\uD83C\uDFC6" },
    { key: "profile", label: "Player Profile", icon: "\uD83D\uDC64" },
    { key: "h2h", label: "Head-to-Head", icon: "\u2694\uFE0F" },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>🎯 Player Profiles &amp; Rankings</h2>
        <p className="caption">PDC player Elo ratings, career stats, form, and head-to-head records.</p>
      </div>
      <hr className="divider" />

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab}>
        <TabPanel>
          <RankingsTab
            players={rankedPlayers}
            allPlayers={players}
            allStats={allStats}
            selectedPlayerId={selectedPlayerId}
            onOpenProfile={openProfile}
          />
        </TabPanel>
        <TabPanel>
          <ProfileTab
            allPlayers={players}
            defaultPlayer={rankedPlayers[0]}
            selectedPlayer={selectedPlayer}
            onSelect={setSelectedPlayer}
            player={player ?? null}
            stats={playerStats ?? null}
            eloHistory={eloHistory ?? []}
            matchHistory={matchHistory ?? []}
          />
        </TabPanel>
        <TabPanel>
          <H2HTab
            allPlayers={players}
            p1={p1}
            p2={p2}
            onP1Change={setP1}
            onP2Change={setP2}
            h2h={h2h ?? null}
          />
        </TabPanel>
      </Tabs>
      <BettingOracleFooter />
    </div>
  );
}

function RankingsTab({
  players, allPlayers, allStats, selectedPlayerId, onOpenProfile,
}: {
  players: Player[];
  allPlayers: Player[] | undefined;
  allStats: Map<number, PlayerStats>;
  selectedPlayerId: number | null;
  onOpenProfile: (p: Player) => void;
}) {
  const maxElo = players.length > 0 ? players[0].elo : 1;

  if (!allPlayers || allPlayers.length === 0) {
    return <div className="empty-state">No player data. Ensure the database is seeded.</div>;
  }

  return (
    <div>
      <h3>BullzIQ Elo Rankings</h3>

      <div style={{ marginTop: 16, marginBottom: 24 }}>
        {players.slice(0, 16).map((p) => {
          const pct = (p.elo / maxElo) * 100;
          return (
            <div key={p.id} style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 160, fontSize: "0.85rem", textAlign: "right", flexShrink: 0 }}>{p.name}</span>
              <div style={{ flex: 1, background: "var(--biq-bg3)", borderRadius: 4, height: 20 }}>
                <div style={{
                  width: `${pct}%`, height: "100%", borderRadius: 4,
                  background: "var(--biq-accent)",
                }} />
              </div>
              <span style={{ fontSize: "0.82rem", width: 60, textAlign: "right" }}>{Math.round(p.elo)}</span>
            </div>
          );
        })}
      </div>

      <h4>Full Rankings Table</h4>
      <p className="caption" style={{ marginBottom: 8 }}>
        Select any row to open that player&apos;s profile.
      </p>
      <div className="table-wrap" style={{ maxHeight: 500, overflow: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Rank</th>
              <th>🏳</th>
              <th>Player</th>
              <th>Nickname</th>
              <th>Elo</th>
              <th>3-Dart Avg</th>
              <th>Checkout %</th>
              <th>Win Rate (L20)</th>
            </tr>
          </thead>
          <tbody>
            {players.map((p, i) => (
              <tr
                key={p.id}
                className={[
                  "clickable",
                  p.id === selectedPlayerId ? "is-current" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                tabIndex={0}
                onClick={() => onOpenProfile(p)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onOpenProfile(p);
                  }
                }}
              >
                <td>{i + 1}</td>
                <td>{natFlag(p.nationality)}</td>
                <td style={{ fontWeight: 600 }}>{p.name}</td>
                <td style={{ color: "var(--biq-muted)" }}>{p.nickname ?? "\u2014"}</td>
                <td>{Math.round(p.elo)}</td>
                <td>{p.avg_3dart != null ? p.avg_3dart.toFixed(2) : "\u2014"}</td>
                <td>{p.checkout_pct != null ? `${p.checkout_pct.toFixed(1)}%` : "\u2014"}</td>
                <td>{(() => { const s = allStats.get(p.id); return s?.win_rate_l20 != null ? `${(s.win_rate_l20 * 100).toFixed(1)}%` : "\u2014"; })()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProfileTab({
  allPlayers, defaultPlayer, selectedPlayer, onSelect, player, stats, eloHistory, matchHistory,
}: {
  allPlayers: Player[] | undefined;
  defaultPlayer: Player | undefined;
  selectedPlayer: Player | null;
  onSelect: (p: Player) => void;
  player: Player | null;
  stats: PlayerStats | null;
  eloHistory: EloHistoryEntry[];
  matchHistory: MatchHistoryEntry[];
}) {
  return (
    <div>
      <h3>Player Profile</h3>
      <div style={{ marginBottom: 16, maxWidth: 420 }}>
        <PlayerPicker
          players={allPlayers ?? []}
          value={selectedPlayer}
          onChange={onSelect}
          onClear={() => defaultPlayer && onSelect(defaultPlayer)}
        />
      </div>

      {!selectedPlayer && (
        <div className="empty-state">Select a player to view their profile.</div>
      )}

      {selectedPlayer && !player && (
        <div className="empty-state">Player not found.</div>
      )}

      {player && (
        <>
          <div className="grid-1-3" style={{ marginBottom: 16 }}>
            <div className="card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: "4rem", lineHeight: 1 }}>{natFlag(player.nationality)}</div>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, marginTop: 8 }}>{player.name}</div>
              {player.nickname && (
                <div style={{ color: "var(--biq-muted)", fontStyle: "italic", marginTop: 4 }}>&ldquo;{player.nickname}&rdquo;</div>
              )}
            </div>
            <div className="metrics-row">
              <div className="metric-card">
                <div className="label">Elo Rating</div>
                <div className="value">{Math.round(player.elo).toLocaleString()}</div>
              </div>
              <div className="metric-card">
                <div className="label">PDC Ranking</div>
                <div className="value">{player.pdc_ranking != null ? `#${player.pdc_ranking}` : "\u2014"}</div>
              </div>
              <div className="metric-card">
                <div className="label">3-Dart Avg</div>
                <div className="value">{player.avg_3dart != null ? player.avg_3dart.toFixed(2) : "\u2014"}</div>
              </div>
              <div className="metric-card">
                <div className="label">Checkout %</div>
                <div className="value">{player.checkout_pct != null ? `${player.checkout_pct.toFixed(1)}%` : "\u2014"}</div>
              </div>
            </div>
          </div>

          <h4>Elo Rating History</h4>
          {eloHistory.length > 0 ? (
            <div style={{ marginBottom: 24 }}>
              <EloChart history={eloHistory} />
            </div>
          ) : (
            <div className="empty-state" style={{ marginBottom: 24 }}>No Elo history available for this player.</div>
          )}

          <h4>Detailed Stats</h4>
          {stats ? (
            <div className="grid-3" style={{ marginBottom: 24 }}>
              <div className="card">
                <div style={{ marginBottom: 12 }}>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>Win Rate (L20)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{stats.win_rate_l20 != null ? `${(stats.win_rate_l20 * 100).toFixed(1)}%` : "\u2014"}</div>
                </div>
                <div>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>PL Win Rate</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{stats.pl_win_rate != null ? `${(stats.pl_win_rate * 100).toFixed(1)}%` : "\u2014"}</div>
                </div>
              </div>
              <div className="card">
                <div style={{ marginBottom: 12 }}>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>3-Dart Avg (L10)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{stats.avg_3dart_l10 != null ? stats.avg_3dart_l10.toFixed(2) : "\u2014"}</div>
                </div>
                <div>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>Checkout % (L10)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{stats.checkout_pct_l10 != null ? `${stats.checkout_pct_l10.toFixed(1)}%` : "\u2014"}</div>
                </div>
              </div>
              <div className="card">
                <div style={{ marginBottom: 12 }}>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>Avg 180s/Match (L10)</div>
                  <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{stats.avg_180s_l10 != null ? stats.avg_180s_l10.toFixed(2) : "\u2014"}</div>
                </div>
                <div>
                  <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>Form (last 5):</div>
                  <div style={{ marginTop: 4 }}>
                    {stats.form_streak ? (
                      stats.form_streak.slice(-5).split("").map((ch, i) => (
                        <span key={i} style={{
                          display: "inline-block",
                          width: 28,
                          height: 28,
                          lineHeight: "28px",
                          textAlign: "center",
                          borderRadius: 4,
                          fontWeight: 700,
                          fontSize: "0.85rem",
                          marginRight: 4,
                          color: "#fff",
                          background: ch === "W" ? "var(--biq-pos)" : "var(--biq-neg)",
                        }}>
                          {ch}
                        </span>
                      ))
                    ) : (
                      "\u2014"
                    )}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state" style={{ marginBottom: 24 }}>No stats available.</div>
          )}

          <h4>Recent Matches (Last 20)</h4>
          {matchHistory.length > 0 ? (
            <div className="table-wrap" style={{ maxHeight: 500, overflow: "auto" }}>
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Opponent</th>
                    <th>Score</th>
                    <th>Result</th>
                    <th>Avg</th>
                    <th>Checkout%</th>
                    <th>180s</th>
                  </tr>
                </thead>
                <tbody>
                  {matchHistory.map((m, i) => (
                    <tr key={i}>
                      <td>{new Date(m.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</td>
                      <td>{m.opponent}</td>
                      <td>{m.score}</td>
                      <td>
                        {m.result === "W" ? (
                          <span style={{ color: "var(--biq-pos)", fontWeight: 700 }}>🟢 W</span>
                        ) : (
                          <span style={{ color: "var(--biq-neg)", fontWeight: 700 }}>🔴 L</span>
                        )}
                      </td>
                      <td>{m.avg != null ? m.avg.toFixed(2) : "\u2014"}</td>
                      <td>{m.checkout_pct != null ? `${m.checkout_pct.toFixed(1)}%` : "\u2014"}</td>
                      <td>{m["180s"] != null ? m["180s"] : "\u2014"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">No match history available.</div>
          )}
        </>
      )}
    </div>
  );
}

function EloChart({ history }: { history: EloHistoryEntry[] }) {
  if (history.length === 0) return null;

  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const svgW = 800;
  const svgH = 300;
  const chartW = svgW - padding.left - padding.right;
  const chartH = svgH - padding.top - padding.bottom;

  const eloValues = history.map((h) => h.elo);
  const minElo = Math.min(...eloValues, 1400);
  const maxElo = Math.max(...eloValues, 1600);
  const eloRange = maxElo - minElo || 1;

  const baseline1500 = chartH - ((1500 - minElo) / eloRange) * chartH;

  const points = history.map((h, i) => {
    const x = padding.left + (i / Math.max(history.length - 1, 1)) * chartW;
    const y = padding.top + chartH - ((h.elo - minElo) / eloRange) * chartH;
    return { x, y, elo: h.elo, date: h.recorded_at };
  });

  const polylinePoints = points.map((p) => `${p.x},${p.y}`).join(" ");

  const yTicks = 5;
  const yTickValues = Array.from({ length: yTicks + 1 }, (_, i) => minElo + (eloRange / yTicks) * i);

  const dateLabels = history.filter((_, i) => {
    const step = Math.max(1, Math.floor(history.length / 6));
    return i % step === 0 || i === history.length - 1;
  });

  return (
    <svg viewBox={`0 0 ${svgW} ${svgH}`} style={{ width: "100%", height: 300 }}>
      {yTickValues.map((val, i) => {
        const y = padding.top + chartH - ((val - minElo) / eloRange) * chartH;
        return (
          <g key={i}>
            <line x1={padding.left} y1={y} x2={svgW - padding.right} y2={y} stroke="var(--biq-border)" strokeWidth={0.5} />
            <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize={10} fill="var(--biq-muted)">{Math.round(val)}</text>
          </g>
        );
      })}

      <line
        x1={padding.left}
        y1={padding.top + baseline1500}
        x2={svgW - padding.right}
        y2={padding.top + baseline1500}
        stroke="var(--biq-muted)"
        strokeWidth={1}
        strokeDasharray="4 4"
      />
      <text x={svgW - padding.right + 4} y={padding.top + baseline1500 + 4} fontSize={9} fill="var(--biq-muted)">1500</text>

      <polyline
        points={polylinePoints}
        fill="none"
        stroke="var(--biq-accent)"
        strokeWidth={2}
        strokeLinejoin="round"
      />

      {points.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={3} fill="var(--biq-accent)" />
      ))}

      {dateLabels.map((h, i) => {
        const idx = history.indexOf(h);
        const x = padding.left + (idx / Math.max(history.length - 1, 1)) * chartW;
        return (
          <text key={i} x={x} y={svgH - 8} textAnchor="middle" fontSize={9} fill="var(--biq-muted)">
            {new Date(h.recorded_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
          </text>
        );
      })}

      <text x={padding.left + chartW / 2} y={svgH - 0} textAnchor="middle" fontSize={10} fill="var(--biq-muted)">Date</text>
      <text x={12} y={padding.top + chartH / 2} textAnchor="middle" fontSize={10} fill="var(--biq-muted)" transform={`rotate(-90, 12, ${padding.top + chartH / 2})`}>Elo Rating</text>
    </svg>
  );
}

function H2HTab({
  allPlayers, p1, p2, onP1Change, onP2Change, h2h,
}: {
  allPlayers: Player[] | undefined;
  p1: Player | null;
  p2: Player | null;
  onP1Change: (p: Player) => void;
  onP2Change: (p: Player) => void;
  h2h: H2HResult | null;
}) {
  const totalMeetings = h2h ? h2h.p1_wins + h2h.p2_wins : 0;

  const stats = useMemo(() => {
    if (!h2h || !p1 || !p2) return null;
    return [
      { label: "Elo Rating", v1: Math.round(p1.elo), v2: Math.round(p2.elo) },
      { label: "3-Dart Avg", v1: p1.avg_3dart?.toFixed(2) ?? "\u2014", v2: p2.avg_3dart?.toFixed(2) ?? "\u2014" },
      { label: "Checkout %", v1: p1.checkout_pct != null ? `${p1.checkout_pct.toFixed(1)}%` : "\u2014", v2: p2.checkout_pct != null ? `${p2.checkout_pct.toFixed(1)}%` : "\u2014" },
      { label: "180s/Leg", v1: p1.avg_180s_per_leg?.toFixed(2) ?? "\u2014", v2: p2.avg_180s_per_leg?.toFixed(2) ?? "\u2014" },
    ];
  }, [h2h, p1, p2]);

  return (
    <div>
      <h3>Head-to-Head Comparison</h3>

      <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 12, marginBottom: 24, alignItems: "end" }}>
        <div>
          <PlayerPicker
            players={allPlayers ?? []}
            value={p1}
            onChange={onP1Change}
            ariaLabel="Player 1"
            placeholder="Search Player 1…"
          />
        </div>
        <div style={{ textAlign: "center", paddingBottom: 10, fontWeight: 600, color: "var(--biq-muted)" }}>vs</div>
        <div>
          <PlayerPicker
            players={allPlayers ?? []}
            value={p2}
            onChange={onP2Change}
            ariaLabel="Player 2"
            placeholder="Search Player 2…"
          />
        </div>
      </div>

      {!p1 || !p2 || p1.id === p2.id ? (
        <div className="empty-state">Select two different players.</div>
      ) : (
        <>
          {stats && (
            <>
              <h4>Stat Comparison</h4>
              <div className="card" style={{ marginBottom: 24 }}>
                <div className="stat-row" style={{ borderBottom: "1px solid var(--biq-border)", paddingBottom: 8, marginBottom: 4 }}>
                  <div className="val right" style={{ fontSize: "1rem" }}>{natFlag(p1!.nationality)} {p1!.name}</div>
                  <div className="label" style={{ fontSize: "0.82rem" }}>vs</div>
                  <div className="val left" style={{ fontSize: "1rem" }}>{natFlag(p2!.nationality)} {p2!.name}</div>
                </div>
                {stats.map((s, i) => (
                  <div key={i} className="stat-row">
                    <div className="val right">{s.v1}</div>
                    <div className="label">{s.label}</div>
                    <div className="val left">{s.v2}</div>
                  </div>
                ))}
              </div>
            </>
          )}

          {h2h && (
            <>
              <h4>Historical H2H Record</h4>
              <div className="metrics-row" style={{ marginBottom: 16 }}>
                <div className="metric-card">
                  <div className="label">{p1!.name} Wins</div>
                  <div className="value">{h2h.p1_wins}</div>
                  <div className="delta">{totalMeetings > 0 ? `${((h2h.p1_wins / totalMeetings) * 100).toFixed(1)}%` : "0%"}</div>
                </div>
                <div className="metric-card">
                  <div className="label">Total Meetings</div>
                  <div className="value">{totalMeetings}</div>
                </div>
                <div className="metric-card">
                  <div className="label">{p2!.name} Wins</div>
                  <div className="value">{h2h.p2_wins}</div>
                  <div className="delta">{totalMeetings > 0 ? `${((h2h.p2_wins / totalMeetings) * 100).toFixed(1)}%` : "0%"}</div>
                </div>
              </div>

              {h2h.matches.length > 0 ? (
                <div className="table-wrap" style={{ maxHeight: 500, overflow: "auto" }}>
                  <table>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Score</th>
                        <th>Winner</th>
                        <th>Avg {p1!.name}</th>
                        <th>Avg {p2!.name}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {h2h.matches.map((m, i) => (
                        <tr key={i}>
                          <td>{new Date(m.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</td>
                          <td>{m.score}</td>
                          <td style={{ fontWeight: 600 }}>
                            {m.winner_id === p1!.id ? p1!.name : p2!.name}
                          </td>
                          <td>{m.avg_p1 != null ? m.avg_p1.toFixed(2) : "\u2014"}</td>
                          <td>{m.avg_p2 != null ? m.avg_p2.toFixed(2) : "\u2014"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="empty-state">No head-to-head matches found between these two players.</div>
              )}
            </>
          )}

          {!h2h && p1 && p2 && p1.id !== p2.id && (
            <div className="empty-state">No head-to-head matches found between these two players.</div>
          )}
        </>
      )}
    </div>
  );
}
