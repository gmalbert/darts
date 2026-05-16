# 03 — Site Features & User Flows

## Page Map

```
/                           Home — live event banner, today's picks, top movers
/tournaments                All DK-covered tournaments with schedules
/tournaments/:slug          Tournament hub (schedule, bracket, form guide)
/players                    Player index
/players/:slug              Player profile (stats, Elo chart, H2H, form)
/matches/:id                Match center (pre-match analysis + live if active)
/picks                      Today's model picks with edge %
/tools/edge-calculator      Manual odds vs model probability
/tools/h2h                  Head-to-head comparison tool
/tools/180s-calculator      180s over/under expected value calc
/stats/leaderboard          Season stat leaders (avg, checkout %, 180s)
/stats/trends               Long-run trends, format analysis
/odds                       Live odds tracker with line movement
/blog                       Analysis articles, tournament previews
/api/v1/*                   Public API (rate-limited, free tier)
```

---

## Feature 1 — Match Center

The most important page. Should exist for every DK-covered match.

```tsx
// components/MatchCenter.tsx
import { Match, PlayerStats, OddsSnapshot } from "@/types"

interface MatchCenterProps {
  match: Match
  player1Stats: PlayerStats
  player2Stats: PlayerStats
  h2hHistory: Match[]
  oddsHistory: OddsSnapshot[]
  modelProbability: number  // our model's p1 win prob
}

export function MatchCenter({
  match, player1Stats, player2Stats,
  h2hHistory, oddsHistory, modelProbability
}: MatchCenterProps) {
  const dkOdds = oddsHistory[oddsHistory.length - 1]
  const edge = calculateEdge(modelProbability, dkOdds?.p1_odds)

  return (
    <div className="match-center">
      <MatchHeader match={match} />
      
      {/* Model Pick Banner */}
      {edge.has_edge && (
        <EdgeBanner
          player={edge.edge_side === "p1" ? match.player1 : match.player2}
          edgePct={edge.edge_pct}
          ourProb={edge.our_prob}
          dkOdds={edge.dk_odds}
        />
      )}
      
      {/* Head-to-head stat bars */}
      <StatComparison
        label="3-dart avg (last 20)"
        p1Value={player1Stats.avg_3dart_recent}
        p2Value={player2Stats.avg_3dart_recent}
        format="number"
        higherIsBetter
      />
      <StatComparison
        label="Checkout %"
        p1Value={player1Stats.checkout_pct_recent}
        p2Value={player2Stats.checkout_pct_recent}
        format="percent"
        higherIsBetter
      />
      <StatComparison
        label="180s per leg"
        p1Value={player1Stats.avg_180s_per_leg}
        p2Value={player2Stats.avg_180s_per_leg}
        format="decimal"
        higherIsBetter
      />
      
      {/* H2H History */}
      <H2HRecord history={h2hHistory} p1={match.player1} p2={match.player2} />
      
      {/* Odds movement chart */}
      <OddsMovementChart snapshots={oddsHistory} />
      
      {/* Tournament form (last 5 matches each) */}
      <RecentForm player1Stats={player1Stats} player2Stats={player2Stats} />
      
      {/* 180s prop calculator */}
      <OneEightiesCalculator
        p1Rate={player1Stats.avg_180s_per_leg}
        p2Rate={player2Stats.avg_180s_per_leg}
        format={match.format}
        legsToWin={match.legs_to_win}
      />
    </div>
  )
}
```

---

## Feature 2 — Player Profile Page

```tsx
// components/PlayerProfile.tsx
// Route: /players/michael-van-gerwen

export function PlayerProfile({ player, stats, matches, eloHistory }) {
  return (
    <div className="player-profile">
      {/* Header */}
      <div className="player-header">
        <Flag nationality={player.nationality} />
        <h1>{player.name}</h1>
        <p className="nickname">"{player.nickname}"</p>
        <EloRatingBadge rating={stats.elo} rank={stats.elo_rank} />
      </div>
      
      {/* Stat Cards */}
      <div className="stats-grid">
        <StatCard label="3-dart avg (career)" value={stats.career_avg} />
        <StatCard label="3-dart avg (last 20)" value={stats.avg_last20} />
        <StatCard label="Checkout %" value={`${stats.checkout_pct}%`} />
        <StatCard label="180s per leg" value={stats.avg_180s_per_leg} />
        <StatCard label="Win rate (DK tournaments)" value={`${stats.dk_win_rate}%`} />
        <StatCard label="Major titles" value={stats.major_titles} />
      </div>
      
      {/* Elo over time — D3 or Recharts line chart */}
      <EloHistoryChart data={eloHistory} />
      
      {/* Tournament-by-tournament breakdown */}
      <TournamentBreakdownTable player={player} />
      
      {/* Recent matches */}
      <RecentMatchesList matches={matches.slice(0, 20)} />
      
      {/* H2H vs top 16 — heatmap style table */}
      <H2HMatrix player={player} top16Only />
    </div>
  )
}
```

