"""Terminal menu: list upcoming events, pick one, show its fight card."""

from __future__ import annotations

from . import apify_source
from .apify_source import ApifySourceError
from .models import Event


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


def _print_card(event: Event) -> None:
    print(f"\nFight card — {event.name}\n")
    if not event.bouts:
        print("  No bouts found.")
        return
    for bout in event.bouts:
        line = f"  {bout.fighter_a} vs. {bout.fighter_b}"
        if bout.weight_class:
            line += f"  [{bout.weight_class}]"
        print(line)


def _prompt_bout_choice(count: int) -> int | None:
    while True:
        raw = input(
            f"\nPick a bout to analyze (1-{count}, or s to skip): "
        ).strip().lower()
        if raw == "" or raw == "s":
            return None
        if raw.isdigit() and 1 <= int(raw) <= count:
            return int(raw) - 1
        print("Not a valid choice, try again.")


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
    _print_card(selected)

    if not selected.bouts:
        return

    bout_choice = _prompt_bout_choice(len(selected.bouts))
    if bout_choice is None:
        return

    bout = selected.bouts[bout_choice]
    fighters = bout.raw.get("fighters") or []
    if len(fighters) < 2:
        print("Couldn't build a matchup: this bout is missing fighter data.")
        return
    fighter_a_url = fighters[0].get("url")
    fighter_b_url = fighters[1].get("url")

    from ufc_predictor.assembly import build_matchup_artifact
    from ufc_predictor.reporting import format_matchup_artifact

    try:
        artifact = build_matchup_artifact(fighter_a_url, fighter_b_url, selected.url)
    except ApifySourceError as exc:
        print(f"Couldn't build the matchup: {exc}")
        return

    print(format_matchup_artifact(artifact))
