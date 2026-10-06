# Backend enhancements — 16 implementation briefs

The preferred near-term design is **immutable SQLite releases**, with an explicit Actions-to-Render publication path and no provider secrets on Render. PostgreSQL can become useful for authenticated user writes later; it is not required to fix current serving and pipeline correctness.

Serving and ingestion must use different database factories. Do not change the shared ORM's global engine to read-only without giving offline jobs a writable engine. SQL examples describe proposed schema additions and must be applied by versioned migrations on Actions.

## B01 — Truly read-only serving and readiness

**Priority: P0 · Effort: M · Target:** backend lifespan, database configuration. **Depends on:** B02.

Replace ensure_seeded at API startup with read-only schema/manifest checks. An invalid or missing serving artifact makes readiness fail; it must not create tables, scrape, compute Elo or train. Keep liveness distinct from readiness.

~~~python
import sqlite3
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def serving_sessions(path: Path):
    resolved = path.resolve(strict=True)
    def connect():
        conn = sqlite3.connect(resolved.as_uri() + "?mode=ro",
                               uri=True, check_same_thread=False)
        conn.execute("PRAGMA query_only=ON")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    engine = create_engine("sqlite://", creator=connect)
    with engine.connect() as conn:
        version = conn.exec_driver_sql("PRAGMA user_version").scalar()
        if version != 2:  # Proposed release schema; migration required.
            raise RuntimeError("Unsupported serving snapshot schema")
    return sessionmaker(bind=engine, expire_on_commit=False)
~~~

Integration sketch: use this factory in backend/api/queries, while Actions retains a separate write-capable factory. Do not run the hypothetical schema-v2 check against today's database without migration.