---

## Feature 3 — Live Picks Feed

```tsx
// components/PicksFeed.tsx
// Shows all today's model picks with edge calculations

interface Pick {
  match: Match
  ourProb: number
  dkOdds: number
  edgePct: number
  confidence: "high" | "medium" | "low"  // high = edge > 5%, medium = 2-5%
  pickSide: "p1" | "p2"
  market: "h2h" | "180s_over" | "180s_under"
  reasoning: string[]  // bullet points for display
}

export function PicksFeed({ picks }: { picks: Pick[] }) {
  const sorted = [...picks].sort((a, b) => b.edgePct - a.edgePct)
  
  return (
    <div className="picks-feed">
      <div className="picks-header">
        <h2>Today's Picks</h2>
        <span className="disclaimer">Model output only. Not betting advice.</span>
      </div>
      
      {sorted.map(pick => (
        <PickCard
          key={pick.match.id}
          pick={pick}
          onClickMatch={() => navigate(`/matches/${pick.match.id}`)}
        />
      ))}
    </div>
  )
}

// Individual pick card
function PickCard({ pick, onClickMatch }) {
  const confidenceColors = {
    high: "text-green-600 bg-green-50",
    medium: "text-amber-600 bg-amber-50",
    low: "text-gray-500 bg-gray-50",
  }
  
  return (
    <div className="pick-card" onClick={onClickMatch}>
      <div className="pick-matchup">
        <span>{pick.match.player1}</span>
        <span className="vs">vs</span>
        <span>{pick.match.player2}</span>
      </div>
      
      <div className="pick-recommendation">
        <strong>{pick.pickSide === "p1" ? pick.match.player1 : pick.match.player2}</strong>
        <span className={`confidence-badge ${confidenceColors[pick.confidence]}`}>
          {pick.confidence} confidence
        </span>
      </div>
      
      <div className="pick-odds-row">
        <div>
          <span className="label">Model prob</span>
          <span className="value">{(pick.ourProb * 100).toFixed(1)}%</span>
        </div>
        <div>
          <span className="label">DK odds</span>
          <span className="value">{formatAmericanOdds(pick.dkOdds)}</span>
        </div>
        <div>
          <span className="label">Edge</span>
          <span className={`value ${pick.edgePct > 0 ? "text-green-600" : "text-red-500"}`}>
            {pick.edgePct > 0 ? "+" : ""}{pick.edgePct.toFixed(1)}%
          </span>
        </div>
      </div>
      
      <ul className="reasoning">
        {pick.reasoning.map((r, i) => <li key={i}>{r}</li>)}
      </ul>
    </div>
  )
}
```

---

## Feature 4 — Odds Movement Tracker

```tsx
// components/OddsMovementChart.tsx
// Recharts line chart showing DK line movement for a match

import { LineChart, Line, XAxis, YAxis, Tooltip, ReferenceLine } from "recharts"

export function OddsMovementChart({ snapshots }) {
  const data = snapshots.map(s => ({
    time: new Date(s.snapshot_time).toLocaleTimeString(),
    p1_implied: impliedProb(s.p1_odds),
    p2_implied: impliedProb(s.p2_odds),
    p1_odds: s.p1_odds,
  }))
  
  const openingLine = data[0]?.p1_implied
  const currentLine = data[data.length - 1]?.p1_implied
  const moved = Math.abs(currentLine - openingLine) > 0.02  // flag >2% move
  
  return (
    <div className="odds-movement">
      <h3>
        Line Movement
        {moved && <span className="steam-badge">🔥 Steam move detected</span>}
      </h3>
      <LineChart data={data} width={600} height={200}>
        <XAxis dataKey="time" />
        <YAxis domain={[0, 1]} tickFormatter={v => `${(v*100).toFixed(0)}%`} />
        <Tooltip formatter={(v, name) => [`${(v*100).toFixed(1)}%`, name]} />
        <ReferenceLine y={0.5} stroke="#ccc" strokeDasharray="4 4" />
        <Line type="monotone" dataKey="p1_implied" stroke="#3b82f6" name="P1 win prob" dot={false} />
      </LineChart>
      <p className="line-note">
        Opening: {(openingLine * 100).toFixed(1)}% → 
        Current: {(currentLine * 100).toFixed(1)}%
        {moved && ` (${((currentLine - openingLine) * 100).toFixed(1)}% shift)`}
      </p>
    </div>
  )
}

function impliedProb(americanOdds: number): number {
  if (americanOdds > 0) return 100 / (americanOdds + 100)
  return Math.abs(americanOdds) / (Math.abs(americanOdds) + 100)
}
```

---

## Feature 5 — 180s Calculator (Interactive Tool)

This is a shareable, linkable tool that drives SEO and engagement.

