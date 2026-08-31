# Phase 1: Event & Fighter Listing — Design

## Purpose

First working slice of the UFC Fight Predictor. A terminal Python app that:

1. Lists the next few upcoming UFC events.
2. Lets the user pick one.
3. Lists the fighters (bouts) on that event's card.

This is deliberately scoped down from the original Phase 1 idea — pulling each
fighter's full stats and fight history is explicitly **out of scope** here and
deferred to a later phase. Phase 1 only lists who's fighting.

As with the rest of this project, the point is to build real backend
engineering skill in stages, not just to end up with a working app (see
`LEARNING-APPROACH.md`).

## Data source

**Apify actor: `automation-lab/ufc-events-fights-fighters`**

Chosen after confirming `ufcstats.com` (the canonical UFC data source that
every open-source scraper and most other Apify actors are built on) now sits
behind a JS proof-of-work bot-check, which rules out a plain `requests`-based
scraper without a headless browser. This actor already handles that, and its
input schema covers everything Phase 1 (and later phases) need from one
source:

- `mode`: `events` | `fights` | `fighters`
- `eventStatus`: `completed` | `upcoming` | `all`
- `startUrls`: explicit ufcstats.com event/fight/fighter URLs
- `fighterSearch`: fighter name lookup (not used in Phase 1 — see below)
- `includeDetails`: fetch full bout cards / stats tables

Other actors considered and rejected for Phase 1's needs:
- `parseforge/ufc-stats-scraper` — no upcoming-event or per-event fighter
  listing support (historical-only, filtered by surname letter).
- `crawlerbros/ufc-stats-scraper` — uses ESPN's API, no upcoming events, no
  detailed per-fight stats.
- `parseforge/sherdog-scraper` — does support upcoming shows, but is a
  separate data source (Sherdog, not ufcstats) with less detailed stats;
  not needed since automation-lab's actor already covers upcoming events.

Auth: `APIFY_API_TOKEN` read from environment (`.env`, via `python-dotenv`).
`.env` is gitignored; `.env.example` documents the variable name.

## Components

```
ufc_predictor/
  apify_source.py   — wraps the actor: get_upcoming_events(), get_event_card(event_url)
  models.py         — Event, Bout dataclasses
  cli.py            — list events -> pick by number -> show fighters on that card
main.py             — entrypoint
.env.example        — APIFY_API_TOKEN placeholder
```

- **`apify_source.py`** is the only module that talks to Apify. It knows how
  to run the actor with given input, poll for completion, and return dataset
  items as plain dicts. Nothing else in the app knows this is Apify
  specifically — swapping the data source later (e.g. a self-built scraper)
  only touches this file.
- **`models.py`** is plain dataclasses, no behavior:
  - `Event`: name, date, venue, status, url
  - `Bout`: fighter_a_name, fighter_b_name, weight_class, card_position
- **`cli.py`** owns the step order: list → pick → list card → render. No
  network calls of its own — it calls into `apify_source`.

No persistence layer in Phase 1. No `Fighter` model or fighter-detail fetch
yet — that's Phase 2's job, once fighter stats/history are back in scope,
along with the caching/staleness design that goes with it (avoiding a full
re-scrape of a fighter who hasn't fought since the last time we looked).

## Data flow

1. `cli.py` calls `apify_source.get_upcoming_events(limit=5)`
   (`mode=events`, `eventStatus=upcoming`). Always a live call — the "what's
   next" list changes as events get scheduled, and it's cheap.
2. User is shown the events with a number to pick from; they type a number.
3. `cli.py` calls `apify_source.get_event_card(event_url)`
   (`mode=fights`, `startUrls=[event_url]`). Live call, returns bout rows.
4. `cli.py` prints the card: fighter vs. fighter, weight class, per bout, in
   card order.

Two live Apify calls per run. No caching needed yet since nothing here is
expensive enough, or stable enough, to be worth persisting.

## Error handling

- Missing `APIFY_API_TOKEN` — clear startup error, not a stack trace, telling
  the user to set it.
- Actor run fails or times out — surface Apify's own error message and exit;
  no silent retries or fallback data for Phase 1.
- No upcoming events returned — tell the user plainly (rare edge case).

## Testing

`apify_source.py` is the only network-touching module. `models.py` and
`cli.py`'s rendering logic can be unit-tested against fixture JSON (a
recorded example dataset) without hitting Apify or spending money on actor
runs.

## Explicitly out of scope for Phase 1

- Fighter profile / fight history scraping (Phase 2)
- Local caching and staleness/refresh logic (Phase 2, once there's
  fighter data worth caching)
- The non-deterministic LLM scouting report (later phase, after fighter
  data exists)
