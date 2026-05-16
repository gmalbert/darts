# 10 — Things Most People Miss

## 1. Odds Movement & Steam Tracking

Line movement tells you more than the current odds alone. When sharp money hits a line, DraftKings moves it fast. Tracking that movement and flagging it is a high-value, low-competition feature.

```python
# jobs/steam_detector.py

STEAM_THRESHOLD_PCT = 3.0  # flag if line moves >3 percentage points implied prob
STEAM_WINDOW_MINUTES = 30

async def detect_steam_moves(match_id: int) -> list[dict]:
    """
    Look at last 30 minutes of odds snapshots.
    Flag if implied probability shifted significantly.
    """
    recent = await get_odds_snapshots(match_id, minutes=STEAM_WINDOW_MINUTES)
    if len(recent) < 2:
        return []

    steam_alerts = []
    first = recent[0]
    latest = recent[-1]

    p1_shift = (latest.p1_implied - first.p1_implied) * 100

    if abs(p1_shift) >= STEAM_THRESHOLD_PCT:
        direction = first.player1 if p1_shift > 0 else first.player2
        steam_alerts.append({
            "match_id": match_id,
            "player_steamed": direction,
            "shift_pct": round(p1_shift, 2),
            "opening_implied": round(first.p1_implied * 100, 1),
            "current_implied": round(latest.p1_implied * 100, 1),
            "opening_odds": first.p1_odds,
            "current_odds": latest.p1_odds,
            "detected_at": latest.snapshot_time.isoformat(),
        })

    return steam_alerts


# Store steam events for display and alerts
async def persist_steam_event(alert: dict):
    await db.execute("""
        INSERT INTO steam_events (match_id, player_steamed, shift_pct, opening_odds, 
                                  current_odds, detected_at)
        VALUES (:match_id, :player_steamed, :shift_pct, :opening_odds, 
                :current_odds, :detected_at)
    """, alert)
```

**Why it matters**: When a sharp bettor hits a line and DraftKings moves it, they're pricing in new information. You can use steam moves as a signal *alongside* your model — a steam move in the same direction as your model pick increases confidence.

---

## 2. Edge Decay — Your Picks Have a Shelf Life

The edge in a pick disappears as the market adjusts. A 4% edge at posting might be 0% by event time.

```python
# Track edge decay for every pick
async def track_edge_over_time(match_id: int, initial_pick: dict):
    """
    Re-calculate edge every 15 minutes as odds update.
    Store history so users can see if they missed the best line.
    """
    history = []
    snapshots = await get_odds_snapshots(match_id)

    for snap in snapshots:
        current_edge = calculate_edge(initial_pick['our_prob'], snap.p1_odds)
        history.append({
            "time": snap.snapshot_time,
            "odds": snap.p1_odds,
            "edge_pct": current_edge['edge_pct'],
        })

    return history

# Display: "Best odds were +140 (4.2% edge) at 2:15pm. Current odds +125 (1.1% edge)."
```

---

## 3. Home / Away Doesn't Apply — But Crowd Does

There's no home/away in individual darts, but venue and crowd effects are real and measurable, especially in the Premier League.

```python
# Feature: crowd_advantage_score
# Premier League visits 15+ cities. Some players have strong local followings.

PLAYER_CROWD_CITIES = {
    "Luke Littler":     ["Manchester", "Liverpool"],
    "Gerwyn Price":     ["Cardiff", "Exeter"],
    "Gary Anderson":    ["Aberdeen", "Edinburgh"],
    "Peter Wright":     ["Edinburgh"],
    "Jonny Clayton":    ["Cardiff"],
    "Simon Whitlock":   [],  # Australian, no UK home crowd advantage
    "Damon Heta":       [],  # Australian
}

def crowd_advantage_feature(player: str, venue_city: str) -> float:
    """Returns 0.0 to 1.0, where 1.0 = strong home crowd advantage."""
    home_cities = PLAYER_CROWD_CITIES.get(player, [])
    return 1.0 if venue_city in home_cities else 0.0

# In your feature matrix, add:
# crowd_p1 - crowd_p2 as a feature
```

---

## 4. Format Variance & Upset Probability

The PDC uses different formats for different tournaments. This is *massively* underappreciated in mainstream betting coverage.

```python
# The key insight: shorter formats (fewer legs) = more variance = better for underdogs

FORMAT_VARIANCE_TABLE = {
    # (legs_to_win, sets_to_win): expected_upset_rate_vs_random
    # An "upset" here means lower-ranked player wins
    (6, None):  0.33,  # Best of 11 legs — typical night match
    (7, None):  0.30,
    (3, 5):     0.36,  # Worlds early rounds (best of 5 sets, 3 legs per set)
    (3, 7):     0.28,  # Worlds later rounds (more sets = less variance)
    (6, None):  0.31,
    (7, 6):     0.25,  # Worlds final (best of 13 sets)
}

def format_adjusted_probability(
    base_prob: float,  # model's base probability for stronger player
    legs_to_win: int,
    sets_to_win: int | None,
) -> float:
    """
    Adjust win probability for format length.
    Short formats compress win probabilities toward 50%.
    Long formats amplify the skill gap.
    """
    if sets_to_win:
        total_sets = sets_to_win * 2 - 1
        # More legs = more regression toward true skill
        # Rough approximation using binomial variance
        skill_signal = (base_prob - 0.5) * (1 + total_sets / 20)
        return max(0.02, min(0.98, 0.5 + skill_signal))
    else:
        legs = legs_to_win * 2 - 1
        skill_signal = (base_prob - 0.5) * (1 + legs / 25)
        return max(0.02, min(0.98, 0.5 + skill_signal))
```

