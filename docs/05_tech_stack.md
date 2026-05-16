# 05 — Tech Stack & Architecture

## Stack Overview

```
Frontend:   Next.js 14 (App Router) + TypeScript + Tailwind CSS
Backend:    FastAPI (Python) — data pipelines, model serving
Database:   PostgreSQL (Supabase free tier to start)
Cache:      Redis (Upstash free tier) — odds snapshots, live scores
Queue:      BullMQ (Redis-backed) — scraper jobs
ORM:        Prisma (frontend queries) + SQLAlchemy (Python scrapers)
Auth:       NextAuth.js (GitHub/Google — for future user accounts)
Deploy:     Vercel (frontend) + Railway (FastAPI) + Supabase (DB)
Analytics:  Plausible (privacy-first, cheap)
Monitoring: Sentry (errors) + Uptime Robot (free tier)
```

**Why split frontend/backend?** Python owns the data science ecosystem (pandas, sklearn, scipy). Next.js owns the DX and deployment story. Keep them separate and communicate via a clean REST API.

---

## Repository Structure

```
darts-site/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/            # App Router pages
│   │   │   │   ├── page.tsx            # Home
│   │   │   │   ├── tournaments/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [slug]/page.tsx
│   │   │   │   ├── players/
│   │   │   │   │   ├── page.tsx
│   │   │   │   │   └── [slug]/page.tsx
│   │   │   │   ├── matches/[id]/page.tsx
│   │   │   │   ├── picks/page.tsx
│   │   │   │   ├── odds/page.tsx
│   │   │   │   └── tools/
│   │   │   │       ├── edge-calculator/page.tsx
│   │   │   │       ├── h2h/page.tsx
│   │   │   │       └── 180s-calculator/page.tsx
│   │   │   ├── components/
│   │   │   ├── lib/
│   │   │   └── types/
│   │   ├── prisma/schema.prisma
│   │   └── package.json
│   │
│   └── api/                    # FastAPI backend
│       ├── main.py
│       ├── routers/
│       │   ├── matches.py
│       │   ├── players.py
│       │   ├── odds.py
│       │   └── picks.py
│       ├── models/
│       │   ├── elo.py
│       │   ├── match_predictor.py
│       │   └── props_model.py
│       ├── scrapers/
│       │   ├── dartsdatabase.py
│       │   ├── dartsdata_api.py
│       │   └── odds_api.py
│       ├── jobs/
│       │   └── scheduler.py
│       └── requirements.txt
│
├── packages/
│   └── shared-types/           # TypeScript types shared across apps
│
└── docker-compose.yml          # Local dev: postgres + redis
```

---

## Database (Prisma Schema)

