# 04 — Design System

## Design Direction

**Aesthetic**: Dark, data-dense, editorial. Think Bloomberg Terminal meets FiveThirtyEight — serious numbers presented with confidence. Avoid generic sportsbook green/gold. Use deep navy + electric amber as primary palette. The site should feel like a quant built it, not a marketing team.

**Typefaces**
```css
/* Import in globals.css */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', monospace; /* for odds, probabilities, scores */
}
```

---

## Color Tokens

```css
/* styles/tokens.css */
:root {
  /* Core palette */
  --color-bg:           #0d1117;  /* near-black, not pure black */
  --color-surface:      #161b22;  /* card/panel background */
  --color-surface-2:    #21262d;  /* elevated surface */
  --color-border:       #30363d;  /* subtle border */
  --color-border-focus: #58a6ff;

  /* Brand */
  --color-amber:        #f0a500;  /* primary accent — darts bullseye gold */
  --color-amber-dim:    #7d5600;  /* muted amber for backgrounds */
  --color-blue:         #58a6ff;  /* links, info */
  
  /* Semantic */
  --color-edge-pos:     #3fb950;  /* positive edge — green */
  --color-edge-neg:     #f85149;  /* negative edge — red */
  --color-edge-neutral: #8b949e;  /* no edge */
  --color-steam:        #f0a500;  /* line movement alert */
  
  /* Text */
  --color-text-primary:   #e6edf3;
  --color-text-secondary: #8b949e;
  --color-text-muted:     #484f58;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  /* Radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Transitions */
  --transition: 120ms ease;
}
```

---

## Tailwind Config

```js
// tailwind.config.ts
import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:         '#0d1117',
        surface:    '#161b22',
        surface2:   '#21262d',
        border:     '#30363d',
        amber:      '#f0a500',
        'amber-dim':'#7d5600',
        'edge-pos': '#3fb950',
        'edge-neg': '#f85149',
        steam:      '#f0a500',
        primary:    '#e6edf3',
        secondary:  '#8b949e',
        muted:      '#484f58',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'stat': ['1.75rem', { lineHeight: '1', fontWeight: '600', letterSpacing: '-0.02em' }],
        'label': ['0.6875rem', { lineHeight: '1.4', fontWeight: '500', letterSpacing: '0.06em' }],
      },
    },
  },
  plugins: [],
}
export default config
```

---

## Core Components

### StatBar — head-to-head comparison

```tsx
// components/ui/StatBar.tsx
interface StatBarProps {
  label: string
  p1Value: number
  p2Value: number
  p1Name: string
  p2Name: string
  format?: 'number' | 'percent' | 'decimal'
  higherIsBetter?: boolean
  precision?: number
}

export function StatBar({ label, p1Value, p2Value, p1Name, p2Name, format = 'number', higherIsBetter = true, precision = 1 }: StatBarProps) {
  const total = p1Value + p2Value || 1
  const p1Pct = (p1Value / total) * 100
  const p2Pct = 100 - p1Pct

  const p1Better = higherIsBetter ? p1Value > p2Value : p1Value < p2Value
  const p2Better = higherIsBetter ? p2Value > p1Value : p2Value < p1Value

  const fmt = (v: number) => {
    if (format === 'percent') return `${(v * 100).toFixed(precision)}%`
    if (format === 'decimal') return v.toFixed(precision + 1)
    return v.toFixed(precision)
  }

  return (
    <div className="py-2">
      <div className="flex justify-between text-label uppercase tracking-widest text-secondary mb-1">
        <span className={p1Better ? 'text-primary font-medium' : ''}>{fmt(p1Value)}</span>
        <span>{label}</span>
        <span className={p2Better ? 'text-primary font-medium' : ''}>{fmt(p2Value)}</span>
      </div>
      <div className="flex h-1.5 rounded-full overflow-hidden bg-surface2">
        <div
          className={`h-full transition-all duration-500 ${p1Better ? 'bg-amber' : 'bg-secondary'}`}
          style={{ width: `${p1Pct}%` }}
        />
        <div
          className={`h-full transition-all duration-500 ${p2Better ? 'bg-amber' : 'bg-secondary'}`}
          style={{ width: `${p2Pct}%` }}
        />
      </div>
    </div>
  )
}
```

### EdgeBadge

```tsx
// components/ui/EdgeBadge.tsx
interface EdgeBadgeProps {
  edgePct: number  // e.g. 4.2 means +4.2% edge
  size?: 'sm' | 'md' | 'lg'
}

export function EdgeBadge({ edgePct, size = 'md' }: EdgeBadgeProps) {
  const isPos = edgePct > 0
  const isHigh = Math.abs(edgePct) > 5

  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  }

  return (
    <span className={`
      font-mono font-medium rounded ${sizeClasses[size]}
      ${isPos
        ? isHigh ? 'bg-edge-pos/20 text-edge-pos ring-1 ring-edge-pos/40' : 'bg-edge-pos/10 text-edge-pos'
        : 'bg-edge-neg/10 text-edge-neg'
      }
    `}>
      {isPos ? '+' : ''}{edgePct.toFixed(1)}%
    </span>
  )
}
```

### OddsDisplay

```tsx
// components/ui/OddsDisplay.tsx
// Renders American odds in monospace with color coding

interface OddsDisplayProps {
  odds: number
  size?: 'sm' | 'md' | 'lg'
  showSign?: boolean
}

export function OddsDisplay({ odds, size = 'md', showSign = true }: OddsDisplayProps) {
  const isFav = odds < 0
  const formatted = isFav ? odds.toString() : `+${odds}`

  const sizeClasses = { sm: 'text-sm', md: 'text-base', lg: 'text-xl' }

  return (
    <span className={`font-mono font-medium ${sizeClasses[size]} ${isFav ? 'text-secondary' : 'text-amber'}`}>
      {formatted}
    </span>
  )
}
```

