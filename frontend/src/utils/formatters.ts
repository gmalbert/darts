const FLAGS: Record<string, string> = {
  ENG: "\u{1F3F4}\u{E0067}\u{E0062}\u{E0065}\u{E006E}\u{E0067}\u{E007F}",
  WAL: "\u{1F3F4}\u{E0067}\u{E0062}\u{E0077}\u{E006C}\u{E0073}\u{E007F}",
  SCO: "\u{1F3F4}\u{E0067}\u{E0062}\u{E0073}\u{E0063}\u{E007F}",
  NED: "\u{1F1F3}\u{1F1F1}",
  BEL: "\u{1F1E7}\u{1F1EA}",
  AUS: "\u{1F1E6}\u{1F1FA}",
  POR: "\u{1F1F5}\u{1F1F9}",
  IRL: "\u{1F1EE}\u{1F1EA}",
  GER: "\u{1F1E9}\u{1F1EA}",
  USA: "\u{1F1FA}\u{1F1F8}",
  NZL: "\u{1F1F3}\u{1F1FF}",
  CAN: "\u{1F1E8}\u{1F1E6}",
};

export function natFlag(nat: string): string {
  return FLAGS[nat] ?? "\u{1F30D}";
}

export function formatAmericanOdds(odds: number): string {
  if (odds === 0) return "N/A";
  return odds > 0 ? `+${odds}` : String(odds);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "TBD";
  return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "TBD";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "TBD";
  return d.toLocaleDateString("en-US", {
    weekday: "short", month: "short", day: "numeric",
    hour: "numeric", minute: "2-digit",
  });
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
}

export function formatPct(v: number, dp = 1): string {
  return `${(v * 100).toFixed(dp)}%`;
}

export function formatPrize(v: number | null): string {
  if (!v) return "\u2014";
  return `\u00A3${v.toLocaleString()}`;
}
