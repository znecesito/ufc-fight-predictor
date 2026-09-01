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