**Done when:** an attempted insert fails on Render, empty artifacts fail readiness clearly, and startup makes no network or data-generation calls. Related pattern: [FastAPI's official full-stack template](https://github.com/fastapi/full-stack-fastapi-template); use only the relevant configuration structure.

## B02 — Validated immutable snapshots and explicit hosted publication

**Priority: P0 · Effort: L · Target:** overnight workflow and deployment build. **Depends on:** B08, B13.

Package the database, forecast export and metadata into one immutable release. Publish only after validation. Build the Render release against an exact snapshot/version; do not expect a Git commit to update a persistent disk automatically. Roll back by deploying the previous validated release.

~~~python
import hashlib
import json
import sqlite3
from pathlib import Path

from contextlib import closing

def stage_database(source: Path, output_dir: Path):
    # Actions only. Caller supplies a new, empty staging directory.
    output_dir.mkdir(parents=True, exist_ok=False)
    candidate = output_dir / "bullziq.db"
    with closing(sqlite3.connect(
            source.resolve().as_uri() + "?mode=ro", uri=True)) as src:
        with closing(sqlite3.connect(candidate)) as dst:
            src.backup(dst)
            if dst.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Invalid database candidate")
            if dst.execute("PRAGMA foreign_key_check").fetchall():
                raise ValueError("Invalid foreign keys")
            schema_version = dst.execute("PRAGMA user_version").fetchone()[0]
            if schema_version != 2:
                raise ValueError("Candidate is not migrated to serving schema v2")
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    manifest = {"schema_version": schema_version, "database_sha256": digest}
    (output_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest
~~~

This standard-library packaging kernel uses the [SQLite backup API](https://www.sqlite.org/backup.html), not a copy of a database with uncheckpointed writes. It requires the proposed schema-v2 migration. Add source timestamps, run/commit IDs, counts, forecast checksum and B08 semantic gates before publishing.

**Concrete handoff:** Actions builds/validates the candidate, commits the tracked DB/export/manifest together with a detailed Markdown commit description, and publishes the versioned release artifact. Configure the Render deployment build to consume that exact revision/artifact and bake its read-only database into the service release. Readiness verifies hashes. Keep at least the prior two valid releases. Do not hot-swap a file under pooled SQLite connections.

**Done when:** a deliberately failed candidate leaves the hosted snapshot/version unchanged; two hosted endpoints report the same manifest; rollback works. The report does not configure or trigger deployment.

## B03 — One canonical forecast ledger for the site and Grid export

**Priority: P0 · Effort: L · Target:** Pick replacement/extension, export script, offline prediction stage. **Depends on:** B05, B06, M01.

Generate and freeze forecasts for all eligible matches on Actions, even when no edge policy selects them. The website and Sports Picks Grid must read the same ledger rather than independently recomputing Elo estimates.

~~~sql
CREATE TABLE forecasts (
  forecast_id TEXT PRIMARY KEY,
  match_key TEXT NOT NULL,
  selection_id TEXT NOT NULL,
  model_version TEXT NOT NULL,
  feature_batch_id TEXT NOT NULL,
  quote_id TEXT,
  batch_id TEXT NOT NULL,
  origin TEXT NOT NULL CHECK (origin IN ('prospective', 'backtest')),
  frozen_at TEXT NOT NULL,
  match_start TEXT NOT NULL,
  probability REAL NOT NULL CHECK (probability BETWEEN 0 AND 1),
  selection_policy TEXT,
  UNIQUE(match_key, selection_id, model_version, batch_id)
);
~~~

~~~python
def persist_forecasts(conn, rows):
    # Actions write connection. All timestamps are normalized UTC strings.
    for row in rows:
        if row["frozen_at"] >= row["match_start"]:
            raise ValueError("Forecast was not frozen before start")
        conn.execute("""
          INSERT INTO forecasts VALUES
          (:forecast_id,:match_key,:selection_id,:model_version,:feature_batch_id,
           :quote_id,:batch_id,:origin,:frozen_at,:match_start,:probability,
           :selection_policy)
          ON CONFLICT(forecast_id) DO NOTHING
        """, row)
~~~

Add foreign keys to canonical match/player/quote tables during migration. Require deterministic IDs and input-hash agreement on retry; a conflict with different inputs should fail, not silently overwrite. The function is transaction-scoped by its caller.

**Done when:** /picks and best_bets_today.json contain the same selected forecast IDs, unselected forecasts remain evaluable, and selected prices/probabilities cannot be edited after publication.

## B04 — Idempotent settlement with a correction journal

**Priority: P0 · Effort: M · Target:** Actions results stage, metric exports. **Depends on:** B03, B05.

Resolve winner, loss, void, push and postponed states explicitly. Store result revisions separately from immutable predictions. An unknown winner is pending/unknown, not a loss.

~~~python
def settle_moneyline(selection_id, winner_id, status, decimal_odds, stake=1.0):
    if stake <= 0 or decimal_odds <= 1:
        raise ValueError("Invalid stake or price")
    if status in ("cancelled", "void"):
        return {"result": "void", "net_profit": 0.0}
    if status != "completed" or winner_id is None:
        return {"result": "pending", "net_profit": None}
    won = selection_id == winner_id
    return {"result": "win" if won else "loss",
            "net_profit": stake * (decimal_odds - 1) if won else -stake}
~~~

~~~sql
CREATE TABLE settlements (
  forecast_id TEXT NOT NULL REFERENCES forecasts(forecast_id),
  result_revision TEXT NOT NULL,
  result TEXT NOT NULL,
  settled_at TEXT NOT NULL,
  net_profit REAL,
  PRIMARY KEY (forecast_id, result_revision)
);
~~~

Validate the winner against match participants before settlement. An Actions transaction inserts a deterministic result_revision once; corrected results add a revision. Metrics select the latest valid revision rather than summing all revisions.

**Done when:** retrying a run leaves row counts/profit unchanged, a correction remains auditable, and -150 wins settle to +0.6667 units per unit stake.

## B05 — Canonical player, fixture and market identities

**Priority: P0 · Effort: L · Target:** ingestion adapters, schema, shared IDs. **Depends on:** source identifiers.

Replace substring name matching with a registry of provider IDs and reviewed aliases. Quarantine ambiguous names. The current raw PDC event_id is a tournament ID, not a unique match ID; do not treat it as a fixture identifier.

~~~python
import unicodedata

def normalized_name(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())

def resolve_player(source, source_id, name, registry, aliases):
    if source_id is not None:
        canonical = registry.get((source, str(source_id)))
        if canonical:
            return canonical
    candidates = aliases.get((source, normalized_name(name)), [])
    if len(candidates) == 1:
        return candidates[0]
    raise ValueError("Unresolved or ambiguous player identity")
~~~

Use reviewed canonical UUIDs or persistent registry IDs; derive match identity from a real source fixture ID when available, otherwise a reviewed composite of edition/round/participants/occurrence. Names alone and mutable scores/times cannot safely define identity. Store participant orientation for each source so odds cannot be reversed accidentally.

**Done when:** aliases such as name-order variants resolve consistently, repeated meetings remain separate, and a rebuild preserves public match links and forecast foreign keys.

## B06 — Measured data provenance and event-specific format rules

**Priority: P0 · Effort: L · Target:** seed metadata, Match constructor, rule registry. **Depends on:** verified source metadata.

Persist rule versions per tournament edition and round: legs/sets target, double-in, win-by-two, deciding-leg policy, throw-order policy. Preserve date precision. Remove hard-coded averages from measured fields; unverified priors belong in a separate annotated table.

~~~python
def import_match_metadata(row, rule_registry):
    key = (row["edition_key"], row["round_key"])
    rule = rule_registry.get(key)
    return {
        "match_key": row["match_key"],
        "date_precision": row.get("date_precision", "unknown"),
        "legs_to_win": rule["legs_to_win"] if rule else None,
        "sets_to_win": rule.get("sets_to_win") if rule else None,
        "double_in": rule.get("double_in") if rule else None,
        "format_verified": bool(rule),
        "format_source": rule.get("source_url") if rule else None,
        "avg_p1": row.get("measured_avg_p1"),
        "avg_p2": row.get("measured_avg_p2"),
    }
~~~

Current scraping assigns tournament startDate to every fixture and emits no match averages. Add source-specific precision flags rather than pretending those timestamps are actual match starts. Migrate legs_to_win to nullable until verified.

**Done when:** format fields are sourced rather than universal defaults, prize/book metadata includes edition/source, and current player measurements cannot be confused with priors.

## B07 — Temporal query guards and valid-outcome semantics

**Priority: P0 · Effort: M · Target:** both query layers. **Depends on:** B06.

Apply a UTC lower bound to upcoming matches and cached odds. Filter active picks by pending result, actual match state and future start. Unknown H2H results must not award either player a win.

~~~python
from datetime import datetime, timedelta, timezone

def upcoming_window(days):
    # Legacy ORM stores naive UTC; convert only at this boundary.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    return now, now + timedelta(days=days)

def h2h_counts(matches, player1_id, player2_id):
    return {
        "p1_wins": sum(m.winner_id == player1_id for m in matches),
        "p2_wins": sum(m.winner_id == player2_id for m in matches),
        "unresolved": sum(m.winner_id not in (player1_id, player2_id) for m in matches),
    }
~~~

~~~sql
SELECT * FROM matches
WHERE is_upcoming = 1 AND winner_id IS NULL
  AND match_date >= :now_utc AND match_date < :cutoff_utc
ORDER BY match_date, id;
~~~

Parameterize SQL or equivalent SQLAlchemy conditions. Handle date-only/provisional starts under an explicit separate fixture status rather than fabricating an instant.

**Done when:** July matches cannot appear as October upcoming fixtures, missing winners are counted separately, and stale prices cannot qualify an expired pick.

## B08 — Semantic quality gates before publication

**Priority: P0 · Effort: M · Target:** Actions validation. **Depends on:** B05, B06.

Replace “DB exists / count above ten” with field-level checks, coverage accounting and quarantine. Separate “source succeeded but no markets” from provider failure. A partial collection must record which books/events are missing.

~~~python
import math

def validate_forecast(row):
    p = row["probability"]
    errors = []
    if not isinstance(p, (int, float)) or not math.isfinite(p) or not 0 <= p <= 1:
        errors.append("invalid_probability")
    if row["feature_available_at"] > row["frozen_at"]:
        errors.append("future_feature")
    if row["frozen_at"] >= row["match_start"]:
        errors.append("post_start_prediction")
    if row.get("quote_time") and row["quote_time"] > row["frozen_at"]:
        errors.append("future_quote")
    if row["player1_id"] == row["player2_id"]:
        errors.append("same_player")
    return errors
~~~

Pure row validator; caller normalizes datetime types and rejects malformed fields before this check. Add price validity, format completeness, referential integrity, duplicate-market keys, expected coverage and hash checks. Quarantine only affects candidate publication, never mutates the last valid serving artifact.

**Done when:** injected semantic failures fail the build, missing-coverage rates are reported, and expected no-market runs publish an honest status. Inspiration: [Pandera](https://github.com/unionai-oss/pandera) for dataset contracts; adopt it if batch complexity warrants a new dependency.

## B09 — One bounded player-stats request, not 813

**Priority: P1 · Effort: M · Target:** PlayersPage, players API, nightly stats stage. **Depends on:** B14, B15.

Build measured stats offline, then return a paged joined response. Missing stats are nullable fields in a valid row, not 404s that reject the entire batch.

~~~sql
SELECT p.id, p.name, p.elo,
       c.win_rate_last20, c.avg_3dart_last10, c.updated_at
FROM players p
LEFT JOIN player_stats_cache c ON c.player_id = p.id
ORDER BY p.elo DESC, p.id
LIMIT :limit OFFSET :offset;
~~~

~~~typescript
type PlayerPage = { items: unknown[]; total: number };
export async function loadPlayerPage(base: string, page: number, signal?: AbortSignal) {
  const response = await fetch(base + "/players?limit=50&offset=" + page * 50,
    { signal });
  if (!response.ok) throw new Error("Player research data is unavailable");
  return response.json() as Promise<PlayerPage>;
}
~~~

Replace the existing collection route contract deliberately, generate types, and remove the page's all-player Promise.all. Limit and offset require validation; sorting/search should be part of the saved-data query.

**Done when:** first rankings render uses one paged query, absent stats are visibly unmeasured, and a profile fetches only its selected player's history.

## B10 — Explicit API contracts, units, timestamps and calculator inputs

**Priority: P1 · Effort: M · Target:** FastAPI schemas, frontend types, calculator mirrors. **Depends on:** none.

Validate finite 0–1 probabilities, meaningful moneylines, positive race lengths, nonnegative rates and bounded parlay size. Serialize UTC offsets explicitly. Generate client types from OpenAPI so camel/snake-case and nullable fields cannot drift silently.

~~~python
from pydantic import BaseModel, Field, field_validator

class EdgeRequestV2(BaseModel):
    model_probability: float = Field(ge=0, le=1, allow_inf_nan=False)
    american_odds: int

    @field_validator("american_odds")
    @classmethod
    def conventional_moneyline(cls, value):
        if abs(value) < 100:
            raise ValueError("Use conventional American odds: <= -100 or >= 100")
        return value

class PerformanceResponseV2(BaseModel):
    status: str
    settled_n: int = Field(ge=0)
    win_rate: float | None = None
    roi_pct: float | None = None
    brier: float | None = None
    snapshot_at: str | None = None
~~~

Version the response migration and update UI formatters together. Strict American validation is a product convention; preserve original decimal provider prices to avoid rounding information loss.

**Done when:** invalid math inputs return 422, null is distinct from zero, every instant includes timezone, and UI assumptions match the validated response.

## B11 — Snapshot-based caching and lazy research loads

**Priority: P1 · Effort: M · Target:** headers, client query cache, HomePage. **Depends on:** B02.

Cache saved responses by immutable snapshot version. Disable automatic focus/reconnect refetches, timers and retries. Load heavy research data only when its view is opened. Keep all requests as read-only artifact access.

~~~tsx
import { useQuery } from "@tanstack/react-query";
export function useSnapshotPlayers(base: string, snapshotId: string) {
  return useQuery({
    queryKey: ["players", snapshotId],
    queryFn: async ({ signal }) => {
      const response = await fetch(base + "/snapshots/" + encodeURIComponent(snapshotId)
        + "/players", { signal });
      if (!response.ok) throw new Error("Saved player snapshot unavailable");
      return response.json();
    },
    staleTime: Infinity,
    refetchInterval: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
    retry: false,
  });
}
~~~

Proposed dependency and versioned endpoint; install/configure QueryClient only during implementation. For HTTP, use a dataset-hash ETag and immutable caching for versioned public routes; mutable manifest routes should revalidate on explicit page load. Do not serve personalized data through public caches.

**Done when:** tab visits reuse saved data, hidden home research panels do not load bulk histories, and leaving the browser open triggers no scheduled requests. Check [TanStack Query defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults), which must be overridden for this architecture.

## B12 — Production origin configuration and safe API errors

**Priority: P0 · Effort: M · Target:** API client, CORS, health/errors. **Depends on:** deployment hostname decision.

Replace loopback with an environment-supplied HTTPS base or a same-origin proxy. Configure explicit allowed frontend origins. Keep database paths and raw exceptions out of public responses; correlate failures through a request ID and server logs.

~~~typescript
export function apiBase(): string {
  const configured = import.meta.env.VITE_API_BASE_URL;
  const base = configured || "/api/v1";
  if (import.meta.env.PROD && base.startsWith("http://"))
    throw new Error("Production API must use HTTPS or a same-origin path");
  return base.replace(/\/$/, "");
}
~~~

~~~python
import logging
import uuid
from fastapi.responses import JSONResponse

async def public_error(request, exc):
    request_id = str(uuid.uuid4())
    logging.getLogger("bullziq.api").error(
        "Unhandled request id=%s path=%s", request_id, request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__))
    return JSONResponse(status_code=500,
        content={"error": "internal_error", "request_id": request_id})
~~~

Sanitize logs that can contain provider query-string credentials; this handler belongs to the serving process, which has no provider key. Use a private operational health view for detailed counts/paths if necessary.

**Done when:** a Cloudflare staging origin can read Render, HTTPS pages make no loopback/mixed-content requests, and public failures reveal no raw path or secret.

## B13 — Reproducible CI and isolated credential scope

**Priority: P0 · Effort: M · Target:** verify/seed/overnight workflows, dependency files. **Depends on:** none.

Separate runtime dependencies from test and ingestion dependencies. The current verify workflow runs pytest without declaring it in requirements.txt. Restrict provider credentials and refresh permission to the dedicated overnight ingestion step; remove provider credentials from the historical seed/export workflow.

~~~yaml
# Fragment to merge into both database-writing workflows.
concurrency:
  group: bullziq-snapshot-publication
  cancel-in-progress: false

# Verification step; requirements-dev.txt should pin pytest and test clients.
# Other workflow fields are intentionally omitted from this fragment.
steps:
  - uses: actions/setup-python@v5
    with:
      python-version: "3.11"
      cache: pip
  - name: Install verification dependencies
    run: pip install -r requirements.txt -r requirements-dev.txt
  - name: Verify code and policy
    run: python -m pytest -q
~~~

Shared concurrency stops overlap but does not establish correct job order or prevent a stale checkout; B14 addresses sequencing. Pin tested dependency versions and Actions SHAs during implementation; tags here match the existing setup pattern and are not claims of latest versions.

**Done when:** fresh CI passes from a clean install, verification has no provider key, only the overnight collection step has credentials, and publication has Markdown commit descriptions. Add semantic UI assertions; screenshot equality alone misses blank panels.

## B14 — Incremental imports that preserve odds and forecast history

**Priority: P0 · Effort: L · Target:** seed_real, schema migrations, workflow dependencies. **Depends on:** B05.

Stop drop_all in incremental refreshes. Upsert source results in staging, rebuild derived ratings on Actions, and preserve odds/forecasts/settlement journals. Sequence historical import before odds/forecast publication using a shared pipeline dependency; if separate workflows remain, publication must verify the input revision and not overwrite a newer release.

~~~sql
CREATE TABLE canonical_results (
  match_key TEXT PRIMARY KEY,
  player1_id TEXT NOT NULL,
  player2_id TEXT NOT NULL,
  winner_id TEXT,
  source_revision TEXT NOT NULL,
  available_at TEXT NOT NULL
);

INSERT INTO canonical_results
  (match_key,player1_id,player2_id,winner_id,source_revision,available_at)
VALUES
  (:match_key,:player1_id,:player2_id,:winner_id,:source_revision,:available_at)
ON CONFLICT(match_key) DO UPDATE SET
  winner_id=excluded.winner_id,
  source_revision=excluded.source_revision,
  available_at=excluded.available_at;
~~~

Use a separate append-only result-revisions table from B15 before updating this current projection. Preserve original participant orientation; changed participants need a reviewed correction, not this automatic upsert. Full rebuilds operate on a candidate derived dataset, not by deleting the durable forecast journal.

**Done when:** an incremental source refresh leaves historical quote/forecast counts intact, repeated imports are idempotent, corrections replay ratings offline, and two jobs cannot publish a mixed revision.

## B15 — Event time, availability time and source lineage

**Priority: P1 · Effort: L · Target:** raw ingestion and feature snapshots. **Depends on:** B05.

Store when an event happened, when the source published it if known, and when BullzIQ first observed it. Availability time is the conservative “could the model have known?” boundary. A current scrape of a 2018 result does not prove it was available in its present form in 2018.

~~~sql
CREATE TABLE source_observations (
  observation_id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  source_entity_key TEXT NOT NULL,
  event_time TEXT,
  source_published_at TEXT,
  observed_at TEXT NOT NULL,
  available_at TEXT NOT NULL,
  payload_sha256 TEXT NOT NULL,
  source_url TEXT,
  precision TEXT NOT NULL,
  batch_id TEXT NOT NULL,
  UNIQUE(source, source_entity_key, payload_sha256)
);
CREATE INDEX observation_lookup
ON source_observations(source, source_entity_key, available_at);
~~~

Normalize UTC timestamp representation before lexical comparisons. Preserve source payloads where rights permit; the serving snapshot only needs derived lineage and hashes.

**Done when:** every forecast feature traces to observations available by cutoff, late corrections are visible, and reconstructed backtests disclose missing historical availability evidence.

## B16 — Publication observability and lightweight model registry

**Priority: P1 · Effort: M · Target:** Actions artifacts, /meta, operations. **Depends on:** B02, B03.

Track run duration, collected coverage, rejected rows, forecast count, publication version and model input hashes. A registry can initially be JSON artifacts; there is no need to host a permanent training/monitoring worker on Render.

~~~python
import hashlib
import json

def model_manifest(model_bytes, feature_names, training_cutoff, metrics, commit):
    feature_json = json.dumps(feature_names, separators=(",", ":")).encode()
    return {
        "artifact_sha256": hashlib.sha256(model_bytes).hexdigest(),
        "features_sha256": hashlib.sha256(feature_json).hexdigest(),
        "training_cutoff": training_cutoff,
        "validation_metrics": metrics,
        "source_commit": commit,
        "serving_mode": "precomputed_forecasts",
    }
~~~

Record drift and calibration summaries offline by cohort. Serve last-success and last-attempt status from saved metadata; use Actions job failures/alerts for operational attention, without installing a continuous data worker.

**Done when:** an operator can explain a missing snapshot from a saved run report, reproduce a forecast's inputs/model version, and reject an artifact with a mismatched hash. Inspiration: [MLflow](https://github.com/mlflow/mlflow); adopt its registry only if JSON becomes inadequate.
