# BullzIQ — Streamlit Visual Reference

> Canonical description of the existing Streamlit UI. The React app must mirror
> this document section-for-section. Anything not listed here is not part of
> the parity contract.

---

## 1. Global shell

| Element | Spec |
|---|---|
| Page title / icon | `BullzIQ — PDC Darts Analytics`, 🎯 |
| Layout | `layout="wide"`, sidebar `expanded` |
| Main content | `.block-container` max-width **1200px**, `padding-top: 1rem`, `padding-bottom: 0` |
| Sidebar | background `--biq-sidebar`, `border-right: 1px solid --biq-border` |
| Sidebar content | BullzIQ logo (`data_files/logo.png`, width **180**) on every sub-page (Home shows logo width **200** in main area) |
| Default Streamlit chrome | hidden (`#MainMenu, footer, header { visibility: hidden }`) |
| Footer (every page) | Betting Oracle footer — see §9 |

### Auto theme
- Day = browser-local hour **07:00–18:59** → **Light - Sky Glass**
- Night = **19:00–06:59** → **Dark - Petrol**
- Streamlit syncs via `?biq_mode=day|night` query param; React must resolve the
  theme from browser-local hour directly (capture harness seeds `Date`).

### Theme tokens (CSS custom properties, `--biq-*`)

| Token | Light - Sky Glass | Dark - Petrol |
|---|---|---|
| `bg` | `#f6fbff` | `#071418` |
| `bg2` (card) | `#ffffff` | `#0f2026` |
| `bg3` (hover/input) | `#e8f2fb` | `#183039` |
| `text` | `#1f3347` | `#d8edf2` |
| `muted` | `#607a95` | `#7ba7b2` |
| `border` | `#c5d9ed` | `#28505c` |
| `accent` | `#0284c7` | `#00b4d8` |
| `accent2` | `#f97316` | `#f77f00` |
| `pos` | `#15803d` | `#2ec4b6` |
| `neg` | `#dc2626` | `#ef476f` |
| `tab` | `#0284c7` | `#00b4d8` |
| `sidebar` | `#ecf5ff` | `#051015` |

Plotly: template `plotly_white` (day) / `plotly_dark` (night); paper & plot bg
transparent; grid color `--biq-border`; font color `--biq-text`; modebar hidden.

### Shared component styles

- **Metric card** (`st.metric`): bg `--biq-bg2`, 1px `--biq-border`, radius 8px, padding `12px 16px`; label uppercase 0.75rem muted, letter-spacing .05em; value 1.5rem/700.
- **Tabs**: tablist `border-bottom: 1px solid --biq-border`; inactive tab text muted; active tab text `--biq-tab`, `border-bottom: 2px solid --biq-tab`, weight 600.
- **Badges** (pill, radius 20px, padding `3px 10px`, font 0.78rem):
  - `edge-high` (edge ≥ 4): green — bg `rgba(63,185,80,.15)`, text/border `--biq-pos`, weight 700
  - `edge-med` (≥ 2): amber — bg `rgba(240,165,0,.12)`, text/border `#f0a500`, weight 700
  - `edge-low` (> 0): muted — bg `rgba(139,148,158,.12)`, text/border `--biq-muted`, weight 600
  - `edge-none` (≤ 0): transparent, muted text, `--biq-border` border
  - `steam-badge`: red — bg `rgba(248,81,73,.15)`, text/border `--biq-neg`, weight 700
  - Confidence: `● HIGH` pos/700 · `● MED` `#f0a500`/700 · `● LOW` muted/600
- **Tables** (`themed_dataframe`): outer wrap 1px `--biq-border`, radius 10px, bg `--biq-bg2`; thead sticky, bg `--biq-bg3`, cells `padding: 8px 10px`, weight 600, 1px `--biq-border` on all cells; tbody td bg `--biq-bg2`, hover row bg `--biq-bg3`; font-size 0.95rem; index hidden.
- **Cards**: `st.container(border=True)` → 1px `--biq-border`, radius ~8–10px, padding ~1rem, bg transparent.
- **Tournament cards**: `.tourn-card` bg `--biq-bg2`, 1px border, radius 10px, padding `14px 18px`, tier accent = 3px left border (`--biq-accent` tier 1, `#f0a500` tier 2, `--biq-accent2` tier 3).
- **RG banner**: bg `--biq-bg2`, `border-left: 3px solid --biq-accent`, radius `0 6px 6px 0`, padding `10px 14px`, 0.8rem muted.
- **Affiliate notice**: transparent bg, 1px `--biq-border`, radius 6px, padding `8px 12px`, 0.75rem muted.
- **Primary button**: bg `--biq-accent`, white text.

