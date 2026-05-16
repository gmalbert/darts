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
Streamlit page: pages/2_Players.py
Page title set via: st.set_page_config(page_title=f"{player_name} Darts Stats | Darts Analytics")
```

**Important SEO note**: Streamlit apps are rendered client-side (React), so Google's crawler may not index individual "pages" the same way it would a server-rendered site. Streamlit is best suited for a logged-in tool or a niche community that discovers the app via direct sharing. If organic Google search traffic is a primary goal, consider:

1. **Hybrid approach**: Use Streamlit for the interactive app, but also generate static HTML player/match summary pages (via `jinja2` + a static site generator or a simple Flask endpoint) that Google can crawl.
2. **Accept the trade-off**: Streamlit gives you faster time-to-launch and zero frontend code. SEO matters less in year 1 — build the product first, optimize distribution later.
3. **st.set_page_config**: Always set meaningful titles and use `st.markdown` to add structured content that _is_ crawlable in Googlebot's JavaScript rendering.

```python
# Standard page config on every page
st.set_page_config(
    page_title=f"{player['name']} Darts Stats | Darts Analytics",
    page_icon="🎯",
    layout="wide",
)
# Use st.write with real text so Googlebot's JS renderer can see content
st.title(f"{player['name']} — Career Stats & Betting Analysis")
st.write(
    f"{player['name']} career stats: {stats['career_avg']:.2f} 3-dart average, "
    f"{stats['checkout_pct']*100:.1f}% checkout rate, Elo {stats['elo']:.0f}. "
    f"Head-to-head record and DraftKings betting analysis."
)
```

### H2H Pages

```
Streamlit approach: a selectbox pair (Player 1 / Player 2) on pages/6_Tools.py
Not a separate URL per matchup — but the data is all there
```

For SEO-indexed H2H pages, generate static markdown or HTML files from the DB (see Hybrid Approach above).

### Sitemap / Robots

Streamlit Community Cloud automatically serves `robots.txt` allowing indexing.

For a hybrid static approach, generate a sitemap at build time:

```python
# scripts/generate_sitemap.py
from db.queries import get_all_players, get_tournaments
from datetime import date

BASE = "https://your-app.streamlit.app"

def generate_sitemap():
    players     = get_all_players()
    tournaments = get_tournaments(dk_covered_only=True)
    today       = date.today().isoformat()

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']

    for url, priority in [
        (BASE,                0.9),
        (f"{BASE}/Picks",     0.9),
        (f"{BASE}/Odds",      0.9),
        (f"{BASE}/Players",   0.8),
        (f"{BASE}/Tournaments", 0.8),
    ]:
        lines.append(f"  <url><loc>{url}</loc><lastmod>{today}</lastmod>"
                     f"<priority>{priority}</priority></url>")

    lines.append("</urlset>")
    with open("static/sitemap.xml", "w") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    generate_sitemap()
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

Every player section should surface:
- Their top 5 H2H matchups (links via selectbox or st.page_link)
- Tournaments they've won
- Recent match analysis

Every match center should link to:
- Both player profiles (st.page_link / st.button navigation)
- The tournament hub
- Similar recent matchups

```python
# Navigation helpers (Streamlit 1.36+)
import streamlit as st

def player_nav_links(player_slug: str, top_h2hs: list[dict]):
    st.subheader("Related")
    for opp in top_h2hs[:5]:
        st.page_link("pages/6_Tools.py",
                     label=f"H2H: {player_slug} vs {opp['slug']}",
                     icon="⚔️")
```