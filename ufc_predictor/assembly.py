"""Wires apify_source, enrichment, and models together into finished artifacts.

This module owns no logic of its own beyond orchestration: it calls
apify_source for raw data, enrichment for the pure record/streak/recent-form/
layoff math, and assembles the results into the models.py dataclasses. It
never talks to Apify directly by inventing its own actor calls, and it never
reimplements enrichment's math.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from . import apify_source, enrichment
from .models import FighterEnrichment, MatchupArtifact, PriorFight


def _compute_age(date_of_birth: str, target_event_date: str) -> int:
    dob = date.fromisoformat(date_of_birth)
    target = date.fromisoformat(target_event_date)
    age = target.year - dob.year
    if (target.month, target.day) < (dob.month, dob.day):
        age -= 1
    return age


def _fighter_and_opponent_index(entry: dict[str, Any], fighter_name: str) -> tuple[int, int]:
    names = [f.get("name") for f in entry.get("fighters") or []]
    idx = names.index(fighter_name)
    opp_idx = 1 - idx
    return idx, opp_idx


def _build_prior_fight(entry: dict[str, Any], fighter_name: str) -> tuple[PriorFight, str]:
    """Build a fully-enriched PriorFight from a raw fightHistory entry.

    Returns the PriorFight plus the real event date, so callers can also
    populate the `event_dates` map that `compute_layoff_days` needs.
    """
    idx, opp_idx = _fighter_and_opponent_index(entry, fighter_name)
    opponent = (entry.get("fighters") or [])[opp_idx]
    result = (entry.get("result") or [])[idx]

    detail = apify_source.get_fight_detail(entry["url"])
    event_url = detail["event"]["url"]
    event_detail = apify_source.get_event_detail(event_url)
    event_date = event_detail.get("date") or ""

    prior_fight = PriorFight(
        fight_id=entry.get("id") or "",
        opponent_name=opponent.get("name") or "",
        opponent_id=opponent.get("id") or "",
        event_id=event_detail.get("id") or event_detail.get("sourceId") or "",
        event_name=event_detail.get("name") or "",
        event_date=event_date,
        result=result,
        method=detail.get("method") or "",
        method_details=detail.get("methodDetails"),
        round=detail.get("round"),
        time=detail.get("time") or "",
        weight_class=detail.get("weightClass") or "",
        totals=detail.get("totals") or {},
        significant_strikes=detail.get("significantStrikes") or {},
    )
    return prior_fight, event_date


def build_fighter_enrichment(
    fighter_url: str, opponent_name: str, target_event_date: str
) -> FighterEnrichment:
    profile = apify_source.get_fighter_profile(fighter_url)
    fighter_name = profile.get("name") or ""

    raw_prior = enrichment.find_prior_fights(
        profile.get("fightHistory") or [], opponent_name, limit=3
    )

    record_entering = enrichment.compute_record_entering(fighter_name, raw_prior)
    streak_entering = enrichment.compute_streak_entering(fighter_name, raw_prior)
    recent_form = enrichment.compute_recent_form(fighter_name, raw_prior)

    prior_fights: list[PriorFight] = []
    event_dates: dict[str, str] = {}
    for entry in raw_prior:
        prior_fight, event_date = _build_prior_fight(entry, fighter_name)
        prior_fights.append(prior_fight)
        event_dates[entry.get("id")] = event_date

    layoff_days_entering = enrichment.compute_layoff_days(
        raw_prior, target_event_date, event_dates
    )

    age_at_fight = _compute_age(profile.get("dateOfBirth") or "", target_event_date)

    return FighterEnrichment(
        fighter_id=profile.get("id") or profile.get("sourceId") or "",
        name=fighter_name,
        nickname=profile.get("nickname") or "",
        height=profile.get("height") or "",
        reach=profile.get("reach") or "",
        stance=profile.get("stance") or "",
        age_at_fight=age_at_fight,
        record_entering=record_entering,
        streak_entering=streak_entering,
        prior_fights=prior_fights,
        recent_form=recent_form,
        layoff_days_entering=layoff_days_entering,
    )


def _find_bout(event: dict[str, Any], fighter_a_url: str, fighter_b_url: str) -> dict[str, Any]:
    for bout in event.get("bouts") or []:
        urls = [f.get("url") for f in bout.get("fighters") or []]
        if fighter_a_url in urls and fighter_b_url in urls:
            return bout
    raise ValueError(
        f"No bout found in event {event.get('url')!r} containing both "
        f"{fighter_a_url!r} and {fighter_b_url!r}"
    )


def _fighter_name_by_url(bout: dict[str, Any], fighter_url: str) -> str:
    for f in bout.get("fighters") or []:
        if f.get("url") == fighter_url:
            return f.get("name") or ""
    raise ValueError(f"Fighter url {fighter_url!r} not found in bout")


def build_matchup_artifact(
    fighter_a_url: str, fighter_b_url: str, event_url: str
) -> MatchupArtifact:
    event = apify_source.get_event_detail(event_url)
    bout = _find_bout(event, fighter_a_url, fighter_b_url)

    fighter_a_name = _fighter_name_by_url(bout, fighter_a_url)
    fighter_b_name = _fighter_name_by_url(bout, fighter_b_url)
    weight_class = bout.get("weightClass") or ""

    event_date = event.get("date") or ""

    fighter_a = build_fighter_enrichment(
        fighter_a_url, opponent_name=fighter_b_name, target_event_date=event_date
    )
    fighter_b = build_fighter_enrichment(
        fighter_b_url, opponent_name=fighter_a_name, target_event_date=event_date
    )

    return MatchupArtifact(
        event_id=event.get("id") or event.get("sourceId") or "",
        event_name=event.get("name") or "",
        event_date=event_date,
        weight_class=weight_class,
        fighter_a=fighter_a,
        fighter_b=fighter_b,
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )
