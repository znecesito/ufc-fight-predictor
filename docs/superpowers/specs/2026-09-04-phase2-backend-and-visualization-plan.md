# Phase 2 Backend Scaffold + Visualization Design

Status: design/research only. Nothing in this doc is built yet.

## Why this exists

Two threads converged in the same conversation: (1) research into how the
eventual scouting-report UI should look, and (2) the realization that we
can't build that UI yet — the deterministic data pipeline behind it
("Phase 2") has only ever been run as one-off scratch scripts, never as
real app code, and its output schema is still actively changing. This doc
captures both, in the order they actually need to happen: **Phase 2
(backend) first, then the visualization phases.**

## Visualization research (not yet built)

Researched how to visualize a two-fighter scouting report combining
deterministic stats with a separate AI-generated prediction, wanting lots
of graphs/animation but staying easy to follow.

**Key findings:**

- **Head-to-head layout**: use the real MMA broadcast convention — a
  side-by-side "Tale of the Tape" (two columns, stat tiles/bars), not a
  redesign of what we already built. The deeper "Uber Tale of the Tape"
  variant (analyst Reed Kuhn) goes further per-metric: age, knockdowns,
  accuracy, defense, takedown success side by side.
  ([Martial Arts Insider](https://martialartsinsider.com/blogs/mma/tale-of-the-tape-ufc),
  [MMAOddsBreaker](https://www.mmaoddsbreaker.com/articles/fightnomics-statistics/157265-uber-tales-of-the-tape-for-ufc-275/))
- **Skip radar/spider charts.** Tempting for "lots of graphs," but they
  actively mislead with mixed-unit stats (%, per-minute rates, counts) and
  are explicitly bad for anything time-based (our strike-trend chart).
  Use small multiples (a mini-chart per stat) or bar-per-metric instead;
  keep line charts for anything over time.
  ([Highcharts](https://www.highcharts.com/blog/tutorials/radar-chart-explained-when-they-work-when-they-fail-and-how-to-use-them-right/))
- **Animation model: scrollytelling, not decorative motion.** One insight
  revealed per scroll step, muted secondary elements so the focal point
  draws the eye, animated transitions between chart states so the reader
  watches change happen rather than reconstructing it from two static
  charts. This is the mechanism for "lots of animation, still legible."
  ([Flourish](https://flourish.studio/blog/scrollytelling-examples/))
- **Every stat needs room for its caveat next to it**, not buried in a
  footnote — "a statistic is context, not a prophecy." Recency, opponent
  quality, and sample size all need a place in the layout.
  ([Fight Matrix, Aug 2026](https://www.fightmatrix.com/2026/08/31/from-the-tale-of-the-tape-to-the-roulette-table-why-numbers-drive-the-experience/))
- **"Disclosure" is a named UI pattern for the deterministic-vs-AI-prediction
  problem**: a persistent visual container/header for the prediction zone,
  verb-based labeling ("Claude's read," not a generic "AI" badge), and
  optionally a distinct type treatment (iA Writer greys out
  unverified/synthetic text) so the reader's eye registers "different kind
  of claim" before reading it.
  ([ShapeofAI.com](https://www.shapeof.ai/patterns/disclosure))

**Recommendation:** side-by-side Tale-of-the-Tape stat tiles/bars (not
radar charts) for the head-to-head comparison, small multiples for
mixed-unit stats, line charts for anything over time, scrollytelling
sequencing for the animation layer, and a persistently-styled "Disclosure"
zone for the prediction section.

### Draft visualization implementation phases (for later — depends on Phase 2 backend existing first)

- **Phase A** — formalize the single-fighter template (placard, stat
  tiles, strike-trend chart, fight-history table) from a one-off artifact
  into a reusable, data-driven component. Can be built against fixture
  JSON.
- **Phase B** — two-fighter head-to-head layout: two-column stat
  tiles/bars, small multiples instead of radar charts, both fighters'
  strike-trend lines on one chart. Also fixture-buildable.
- **Phase C** — scrollytelling sequencing on top of the now-static Phase B
  layout: staggered reveals, muted-until-relevant styling, animated
  chart-state transitions. Presentation only, no new data.
- **Phase D** — the "Disclosure"-pattern prediction section, plus wiring
  the whole report to real Apify-sourced data (via the Phase 2 pipeline
  below) instead of fixtures, plus integrating the prediction step's
  output once that exists.

## Phase 2: backend scaffold ("walking skeleton") — the actual next step

Goal: turn everything we've been doing by hand in scratch scripts across
three blind tests into real, tested app code, exposed through the
existing terminal CLI as a bare-bones "walking skeleton" (a tracer-bullet
end-to-end path, proven before any UI polish).

Ordered to front-load what we're already 100% confident in (verified by
hand three times this session) and push the one genuinely new, unverified
part (live wiring) to the end:

1. **Settle the artifact schema first** — a decision, not code: what
   fields does one fighter's enrichment record have (profile, physical
   stats, last-3-fights with granular stats + event date, computed
   recent-form numbers, computed layoff). Unblocks everything below.
2. **Pure computation logic, fixture-tested, no network.** Port the
   by-hand logic into real functions: find-target-fight-and-take-prior-N,
   recent-form math (SLpM/SApM/streak/finish-rate), layoff/frequency from
   event dates. Test against the JSON already saved from the three blind
   tests — we already know the correct answers, so these tests write
   themselves.
3. **Network-fetching functions** — extend `apify_source.py` with fighter/
   fight/event lookups, mirroring the existing Phase 1 pattern. Mocked in
   tests the same way.
4. **Assembly** — one function wiring 2+3 together: given two fighters,
   produce the one artifact record from step 1.
5. **CLI wiring (the actual skeleton)** — extend the existing terminal
   app: after picking an event/fight, run step 4, print the raw artifact.
   The only step touching real, live Apify calls end-to-end.
6. **Persistence — deferred**, added as its own follow-up slice once the
   artifact shape has proven stable, same reasoning as Phase 1's deferred
   persistence. Wires into the already-approved SQLite design.

## Not yet decided

- The actual artifact schema fields (step 1 above) — the next concrete
  decision to make before writing any code.
