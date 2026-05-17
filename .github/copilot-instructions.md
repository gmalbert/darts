# Copilot Instructions for BullzIQ

## Project Context
- Stack: Python, Streamlit, SQLAlchemy, SQLite.
- App entrypoint: `predictions.py`.
- Data model: ORM in `db/schema.py`, query layer in `db/queries.py`.
- Seeding pipeline: `db/seed_real.py` (real data) and `db/seed.py` (startup guard).
- Odds ingestion: `scrapers/odds_api.py` using odds-api.io.

## Non-Negotiable Rules
- Real-data-first: do not add or re-enable automatic demo fallback behavior.
- Never commit secrets (`.env`, tokens, API keys).
- Preserve existing public function signatures unless explicitly asked to break them.
- Keep edits minimal and scoped to the user request.
- Do not introduce destructive git commands in scripts or docs.

## Odds/API Constraints
- Active odds provider: odds-api.io (`ODDS_API_IO_KEY`).
- Current hard limit: 100 requests/hour.
- Prefer cached event fetches and avoid duplicate pagination.
- Avoid per-event loops unless necessary; if needed, filter to near-term fixtures first.
- If no lines are available, show user-facing copy indicating markets are not open yet.

## UI/Streamlit Conventions
- Theme is automatic by browser local time:
  - Day: `Light - Sky Glass`
  - Night: `Dark - Petrol`
- Do not reintroduce a theme dropdown unless user asks.
- Use `themed_dataframe(...)` from `components/styles.py` for tabular data.
- For charts, use `chart_style(...)` tokens instead of hard-coded dark colors.
- Use explicit fallbacks for nullable fields (`round`, odds, averages) to avoid showing `None`.

## Data Safety and Robustness
- Guard all numeric formatting against `None`/NaN.
- Use `pd.to_numeric(..., errors="coerce")` where data quality is uncertain.
- Keep `OddsSnapshot` writes conditional on actual odds availability.
- Do not assume sportsbook lines exist for all upcoming fixtures.

## Validation Before Finishing
- Run a focused error check on modified files.
- If data flow is touched, run a lightweight runtime sanity command when practical.
- Keep output/user copy accurate (avoid suggesting actions already automatic).

## GitHub/Repo Hygiene
- Track `data_files/bullziq.db` and `data_files/db_is_real.flag` as configured.
- Do not add virtualenv contents (`venv/`, `.venv/`) to Git.
- If a file could grow large, assess GitHub size limits and recommend LFS only when needed.
