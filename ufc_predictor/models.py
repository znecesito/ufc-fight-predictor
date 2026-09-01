"""Plain data shapes for Phase 1. No behavior, just structure.

Field names confirmed against a live run of automation-lab/ufc-events-fights-fighters
(mode=events, includeDetails=true): each event record nests its full bout card
under "bouts", and each bout has a two-item "fighters" array. `raw` keeps the
untouched source record for anything not modeled yet.
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