```tsx
// pages/tools/180s-calculator.tsx

export function OneEightiesCalculator() {
  const [p1Rate, setP1Rate] = useState(0.12)
  const [p2Rate, setP2Rate] = useState(0.10)
  const [legsToWin, setLegsToWin] = useState(6)
  const [totalLine, setTotalLine] = useState(10.5)
  
  const expectedLegs = legsToWin * 1.6  // typical match goes ~80% of max legs
  const p1Expected = p1Rate * expectedLegs
  const p2Expected = p2Rate * expectedLegs
  const combinedExpected = p1Expected + p2Expected
  
  // Poisson over probability
  const probOver = 1 - poissonCDF(Math.floor(totalLine), combinedExpected)
  const probUnder = 1 - probOver
  
  // Fair odds
  const fairOverOdds = toAmericanOdds(probOver)
  const fairUnderOdds = toAmericanOdds(probUnder)
  
  return (
    <div className="calculator">
      <h1>180s Over/Under Calculator</h1>
      <p>Compare DraftKings' 180s total against expected value from player rates.</p>
      
      <div className="inputs">
        <SliderInput
          label="Player 1 — 180s per leg"
          value={p1Rate} min={0} max={0.3} step={0.005}
          onChange={setP1Rate}
          display={v => v.toFixed(3)}
        />
        <SliderInput
          label="Player 2 — 180s per leg"
          value={p2Rate} min={0} max={0.3} step={0.005}
          onChange={setP2Rate}
          display={v => v.toFixed(3)}
        />
        <SliderInput
          label="Legs to win"
          value={legsToWin} min={3} max={13} step={1}
          onChange={setLegsToWin}
          display={v => v.toString()}
        />
        <NumberInput
          label="DraftKings total line"
          value={totalLine} step={0.5}
          onChange={setTotalLine}
        />
      </div>
      
      <div className="results">
        <ResultRow label="Expected 180s (combined)" value={combinedExpected.toFixed(1)} />
        <ResultRow label="Prob over" value={`${(probOver * 100).toFixed(1)}%`} />
        <ResultRow label="Fair OVER odds" value={fairOverOdds > 0 ? `+${fairOverOdds}` : fairOverOdds} />
        <ResultRow label="Fair UNDER odds" value={fairUnderOdds > 0 ? `+${fairUnderOdds}` : fairUnderOdds} />
      </div>
      
      <p className="note">
        Enter the DraftKings line for OVER and UNDER below to see your edge.
      </p>
      <EdgeComparisonInput probOver={probOver} probUnder={probUnder} />
    </div>
  )
}

// Poisson CDF — used client-side so no server needed
function poissonCDF(k: number, lambda: number): number {
  let sum = 0
  let term = Math.exp(-lambda)
  for (let i = 0; i <= k; i++) {
    sum += term
    term *= lambda / (i + 1)
  }
  return sum
}
```

---

## Feature 6 — Tournament Hub

```tsx
// pages/tournaments/[slug].tsx

export function TournamentHub({ tournament, currentYear, bracket, schedule }) {
  return (
    <div>
      <TournamentHeader tournament={tournament} />
      
      {/* Format explainer — important for new bettors */}
      <FormatCard
        format={tournament.format}
        legsToWin={tournament.legs_to_win}
        setsToWin={tournament.sets_to_win}
        description={tournament.format_description}
      />
      
      {/* Live bracket / draw */}
      {bracket && <BracketViewer bracket={bracket} />}
      
      {/* Schedule with model picks */}
      <ScheduleTable
        matches={schedule}
        showPicks
        showOdds
      />
      
      {/* Historical results — who has won this before */}
      <PastWinnersTable tournament={tournament} />
      
      {/* Player form guide — ranking players by current form */}
      <FormGuide
        players={tournament.entrants}
        statKeys={["elo", "avg_3dart", "checkout_pct", "win_rate_last20"]}
      />
      
      {/* DraftKings outright market odds */}
      <OutrightOddsTable tournament={tournament} currentYear={currentYear} />
    </div>
  )
}
```

---

## Feature Priority Matrix (MVP vs Later)

| Feature | MVP | V2 | V3 |
|---------|-----|----|-----|
| Player profiles with Elo | ✓ | | |
| Match center (pre-match) | ✓ | | |
| Today's picks feed | ✓ | | |
| 180s calculator tool | ✓ | | |
| Tournament hub pages | ✓ | | |
| Odds movement chart | ✓ | | |
| H2H comparison tool | ✓ | | |
| Live scores (during events) | | ✓ | |
| Live model updates | | ✓ | |
| Email/push alerts for picks | | ✓ | |
| Custom model weighting | | ✓ | |
| Free public API | | ✓ | |
| Prop model (checkout %) | | ✓ | |
| User accounts + bet tracking | | | ✓ |
| Fantasy darts integration | | | ✓ |
| In-play betting signals | | | ✓ |
