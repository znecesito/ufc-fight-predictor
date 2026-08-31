"""Terminal menu: list upcoming events, pick one, show its fight card."""

from __future__ import annotations

from . import apify_source
from .apify_source import ApifySourceError
from .models import Bout, Event


def _prompt_choice(count: int) -> int:
    while True:
        raw = input(f"\nPick an event (1-{count}, or q to quit): ").strip().lower()
        if raw == "q":
            raise SystemExit(0)
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw) - 1
        print("Not a valid choice, try again.")


def _print_events(events: list[Event]) -> None:
    print("\nUpcoming UFC events:\n")
    for i, event in enumerate(events, start=1):
        line = f"  {i}. {event.name}"
        if event.date:
            line += f" — {event.date}"
        if event.venue:
            line += f" ({event.venue})"
        print(line)


def _print_card(event: Event, bouts: list[Bout]) -> None:
    print(f"\nFight card — {event.name}\n")
    if not bouts:
        print("  No bouts found.")
        return
    for bout in bouts:
        line = f"  {bout.fighter_a} vs. {bout.fighter_b}"
        if bout.weight_class:
            line += f"  [{bout.weight_class}]"
        print(line)


def run() -> None:
    try:
        raw_events = apify_source.get_upcoming_events(limit=5)
    except ApifySourceError as exc:
        print(f"Couldn't load upcoming events: {exc}")
        return

    events = [Event.from_dict(r) for r in raw_events]
    _print_events(events)
    choice = _prompt_choice(len(events))
    selected = events[choice]

    if not selected.url:
        print(f"\n{selected.name} has no source URL to look up its card — can't continue.")
        return

    try:
        raw_bouts = apify_source.get_event_card(selected.url)
    except ApifySourceError as exc:
        print(f"Couldn't load the fight card: {exc}")
        return

    bouts = [Bout.from_dict(r) for r in raw_bouts]
    _print_card(selected, bouts)