### MatchCard

```tsx
// components/ui/MatchCard.tsx
export function MatchCard({ match, pick, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-surface border border-border rounded-lg p-4 
                 hover:border-amber/40 hover:bg-surface2 transition-all duration-150 
                 focus:outline-none focus:ring-2 focus:ring-amber/40"
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-label uppercase tracking-widest text-secondary">
          {match.tournament} · {match.round}
        </span>
        {match.isLive && (
          <span className="flex items-center gap-1 text-edge-pos text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-edge-pos animate-pulse" />
            Live
          </span>
        )}
      </div>

      <div className="flex items-center justify-between gap-4">
        <div className="flex-1">
          <p className="text-primary font-medium">{match.player1}</p>
          <OddsDisplay odds={match.p1Odds} size="sm" />
        </div>

        <div className="text-center text-secondary text-sm font-mono">
          {match.isLive ? `${match.score1} – ${match.score2}` : 'vs'}
        </div>

        <div className="flex-1 text-right">
          <p className="text-primary font-medium">{match.player2}</p>
          <OddsDisplay odds={match.p2Odds} size="sm" />
        </div>
      </div>

      {pick && (
        <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
          <span className="text-secondary text-sm">
            Model pick: <span className="text-primary font-medium">{pick.player}</span>
          </span>
          <EdgeBadge edgePct={pick.edgePct} size="sm" />
        </div>
      )}
    </button>
  )
}
```

### PlayerAvatar

```tsx
// components/ui/PlayerAvatar.tsx
// Flag + name initials since we won't have player photos initially

const FLAG_EMOJI: Record<string, string> = {
  NED: '🇳🇱', ENG: '🏴󠁧󠁢󠁥󠁮󠁧󠁿', WAL: '🏴󠁧󠁢󠁷󠁬󠁳󠁿', SCO: '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
  AUS: '🇦🇺', GER: '🇩🇪', BEL: '🇧🇪', IRL: '🇮🇪',
  NZL: '🇳🇿', USA: '🇺🇸', CAN: '🇨🇦', AUT: '🇦🇹',
}

export function PlayerAvatar({ player, size = 40 }) {
  const initials = player.name.split(' ').map(n => n[0]).join('').slice(0, 2)
  const flag = FLAG_EMOJI[player.nationality] ?? '🎯'

  return (
    <div className="flex items-center gap-2">
      <div
        className="flex items-center justify-center rounded-full bg-surface2 border border-border text-primary font-medium text-sm flex-shrink-0"
        style={{ width: size, height: size, fontSize: size * 0.35 }}
      >
        {initials}
      </div>
      <div>
        <p className="text-primary font-medium leading-tight">{player.name}</p>
        <p className="text-secondary text-xs">{flag} {player.nationality}</p>
      </div>
    </div>
  )
}
```

---

## Layout

```tsx
// components/layout/AppLayout.tsx
export function AppLayout({ children }) {
  return (
    <div className="min-h-screen bg-bg text-primary font-sans">
      <TopNav />
      <div className="max-w-6xl mx-auto px-4 py-6">
        <LiveEventBanner />  {/* sticky when there's a live match */}
        {children}
      </div>
      <Footer />
    </div>
  )
}

// components/layout/TopNav.tsx
export function TopNav() {
  return (
    <nav className="border-b border-border bg-bg/95 backdrop-blur sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <div className="flex items-center gap-6">
          <Logo />
          <NavLink href="/tournaments">Tournaments</NavLink>
          <NavLink href="/picks">Picks</NavLink>
          <NavLink href="/players">Players</NavLink>
          <NavLink href="/odds">Odds</NavLink>
          <NavLink href="/tools">Tools</NavLink>
        </div>
        <div className="flex items-center gap-3">
          <LiveIndicator />
          <DKAffiliateButton />
        </div>
      </div>
    </nav>
  )
}
```

---

## Chart Theming (Recharts)

```tsx
// lib/chartTheme.ts
export const CHART_THEME = {
  background: 'transparent',
  gridColor: '#30363d',
  textColor: '#8b949e',
  axisColor: '#30363d',
  tooltipBg: '#161b22',
  tooltipBorder: '#30363d',
  p1Color: '#f0a500',   // amber
  p2Color: '#58a6ff',   // blue
  edgePosColor: '#3fb950',
  edgeNegColor: '#f85149',
}

export const defaultChartProps = {
  style: { background: 'transparent' },
}

export const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-surface border border-border rounded-md p-2 text-sm">
      <p className="text-secondary mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }} className="font-mono">
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  )
}
```

---

## Responsive Breakpoints

```
Mobile  (<640px):  Single column, collapsible stat panels, bottom tab nav
Tablet  (640–1024px): 2-col match grid, sidebar stats
Desktop (>1024px): 3-col layout: sidebar | main | sidebar
```

```tsx
// Match center layout example
<div className="grid grid-cols-1 lg:grid-cols-[240px_1fr_240px] gap-6">
  <aside className="hidden lg:block">  {/* Player 1 deep stats */}  </aside>
  <main>  {/* Match center */}  </main>
  <aside className="hidden lg:block">  {/* Player 2 deep stats */}  </aside>
</div>
```
