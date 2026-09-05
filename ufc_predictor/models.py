"""Plain data shapes. No behavior, just structure.

Phase 1 shapes (Event, Bout) are confirmed against a live run of
automation-lab/ufc-events-fights-fighters (mode=events, includeDetails=true):
each event record nests its full bout card under "bouts", and each bout has a
two-item "fighters" array. `raw` keeps the untouched source record for
anything not modeled yet.

Phase 2 shapes (PriorFight, FighterEnrichment, MatchupArtifact) describe the
deterministic enrichment artifact: a fighter's profile plus their last 3
fights before a given matchup, each with full granular per-fight detail (not
just totals - that detail is what surfaced real signal in testing, e.g. a
submission win despite losing every surface stat). These are assembled from
multiple Apify calls (fighters mode, fights mode, events mode) plus computed
recent-form/layoff math, so unlike Event/Bout they have no from_dict - their
construction logic is a later step, not a single-record parse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Bout:
    fighter_a: str
    fighter_b: str
    weight_class: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "Bout":
        fighters = record.get("fighters") or []
        names = [f.get("name", "?") for f in fighters if isinstance(f, dict)]
        while len(names) < 2:
            names.append("?")
        return cls(
            fighter_a=names[0],
            fighter_b=names[1],
            weight_class=record.get("weightClass") or "",
            raw=record,
        )


@dataclass
class Event:
    name: str
    date: str
    venue: str
    url: str
    bouts: list[Bout]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "Event":
        bouts = [Bout.from_dict(b) for b in record.get("bouts") or []]
        return cls(
            name=record.get("name") or "Unknown event",
            date=record.get("date") or "",
            venue=record.get("location") or "",
            url=record.get("url") or "",
            bouts=bouts,
            raw=record,
        )


@dataclass
class PriorFight:
    fight_id: str
    opponent_name: str
    opponent_id: str
    event_id: str
    event_name: str
    event_date: str
    result: str  # "win" | "loss" | "draw" | "no_contest"
    method: str
    method_details: str | None
    round: int
    time: str
    weight_class: str
    totals: dict[str, dict[str, str]]
    significant_strikes: dict[str, dict[str, str]]


@dataclass
class FighterEnrichment:
    fighter_id: str
    name: str
    nickname: str
    height: str
    reach: str
    stance: str
    age_at_fight: int
    record_entering: str
    streak_entering: tuple[str, int]  # (result_type, length); a draw/no_contest breaks the streak
    prior_fights: list[PriorFight]
    recent_form: dict[str, float | int]
    layoff_days_entering: int | None


@dataclass
class MatchupArtifact:
    event_id: str
    event_name: str
    event_date: str
    weight_class: str
    fighter_a: FighterEnrichment
    fighter_b: FighterEnrichment
    fetched_at: str
