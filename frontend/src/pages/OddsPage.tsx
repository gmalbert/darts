import { useState, useMemo } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { Tabs } from "../components/controls/Tabs";
import { BettingOracleFooter } from "../components/legal/Footer";
import { formatAmericanOdds, formatDate, formatDateTime, formatTime, natFlag } from "../utils/formatters";
import type { OddsEntry, OddsHistoryEntry, SteamEvent } from "../types";

function TabPanel({ tabKey, active, children }: { tabKey: string; active: string; children: React.ReactNode }) {
  return <div className={`tab-content${tabKey === active ? " active" : ""}`}>{children}</div>;
}

export default function OddsPage() {
  const { data: odds } = useApi(() => api.odds(), []);
  const [tournamentFilter, setTournamentFilter] = useState("All");
  const [matchIdx, setMatchIdx] = useState(0);
  const [steamHours, setSteamHours] = useState(24);

  const { data: oddsHistory } = useApi(
    () => {
      if (!odds || odds.length === 0) return Promise.resolve([]);
      const matchId = odds[matchIdx]?.match_id;
      if (matchId == null) return Promise.resolve([]);
      return api.oddsHistory(matchId);
    },
    [odds, matchIdx]
  );

  const { data: steamEvents } = useApi(() => api.steam(steamHours), [steamHours]);

  const tournaments = useMemo(() => {
    if (!odds) return [];
    const set = new Set(odds.map((o) => o.tournament));
    return Array.from(set).sort();
  }, [odds]);

  const filteredOdds = useMemo(() => {
    if (!odds) return [];
    if (tournamentFilter === "All") return odds;
    return odds.filter((o) => o.tournament === tournamentFilter);
  }, [odds, tournamentFilter]);

  const tabs = [
    { key: "lines", label: "Cached Lines", icon: "\uD83D\uDCB0" },
    { key: "movement", label: "Line Movement", icon: "\uD83D\uDCC8" },
    { key: "steam", label: "Steam Moves", icon: "\uD83D\uDD25" },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>🧠 BullzIQ Odds Tracker</h2>
      </div>
      <hr className="divider" />

      <Tabs tabs={tabs}>
        <TabPanel tabKey="lines" active={tabs[0].key}>
          <CurrentLinesTab
            odds={filteredOdds}
            allOdds={odds}
            tournaments={tournaments}
            tournamentFilter={tournamentFilter}
            onTournamentChange={setTournamentFilter}
          />
        </TabPanel>
        <TabPanel tabKey="movement" active={tabs[0].key}>
          <LineMovementTab
            odds={odds}
            oddsHistory={oddsHistory}
            matchIdx={matchIdx}
            onMatchChange={setMatchIdx}
          />
        </TabPanel>
        <TabPanel tabKey="steam" active={tabs[0].key}>
          <SteamMovesTab
            events={steamEvents}
            hours={steamHours}
            onHoursChange={setSteamHours}
          />
        </TabPanel>
      </Tabs>
      <BettingOracleFooter />
    </div>
  );
}

