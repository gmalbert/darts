"""
jobs/scheduler.py — APScheduler background jobs for BullzIQ.

Jobs:
  - odds_refresh:  Every 30 minutes — fetch new DraftKings/Bet365 odds
  - steam_check:   Every 5 minutes  — check for steam moves
  - nightly_stats: Daily at 3 AM UTC — rebuild player stats cache

Run this as a SEPARATE process (not in the Streamlit app thread):
    python -m jobs.scheduler

Or integrate with your deployment setup (Railway worker, etc.)
"""

from __future__ import annotations

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("bullziq.scheduler")

try:
    from apscheduler.schedulers.blocking import BlockingScheduler
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    log.warning("APScheduler not installed. Install with: pip install apscheduler")


def job_refresh_odds() -> None:
    log.info("Running odds refresh job...")
    try:
        from scrapers.odds_api import refresh_all_odds
        n = refresh_all_odds()
        log.info(f"Odds refresh: {n} snapshots written")
    except Exception as exc:
        log.error(f"Odds refresh failed: {exc}")


def job_detect_steam() -> None:
    log.info("Running steam detection job...")
    try:
        from db.schema import SessionLocal, Match, OddsSnapshot, SteamEvent
        from datetime import timedelta

        STEAM_THRESHOLD_PCT = 3.0
        WINDOW_MINUTES = 30

        with SessionLocal() as s:
            upcoming_ids = [
                row[0] for row in s.query(Match.id).filter(Match.is_upcoming == True).all()
            ]
            if not upcoming_ids:
                return

            steam_count = 0
            now = datetime.utcnow()
            cutoff = now - timedelta(minutes=WINDOW_MINUTES)

            for mid in upcoming_ids:
                snaps = (
                    s.query(OddsSnapshot)
                    .filter(
                        OddsSnapshot.match_id == mid,
                        OddsSnapshot.snapshot_time >= cutoff,
                    )
                    .order_by(OddsSnapshot.snapshot_time)
                    .all()
                )
                if len(snaps) < 2:
                    continue

                first = snaps[0]
                latest = snaps[-1]
                shift = (latest.p1_implied - first.p1_implied) * 100

                if abs(shift) >= STEAM_THRESHOLD_PCT:
                    match = s.query(Match).get(mid)
                    direction = ""
                    if match:
                        from db.schema import Player
                        p1 = s.query(Player).get(match.player1_id)
                        p2 = s.query(Player).get(match.player2_id)
                        direction = (p1.name if shift > 0 else p2.name) if p1 and p2 else ""

                    steam = SteamEvent(
                        match_id=mid,
                        player_steamed=direction,
                        shift_pct=round(shift, 2),
                        opening_odds=first.p1_odds,
                        current_odds=latest.p1_odds,
                        opening_implied=first.p1_implied,
                        current_implied=latest.p1_implied,
                        detected_at=now,
                    )
                    s.add(steam)
                    steam_count += 1
                    log.info(f"Steam detected: match {mid}, shift {shift:+.2f}pp on {direction}")

            s.commit()
            log.info(f"Steam detection: {steam_count} events flagged")

    except Exception as exc:
        log.error(f"Steam detection failed: {exc}")


def job_nightly_stats() -> None:
    log.info("Running nightly stats rebuild...")
    try:
        from db.schema import SessionLocal, Player, Match, PlayerStatsCache
        from sqlalchemy import func

        with SessionLocal() as s:
            players = s.query(Player).all()
            updated = 0

            for player in players:
                recent_matches = (
                    s.query(Match)
                    .filter(
                        ((Match.player1_id == player.id) | (Match.player2_id == player.id)),
                        Match.is_upcoming == False,
                    )
                    .order_by(Match.match_date.desc())
                    .limit(20)
                    .all()
                )

                if not recent_matches:
                    continue

                wins = sum(1 for m in recent_matches if m.winner_id == player.id)
                win_rate = wins / len(recent_matches)

                avgs = [
                    m.avg_p1 if m.player1_id == player.id else m.avg_p2
                    for m in recent_matches[:10]
                    if (m.avg_p1 if m.player1_id == player.id else m.avg_p2) is not None
                ]
                avg_last10 = sum(avgs) / len(avgs) if avgs else player.avg_3dart

                existing = s.query(PlayerStatsCache).filter(
                    PlayerStatsCache.player_id == player.id
                ).first()

                if existing:
                    existing.win_rate_last20 = round(win_rate, 3)
                    existing.avg_3dart_last10 = round(avg_last10, 2)
                    existing.updated_at = datetime.utcnow()
                else:
                    s.add(PlayerStatsCache(
                        player_id=player.id,
                        win_rate_last20=round(win_rate, 3),
                        avg_3dart_last10=round(avg_last10, 2),
                        updated_at=datetime.utcnow(),
                    ))
                updated += 1

            s.commit()
            log.info(f"Nightly stats: updated {updated} player caches")

    except Exception as exc:
        log.error(f"Nightly stats rebuild failed: {exc}")


def run_scheduler() -> None:
    if not APSCHEDULER_AVAILABLE:
        log.error("Cannot start scheduler — APScheduler not installed.")
        return

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(job_refresh_odds, "interval", minutes=30, id="odds_refresh")
    scheduler.add_job(job_detect_steam, "interval", minutes=5, id="steam_check")
    scheduler.add_job(
        job_nightly_stats, "cron", hour=3, minute=0, id="nightly_stats"
    )

    log.info("BullzIQ scheduler starting...")
    log.info("  odds_refresh: every 30 minutes")
    log.info("  steam_check:  every 5 minutes")
    log.info("  nightly_stats: 03:00 UTC daily")

    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("Scheduler stopped.")


if __name__ == "__main__":
    run_scheduler()
