"""Wraps the automation-lab/ufc-events-fights-fighters Apify actor.

This is the only module in the app that knows it's talking to Apify.
Everything downstream works with plain dicts / dataclasses.
"""

from __future__ import annotations

import os

from apify_client import ApifyClient

ACTOR_ID = "automation-lab/ufc-events-fights-fighters"


class ApifySourceError(RuntimeError):
    """Raised when the actor run fails, is misconfigured, or returns nothing usable."""


def _get_client() -> ApifyClient:
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        raise ApifySourceError(
            "APIFY_API_TOKEN is not set. Copy .env.example to .env and add your Apify API token."
        )
    return ApifyClient(token)


def _run_actor(run_input: dict) -> list[dict]:
    client = _get_client()
    try:
        run = client.actor(ACTOR_ID).call(run_input=run_input)
    except Exception as exc:
        raise ApifySourceError(f"Apify actor run failed: {exc}") from exc

    if not run or not run.default_dataset_id:
        raise ApifySourceError("Apify actor run did not return a dataset.")

    return client.dataset(run.default_dataset_id).list_items().items


def get_upcoming_events(limit: int = 5) -> list[dict]:
    """Return the next `limit` upcoming UFC events, each with its full bout card nested under "bouts"."""
    items = _run_actor(
        {
            "mode": "events",
            "eventStatus": "upcoming",
            "includeDetails": True,
            "maxItems": limit,
        }
    )
    if not items:
        raise ApifySourceError("No upcoming events were returned.")
    return items


def get_fighter_profile(fighter_url: str) -> dict:
    """Return the full profile record for a single fighter."""
    items = _run_actor(
        {
            "mode": "fighters",
            "startUrls": [{"url": fighter_url}],
            "includeDetails": True,
            "maxItems": 1,
        }
    )
    if not items:
        raise ApifySourceError("No fighter profile was returned.")
    return items[0]


def get_fight_detail(fight_url: str) -> dict:
    """Return the full detail record for a single fight."""
    items = _run_actor(
        {
            "mode": "fights",
            "eventStatus": "all",
            "startUrls": [{"url": fight_url}],
            "includeDetails": True,
            "maxItems": 1,
        }
    )
    if not items:
        raise ApifySourceError("No fight detail was returned.")
    return items[0]


def get_event_detail(event_url: str) -> dict:
    """Return the event record for a single event.

    Uses `includeDetails: False` and `events` mode specifically: the `date`
    field inside a `fights`-mode response's nested `event` object always
    comes back null (a verified actor bug), but calling `events` mode
    directly on the same event's URL reliably returns the real date. This
    function exists to backfill that date, not to fetch bout details.
    """
    items = _run_actor(
        {
            "mode": "events",
            "eventStatus": "all",
            "startUrls": [{"url": event_url}],
            "includeDetails": False,
            "maxItems": 1,
        }
    )
    if not items:
        raise ApifySourceError("No event detail was returned.")
    return items[0]