function CurrentLinesTab({
  odds, allOdds, tournaments, tournamentFilter, onTournamentChange,
}: {
  odds: OddsEntry[];
  allOdds: OddsEntry[] | undefined;
  tournaments: string[];
  tournamentFilter: string;
  onTournamentChange: (v: string) => void;
}) {
  return (
    <div>
      <h3>Cached DraftKings Lines</h3>
      <div style={{ marginBottom: 16 }}>
        <label>Tournament</label>
        <select
          value={tournamentFilter}
          onChange={(e) => onTournamentChange(e.target.value)}
        >
          <option value="All">All</option>
          {tournaments.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {allOdds && allOdds.length === 0 && (
        <div className="empty-state">No upcoming fixtures found in the next 7 days.</div>
      )}

      {allOdds && allOdds.length > 0 && odds.length === 0 && (
        <div className="empty-state">Upcoming fixture(s) found, but DraftKings moneylines are not posted yet.</div>
      )}

      {odds.map((o) => {
        const hasOdds = o.p1_odds !== 0 && o.p2_odds !== 0;
        const p1Win = o.p1_implied > o.p2_implied;
        return (
          <div key={o.match_id} className="card card-border" style={{ marginBottom: 12 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
              <span style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>
                {o.tournament} · {formatDate(o.match_date)}, {formatTime(o.match_date)}
              </span>
              <span style={{ color: "var(--biq-muted)", fontSize: "0.75rem" }}>
                Snapshot {formatDateTime(o.updated && !/(Z|[+-]\d{2}:\d{2})$/i.test(o.updated) ? `${o.updated}Z` : o.updated)}
              </span>
            </div>

            {hasOdds ? (
              <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr 3fr", gap: 16, alignItems: "center" }}>
                <div>
                  <div style={{ fontWeight: 700 }}>
                    {natFlag(o.p1_nationality)} {o.player1}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span style={{ fontSize: "1.3rem", fontWeight: 700, color: p1Win ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                      {formatAmericanOdds(o.p1_odds)}
                    </span>
                    <span style={{ fontSize: "0.8rem", color: "var(--biq-muted)", marginLeft: 6 }}>
                      ({(o.p1_implied * 100).toFixed(1)}% implied)
                    </span>
                  </div>
                </div>

                <div>
                  <div style={{ display: "flex", height: 8, borderRadius: 4, overflow: "hidden" }}>
                    <div style={{ width: `${o.p1_implied * 100}%`, background: "var(--biq-accent)" }} />
                    <div style={{ width: `${o.p2_implied * 100}%`, background: "var(--biq-accent2)" }} />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginTop: 4, fontSize: "0.75rem", color: "var(--biq-muted)" }}>
                    <span>{(o.p1_implied * 100).toFixed(1)}%</span>
                    <span>{(o.p2_implied * 100).toFixed(1)}%</span>
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontWeight: 700 }}>
                    {o.player2} {natFlag(o.p2_nationality)}
                  </div>
                  <div style={{ marginTop: 4 }}>
                    <span style={{ fontSize: "0.8rem", color: "var(--biq-muted)", marginRight: 6 }}>
                      ({(o.p2_implied * 100).toFixed(1)}% implied)
                    </span>
                    <span style={{ fontSize: "1.3rem", fontWeight: 700, color: !p1Win ? "var(--biq-pos)" : "var(--biq-neg)" }}>
                      {formatAmericanOdds(o.p2_odds)}
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ color: "var(--biq-muted)", fontSize: "0.85rem" }}>Lines not open yet</div>
            )}
          </div>
        );
      })}

      {odds.length > 0 && <hr className="divider" />}
    </div>
  );
}

