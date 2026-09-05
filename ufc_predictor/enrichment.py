"""Pure computation logic for Phase 2 enrichment.

Everything here operates on raw dicts already fetched from Apify (fighters
mode `fightHistory` entries) - no network calls, no Apify client usage. This
is the by-hand math from three blind-test scratch sessions ported into real,
tested functions: locating the prior-N fights before a given matchup, and
deriving record/streak/recent-form/layoff numbers from them.
"""

from __future__ import annotations

from datetime import date
from typing import Any


def _fighter_index(fight: dict[str, Any], fighter_name: str) -> int:
    for i, entry in enumerate(fight.get("fighters") or []):
        if entry.get("name") == fighter_name:
            return i
    raise ValueError(f"{fighter_name!r} not found in fight {fight.get('id')!r}")


def _parse_time(time_str: str) -> int:
    minutes, seconds = time_str.split(":")
    return int(minutes) * 60 + int(seconds)


def find_prior_fights(
    fight_history: list[dict[str, Any]], opponent_name: str, limit: int = 3
) -> list[dict[str, Any]]:
    target_index = None
    for i, fight in enumerate(fight_history):
        names = [f.get("name") for f in fight.get("fighters") or []]
        if opponent_name in names:
            target_index = i
            break
    if target_index is None:
        return []
    return fight_history[target_index + 1 : target_index + 1 + limit]


def compute_record_entering(fighter_name: str, prior_fights: list[dict[str, Any]]) -> str:
    wins = 0
    losses = 0
    for fight in prior_fights:
        idx = _fighter_index(fight, fighter_name)
        result = fight["result"][idx]
        if result == "win":
            wins += 1
        elif result == "loss":
            losses += 1
    return f"{wins}-{losses}"


def compute_streak_entering(
    fighter_name: str, prior_fights: list[dict[str, Any]]
) -> tuple[str, int]:
    if not prior_fights:
        return ("none", 0)
    streak_type: str | None = None
    count = 0
    for fight in prior_fights:
        idx = _fighter_index(fight, fighter_name)
        result = fight["result"][idx]
        if result not in ("win", "loss"):
            break
        if streak_type is None:
            streak_type = result
        elif result != streak_type:
            break
        count += 1
    if streak_type is None:
        return ("none", 0)
    return (streak_type, count)


def compute_recent_form(fighter_name: str, prior_fights: list[dict[str, Any]]) -> dict[str, float | int]:
    if not prior_fights:
        return {
            "fights_considered": 0,
            "slpm": 0.0,
            "sapm": 0.0,
            "td_avg_per_15": 0.0,
            "kd_total": 0,
            "finishes": 0,
        }

    total_seconds = 0
    strikes_for = 0
    strikes_against = 0
    takedowns_for = 0
    knockdowns_total = 0
    finishes = 0

    for fight in prior_fights:
        idx = _fighter_index(fight, fighter_name)
        opp_idx = 1 - idx
        total_seconds += (fight["round"] - 1) * 5 * 60 + _parse_time(fight["time"])
        strikes_for += int(fight["significantStrikes"][idx])
        strikes_against += int(fight["significantStrikes"][opp_idx])
        takedowns_for += int(fight["takedowns"][idx])
        knockdowns_total += int(fight["knockdowns"][idx])
        if fight["result"][idx] == "win" and fight.get("method") in ("KO/TKO", "SUB"):
            finishes += 1

    minutes = total_seconds / 60
    if minutes <= 0:
        slpm = sapm = td_avg_per_15 = 0.0
    else:
        slpm = strikes_for / minutes
        sapm = strikes_against / minutes
        td_avg_per_15 = (takedowns_for / minutes) * 15

    return {
        "fights_considered": len(prior_fights),
        "slpm": slpm,
        "sapm": sapm,
        "td_avg_per_15": td_avg_per_15,
        "kd_total": knockdowns_total,
        "finishes": finishes,
    }


def compute_layoff_days(
    prior_fights: list[dict[str, Any]],
    target_event_date: str,
    event_dates: dict[str, str],
) -> int | None:
    if not prior_fights:
        return None
    most_recent = prior_fights[0]
    date_str = event_dates.get(most_recent.get("id"))
    if date_str is None:
        return None
    previous_date = date.fromisoformat(date_str)
    target_date = date.fromisoformat(target_event_date)
    return (target_date - previous_date).days