```prisma
// apps/web/prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Player {
  id          Int       @id @default(autoincrement())
  name        String    @unique
  slug        String    @unique
  nickname    String?
  nationality String?
  dob         DateTime?
  pdcId       String?
  dartdbId    String?
  createdAt   DateTime  @default(now())

  matchesAsP1   Match[]  @relation("Player1")
  matchesAsP2   Match[]  @relation("Player2")
  winsAsWinner  Match[]  @relation("Winner")
  statsCache    PlayerStatsCache[]
  eloHistory    EloHistory[]
}

model Tournament {
  id          Int      @id @default(autoincrement())
  name        String
  slug        String   @unique
  shortName   String?
  category    String   // 'major' | 'series' | 'premier_league' | 'european_tour'
  dkCovered   Boolean  @default(false)
  format      String   // 'sets' | 'legs'
  legsToWin   Int?
  setsToWin   Int?
  startMonth  Int?
  endMonth    Int?

  matches     Match[]
}

model Match {
  id            Int        @id @default(autoincrement())
  tournamentId  Int
  tournament    Tournament @relation(fields: [tournamentId], references: [id])
  year          Int
  round         String
  player1Id     Int
  player1       Player     @relation("Player1", fields: [player1Id], references: [id])
  player2Id     Int
  player2       Player     @relation("Player2", fields: [player2Id], references: [id])
  score1        Int?
  score2        Int?
  winnerId      Int?
  winner        Player?    @relation("Winner", fields: [winnerId], references: [id])
  matchDate     DateTime?
  venue         String?
  avg1          Decimal?   @db.Decimal(5, 2)
  avg2          Decimal?   @db.Decimal(5, 2)
  checkoutPct1  Decimal?   @db.Decimal(5, 2)
  checkoutPct2  Decimal?   @db.Decimal(5, 2)
  oneEighties1  Int?
  oneEighties2  Int?
  highCheckout1 Int?
  highCheckout2 Int?
  createdAt     DateTime   @default(now())

  oddsSnapshots OddsSnapshot[]

  @@index([player1Id])
  @@index([player2Id])
  @@index([tournamentId, year])
}

model OddsSnapshot {
  id           Int      @id @default(autoincrement())
  matchId      Int
  match        Match    @relation(fields: [matchId], references: [id])
  bookmaker    String
  market       String
  outcome      String
  price        Int      // American odds
  impliedProb  Decimal  @db.Decimal(5, 4)
  snapshotTime DateTime @default(now())

  @@index([matchId, snapshotTime])
}

model PlayerStatsCache {
  id             Int      @id @default(autoincrement())
  playerId       Int
  player         Player   @relation(fields: [playerId], references: [id])
  tournamentSlug String?  // null = all tournaments
  yearFrom       Int
  yearTo         Int
  matchesPlayed  Int
  matchesWon     Int
  winRate        Decimal  @db.Decimal(5, 4)
  avg3dart       Decimal? @db.Decimal(5, 2)
  avgCheckout    Decimal? @db.Decimal(5, 2)
  avg180sPerLeg  Decimal? @db.Decimal(5, 3)
  updatedAt      DateTime @updatedAt

  @@unique([playerId, tournamentSlug, yearFrom, yearTo])
}

model EloHistory {
  id        Int      @id @default(autoincrement())
  playerId  Int
  player    Player   @relation(fields: [playerId], references: [id])
  rating    Decimal  @db.Decimal(7, 2)
  matchId   Int?
  recordedAt DateTime @default(now())

  @@index([playerId, recordedAt])
}
```

---

## FastAPI Backend

```python
# apps/api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import matches, players, odds, picks
from jobs.scheduler import start_scheduler
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield

app = FastAPI(title="Darts Analytics API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "http://localhost:3000"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(matches.router, prefix="/v1/matches")
app.include_router(players.router, prefix="/v1/players")
app.include_router(odds.router, prefix="/v1/odds")
app.include_router(picks.router, prefix="/v1/picks")
```

```python
# apps/api/routers/picks.py
from fastapi import APIRouter, Query
from models.elo import DartsElo
from models.match_predictor import DartsMatchPredictor
from models.props_model import PropsModels, calculate_edge
from db import get_upcoming_matches, get_latest_odds, get_player_stats
import joblib

router = APIRouter()
elo = DartsElo()
predictor = DartsMatchPredictor.load("models/match_predictor.pkl")

@router.get("/today")
async def get_todays_picks(min_edge: float = Query(0.02, ge=0, le=0.2)):
    upcoming = await get_upcoming_matches(days_ahead=1)
    picks = []

    for match in upcoming:
        stats = await get_player_stats([match["player1_id"], match["player2_id"]])
        odds = await get_latest_odds(match["id"])
        if not odds:
            continue

        prob = predictor.predict_proba(match, stats)
        edge = calculate_edge(prob, odds["p1_odds"])

        if edge["edge"] >= min_edge:
            picks.append({
                "match_id": match["id"],
                "tournament": match["tournament_name"],
                "player1": match["player1"],
                "player2": match["player2"],
                "pick": match["player1"] if edge["edge"] > 0 else match["player2"],
                "our_prob": edge["our_prob"],
                "dk_odds": edge["dk_odds"],
                "edge_pct": edge["edge_pct"],
                "kelly_quarter": edge["kelly_quarter"],
                "reasoning": build_reasoning(match, stats, edge),
            })

    return sorted(picks, key=lambda p: p["edge_pct"], reverse=True)


def build_reasoning(match, stats, edge) -> list[str]:
    reasons = []
    s1, s2 = stats[match["player1_id"]], stats[match["player2_id"]]

    avg_diff = s1.get("avg_3dart", 0) - s2.get("avg_3dart", 0)
    if abs(avg_diff) > 2:
        better = match["player1"] if avg_diff > 0 else match["player2"]
        reasons.append(f"{better} has a {abs(avg_diff):.1f} point 3-dart average advantage (last 20 matches)")

    if s1.get("elo", 1500) - s2.get("elo", 1500) > 50:
        reasons.append(f"{match['player1']} rated {s1['elo']:.0f} Elo vs {s2['elo']:.0f} — significant rating gap")

    return reasons[:3]  # max 3 bullets
```

