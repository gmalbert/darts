import { useState, useMemo } from "react";
import { useApi } from "../hooks/useApi";
import { api } from "../api/client";
import { Tabs } from "../components/controls/Tabs";
import { BettingOracleFooter } from "../components/legal/Footer";
import { formatPrize } from "../utils/formatters";
import type { Tournament, TournamentResult } from "../types";

export default function TournamentsPage() {
  const { data: tournaments } = useApi(() => api.tournaments(), []);
  const [tierFilter, setTierFilter] = useState("All");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: selected } = useApi(
    () => selectedId ? api.tournament(selectedId) : Promise.resolve(null),
    [selectedId]
  );
  const { data: results } = useApi(
    () => selectedId ? api.tournamentResults(selectedId) : Promise.resolve([]),
    [selectedId]
  );

  const filtered = useMemo(() => {
    if (!tournaments) return [];
    if (tierFilter === "Majors (Tier 1)") return tournaments.filter((t) => t.prestige_tier === 1);
    if (tierFilter === "Ranking (Tier 2)") return tournaments.filter((t) => t.prestige_tier === 2);
    return tournaments;
  }, [tournaments, tierFilter]);

  const dkCovered = tournaments?.filter((t) => t.dk_covered).length ?? 0;
  const majorCount = tournaments?.filter((t) => t.prestige_tier === 1).length ?? 0;
  const totalPrize = tournaments?.reduce((s, t) => s + (t.prize_fund ?? 0), 0) ?? 0;

  const tabs = [
    { key: "all", label: "All Tournaments", icon: "\uD83D\uDCC2" },
    { key: "detail", label: "Tournament Detail", icon: "\uD83D\uDCCA" },
  ];

  return (
    <div>
      <div className="page-header">
        <h2>🏆 Tournament Hub</h2>
        <p className="caption">PDC events covered on DraftKings — formats, prize money, and results.</p>
      </div>
      <hr className="divider" />

      <div className="metrics-row">
        <div className="metric-card"><div className="label">DK-Covered Tournaments</div><div className="value">{dkCovered}</div></div>
        <div className="metric-card"><div className="label">Major Events</div><div className="value">{majorCount}</div></div>
        <div className="metric-card"><div className="label">Total Prize Pool</div><div className="value">{formatPrize(totalPrize)}</div></div>
        <div className="metric-card"><div className="label">Active Years Coverage</div><div className="value">2000–2026</div></div>
      </div>
      <hr className="divider" />

      <Tabs tabs={tabs}>
        <TabPanel tabKey="all" active={tabs[0].key}>
          <AllTournamentsTab
            tournaments={filtered}
            tierFilter={tierFilter}
            onTierChange={setTierFilter}
          />
        </TabPanel>
        <TabPanel tabKey="detail" active={tabs[0].key}>
          <DetailTab
            tournaments={tournaments ?? []}
            selected={selected ?? null}
            results={results ?? []}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </TabPanel>
      </Tabs>
      <BettingOracleFooter />
    </div>
  );
}

