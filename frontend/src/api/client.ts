const BASE = "http://127.0.0.1:8001/api/v1";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} → ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} → ${res.status}`);
  return res.json();
}

import type {
  Player, PlayerStats, EloHistoryEntry, MatchHistoryEntry,
  H2HResult, Match, MatchDetail, Tournament, TournamentResult,
  OddsEntry, OddsHistoryEntry, Pick, SteamEvent,
  ModelRecord, YearlyStats, EraStats, BulkEloEntry,
} from "../types";

export const api = {
  health: () => get<{ status: string; player_count: number; tournament_count: number; match_count: number }>("/health"),
  meta: () => get<Record<string, unknown>>("/meta"),

  players: () => get<Player[]>("/players"),
  player: (id: number) => get<Player>(`/players/${id}`),
  playerEloHistory: (id: number) => get<EloHistoryEntry[]>(`/players/${id}/elo-history`),
  playerMatches: (id: number, limit = 30) => get<MatchHistoryEntry[]>(`/players/${id}/matches?limit=${limit}`),
  playerStats: (id: number) => get<PlayerStats>(`/players/${id}/stats`),
  playerStatsBatch: (ids: number[]) => get<PlayerStats[]>(`/players/stats-batch?ids=${ids.join(",")}`),
  h2h: (p1: number, p2: number) => get<H2HResult>(`/players/h2h?p1=${p1}&p2=${p2}`),

  matches: (params?: { upcoming?: boolean; days?: number; limit?: number }) => {
    const q = new URLSearchParams();
    if (params?.upcoming) q.set("upcoming", "true");
    if (params?.days) q.set("days", String(params.days));
    if (params?.limit) q.set("limit", String(params.limit));
    const qs = q.toString();
    return get<Match[]>(`/matches${qs ? "?" + qs : ""}`);
  },
  match: (id: number) => get<MatchDetail>(`/matches/${id}`),
  oddsHistory: (id: number) => get<OddsHistoryEntry[]>(`/matches/${id}/odds-history`),

  tournaments: () => get<Tournament[]>("/tournaments"),
  tournament: (id: number) => get<Tournament>(`/tournaments/${id}`),
  tournamentResults: (id: number, limit = 100) =>
    get<TournamentResult[]>(`/tournaments/${id}/results?limit=${limit}`),

  odds: () => get<OddsEntry[]>("/odds"),
  picks: (minEdge = 0) => get<Pick[]>(`/picks?min_edge=${minEdge}`),
  steam: (hours = 24) => get<SteamEvent[]>(`/steam?hours=${hours}`),

  modelRecord: (days = 30) => get<ModelRecord>(`/model/record?days=${days}`),
  eloHistoryBulk: () => get<BulkEloEntry[]>("/model/elo-history"),
  yearlyStats: () => get<YearlyStats[]>("/analytics/yearly"),
  eraPerformance: () => get<EraStats[]>("/analytics/era"),

  calcEdge: (modelProb: number, dkOdds: number) =>
    post<{ model_prob: number; dk_implied: number; edge_pct: number; expected_value: number; grade: string }>("/calc/edge", { model_prob: modelProb, dk_odds: dkOdds }),
  calcEloProb: (eloA: number, eloB: number) =>
    post<{ prob_a: number; prob_b: number; fair_odds_a: number }>("/calc/elo-prob", { elo_a: eloA, elo_b: eloB }),
  calcFormatAdjust: (baseProb: number, legsToWin: number) =>
    post<{ adjusted_prob: number }>("/calc/format-adjust", { base_prob: baseProb, legs_to_win: legsToWin }),
  calc180s: (avgPerLeg: number, legsToWin: number, line: number) =>
    post<{ expected_180s: number; prob_over: number; prob_under: number }>("/calc/180s", {
      avg_180s_per_leg: avgPerLeg, legs_to_win: legsToWin, line,
    }),
  calcParlay: (legs: Array<{ prob: number; odds: number }>) =>
    post<{ combined_model_prob: number; combined_implied_prob: number; combined_decimal_odds: number; edge_pct: number; ev_per_100: number }>("/calc/parlay", { legs }),

  legalFooter: () => get<Record<string, string>>("/legal/footer"),
};