### Nationality flags
`ENG` 🏴󠁧󠁢󠁥󠁮󠁧󠁿 `WAL` 🏴󠁧󠁢󠁷󠁬󠁳󠁿 `SCO` 🏴󠁧󠁢󠁳󠁣󠁴󠁿 `NED` 🇳🇱 `BEL` 🇧🇪 `AUS` 🇦🇺 `POR` 🇵🇹 `IRL` 🇮🇪 `GER` 🇩🇪 `USA` 🇺🇸 `NZL` 🇳🇿 `CAN` 🇨🇦 — fallback 🌍.

### American odds format
`format_american_odds(int)`: `0 → "N/A"`, positive → `"+N"`, negative → `"-N"`.

---

## 2. Home (`/`) — `predictions.py`

**Header:** logo image width **200** (main content area) → `st.divider()`.

**Top metric row** — 4 equal columns:
1. `30-Day Record` — value `{wins}–{losses}`, delta `{win_pct}% win rate`
2. `Model ROI (30d)` — value `+{roi_pct}%`, delta `vs. flat bet`
3. `Active Picks Today` — value `{n}`, delta `all matches`
4. `Best Edge Today` — value `+{best}%` (or `{best}%` when ≤ 0), delta `vs. DraftKings line`

→ `st.divider()` → tabs:
`🎯 Today's Picks` · `📅 Schedule` · `🔥 Steam Moves` · `📊 Model Info` · `📈 Historical`

