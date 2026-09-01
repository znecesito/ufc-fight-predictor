# Persistence + Freshness Cache — Design (approved, not yet built)

Status: design approved in conversation on 2026-08-31. **Not implemented yet** —
user wants to dissect the Apify results further before building. This doc
exists so the design isn't lost in the meantime.

## Problem

Phase 1 makes a live Apify call every single run and discards the result the
moment the program exits. That's wasteful (re-paying for the same data) and
leaves no durable record of anything the app has ever fetched.

## Design

1. **New `ufc_predictor/db.py`** — the only module that talks to storage.
   SQLite file (`ufc_predictor.db`, gitignored like `.env`), two tables:
   - `events`: id (ufcstats sourceId), name, date, venue, url, fetched_at
   - `bouts`: id (ufcstats sourceId), event_id (FK), fighter_a, fighter_b,
     weight_class
   Plain, portable SQL — no SQLite-only syntax — so the eventual move to a
   hosted Postgres instance (Neon or Supabase, both cheap/free-tier, both
   speak near-identical SQL) is a small connection-string change, not a
   rewrite. This is the standard scaling path for "make this usable by
   other people" — SQLite is single-machine only, Postgres is a real
   client-server DB reachable over a network.

2. **Upsert by ufcstats sourceId** on every save — re-fetching the same
   event overwrites its row instead of accumulating duplicates.

3. **Save immediately after fetching, before displaying** — so a crash or
   Ctrl+C right after a fetch doesn't lose the data that was already pulled.

4. **Sort fix (bundled into the same change):** `apify_source.get_upcoming_events`
   currently trusts the actor's return order. Every run so far has
   happened to come back in date order, but nothing guarantees that. Fix:
   explicitly sort parsed events by date ascending before returning, so
   list position #1 is *always* the genuinely soonest event, by
   construction — not by luck.

5. **Freshness gate (avoid re-paying Apify for calls we don't need):**
   Before calling Apify, check the newest `fetched_at` already stored.
   Skip the live call and read from SQLite instead **unless a Sunday
   midnight has passed since that last fetch** — i.e., the cache is valid
   for the whole week and only forced stale once the current fight
   weekend has concluded (since that's the only point at which "what's
   next" could actually have changed). A `--refresh` CLI flag forces a
   live call regardless, for when the user knows something changed (e.g.
   a newly announced card) ahead of that boundary.

   Concretely: compute the next Sunday 00:00 strictly after `fetched_at`;
   if `now` is before that boundary, reuse the cached data.

## Explicitly not decided/built yet

- Whether to also persist fighter-mode data (Phase 2 concern, once that
  mode is actually called)
- Any Postgres/deployment code — only the design intent is captured here;
  nothing beyond SQLite gets built until deployment is real