function AllTournamentsTab({
  tournaments, tierFilter, onTierChange,
}: {
  tournaments: Tournament[];
  tierFilter: string;
  onTierChange: (v: string) => void;
}) {
  const tierLabel = (t: Tournament) => t.prestige_tier === 1 ? "\uD83C\uDFC5 MAJOR" : "\uD83C\uDFAF RANKING";
  const tierClass = (t: Tournament) =>
    t.prestige_tier === 1 ? "tourn-tier-1" : t.prestige_tier === 2 ? "tourn-tier-2" : "tourn-tier-3";

  return (
    <div>
      <h3>All PDC Tournaments</h3>
      <div style={{ margin: "12px 0" }}>
        <label>Filter by tier</label>
        <div style={{ display: "flex", gap: 12 }}>
          {["All", "Majors (Tier 1)", "Ranking (Tier 2)"].map((opt) => (
            <label key={opt} style={{ display: "flex", alignItems: "center", gap: 4, cursor: "pointer", textTransform: "none", fontSize: "0.9rem", color: tierFilter === opt ? "var(--biq-accent)" : "var(--biq-text)" }}>
              <input type="radio" name="tier" checked={tierFilter === opt} onChange={() => onTierChange(opt)} style={{ width: "auto" }} />
              {opt}
            </label>
          ))}
        </div>
      </div>

      {tournaments.map((t) => (
        <div key={t.id} className={`tourn-card ${tierClass(t)}`}>
          <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr 1.5fr 1.5fr", gap: 12, alignItems: "center" }}>
            <div>
              <strong>{t.name}</strong>
              <div style={{ color: "var(--biq-muted)", fontSize: "0.8rem" }}>{tierLabel(t)} · {t.typical_month ?? "\u2014"}</div>
            </div>
            <div style={{ color: "var(--biq-muted)", fontSize: "0.82rem" }}>{t.format_desc ?? "\u2014"}</div>
            <div style={{ color: "var(--biq-accent2)", fontWeight: 700 }}>{formatPrize(t.prize_fund)}</div>
            <div style={{ fontSize: "0.9rem" }}>{t.dk_covered ? "\u2705 DK" : "\u274C"}</div>
          </div>
        </div>
      ))}

      {tournaments.length > 0 && (
        <>
          <h3 style={{ marginTop: 24 }}>Prize Fund Comparison</h3>
          <div style={{ marginTop: 12 }}>
            {tournaments.map((t) => {
              const maxPrize = Math.max(...tournaments.map((x) => x.prize_fund ?? 0));
              const pct = maxPrize > 0 ? ((t.prize_fund ?? 0) / maxPrize) * 100 : 0;
              return (
                <div key={t.id} style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 200, fontSize: "0.82rem", textAlign: "right", flexShrink: 0 }}>{t.name}</span>
                  <div style={{ flex: 1, background: "var(--biq-bg3)", borderRadius: 4, height: 20 }}>
                    <div style={{
                      width: `${pct}%`, height: "100%", borderRadius: 4,
                      background: t.prestige_tier === 1 ? "var(--biq-accent)" : "var(--biq-accent2)",
                    }} />
                  </div>
                  <span style={{ fontSize: "0.82rem", width: 100 }}>{formatPrize(t.prize_fund)}</span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function DetailTab({
  tournaments, selected, results, selectedId, onSelect,
}: {
  tournaments: Tournament[];
  selected: Tournament | null;
  results: TournamentResult[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}) {
  return (
    <div>
      <h3>Tournament Results</h3>
      <div style={{ marginBottom: 16 }}>
        <label>Select tournament</label>
        <select value={selectedId ?? ""} onChange={(e) => onSelect(Number(e.target.value) || null)}>
          <option value="">Select a tournament</option>
          {tournaments.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>

      {selected && (
        <>
          <div style={{ marginBottom: 12 }}>
            <strong>Format:</strong> {selected.format_desc ?? "\u2014"}<br />
            <strong>Prize Fund:</strong> {formatPrize(selected.prize_fund)}<br />
            <strong>Typical Month:</strong> {selected.typical_month ?? "\u2014"}
          </div>
          <hr className="divider" />
        </>
      )}

      {results.length > 0 ? (
        <>
          <div className="table-wrap" style={{ maxHeight: 500, overflow: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Date</th><th>Round</th><th>Player 1</th><th>Score</th><th>Player 2</th><th>Winner</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}>
                    <td>{new Date(r.date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</td>
                    <td>{r.round ?? "TBD"}</td><td>{r.player1}</td><td>{r.score}</td><td>{r.player2}</td><td>{r.winner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h3 style={{ marginTop: 16 }}>Most Wins in This Tournament</h3>
          {(() => {
            const winCounts: Record<string, number> = {};
            results.forEach((r) => { if (r.winner) winCounts[r.winner] = (winCounts[r.winner] ?? 0) + 1; });
            const sorted = Object.entries(winCounts).sort((a, b) => b[1] - a[1]).slice(0, 10);
            const maxWins = sorted[0]?.[1] ?? 1;
            return (
              <div style={{ marginTop: 12 }}>
                {sorted.map(([name, wins]) => (
                  <div key={name} style={{ marginBottom: 6, display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ width: 160, fontSize: "0.85rem", textAlign: "right" }}>{name}</span>
                    <div style={{ flex: 1, background: "var(--biq-bg3)", borderRadius: 4, height: 20 }}>
                      <div style={{ width: `${(wins / maxWins) * 100}%`, height: "100%", borderRadius: 4, background: "var(--biq-accent)" }} />
                    </div>
                    <span style={{ fontSize: "0.82rem", width: 40, textAlign: "right" }}>{wins}</span>
                  </div>
                ))}
              </div>
            );
          })()}
        </>
      ) : selectedId ? (
        <div className="empty-state">No results logged for this tournament yet.</div>
      ) : (
        <div className="empty-state">Select a tournament to view results.</div>
      )}
    </div>
  );
}

// Needed for inline TabPanel children
function TabPanel({ tabKey, active, children }: { tabKey: string; active: string; children: React.ReactNode }) {
  return <div className={`tab-content${tabKey === active ? " active" : ""}`}>{children}</div>;
}
