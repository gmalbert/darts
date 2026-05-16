# 08 — SEO & Content Strategy

## Core Insight

Darts betting is a long-tail SEO opportunity. There are virtually no well-optimized English-language analytics sites for PDC darts. The competition is:
- Generic sportsbook review sites with thin darts pages
- UK tabloids (Mirror, Sun) with tournament news but no data
- Scattered Reddit threads

A data-driven site with 500+ well-structured pages will rank for a huge volume of low-competition keywords with meaningful betting intent.

---

## Keyword Targets

### Tier 1 — High intent, low competition (target first 90 days)

```
[player name] darts stats          e.g. "luke littler darts stats"
[player name] darts average        e.g. "gerwyn price 3 dart average"
[player name] checkout percentage  e.g. "michael van gerwen checkout percentage"
[player 1] vs [player 2] darts     e.g. "van gerwen vs littler darts"
[tournament] darts results         e.g. "pdc world championship 2024 results"
[tournament] darts betting picks   e.g. "premier league darts betting picks"
```

### Tier 2 — Moderate competition, high volume (months 3–6)

```
PDC world championship odds
premier league darts predictions
darts betting tips today
darts 180s over under
pdc player rankings
darts head to head record
```

### Tier 3 — Competitive, worth targeting by month 12

```
darts betting
darts odds
darts predictions
PDC world championship winner odds
```

---

## Programmatic SEO Pages

These pages are generated automatically from your database — one template, thousands of URL variations.

### Player Pages (200+ pages)

```
URL: /players/[slug]
Title: "[Name] Darts Stats, Elo Rating & Career Record | YourSite"
H1: "[Name] — Career Statistics & Betting Analysis"
```

```ts
// Metadata generation at scale
export async function generateMetadata({ params }): Promise<Metadata> {
  const player = await getPlayer(params.slug)
  const stats = player.stats

  return {
    title: `${player.name} Darts Stats, Elo Rating & Betting Analysis`,
    description: `${player.name} career stats: ${stats.career_avg} 3-dart average, ` +
      `${(stats.checkout_pct * 100).toFixed(1)}% checkout rate, Elo ${stats.elo}. ` +
      `Head-to-head record and DraftKings betting analysis.`,
    keywords: [
      player.name,
      `${player.name} darts`,
      `${player.name} stats`,
      `${player.name} average`,
      `${player.name} betting`,
      player.nickname && `${player.nickname} darts`,
    ].filter(Boolean),
    openGraph: {
      title: `${player.name} — Darts Analytics`,
      description: `Elo: ${stats.elo} | Avg: ${stats.career_avg} | Checkout: ${(stats.checkout_pct*100).toFixed(1)}%`,
      type: 'profile',
      url: `https://yourdomain.com/players/${params.slug}`,
    },
    alternates: { canonical: `https://yourdomain.com/players/${params.slug}` },
  }
}
```

### H2H Pages (thousands of pages)

```
URL: /h2h/[player1-slug]-vs-[player2-slug]
Title: "[Player 1] vs [Player 2]: Head-to-Head Darts Record"
```

```ts
// apps/web/src/app/h2h/[matchup]/page.tsx
// matchup = "van-gerwen-vs-littler"

export async function generateStaticParams() {
  // Pre-render H2H pages for top 50 players against each other
  // That's 50 * 49 / 2 = 1,225 pages
  const top50 = await getTopPlayers(50)
  const pairs = []
  for (let i = 0; i < top50.length; i++) {
    for (let j = i + 1; j < top50.length; j++) {
      pairs.push({ matchup: `${top50[i].slug}-vs-${top50[j].slug}` })
    }
  }
  return pairs
}

