export interface Player {
  id: number;
  name: string;
  nationality: string;
  elo: number;
  pdc_ranking: number | null;
  nickname: string | null;
  avg_3dart: number | null;
  checkout_pct: number | null;
  avg_180s_per_leg: number | null;
  win_rate_last20: number | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface PlayerStats {
  player_id: number;
  win_rate_l20: number | null;
  pl_win_rate: number | null;
  avg_3dart_l10: number | null;
  checkout_pct_l10: number | null;
  avg_180s_l10: number | null;
  form_streak: string | null;
}

export interface EloHistoryEntry {
  recorded_at: string;
  elo: number;
}

export interface MatchHistoryEntry {
  date: string;
  opponent: string;
  score: string;
  result: "W" | "L";
  avg: number | null;
  checkout_pct: number | null;
  "180s": number | null;
}

export interface H2HResult {
  matches: Array<{
    date: string;
    score: string;
    winner_id: number;
    avg_p1: number | null;
    avg_p2: number | null;
  }>;
  p1_wins: number;
  p2_wins: number;
}

export interface Match {
  match_id: number;
  tournament: string;
  round: string | null;
  match_date: string | null;
  player1: string;
  player2: string;
  p1_nationality: string;
  p2_nationality: string;
  legs_to_win: number | null;
}

export interface MatchDetail {
  id: number;
  tournament: string;
  round: string | null;
  match_date: string | null;
  legs_to_win: number | null;
  score1: number | null;
  score2: number | null;
  is_upcoming: boolean;
  player1_id: number;
  player2_id: number;
  player1: string;
  player2: string;
  winner_id: number | null;
  winner: string;
  avg_p1: number | null;
  avg_p2: number | null;
  checkout_pct_p1: number | null;
  checkout_pct_p2: number | null;
  legs_180_p1: number | null;
  legs_180_p2: number | null;
}

export interface Tournament {
  id: number;
  name: string;
  country: string | null;
  prestige_tier: number | null;
  format_desc: string | null;
  prize_fund: number | null;
  typical_month: string | null;
  dk_covered: boolean;
  created_at: string | null;
}

export interface TournamentResult {
  date: string;
  round: string | null;
  player1: string;
  player2: string;
  score: string;
  winner: string;
}

export interface OddsEntry {
  match_id: number;
  tournament: string;
  match_date: string | null;
  player1: string;
  player2: string;
  p1_nationality: string;
  p2_nationality: string;
  p1_odds: number;
  p2_odds: number;
  p1_implied: number;
  p2_implied: number;
  updated: string | null;
}

export interface OddsHistoryEntry {
  time: string;
  p1_odds: number;
  p2_odds: number;
  p1_implied: number;
  p2_implied: number;
}

export interface Pick {
  pick_id: number;
  match_id: number;
  tournament: string;
  round: string | null;
  match_date: string | null;
  player1: string;
  player2: string;
  pick: string;
  dk_odds: number;
  model_prob: number;
  dk_implied: number;
  edge_pct: number;
  confidence: string;
  reasoning: string | null;
  pick_time: string | null;
}

export interface SteamEvent {
  detected_at: string | null;
  tournament: string;
  player1: string;
  player2: string;
  player_steamed: string;
  shift_pct: number;
  opening_odds: number;
  current_odds: number;
  match_date: string | null;
}

export interface ModelRecord {
  wins: number;
  losses: number;
  win_rate: number;
  roi_pct: number;
  avg_edge: number;
  brier_score: number;
  days: number;
}

export interface YearlyStats {
  year: number;
  total_matches: number;
}

export interface EraStats {
  era: string;
  player_name: string;
  wins: number;
  total: number;
  win_rate: number;
}

export interface BulkEloEntry {
  player_id: number;
  player_name: string;
  recorded_at: string;
  elo: number;
}