**Content angle**: Write a piece explaining why the World Championship's sets format makes early-round upsets more common than you'd expect. This is counterintuitive and shareable.

---

## 5. Seasonal Fatigue & Travel

The PDC calendar is relentless — 30+ events per year. Players traveling to World Series legs in Australia, New Zealand, and Japan show measurable performance dips.

```python
# Feature: days_since_last_event, travel_distance_km
import math

def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Straight-line distance between two coordinates."""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

VENUE_COORDS = {
    "alexandra_palace": (51.5935, -0.1295),
    "sydney": (-33.8688, 151.2093),
    "melbourne": (-37.8136, 144.9631),
    "auckland": (-36.8509, 174.7645),
    "amsterdam": (52.3676, 4.9041),
    "dortmund": (51.5136, 7.4653),
}

def travel_fatigue_feature(player_home_city: str, last_venue: str, current_venue: str) -> float:
    """
    Returns a 0–1 fatigue score based on travel since last event.
    1.0 = maximum expected fatigue (e.g. UK player just flew from Sydney).
    """
    coords_last = VENUE_COORDS.get(last_venue)
    coords_current = VENUE_COORDS.get(current_venue)
    if not coords_last or not coords_current:
        return 0.0

    dist_km = haversine_km(*coords_last, *coords_current)
    # Scale: 0km = 0 fatigue, 20,000km = 1.0 fatigue
    return min(1.0, dist_km / 20000)
```

---

## 6. The "Oche" Effect — In-Person vs TV-Only Events

Some smaller events are not broadcast live and have no crowd. Players perform differently. Track this.

```python
TV_EVENTS = {
    "world_championship", "premier_league", "world_matchplay",
    "grand_slam", "uk_open", "world_grand_prix",
    "players_championship_finals", "world_series_finals",
}

def is_tv_event(tournament_slug: str) -> bool:
    return tournament_slug in TV_EVENTS

# Add is_tv as a binary feature in your match predictor.
# Some players consistently overperform on TV (crowd energy, adrenaline).
# Others underperform (nerves).
```

---

## 7. The Recency Trap in Darts

Unlike team sports, individual darts performance can shift dramatically in days. Phil Taylor at 57 is not Phil Taylor at 40. Your model needs smart time-weighting.

```python
def time_weighted_average(
    values: list[tuple[str, float]],  # (date_str, value)
    half_life_days: int = 180,  # performance halves in weight every 6 months
) -> float:
    """
    Exponentially weighted average where recent matches count more.
    """
    from datetime import datetime
    import math

    today = datetime.today()
    total_weight = 0.0
    weighted_sum = 0.0

    for date_str, value in values:
        date = datetime.strptime(date_str, "%Y-%m-%d")
        days_ago = (today - date).days
        weight = math.exp(-days_ago * math.log(2) / half_life_days)
        weighted_sum += value * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else 0.0

# Use this for 3-dart averages, checkout %, etc.
# Don't use simple 20-match rolling average — career form changes.
```

---

## 8. Competitor Intelligence

Sites to watch and learn from. Not darts-specific but analogs in adjacent niches:

| Site | What to Learn |
|------|---------------|
| covers.com | Layout for match center pages, historical results |
| FiveThirtyEight (archived) | Model presentation, confidence display |
| Betsperts | Affiliate strategy, edge display |
| Action Network | Email list tactics, picks formatting |
| Bet On Lacrosse (your future competitor) | Niche sports site that works |

Key differentiator from all of them: **show your math**. Display Brier scores, calibration curves, and backtest accuracy. Sharp bettors want to evaluate your model, not just your picks. Transparency is a moat.

---

## 9. Google Core Update Risk

Sports betting and gambling content is a "Your Money, Your Life" (YMYL) category. Google applies extra scrutiny. Mitigations:

- Clear author bylines with real credentials
- Regular content updates (stale darts stats hurt rankings)
- No thin pages — every player profile needs substantial unique content
- Cite sources (dartsdatabase.co.uk, PDC official, etc.)
- Genuine expertise signal: show the model code, explain the methodology

```tsx
// components/AuthorByline.tsx
export function AuthorByline({ updatedAt }: { updatedAt: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-secondary py-3 border-t border-border">
      <div>
        <p>
          Stats updated: <time dateTime={updatedAt}>{formatDate(updatedAt)}</time>
        </p>
        <p>
          Data sources: dartsdatabase.co.uk, PDC official, The Odds API
        </p>
      </div>
    </div>
  )
}
```

---

## 10. PDC Calendar Integration

The PDC publishes an official calendar. Sync it to know when to activate your scrapers and writers.

```python
# utils/pdc_calendar.py
import requests
from icalendar import Calendar
from datetime import datetime

PDC_ICAL_URL = "https://www.pdc.tv/events/calendar.ics"  # verify this exists

def get_upcoming_pdc_events(days_ahead: int = 90) -> list[dict]:
    resp = requests.get(PDC_ICAL_URL, timeout=10)
    cal = Calendar.from_ical(resp.content)
    events = []
    now = datetime.now()

    for component in cal.walk():
        if component.name == "VEVENT":
            dtstart = component.get('dtstart').dt
            if hasattr(dtstart, 'date'):
                dtstart = datetime.combine(dtstart, datetime.min.time())
            days_until = (dtstart - now).days
            if 0 <= days_until <= days_ahead:
                events.append({
                    "name": str(component.get('summary')),
                    "start": dtstart.isoformat(),
                    "location": str(component.get('location', '')),
                    "days_until": days_until,
                })

    return sorted(events, key=lambda e: e['start'])
```
