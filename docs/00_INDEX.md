# Darts Betting Analytics Site — Roadmap Index

A comprehensive build guide for a darts betting analytics and stats site focused on DraftKings-covered tournaments.

## Files in This Roadmap

| File | Contents |
|------|----------|
| `01_data_sources.md` | Where to get data, how to fetch/scrape it, schema design |
| `02_models.md` | Predictive models, feature engineering, betting edge calculations |
| `03_features.md` | Site features, pages, tools, and user flows |
| `04_design.md` | Visual design system, components, UI patterns |
| `05_tech_stack.md` | Full stack architecture, infra, deployment |
| `06_roadmap_near_term.md` | MVP — first 90 days, what to ship first |
| `07_roadmap_far_term.md` | 6–24 months, monetization, scale, expansion |
| `08_seo_and_content.md` | Content strategy, SEO, programmatic pages |
| `09_legal_and_compliance.md` | Affiliate compliance, responsible gambling, disclaimers |
| `10_overlooked.md` | Things most people miss — odds movement, steam tracking, community |

## Target DraftKings Tournaments (Priority Order)

These are the PDC/darts events DraftKings actively books — build data pipelines and content around these first:

1. **PDC World Championship** (Dec–Jan) — biggest event, most betting volume
2. **Premier League Darts** (Feb–May) — 16-week league format, weekly matches, best for in-season modeling
3. **World Matchplay** (July)
4. **Grand Slam of Darts** (Nov)
5. **World Series of Darts** (multiple legs, Apr–Oct) — international events
6. **European Tour** (multiple legs) — DK has shown several legs
7. **UK Open** (Mar)
8. **World Grand Prix** (Oct)
9. **Players Championship Finals** (Nov)

## Quick Start

```bash
git clone <your-repo>
cd darts-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m scrapers.dartsdatabase seed --start-year 2000  # seed historical data
streamlit run app.py
```