function LineMovementTab({
  odds, oddsHistory, matchIdx, onMatchChange,
}: {
  odds: OddsEntry[] | undefined;
  oddsHistory: OddsHistoryEntry[] | undefined;
  matchIdx: number;
  onMatchChange: (i: number) => void;
}) {
  const matchOptions = useMemo(() => {
    if (!odds) return [];
    return odds.map((o, i) => ({
      idx: i,
      label: `${o.player1} vs ${o.player2} — ${o.tournament}`,
    }));
  }, [odds]);

  return (
    <div>
      <h3>Odds Line Movement Chart</h3>
      <p style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        Track how DraftKings implied probabilities shift over time for each match.
      </p>

      <div style={{ marginBottom: 16 }}>
        <label>Select match</label>
        <select
          value={matchIdx}
          onChange={(e) => onMatchChange(Number(e.target.value))}
        >
          {matchOptions.map((opt) => (
            <option key={opt.idx} value={opt.idx}>{opt.label}</option>
          ))}
        </select>
      </div>

      {!odds || odds.length === 0 ? (
        <div className="empty-state">No upcoming matches available.</div>
      ) : !oddsHistory || oddsHistory.length === 0 ? (
        <div className="empty-state">No odds history available for this match.</div>
      ) : (
        <>
          <div className="table-wrap" style={{ maxHeight: 400, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>P1 Odds</th>
                  <th>P2 Odds</th>
                  <th>P1 Implied%</th>
                  <th>P2 Implied%</th>
                </tr>
              </thead>
              <tbody>
                {oddsHistory.map((h, i) => (
                  <tr key={i}>
                    <td>{formatTime(h.time)}</td>
                    <td>{formatAmericanOdds(h.p1_odds)}</td>
                    <td>{formatAmericanOdds(h.p2_odds)}</td>
                    <td>{(h.p1_implied * 100).toFixed(1)}%</td>
                    <td>{(h.p2_implied * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {oddsHistory.length >= 2 && (
            <div style={{ marginTop: 16 }}>
              <h4>Movement Summary</h4>
              {(() => {
                const open = oddsHistory[0];
                const cur = oddsHistory[oddsHistory.length - 1];
                const rows = [
                  {
                    label: odds![matchIdx].player1,
                    openOdds: open.p1_odds,
                    curOdds: cur.p1_odds,
                    openImpl: open.p1_implied,
                    curImpl: cur.p1_implied,
                  },
                  {
                    label: odds![matchIdx].player2,
                    openOdds: open.p2_odds,
                    curOdds: cur.p2_odds,
                    openImpl: open.p2_implied,
                    curImpl: cur.p2_implied,
                  },
                ];
                return (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th></th>
                          <th>Opening Odds</th>
                          <th>Current Odds</th>
                          <th>Open Implied</th>
                          <th>Current Implied</th>
                          <th>Shift (pp)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((r) => {
                          const shift = r.curImpl - r.openImpl;
                          return (
                            <tr key={r.label}>
                              <td style={{ fontWeight: 700 }}>{r.label}</td>
                              <td>{formatAmericanOdds(r.openOdds)}</td>
                              <td>{formatAmericanOdds(r.curOdds)}</td>
                              <td>{(r.openImpl * 100).toFixed(1)}%</td>
                              <td>{(r.curImpl * 100).toFixed(1)}%</td>
                              <td style={{ color: shift > 0 ? "var(--biq-pos)" : shift < 0 ? "var(--biq-neg)" : "var(--biq-text)", fontWeight: 600 }}>
                                {shift > 0 ? "+" : ""}{(shift * 100).toFixed(1)}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                );
              })()}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function SteamMovesTab({
  events, hours, onHoursChange,
}: {
  events: SteamEvent[] | undefined;
  hours: number;
  onHoursChange: (v: number) => void;
}) {
  return (
    <div>
      <h3>🔥 Steam Moves</h3>
      <p style={{ color: "var(--biq-muted)", fontSize: "0.85rem", marginBottom: 16 }}>
        Steam = significant sharp-money line movement. Flagged when implied probability shifts ≥3 percentage points within 30 minutes.
      </p>

      <div style={{ marginBottom: 16 }}>
        <label>Look-back window (hours)</label>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4 }}>
          <input
            type="range"
            min={1}
            max={48}
            value={hours}
            onChange={(e) => onHoursChange(Number(e.target.value))}
            style={{ flex: 1 }}
          />
          <span style={{ fontSize: "0.9rem", fontWeight: 600, minWidth: 40 }}>{hours}h</span>
        </div>
      </div>

      {!events ? (
        <div className="empty-state">Loading steam moves...</div>
      ) : events.length === 0 ? (
        <div className="empty-state">No steam moves detected in the last {hours} hours.</div>
      ) : (
        <>
          <div style={{ padding: "10px 14px", borderRadius: 8, background: "var(--biq-bg2)", border: "1px solid var(--biq-accent)", marginBottom: 16, fontSize: "0.9rem" }}>
            <strong>{events.length} steam move(s) detected</strong> in the last {hours} hours.
          </div>

          {events.map((ev, i) => {
            const absShift = Math.abs(ev.shift_pct);
            const emoji = absShift >= 5 ? "\uD83D\uDD34\uD83D\uDD34\uD83D\uDD34" : absShift >= 3 ? "\uD83D\uDD34\uD83D\uDD34" : "\uD83D\uDD34";
            const direction = ev.shift_pct > 0 ? "\u25B2" : "\u25BC";
            return (
              <div key={i} className="card card-border" style={{ marginBottom: 12 }}>
                <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr 2fr 1.5fr", gap: 16, alignItems: "center" }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{ev.player1} vs {ev.player2}</div>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem", marginTop: 2 }}>{ev.tournament}</div>
                  </div>
                  <div>
                    <span className="badge-steam" style={{ display: "inline-block" }}>
                      {direction} STEAM on {ev.player_steamed}
                    </span>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.8rem", marginTop: 4 }}>
                      Shift: {ev.shift_pct > 0 ? "+" : ""}{ev.shift_pct.toFixed(1)}pp
                    </div>
                  </div>
                  <div>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>Open → Current</div>
                    <div style={{ fontWeight: 700, marginTop: 2 }}>{formatAmericanOdds(ev.opening_odds)} → {formatAmericanOdds(ev.current_odds)}</div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "1.1rem" }}>{emoji}</div>
                    <div style={{ color: "var(--biq-muted)", fontSize: "0.8rem", marginTop: 2 }}>{formatDate(ev.match_date)}</div>
                  </div>
                </div>
              </div>
            );
          })}

          <div style={{ padding: "12px 16px", borderRadius: 8, background: "var(--biq-bg2)", border: "1px solid var(--biq-border)", marginTop: 16, fontSize: "0.85rem", color: "var(--biq-muted)" }}>
            <strong>What is steam?</strong> Steam moves indicate sharp-money action — when professional bettors place large wagers that move the line significantly in a short window. A shift of ≥3 percentage points in implied probability within 30 minutes typically signals informed betting activity, often preceding lineup changes or market corrections.
          </div>
        </>
      )}
    </div>
  );
}