### Tab 1 — Today's Picks
- `### Today's Model Picks`
- Controls row: `st.columns([2, 1])` — slider `Minimum edge %` (0.0–8.0, default 1.0, step 0.5) · selectbox `Sort by` (`Edge %`, `Match time`, `Confidence`)
- Empty: info `No picks meet the current edge filter. Lower the slider to see more.`
- Otherwise: inline model-disclaimer info box, spacer, then one **Pick card** per pick:
  - Container(border). Columns `[3, 1]`:
    - left: `**{p1}** vs **{p2}**` newline, muted 0.85rem `{tournament} · {round} · {HH:MM AM/PM}`
    - right: `Edge badge` + `Confidence badge`
  - `---`
  - 4 equal metric columns: `Pick` (player name) · `DK Odds` (american) · `Model Prob` (`{x}%`, 1dp) · `DK Implied` (`{x}%`, 1dp)
  - Expander `📖 Reasoning`: reasoning text + DK CTA link-button `Bet {odds} on DraftKings →` (primary, https://sportsbook.draftkings.com)

### Tab 2 — Schedule
- `### Upcoming PDC Matches (DraftKings covered)`
- Slider `Days ahead` (1–14, default 7)
- Empty: info `No upcoming matches in the database.`
- Grouped by tournament: `#### {tournament}` then one **Schedule card** per match:
  - Container(border). Columns `[2, 1.5, 0.3, 1.5, 1.5]`:
    1. muted 0.8rem `{Day Mon DD · HH:MM AM/PM}` `<br>` muted 0.78rem `{round or "TBD"}`
    2. `**{p1}**`
    3. centered muted `vs`
    4. `**{p2}**`
    5. `{o1} / {o2}` in `--biq-accent2`, or muted `Lines not open yet`
  - spacer after each tournament group

### Tab 3 — Steam Moves
- `### 🔥 Steam Moves — Significant Line Movement`
- caption `Flagged when implied probability shifts ≥3pp within 30 minutes.`
- Empty: info `No steam moves detected in the last 24 hours.`
- One **Steam card** per event, container(border), columns `[3, 2, 1]`:
  1. `**{p1} vs {p2}**` newline muted 0.82rem `{tournament}`
  2. `steam-badge` `{▲|▼} STEAM: {player}` then muted 0.82rem `{open} → {curr} ({+shift}pp)`
  3. muted 0.8rem `{HH:MM}` (detected time)
  - Arrow: `▲` if shift > 0 else `▼`

### Tab 4 — Model Info
- `### How the Model Works`, then 2 equal columns:
  - Left: markdown — `#### Elo Rating System` (2015–present; tournament K-multipliers 1.5× Worlds; margin of victory; format length), `#### Match Predictor` (calibrated logistic regression: recent form L20, 3-dart avg & checkout % diff, H2H last 10, tournament win rates, ranking differential), `#### Edge Calculation` (`Edge % = (Model Prob − DK Implied) × 100`)
  - Right: `#### 30-Day Performance Summary` — table (2 cols `Metric`/`Value`, rows Record, Win Rate, ROI, Avg Edge, Brier Score); info callout `**Brier Score**: Calibration metric (0 = perfect, 1 = worst). Industry benchmark for well-calibrated models ≈ 0.22.`; then histogram of active pick edges (Plotly, `nbinsx=20`, marker `--biq-accent`, title `Current Pick Edge Distribution`, height 260, margins `l10 r10 t40 b30`)

### Tab 5 — Historical
- `### 📈 Historical Model Performance (2015–Present)` + caption `Elo ratings and performance metrics built from 10+ years of PDC match data.`
- `#### Elo Rating Trajectories` — multiselect `Select players to compare` (top-12 by Elo, default first 5). Line chart (one 2px line per player, 12-color palette: accent, accent2, pos, `#f0a500`, `#a855f7`, `#14b8a6`, `#ec4899`, `#f59e0b`, `#6366f1`, `#34d399`, `#f87171`, `#facc15`), height 380, legend horizontal `y=-0.25`. Empty selection: info `Select at least one player above to display Elo trajectories.`
- `st.divider()` → `#### Year-by-Year Match Volume & Model Accuracy` — columns `[3, 2]`: bar chart (x=year str, y=total_matches, `--biq-accent2`) + table `Year` / `Matches`
- `st.divider()` → `#### Era Performance — Top Win Rates by Period` — grouped bar chart (eras `2015–2018`, `2019–2022`, `2023–Now`; top 8 players per era by win rate; y tick format `.0%`; height 320; legend horizontal `y=-0.4`)

---

## 3. Players (`/Players`) — `pages/1_Players.py`

Header `## 🎯 Player Profiles & Rankings`, caption `PDC player Elo ratings, career stats, form, and head-to-head records.`, divider.

Tabs: `🏆 Rankings` · `👤 Player Profile` · `⚔️ Head-to-Head`

### Tab 1 — Rankings
- `### BullzIQ Elo Rankings`
- Horizontal bar chart, top 16 by Elo (reversed so #1 on top), marker `--biq-accent`, text outside, height 520, margins `l10 r60 t20 b10`, x title `Elo Rating`
- `#### Full Rankings Table` — table (height 500): `Rank`, `🏳` (flag), `Player`, `Nickname`, `Elo` (int), `3-Dart Avg`, `Checkout %` (`xx.x%`), `Win Rate (L20)` (`xx.x%`), `PDC Rank`
- Empty: warning `No player data. Ensure the database is seeded.`

### Tab 2 — Player Profile
- Selectbox `Select a player`
- Header columns `[1, 3]`:
  - left card: centered — flag at 4rem, name 1.5rem/700, nickname muted in quotes
  - right: 4 equal metrics — `Elo Rating` (`{int:,}`), `PDC Ranking` (`#{n}` or `—`), `3-Dart Avg` (`{x.2f}` or `—`), `Checkout %` (`{x.1f}%` or `—`)
- `#### Elo Rating History` — line chart (accent, width 2), hline `y=1500` dotted grid-colored annotated `Baseline 1500` (bottom right), height 300, no legend. Empty: info `No Elo history available for this player.`
- `#### Detailed Stats` — 3 equal columns (2 metrics each):
  - col 1: `Win Rate (L20)` (`x.1f%`), `PL Win Rate` (`x.1f%`)
  - col 2: `3-Dart Avg (L10)` (`x.2f`), `Checkout % (L10)` (`x.1f%`)
  - col 3: `Avg 180s/Match (L10)` (`x.2f`), then `**Form (last 5):**` + W/L letter spans (W = `--biq-pos`, else `--biq-neg`)
- `#### Recent Matches (Last 20)` — table: `Date`, `Opponent`, `Score`, `Result` (`🟢 W` / `🔴 L`), `Avg` (2dp), `Checkout%` (`x.1f%`, NaN→0), `180s`. Empty: info `No match history available.`
- Missing player: warning `Player not found.`

### Tab 3 — Head-to-Head
- `### Head-to-Head Comparison`
- Picker columns `[2, 0.5, 2]`: selectbox `Player 1` (default idx 0) · centered `vs` (margin-top 28px, 1.4rem) · selectbox `Player 2` (default idx 1)
- Same player: warning `Select two different players.`
- `#### Stat Comparison` — name row: right-aligned `h4` `{flag} {p1}` (col 1) / left-aligned `h4` `{flag} {p2}` (col 2); then 4 stat rows, each columns `[5, 0.5, 5]` — right-aligned value · centered muted 0.75rem label · left-aligned value. Rows: `Elo Rating` (`{:.0f}`), `3-Dart Avg` (`{:.2f}`), `Checkout %` (`{:.1f}%`), `180s/Leg` (`{:.3f}`)
- `#### Historical H2H Record` — 3 equal metrics: `{p1} Wins` (delta `{pct}%`), `Total Meetings`, `{p2} Wins` (delta `{pct}%`); then table: `Date`, `Score`, `Winner`, `Avg {p1}`, `Avg {p2}`
- Empty: info `No head-to-head matches found between these two players.`

---

## 4. Matches (`/Matches`) — `pages/2_Matches.py`

Header `## 🎮 Match Center`, caption `Upcoming fixtures, live odds, match statistics, and historical results.`, divider.

Tabs: `📅 Upcoming` · `📋 Recent Results` · `🔍 Match Detail`

### Tab 1 — Upcoming
- `### Upcoming PDC Fixtures`
- Slider `Show matches over next N days` (1–14, default 7)
- Empty: info `No upcoming matches in the database.`
- Grouped by tournament `#### {name}`, one **match card** per match — container(border), columns `[2, 2.5, 0.3, 2.5, 2, 1.5]`:
  1. muted 0.82rem `{Day Mon DD, HH:MM AM/PM}` `<br>` muted 0.75rem `{round or "TBD"}`
  2. `{flag} **{p1}**` + optional muted 0.78rem `{x.1f}% implied`
  3. centered muted `vs` (margin-top 8px)
  4. `{flag} **{p2}**` + optional implied
  5. `{o1} / {o2}` — each bold 700, `--biq-pos` if odds > 0 else `--biq-neg`, muted ` / ` separator; else muted `Lines not open yet`
  6. `--biq-accent2` 0.78rem `BO{legs*2-1}` (default BO11)

### Tab 2 — Recent Results
- `### Recent Results`
- 2 equal columns: selectbox `Filter by tournament` (`All` + uniques) · selectbox `Filter by player` (`All` + union of players)
- Table (height 550): `Date` (`Mon DD, YYYY`), `Tournament`, `Round`, `Player 1`, `Score`, `Player 2`, `Winner` — limit 100
- Empty: info `No results in the database.`

### Tab 3 — Match Detail
- `### Match Detail — Odds Movement`
- Selectbox `Select a match` — labels `{p1} vs {p2} — {tournament}` (upcoming next 14 days)
- Empty: info `No upcoming matches available for detail view.`
- `#### {p1} vs {p2}` + caption `{tournament} · {round}`
- Odds movement chart: 2 traces lines+markers (p1 `--biq-accent`, p2 `--biq-accent2`, marker 6), hline `y=50` dotted annotated `50% line` (bottom right), title `DraftKings Implied Probability — 3-Hour Window`, y range 0–100 with `%` suffix, height 380, legend horizontal `y=-0.15`
- Empty: info `No odds history available for this match.`
- `#### Line Movement Summary` — 4 equal metrics: `{p1} — Open`, `{p1} — Current` (delta = int odds diff), `{p2} — Open`, `{p2} — Current` (delta = int odds diff)
- `#### Historical Head-to-Head` — 3 metrics (`{p1} Wins`, `Total Meetings`, `{p2} Wins`) + table `date`, `score`, `winner_id` (raw, first 10). Empty: info `No previous meetings found.`

---

## 5. Tournaments (`/Tournaments`) — `pages/3_Tournaments.py`

Header `## 🏆 Tournament Hub`, caption `PDC events covered on DraftKings — formats, prize money, and results.`, divider.

**Page-level metric row (above tabs)** — 4 equal metrics: `DK-Covered Tournaments` (count), `Major Events` (tier-1 count), `Total Prize Pool` (`£{x:,.0f}`), `Active Years Coverage` (static `2000–2026`). Then second divider.

Tabs: `🗂️ All Tournaments` · `📊 Tournament Detail`

### Tab 1 — All Tournaments
- `### All PDC Tournaments`
- Radio `Filter by tier` (horizontal): `All` / `Majors (Tier 1)` / `Ranking (Tier 2)`
- One **tournament card** per event — container(border), columns `[3, 2, 1.5, 1.5]`:
  1. `**{name}**` newline muted 0.8rem `{🏅 MAJOR | 🎯 RANKING} · {typical_month or "—"}`
  2. muted 0.82rem `{format_desc or "—"}`
  3. `--biq-accent2` bold `£{prize:,}` or `—`
  4. 0.9rem `✅ DK` or `❌`
- `#### Prize Fund Comparison` — horizontal bar chart sorted ascending, majors `--biq-accent` / ranking `--biq-accent2` per bar, text `£{x:,}` outside, height 380, margins `l10 r100 t20 b20`, x title `Prize Fund (£)`
- Empty (page level): warning `No tournament data. Ensure the database is seeded.`

### Tab 2 — Tournament Detail
- Selectbox `Select tournament`
- `### Tournament Results`
- Info block (plain markdown): `**Format:** {format_desc or "—"}  ` / `**Prize Fund:** £{x:,}  ` / `**Typical Month:** {month or "—"}` → divider
- Table (height 500): `Date` (`Mon DD, YYYY`), `Round`, `Player 1`, `Score`, `Player 2`, `Winner` — limit 100
- Empty: info `No results logged for this tournament yet.`
- `#### Most Wins in This Tournament` — horizontal bar (top 10 winners, `--biq-accent`), height 300, y autorange reversed, x title `Match Wins`

---

## 6. Odds (`/Odds`) — `pages/4_Odds.py`

Header `## 📊 Odds Tracker`, caption `Live DraftKings moneylines, line movement, and steam detection for PDC events.`, divider.

Tabs: `💰 Current Lines` · `📈 Line Movement` · `🔥 Steam Moves`

### Tab 1 — Current Lines
- `### Current DraftKings Lines`
- Selectbox `Tournament` (`All` + uniques)
- Empty states: info `No upcoming fixtures found in the next 7 days.` / info `{n} upcoming fixture(s) found, but DraftKings moneylines are not posted yet.` + caption `Odds will appear automatically when the sportsbook opens markets.`
- One **odds card** per match — container(border):
  - Header `[5, 1]`: muted 0.82rem `{tournament} · {Day Mon DD, HH:MM AM/PM}` · muted 0.75rem `Updated {HH:MM}`
  - Body `[3, 2, 3]`:
    - p1: `**{p1}**` newline, odds at 1.3rem/700 in `--biq-pos` (positive) or `--biq-neg` (negative) + muted 0.8rem `({impl}% implied)`
    - center: vig-normalized probability bar — flex row height 8px radius 4px, left `--biq-accent` `{p1_pct}%`, right `--biq-accent2`; below, space-between muted 0.75rem percentages
    - p2: mirror
- After cards: divider + caption `Odds data sourced from DraftKings. Refresh page for latest lines.`

### Tab 2 — Line Movement
- `### Odds Line Movement Chart` + caption `Track how DraftKings implied probabilities shift over time for each match.`
- Selectbox `Select match` — labels `{p1} vs {p2} — {tournament}`
- Empty: info `No upcoming matches available.` / info `No odds history available for this match.`
- Chart 1 — Implied probability: 2 traces lines+markers (p1 accent / p2 accent2, width 2.5, marker 7), hline `y=50` dashed annotated `50%` (right), title `Implied Probability: {p1} vs {p2}`, x `Snapshot Time`, y `Implied Probability (%)` range 0–100, height 400, legend horizontal `y=-0.2`
- Chart 2 — Moneyline: 2 traces lines+markers (width 2, marker 6, names `{p} (ML)`), hline `y=0` dotted, title `American Moneyline Movement`, height 300, legend horizontal `y=-0.25`
- `#### Movement Summary` — table 6 cols: `(blank)`, `Opening Odds`, `Current Odds`, `Open Implied`, `Current Implied`, `Shift (pp)` — one row per player; shift `{+x.2f}`

### Tab 3 — Steam Moves
- `### 🔥 Steam Moves` + caption `Steam = significant sharp-money line movement. Flagged when implied probability shifts ≥3 percentage points within 30 minutes.`
- Slider `Look-back window (hours)` (1–48, default 24)
- Empty: info `No steam moves detected in the last {h} hours.`; else success `**{n} steam move(s) detected** in the last {h} hours.`
- One **steam card** per event — container(border), columns `[3, 2, 2, 1.5]`:
  1. `**{p1} vs {p2}**` newline muted 0.82rem `{tournament}`
  2. `steam-badge` `{▲|▼} STEAM on {player}` + muted 0.8rem `Shift: {+x.1f}pp`
  3. muted 0.82rem `Open → Current` `<br>` bold `{open} → {curr}`
  4. intensity (`🔴🔴🔴` if |shift| ≥ 5, `🔴🔴` if ≥ 3, else `🔴`) `<br>` muted 0.8rem `{Mon DD, HH:MM}`
- Info callout: `**What does steam mean for your bet?** When sharp money hits a line and the book moves it quickly, that movement signals new information. A steam move in the same direction as a BullzIQ model pick increases confidence. A steam move against a pick is a warning sign to reassess.`

---

## 7. Tools (`/Tools`) — `pages/5_Tools.py`

Header `## 🔧 Analytics Tools`, caption `Interactive calculators for edge, props, and format analysis.`, divider.

Tabs: `💰 Edge Calculator` · `🎯 180s Calculator` · `📐 Format Variance` · `🔗 Parlay Edge`

### Tab 1 — Edge Calculator
- `### 💰 Betting Edge Calculator` + text `Enter your estimated win probability and the DraftKings odds to calculate edge. **Edge > 0** means the model sees value.`
- Columns `[1, 1]`:
  - **Left (inputs)** — `#### Method 1 — Elo-Based`; selectbox `Player 1 (favourite)` (idx 0); selectbox `Player 2 (underdog)` (idx 1); selectbox `Legs to win` (`5,6,7,8,10`, default idx 1 → 6); number input `DK Odds for Player 1 (e.g. -140 or +110)` (default −150, step 5)
  - **Right (results)** — `#### Result`; 2 equal sub-columns:
    - r1: metric `Model Probability` (`{x.1f}%`), metric `DK Implied Prob` (`{x.1f}%`)
    - r2: **Edge card** — centered, bg `--biq-bg2`, border 1px edge-color, radius 8px, padding 16px: big value 2.2rem/700 `{+edge.2f}%`, label muted `EDGE`, grade 1.2rem; edge-color = `--biq-pos` if edge > 0 else `--biq-neg`. Then metric `EV (per $100 bet)` (`${+x.2f}`, delta `Grade {grade}`)
  - `#### Elo Context` bullets: `**{p1} Elo:** {x.0f}`, `**{p2} Elo:** {x.0f}`, `**Raw Elo Win Prob:** {x.1f}%`, `**Format-Adjusted Prob:** {x.1f}%`, `**Fair Odds:** {american}`
  - (result column blank when both picks are the same player)
- divider → expander `📖 How to use this tool` (4-step list + grade legend `A (≥5%), B (≥3%), C (≥1.5%), D (<1.5%)` + RG warning `⚠️ This is a model estimate, not a guaranteed bet. Always gamble responsibly.`)
- `#### Manual Entry` — 3 equal columns: number input `Your win probability (%)` (1–99, 55.0, 0.5) · number input `DraftKings odds` (−120, step 5) · button `Calculate` → result markdown in col 3: `**Edge:** {+x.2f}%  ` / `**EV:** ${+x.2f} per $100  ` / `**Grade:** {grade}` (edge colored pos/neg)

### Tab 2 — 180s Calculator
- `### 🎯 180s Probability Calculator` + text `Uses a Poisson distribution model to estimate the probability of a player hitting over/under a 180s prop line.`
- Columns `[1, 1]`:
  - **Left (inputs):** selectbox `Select player`; slider `Legs to win (match format)` (3–10, 6); number input `180s line (over/under)` (0.5–20.0, 3.5, 0.5); number input `DK odds for OVER` (−115, 5); number input `DK odds for UNDER` (−115, 5); number input `Override {player}'s avg 180s/leg` (0.01–0.50, default = player's `avg_180s_per_leg` or 0.10, step 0.005, `%.3f`)
  - **Right:** `#### Results`; 2 equal sub-columns:
    - rc1: metric `Expected 180s` (`{x.2f}`) + **OVER card** (bg `--biq-bg2`, 1px border in pos/neg by edge, radius 8px, padding 12px, centered): muted 0.78rem `OVER {line.1f}`, value 1.5rem/700 `{x.1f}%`, footer colored 0.9rem/700 `Edge: {+x.2f}% ({grade})`
    - rc2: metric `Model (Poisson μ)` (`λ={x.2f}`) + matching **UNDER card**
  - Poisson bar chart (k = 0 … `int(expected*3)+2`, pmf×100, `--biq-accent` if k > line else `--biq-accent2`), vline at line dashed annotated `Line: {line}` (top), title `Poisson Distribution — {player} 180s`, x `Number of 180s`, y `Probability (%)`, height 280, no legend
- Info callout: `**Poisson model**: λ (expected 180s) = avg_180s_per_leg × expected_legs, where expected_legs ≈ legs_to_win × 1.6. The bar chart shows P(X=k) for each 180s count — blue = under line, red = over line.`

### Tab 3 — Format Variance
- `### 📐 Format Variance Explainer` + text `Shorter PDC formats (fewer legs) compress win probabilities toward 50%, giving underdogs better value. Adjust the sliders to explore.`
- 2 equal columns:
  - Left: slider `Base win probability for stronger player (%)` (50–90, 65, 0.5); chart — 2 traces lines+markers over formats `Best of 5/7/9/11/13/15/19` (legs_to_win = 3,4,5,6,7,8,10): `Favourite Win %` (accent, width 2.5, marker 8), `Underdog Win %` (accent2); hline `y=50` dotted; title `Format Impact (Base: {x.0f}% favourite)`, height 320, legend horizontal `y=-0.25`
  - Right: `#### Format Reference Table` — table `Format` / `Fav Win %` / `Underdog %` (1dp); spacer; info callout `**Key takeaway**: In a Best of 5 (legs to win = 3) match, a player with 65% base probability wins ~60% of the time. In a Best of 19 (legs to win = 10), that same player wins ~72%. Shorter formats = more variance = better underdog value.`; `#### PDC Tournament Formats` — hardcoded 7-row table `Tournament` / `Format` (World Championship Final = Best of 13 sets; Premier League = Best of 11 legs; World Matchplay Final = Best of 31 legs; Grand Slam Final = Best of 19 legs; UK Open Final = Best of 11 legs; World Grand Prix = Best of 5 sets (3-leg); PC Finals Final = Best of 21 legs)

### Tab 4 — Parlay Edge
- `### 🔗 Parlay Edge Calculator` + text `Add up to 4 individual bets to calculate combined parlay probability and edge.`
- Number input `Number of parlay legs` (2–4, 2, 1)
- Dynamic equal columns (one per leg), each: bold `**Leg {i+1}**`, number input `Model prob (%) — Leg {i+1}` (1–99, 55.0, 0.5), number input `DK odds — Leg {i+1}` (−130, 5)
- divider → 4 equal metrics: `Parlay Model Prob` (`{x.2f}%`), `DK Implied Prob` (`{x.2f}%`), `Parlay Edge` (`{+x.2f}%`, normal/inverse delta color), `EV per $100` (`${+x.2f}`)
- Info callout: `⚠️ Parlays multiply both your potential payout and the book's edge. Even if each individual leg has positive edge, the combined parlay edge decreases significantly. Use with caution.`

---

## 8. Calculator formulas (numerical contract)

Source of truth: `backend/calculators/client_math.py` ≡ `models/elo.py` + `models/props_model.py`. The React `utils/calculators.ts` port must match to ≤1e-6 on probabilities and exactly on odds conversion.

- `elo_win_probability(a, b) = 1 / (1 + 10 ** ((b - a) / 400))`
- `implied_prob_from_american(odds)`: odds < 0 → `(-odds)/(-odds+100)`; else `100/(odds+100)`
- `to_american_odds(p)`: clamp p to [0.01, 0.99]; p ≥ 0.5 → `-round(p/(1-p)*100)`; else `round((1-p)/p*100)`
- `to_decimal_odds(p) = round(1/clamp(p), 2)`
- `calculate_edge(model_prob, dk_odds)`: `dk_implied` per above; `edge_pct = (model_prob - dk_implied) * 100`; `payout = odds ≥ 0 ? odds : 10000/(-odds)`; `ev = model_prob*payout - (1-model_prob)*100`; grade `A ≥ 5, B ≥ 3, C ≥ 1.5, else D`; rounds model_prob/dk_implied to 4dp, edge_pct/EV to 2dp
- `_poisson_cdf(k, mu)`: recurrence `p₀ = e^-mu; pᵢ = pᵢ₋₁ × mu/i`; cumulative sum, min 1.0
- `prob_180s_over(expected, line) = 1 - poisson_cdf(floor(line), expected)`; under = complement
- `expected_180s_in_match(avg_per_leg, legs_to_win) = avg × legs_to_win × 1.6`
- `format_adjusted_probability(base, legs_to_win, sets_to_win?)`: legs → `clamp(0.5 + (base-0.5)*(0.6 + legs/15), 0.02, 0.98)`; sets → `clamp(0.5 + (base-0.5)*(1 + (sets*2-1)/20), 0.02, 0.98)`
- `parlay(legs)`: per leg `dk_impl` and `decimal = odds<0 ? 1+100/(-odds) : 1+odds/100`; products across legs; `edge = (Πprob − Πimpl) × 100`; `ev_100 = Πprob × (Πdecimal − 1) × 100 − (1 − Πprob) × 100`; rounds probs/decimal to 4dp, edge/EV to 2dp

---

## 9. Legal / footer copy

Every page ends with the Betting Oracle footer (`page_footer()`):
- `Powered by **Betting Oracle**` (link https://www.betting-oracle.com)
- `Sports Prediction Analytics` + `All content is for informational purposes only and does not constitute betting advice. Wager responsibly.`
- Betting Oracle logo image (height 60)

Legal copy (mirrored by `GET /api/v1/legal/footer`):
- RG: `21+ only. Gambling involves risk. If you or someone you know has a gambling problem, call 1-800-GAMBLER or visit ncpgambling.org.`
- Affiliate: `BullzIQ may earn a commission from DraftKings through referral links. This does not affect our model's picks. Picks are generated independently.`
- Model: `Model picks are for informational purposes only and are not guaranteed. Past performance does not predict future results. Bet responsibly.`
- DK CTA: `Bet {odds} on DraftKings →` → https://sportsbook.draftkings.com (help text: `Must be 21+. Available in eligible US states. Gambling problem? Call 1-800-GAMBLER.`)

---

## 10. Responsive observations

- Streamlit `st.columns` ratios are proportional (`fr`) and hold at all widths until the mobile breakpoint, where columns stack vertically (each becomes full-width, in DOM order).
- The sidebar collapses to a hamburger-triggered drawer below ~992px.
- Charts (`width="stretch"`) fill the container; fixed pixel heights are kept.
- The 6 parity viewports: 1440×1000, 1280×800, 768×1024, 430×932, 390×844, 375×812.
