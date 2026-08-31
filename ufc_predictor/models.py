"""Plain data shapes for Phase 1. No behavior, just structure.

Field names in the actor's dataset records aren't documented anywhere beyond
its description, so `from_dict` tries a handful of likely key spellings and
falls back gracefully. `raw` keeps the untouched source record so real field
names can be confirmed (and this parsing tightened) against a live run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _first(record: dict, *keys: str, default: str = "") -> str:
    for key in keys:
        value = record.get(key)
        if value not in (None, ""):
            return str(value)
    return default


@dataclass
class Event:
    name: str
    date: str
    venue: str
    url: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "Event":
        return cls(
            name=_first(record, "name", "eventName", "title", default="Unknown event"),
            date=_first(record, "date", "eventDate"),
            venue=_first(record, "venue", "location"),
            url=_first(record, "url", "eventUrl", "sourceUrl"),
            raw=record,
        )


@dataclass
class Bout:
    fighter_a: str
    fighter_b: str
    weight_class: str
    card_position: str
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(cls, record: dict[str, Any]) -> "Bout":
        return cls(
            fighter_a=_first(
                record, "fighterAName", "redFighter", "fighter1Name", "fighterA", default="?"
            ),
            fighter_b=_first(
                record, "fighterBName", "blueFighter", "fighter2Name", "fighterB", default="?"
            ),
            weight_class=_first(record, "weightClass", "division"),
            card_position=_first(record, "cardSegment", "cardPosition", "billing"),
            raw=record,
        )