export default async function H2HPage({ params }) {
  const [slug1, slug2] = params.matchup.split('-vs-')
  const [p1, p2, history] = await Promise.all([
    getPlayer(slug1),
    getPlayer(slug2),
    getH2HHistory(slug1, slug2),
  ])

  const p1Wins = history.filter(m => m.winner_slug === slug1).length
  const p2Wins = history.length - p1Wins

  return (
    <main>
      <h1>{p1.name} vs {p2.name}: Head-to-Head Record</h1>
      <p className="lead">
        {p1.name} and {p2.name} have met {history.length} times in PDC competition.
        {p1.name} leads {p1Wins}–{p2Wins}.
      </p>
      <H2HStatsTable p1={p1} p2={p2} history={history} />
      <MatchHistoryList matches={history} p1={p1} p2={p2} />
    </main>
  )
}
```

### Sitemap

```ts
// apps/web/src/app/sitemap.ts
import { MetadataRoute } from 'next'
import { getAllPlayers, getAllMatches, getAllTournaments } from '@/lib/db'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const [players, matches, tournaments] = await Promise.all([
    getAllPlayers(),
    getAllMatches({ yearFrom: 2020 }),
    getAllTournaments(),
  ])

  const BASE = 'https://yourdomain.com'

  const playerUrls = players.map(p => ({
    url: `${BASE}/players/${p.slug}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }))

  const matchUrls = matches.map(m => ({
    url: `${BASE}/matches/${m.id}`,
    lastModified: m.match_date ? new Date(m.match_date) : new Date(),
    changeFrequency: 'never' as const,  // historical matches don't change
    priority: 0.5,
  }))

  const tournamentUrls = tournaments.map(t => ({
    url: `${BASE}/tournaments/${t.slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.9,
  }))

  // H2H pages for top 50 pairs
  const top50 = players.slice(0, 50)
  const h2hUrls = []
  for (let i = 0; i < top50.length; i++) {
    for (let j = i + 1; j < top50.length; j++) {
      h2hUrls.push({
        url: `${BASE}/h2h/${top50[i].slug}-vs-${top50[j].slug}`,
        lastModified: new Date(),
        changeFrequency: 'monthly' as const,
        priority: 0.6,
      })
    }
  }

  return [
    { url: BASE, lastModified: new Date(), priority: 1.0 },
    { url: `${BASE}/picks`, lastModified: new Date(), priority: 1.0 },
    { url: `${BASE}/tournaments`, lastModified: new Date(), priority: 0.9 },
    { url: `${BASE}/players`, lastModified: new Date(), priority: 0.8 },
    { url: `${BASE}/odds`, lastModified: new Date(), priority: 0.9 },
    ...tournamentUrls,
    ...playerUrls,
    ...h2hUrls,
    ...matchUrls,
  ]
}
```

---

## Content Calendar

### Pre-Event Content (publish 3–5 days before each DK event)

```
Title format: "[Tournament Year] Darts Betting Preview: Model Picks, Odds & Analysis"
Sections:
  - Draw/bracket analysis
  - Form guide (top 8 players)
  - Model's top 3 picks with reasoning
  - Value outrights (players the model likes at long odds)
  - 180s props analysis
  - Our model accuracy in recent editions of this event
```

### Tournament Result Posts (publish within 24h of completion)

```
Title format: "[Player] Wins [Tournament]: Darts Results & Betting Recap"
Sections:
  - Winner's path through the draw
  - Key stats (avgs, checkouts, 180s)
  - How the model performed (picks hit/miss)
  - Updated Elo ratings post-event
  - Looking ahead: next event odds
```

### Evergreen Content (write once, update annually)

```
- "How Does PDC Darts Scoring Work? A Betting Guide"
- "What Is the 3-Dart Average in Darts and Why Does It Matter for Betting?"
- "PDC World Championship Format Explained"
- "How to Bet on Darts at DraftKings: A Beginner's Guide"
- "Darts 180s Betting: Over/Under Strategy and Expected Value"
- "Premier League Darts Format: How Betting Works"
- "Best Darts Statistics Sites for Betting Research"
```

---

## Internal Linking Strategy

Every player page should link to:
- Their top 5 H2H matchup pages
- Tournaments they've won
- Recent match center pages

Every match center page should link to:
- Both player profiles
- The tournament hub
- Similar recent matchups

Every tournament hub should link to:
- All entrant player profiles
- Past result pages for that tournament
- Preview/recap blog posts

```tsx
// components/RelatedLinks.tsx — add to bottom of every major page
export function RelatedLinks({ type, context }) {
  // context contains the relevant slugs to generate links
  switch (type) {
    case 'player':
      return (
        <nav aria-label="Related pages">
          <h3>Related</h3>
          <ul>
            {context.topH2Hs.map(opp => (
              <li key={opp.slug}>
                <Link href={`/h2h/${context.slug}-vs-${opp.slug}`}>
                  {context.name} vs {opp.name} — Head-to-Head Record
                </Link>
              </li>
            ))}
            {context.tournaments.map(t => (
              <li key={t.slug}>
                <Link href={`/tournaments/${t.slug}`}>{t.name} results and betting</Link>
              </li>
            ))}
          </ul>
        </nav>
      )
    // other types...
  }
}
```
