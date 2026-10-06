"""
backend/app.py — BullzIQ FastAPI entry point.

Substitutes the Cloudflare Worker / D1 stack from
`docs/BullzIQ_Streamlit_to_React_Cloudflare_Conversion_Guide.md` with a
FastAPI service backed by the existing local SQLite database.

Heavy Python (scikit-learn model training, dartsdatabase scraping, full
historical rebuilds) stays outside the request path — see `jobs/`.

Run:
    python -m backend.app           # uvicorn programmatically
    # or:
    uvicorn backend.app:app --reload --port 8000

Health:
    GET /api/v1/health
    GET /api/v1/meta
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.api import queries
from backend.calculators import client_math


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Lazy DB initialisation — same semantics as Streamlit's ensure_seeded().
    try:
        from db.seed import ensure_seeded
        ensure_seeded()
    except Exception as exc:  # pragma: no cover — surface but don't crash
        # Empty / missing real data is acceptable; the React client will
        # render empty states per the .md guidance.
        print(f"[backend] ensure_seeded warning: {exc}")
    yield


app = FastAPI(
    title="BullzIQ API",
    version="1.0.0",
    description="FastAPI replacement for the BullzIQ Streamlit query layer.",
    lifespan=lifespan,
)

# CORS — dev origins.  Lock down for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Response models ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    db_path: str
    db_exists: bool
    player_count: int
    tournament_count: int
    match_count: int
    server_time: str


class MetaResponse(BaseModel):
    api_version: str
    theme_default_day: str
    theme_default_night: str
    auto_theme_window: dict[str, int]
    provider: dict[str, Any]


# ── Routes: meta & health ───────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> HealthResponse:
    db_path = queries.db_path()
    counts = queries.table_counts()
    return HealthResponse(
        status="ok",
        db_path=str(db_path),
        db_exists=db_path.exists(),
        player_count=counts["players"],
        tournament_count=counts["tournaments"],
        match_count=counts["matches"],
        server_time=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/v1/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    return MetaResponse(
        api_version="v1",
        theme_default_day="Light - Sky Glass",
        theme_default_night="Dark - Petrol",
        auto_theme_window={"day_start_hour": 7, "day_end_hour_exclusive": 19},
        provider={
            "name": "odds-api.io",
            "sport": "darts",
            "request_budget_per_hour": 100,
            "batch_endpoint": "/odds/multi",
            "bookmakers": ["DraftKings", "Bet365"],
        },
    )


# ── Routes: players ─────────────────────────────────────────────────────────

@app.get("/api/v1/players")
def list_players() -> list[dict]:
    return queries.get_all_players()


@app.get("/api/v1/players/h2h")
def player_h2h(p1: int = Query(...), p2: int = Query(...)) -> dict:
    return queries.get_h2h(p1, p2)


@app.get("/api/v1/players/stats-batch")
def players_stats_batch(ids: str = Query(...)) -> list[dict]:
    try:
        player_ids = [int(x) for x in ids.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(422, "ids must be a comma-separated list of integers")
    return queries.get_players_stats_cache(player_ids)


@app.get("/api/v1/players/{player_id}")
def get_player(player_id: int) -> dict:
    player = queries.get_player_by_id(player_id)
    if not player:
        raise HTTPException(404, f"Player {player_id} not found")
    return player


@app.get("/api/v1/players/{player_id}/elo-history")
def player_elo_history(player_id: int) -> list[dict]:
    return queries.get_elo_history(player_id)


@app.get("/api/v1/players/{player_id}/matches")
def player_matches(player_id: int, limit: int = Query(30, ge=1, le=200)) -> list[dict]:
    return queries.get_player_match_history(player_id, limit=limit)


@app.get("/api/v1/players/{player_id}/stats")
def player_stats(player_id: int) -> dict:
    cache = queries.get_player_stats_cache(player_id)
    if not cache:
        raise HTTPException(404, f"No stats cache for player {player_id}")
    return cache


# ── Routes: matches ─────────────────────────────────────────────────────────

@app.get("/api/v1/matches")
def list_matches(
    upcoming: bool | None = Query(None),
    days: int | None = Query(None, ge=1, le=30),
    limit: int | None = Query(50, ge=1, le=500),
) -> list[dict]:
    if upcoming:
        return queries.get_upcoming_matches(days=days or 7)
    return queries.get_recent_results(limit=limit or 50)


@app.get("/api/v1/matches/{match_id}")
def get_match(match_id: int) -> dict:
    m = queries.get_match_by_id(match_id)
    if not m:
        raise HTTPException(404, f"Match {match_id} not found")
    return m


@app.get("/api/v1/matches/{match_id}/odds-history")
def match_odds_history(match_id: int) -> list[dict]:
    return queries.get_odds_history(match_id)


# ── Routes: tournaments ─────────────────────────────────────────────────────

@app.get("/api/v1/tournaments")
def list_tournaments() -> list[dict]:
    return queries.get_all_tournaments()


@app.get("/api/v1/tournaments/{tournament_id}")
def get_tournament(tournament_id: int) -> dict:
    t = queries.get_tournament_by_id(tournament_id)
    if not t:
        raise HTTPException(404, f"Tournament {tournament_id} not found")
    return t


@app.get("/api/v1/tournaments/{tournament_id}/results")
def tournament_results(tournament_id: int, limit: int = Query(100, ge=1, le=500)) -> list[dict]:
    return queries.get_tournament_results(tournament_id, limit=limit)


# ── Routes: odds / picks / steam ─────────────────────────────────────────────

@app.get("/api/v1/odds")
def current_odds() -> list[dict]:
    return queries.get_current_odds()


@app.get("/api/v1/picks")
def active_picks(min_edge: float = Query(0.0, ge=-50.0, le=50.0)) -> list[dict]:
    return queries.get_active_picks(min_edge=min_edge)


@app.get("/api/v1/steam")
def steam_events(hours: int = Query(24, ge=1, le=168)) -> list[dict]:
    return queries.get_recent_steam_events(hours=hours)


# ── Routes: model / analytics ────────────────────────────────────────────────

@app.get("/api/v1/model/record")
def model_record(days: int = Query(30, ge=1, le=365)) -> dict:
    return queries.get_model_record(days=days)


@app.get("/api/v1/model/elo-history")
def all_elo_history() -> list[dict]:
    """Bulk endpoint used by the Historical tab trajectory chart."""
    return queries.get_all_elo_history()


@app.get("/api/v1/analytics/yearly")
def yearly_stats() -> list[dict]:
    df = queries.get_yearly_stats()
    if df is None or df.empty:
        return []
    return df.to_dict(orient="records")


@app.get("/api/v1/analytics/era")
def era_performance() -> list[dict]:
    df = queries.get_era_performance()
    if df is None or df.empty:
        return []
    return df.to_dict(orient="records")


# ── Routes: client-portable calculators ─────────────────────────────────────
# These mirror models/props_model.py + models/elo.py 1:1 so the React client
# can hit them when needed.  Calculators also live as pure TypeScript modules
# in frontend/src/utils/calculators.ts so they can run client-side per the
# .md requirement.

class EdgeRequest(BaseModel):
    model_prob: float
    dk_odds: int


class EdgeResponse(BaseModel):
    model_prob: float
    dk_implied: float
    edge_pct: float
    expected_value: float
    grade: str


@app.post("/api/v1/calc/edge", response_model=EdgeResponse)
def calc_edge(req: EdgeRequest) -> EdgeResponse:
    return EdgeResponse(**client_math.calculate_edge(req.model_prob, req.dk_odds))


class EloProbRequest(BaseModel):
    elo_a: float
    elo_b: float


class EloProbResponse(BaseModel):
    prob_a: float
    prob_b: float
    fair_odds_a: int


@app.post("/api/v1/calc/elo-prob", response_model=EloProbResponse)
def calc_elo_prob(req: EloProbRequest) -> EloProbResponse:
    p_a = client_math.elo_win_probability(req.elo_a, req.elo_b)
    p_b = 1.0 - p_a
    return EloProbResponse(
        prob_a=round(p_a, 4),
        prob_b=round(p_b, 4),
        fair_odds_a=client_math.to_american_odds(p_a),
    )


class FormatAdjustRequest(BaseModel):
    base_prob: float
    legs_to_win: int
    sets_to_win: int | None = None


class FormatAdjustResponse(BaseModel):
    adjusted_prob: float


@app.post("/api/v1/calc/format-adjust", response_model=FormatAdjustResponse)
def calc_format_adjust(req: FormatAdjustRequest) -> FormatAdjustResponse:
    return FormatAdjustResponse(
        adjusted_prob=client_math.format_adjusted_probability(
            req.base_prob, req.legs_to_win, req.sets_to_win,
        ),
    )


class OneEightyRequest(BaseModel):
    avg_180s_per_leg: float
    legs_to_win: int
    line: float
    expected_legs: float | None = None


class OneEightyResponse(BaseModel):
    expected_180s: float
    prob_over: float
    prob_under: float


@app.post("/api/v1/calc/180s", response_model=OneEightyResponse)
def calc_180s(req: OneEightyRequest) -> OneEightyResponse:
    expected = client_math.expected_180s_in_match(
        req.avg_180s_per_leg, req.legs_to_win, req.expected_legs,
    )
    over = client_math.prob_180s_over(expected, req.line)
    return OneEightyResponse(
        expected_180s=round(expected, 3),
        prob_over=round(over, 4),
        prob_under=round(1.0 - over, 4),
    )


class ParlayLeg(BaseModel):
    prob: float
    odds: int


class ParlayRequest(BaseModel):
    legs: list[ParlayLeg]


class ParlayResponse(BaseModel):
    combined_model_prob: float
    combined_implied_prob: float
    combined_decimal_odds: float
    edge_pct: float
    ev_per_100: float


@app.post("/api/v1/calc/parlay", response_model=ParlayResponse)
def calc_parlay(req: ParlayRequest) -> ParlayResponse:
    out = client_math.parlay([{"prob": l.prob, "odds": l.odds} for l in req.legs])
    return ParlayResponse(**out)


# ── Routes: static legal copy (so React can render from API) ────────────────

@app.get("/api/v1/legal/footer")
def legal_footer() -> dict:
    return {
        "brand": "Betting Oracle",
        "url": "https://www.betting-oracle.com",
        "tagline": "Sports Prediction Analytics",
        "blurb": (
            "All content is for informational purposes only and does not "
            "constitute betting advice. Wager responsibly."
        ),
        "logo_url": "https://raw.githubusercontent.com/gmalbert/betting-oracle/main/data_files/logo.png",
        "rg_notice": (
            "21+ only. Gambling involves risk. "
            "If you or someone you know has a gambling problem, "
            "call 1-800-GAMBLER or visit ncpgambling.org."
        ),
        "affiliate_disclosure": (
            "BullzIQ may earn a commission from DraftKings through referral links. "
            "This does not affect our model's picks. Picks are generated independently."
        ),
        "model_disclaimer": (
            "Model picks are for informational purposes only and are not guaranteed. "
            "Past performance does not predict future results. Bet responsibly."
        ),
    }


# ── Error handler ───────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled(_request, exc):  # pragma: no cover — defensive
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": str(exc)},
    )
