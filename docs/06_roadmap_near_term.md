# 06 — Near-Term Roadmap (Days 1–90)

## Philosophy

Resist building everything. The goal of the first 90 days is one thing: **be the best page on the internet for any DK-covered darts match**. That means one excellent match center beats ten mediocre pages.

---

## Week 1–2: Foundation

### Tasks
- [ ] Set up monorepo (`pnpm workspaces` or `turborepo`)
- [ ] Spin up Supabase project (free tier: 500MB, plenty for year 1)
- [ ] Run `prisma migrate dev` to create schema
- [ ] Run historical seed from dartsdatabase.co.uk (2000–present)
- [ ] Verify data: spot-check 10 known match results
- [ ] Stand up FastAPI with `/health` endpoint on Railway (free tier)
- [ ] Stand up Next.js on Vercel
- [ ] Connect them — Next.js fetches from Railway API

```bash
# Bootstrap commands
npx create-turbo@latest darts-site
cd darts-site
pnpm add -D prisma
npx prisma init

# Seed historical data
cd apps/api
pip install -r requirements.txt
python -m scrapers.dartsdatabase seed --start-year 2000

# Verify
python -c "
import sqlite3
conn = sqlite3.connect('darts.db')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM matches')
print('Total matches:', cur.fetchone()[0])
cur.execute('SELECT year, COUNT(*) FROM matches GROUP BY year ORDER BY year DESC LIMIT 5')
print('Recent years:', cur.fetchall())
"
```

### Deliverable
A local Postgres DB with ~15,000 historical PDC matches.

---

## Week 3–4: Player Profiles

Build `/players/[slug]` first — it's the lowest-risk page with the highest SEO value.

### Tasks
- [ ] Build Elo model, train on full history, store results in `elo_history`
- [ ] Build `PlayerStatsCache` refresh job (runs nightly)
- [ ] Build `/players` index page — searchable table of all active PDC players
- [ ] Build `/players/[slug]` profile page with:
  - Career stats card
  - Elo history line chart (Recharts)
  - Tournament win rate table
  - Last 20 match results list
- [ ] Add `generateStaticParams` for top 50 players (SSG for speed)
- [ ] Submit sitemaps to Google

```ts
// apps/web/src/app/players/[slug]/page.tsx
import { Metadata } from 'next'
import { getPlayer } from '@/lib/api'
import { PlayerProfile } from '@/components/PlayerProfile'
import { notFound } from 'next/navigation'

// Pre-render top 50 players at build time
export async function generateStaticParams() {
  const top50 = await fetch(`${process.env.API_URL}/v1/players?limit=50&sort=elo`)
  const players = await top50.json()
  return players.map(p => ({ slug: p.slug }))
}

export async function generateMetadata({ params }): Promise<Metadata> {
  const player = await getPlayer(params.slug)
  if (!player) return {}
  return {
    title: `${player.name} Darts Stats, Elo Rating & Betting Analysis`,
    description: `${player.name} career stats, 3-dart average, checkout %, Elo rating, 
                  head-to-head record and DraftKings betting analysis.`,
    openGraph: {
      title: `${player.name} — Darts Analytics`,
      type: 'profile',
    },
  }
}

export default async function PlayerPage({ params }) {
  const player = await getPlayer(params.slug)
  if (!player) notFound()
  return <PlayerProfile player={player} />
}
```

### Deliverable
~200 live player profile pages indexed by Google.

---

## Week 5–6: Match Center + Pre-Match Analysis

### Tasks
- [ ] Build `/matches/[id]` — the core page
- [ ] Add stat comparison bars (avg, checkout%, 180s)
- [ ] Add H2H history table (last 10 meetings)
- [ ] Add odds snapshot display (latest DK line, if available)
- [ ] Set up The Odds API polling (every 15 min) for upcoming DK darts events
- [ ] Train logistic regression match predictor on historical data
- [ ] Backtest model — log Brier score and accuracy
- [ ] Display model probability on match center page

```python
# Train and evaluate the model
# apps/api/scripts/train_predictor.py
from models.match_predictor import DartsMatchPredictor
from models.backtester import backtest_model
from db import get_all_matches_with_stats

matches = get_all_matches_with_stats()
stats_cache = build_stats_cache(matches)

predictor = DartsMatchPredictor()
results = backtest_model(predictor, matches, stats_cache)

print(f"Brier Score: {results['brier_score']}")    # target < 0.22
print(f"Accuracy:    {results['accuracy']:.1%}")   # target > 60%
print(f"N:           {results['n_predictions']}")

# Retrain on full dataset and save
predictor.train(matches, stats_cache)
predictor.save("models/match_predictor.pkl")
```

### Deliverable
Match center pages for all upcoming DK-covered darts events, with model probability displayed.

---

## Week 7–8: Picks Feed + Edge Calculator

### Tasks
- [ ] Build `/picks` page — today's model picks with edge %
- [ ] Build `/tools/edge-calculator` — manual odds vs probability input
- [ ] Build `/tools/180s-calculator` — Poisson-based prop tool
- [ ] Add responsible gambling disclaimer to all picks pages
- [ ] Wire up DraftKings affiliate link (see `09_legal_and_compliance.md`)
- [ ] Add "Bet at DraftKings" CTA buttons linked to specific event pages