---

## Next.js Data Fetching

```ts
// apps/web/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export async function getTodaysPicks(minEdge = 0.02) {
  const res = await fetch(`${API_BASE}/v1/picks/today?min_edge=${minEdge}`, {
    next: { revalidate: 300 },  // cache 5 min
  })
  if (!res.ok) throw new Error('Failed to fetch picks')
  return res.json()
}

export async function getPlayer(slug: string) {
  const res = await fetch(`${API_BASE}/v1/players/${slug}`, {
    next: { revalidate: 3600 },  // cache 1 hr
  })
  if (!res.ok) throw new Error(`Player not found: ${slug}`)
  return res.json()
}

export async function getMatch(id: string) {
  const res = await fetch(`${API_BASE}/v1/matches/${id}`, {
    next: { revalidate: 60 },  // 1 min — faster during live events
  })
  return res.json()
}

export async function getOddsHistory(matchId: string) {
  const res = await fetch(`${API_BASE}/v1/odds/${matchId}/history`, {
    next: { revalidate: 120 },
  })
  return res.json()
}
```

---

## WebSocket (Live Scores)

```python
# apps/api/routers/ws.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from scrapers.dartsdata_api import get_live_matches
import asyncio, json

router = APIRouter()

class LiveManager:
    def __init__(self):
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket):
        self.connections.remove(ws)

    async def broadcast(self, data: dict):
        msg = json.dumps(data)
        for ws in self.connections:
            try:
                await ws.send_text(msg)
            except Exception:
                pass

manager = LiveManager()

@router.websocket("/ws/live")
async def live_scores(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            matches = get_live_matches()
            if matches:
                await manager.broadcast({"type": "live_update", "matches": matches})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

```tsx
// apps/web/src/hooks/useLiveScores.ts
import { useEffect, useState } from 'react'

export function useLiveScores() {
  const [scores, setScores] = useState<LiveMatch[]>([])

  useEffect(() => {
    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/live`)

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'live_update') {
        setScores(data.matches)
      }
    }

    ws.onerror = () => console.warn('Live scores WS error — falling back to polling')

    return () => ws.close()
  }, [])

  return scores
}
```

---

## Docker Compose (Local Dev)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: darts
      POSTGRES_USER: darts
      POSTGRES_PASSWORD: darts
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://darts:darts@postgres:5432/darts
      REDIS_URL: redis://redis:6379
      ODDS_API_KEY: ${ODDS_API_KEY}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./apps/api:/app
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

volumes:
  pgdata:
```

---

## Environment Variables

```bash
# apps/web/.env.local
DATABASE_URL=postgresql://darts:darts@localhost:5432/darts
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXTAUTH_SECRET=generate-with-openssl-rand-hex-32
NEXTAUTH_URL=http://localhost:3000

# apps/api/.env
DATABASE_URL=postgresql://darts:darts@localhost:5432/darts
REDIS_URL=redis://localhost:6379
ODDS_API_KEY=your_key_here
DARTSDATA_REFERER=https://www.dartsdata.com/
```