```tsx
// Key affiliate CTA component
// components/ui/DKButton.tsx
const DK_BASE = 'https://sportsbook.draftkings.com'
const AFFILIATE_TAG = process.env.NEXT_PUBLIC_DK_AFFILIATE_TAG

interface DKButtonProps {
  eventSlug?: string  // e.g. 'sports/darts'
  label?: string
}

export function DKButton({ eventSlug = 'sports/darts', label = 'Bet at DraftKings' }: DKButtonProps) {
  const url = `${DK_BASE}/${eventSlug}${AFFILIATE_TAG ? `?${AFFILIATE_TAG}` : ''}`
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer sponsored"
      className="inline-flex items-center gap-2 bg-amber text-bg font-semibold 
                 px-4 py-2 rounded-md hover:bg-amber/90 transition-colors text-sm"
    >
      {label}
      <svg width="12" height="12" viewBox="0 0 12 12" fill="currentColor">
        <path d="M6.5 1H11v4.5M11 1L5 7M2 3H1v8h8V9" stroke="currentColor" strokeWidth="1.5" fill="none"/>
      </svg>
    </a>
  )
}
```

### Deliverable
A functional picks feed and two interactive tools.

---

## Week 9–10: Tournament Hubs

### Tasks
- [ ] Build `/tournaments` index
- [ ] Build `/tournaments/[slug]` hub for each of the 9 DK-covered tournaments
- [ ] Add schedule table, past winners, and form guide
- [ ] Write 500-word tournament explainer for each (format, history, betting notes)
- [ ] Add outright winner market odds table

```ts
// Static tournament metadata
// apps/web/src/lib/tournaments.ts
export const DK_TOURNAMENTS = [
  {
    slug: 'pdc-world-championship',
    name: 'PDC World Championship',
    shortName: 'Worlds',
    category: 'major',
    format: 'sets',
    setsToWin: 7,  // final
    month: 'December–January',
    venue: 'Alexandra Palace, London',
    dkSportKey: 'darts_pdc_world_championship',
    description: `The biggest event in darts. Held every December–January at "Ally Pally," 
    the World Championship draws the largest betting volume of any darts event on DraftKings 
    by a significant margin. The sets format (rather than legs) increases variance in early 
    rounds, creating value on underdog outright picks.`,
    bettingNotes: [
      'Early round upsets are more common than in legs-only formats — sets give underdogs more chances',
      'MVG and Luke Littler have dominated recent editions — outrights on them typically offer little value',
      'Quarter-final and semi-final match markets offer the best risk-adjusted edge opportunities',
      'The draw is seeded — identify bracket quadrants where high seeds meet early',
    ],
  },
  {
    slug: 'premier-league-darts',
    name: 'Premier League Darts',
    shortName: 'Premier League',
    category: 'premier_league',
    format: 'legs',
    legsToWin: 6,  // regular night (best of 11)
    month: 'February–May',
    venue: 'Multiple UK/European cities',
    dkSportKey: 'darts_premier_league',
    description: `A 16-week league featuring the top 8-9 PDC players. Weekly Thursday-night 
    events across the UK and Europe. Best format for in-season modeling because the same players 
    compete every week — form, fatigue, and travel effects are all trackable.`,
    bettingNotes: [
      'Players who travel far (e.g. Australian players to European legs) show measurable performance dips',
      'The Night Winner market (best of 11 legs) has more variance than full-season markets — good for model edge',
      'Form in the first 4 weeks is a strong predictor of Play-Off qualification',
      'Home crowd effects are significant in cities where a player has local support',
    ],
  },
  // ... remaining tournaments
]
```

### Deliverable
9 tournament hub pages, all with SEO metadata, indexed by Google.

---

## Week 11–12: Polish, SEO & Analytics

### Tasks
- [ ] Add `sitemap.xml` generator (Next.js built-in)
- [ ] Add `robots.txt`
- [ ] Structured data (JSON-LD) on player and match pages
- [ ] Add Plausible analytics snippet
- [ ] Core Web Vitals audit (Lighthouse) — target LCP < 2.5s
- [ ] Add error boundaries and loading skeletons throughout
- [ ] Set up Sentry for error tracking
- [ ] Write first 5 blog posts (tournament previews, model explainers)

```ts
// apps/web/src/app/players/[slug]/page.tsx — add JSON-LD
function PlayerJsonLd({ player, stats }) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Person',
    name: player.name,
    nationality: player.nationality,
    knowsAbout: 'Darts',
    description: `Professional darts player. Elo rating: ${stats.elo}. Career 3-dart average: ${stats.career_avg}.`,
  }
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  )
}
```

---

## 90-Day Success Metrics

| Metric | Target |
|--------|--------|
| Google-indexed pages | 500+ |
| Organic sessions/month | 2,000+ |
| Model Brier score | < 0.22 |
| Model accuracy | > 60% |
| DraftKings affiliate clicks | 200+/month |
| Uptime | > 99.5% |
| Page LCP | < 2.5s |
