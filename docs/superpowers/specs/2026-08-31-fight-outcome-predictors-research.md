# Fight Outcome Predictors — Research + Apify Data-Gap Check

Status: research complete, informing Phase 2 design. No code built from this yet.

## Why this exists

Before building the app further, we need to know (1) which fighter stats
actually predict fight outcomes, per real research, and (2) whether our
Apify actor (`automation-lab/ufc-events-fights-fighters`) can actually supply
those stats. The goal is a **deterministic** data-gathering pipeline (Apify
→ local DB) that produces a stored "artifact" per fighter/matchup, which a
**separate, non-deterministic** LLM step then turns into a scouting-style
prediction, guided by written MD instructions. This doc solidifies the data
side before that MD-instructions design is written.

## Research: what actually predicts fight outcomes

**TL;DR:** Striking-volume/accuracy differentials and takedown metrics are
the most consistently-cited predictors, age has a real-but-small effect,
reach is a weak standalone predictor (except heavyweight), and recent-form/
streak data outperforms full-career averages — using lifetime stats instead
of rolling recent-form is a specific, named methodological mistake that
inflates backtested accuracy without reflecting real predictive power.

### Key findings

- **A real, concrete feature-importance ranking** comes from a Stanford
  CS229 study ([McQuaide, Stanford](https://cs229.stanford.edu/proj2019aut/data/assignment_308832_raw/26647731.pdf)),
  134 features, 3,355 fights, scraped from ufcstats.com (the same
  underlying source we use). Its Gradient Boosting model's top features, in
  order: opponent's average significant strikes landed against this fighter
  (a durability/strikes-absorbed proxy), both fighters' age, significant
  strike percentage, total strikes landed, takedown percentage, then
  strike-location breakdowns (head/body landed, distance landed). A second
  model in the same paper surfaced win/loss streaks, career win counts, and
  finish-method history (decision type, KO/TKO, submission rate) as
  significant — reach appeared, but far down the list.
- **Age**: real but small. [AgentMMA, citing a 2,229-bout study](https://agentmma.com/mma-lab/ufc-fighter-peak-age):
  winners average 29.8 vs. 30.7 for losers — a 0.82-year gap, explicitly
  described as a small effect that "should adjust predictions modestly
  rather than determine outcomes."
- **Reach**: weak standalone predictor. [Same source](https://agentmma.com/mma-lab/ufc-reach-advantage):
  longer-reach fighters won only 51.65% of the time overall; heavyweight was
  the only division with a real effect. A cited academic source (Barley et
  al.) found reach explained only 1.6–2.0% of variance in punch type.
- **Recent form > career average, methodologically.** One source flagged
  that studies using full-career stats saw accuracy inflated by 6–9
  percentage points vs. rolling/recent-form features — a data-leakage
  artifact, not real signal. This is the single most actionable methodology
  point for our own design.
- **Established reference methodology**: MMA-specific Elo/Glicko rating
  systems exist (e.g. [Fight Matrix](https://www.fightmatrix.com/faq/),
  K-factor 170) as an alternative/complementary approach to raw-stat
  regression — win/loss history only, no fighter stats. Worth knowing as a
  fallback framing, not something we're building now.
- **Known limitations**: small per-fighter sample sizes (most fighters have
  single-digit-to-low-double-digit UFC fights, unlike large ML datasets);
  judge scoring inconsistency for decisions; best published accuracies
  cluster around **~60–65%**, not dramatically better than a red-corner-only
  heuristic (62.6% win rate for the red corner in the CS229 dataset) — a
  real ceiling to set expectations against, and a reminder that "the model
  is usually right" is not the same as "the model beats a coin flip by
  much."

### Sources

1. [Applying Machine Learning Algorithms to Predict UFC Fight Outcomes (Stanford CS229)](https://cs229.stanford.edu/proj2019aut/data/assignment_308832_raw/26647731.pdf)
2. [Artificial Intelligence in UFC Outcome Prediction and Fighter Strategies Optimization (ACM, 2024)](https://dl.acm.org/doi/10.1145/3696952.3696966)
3. [A Comparative Study of Machine Learning Algorithms for Prior Prediction of UFC Fights](https://link.springer.com/chapter/10.1007/978-981-13-0761-4_7)
4. [What Age Do UFC Fighters Peak? Data by Weight Class (AgentMMA)](https://agentmma.com/mma-lab/ufc-fighter-peak-age)
5. [UFC Reach Advantage (AgentMMA)](https://agentmma.com/mma-lab/ufc-reach-advantage)
6. [How Does an AI UFC Prediction Model Actually Work? (AgentMMA)](https://agentmma.com/mma-lab/ai-ufc-prediction-model)
7. [Ranking MMA fighters using the Elo rating system (Medium)](https://medium.com/geekculture/ranking-mma-fighters-using-the-elo-rating-system-2704adbf0c94)
8. [Fight Matrix FAQ](https://www.fightmatrix.com/faq/)
9. [Exploring Patterns and Predictors in UFC Fight Outcomes (CMU capstone)](https://www.stat.cmu.edu/capstoneresearch/fall2024/315files_f24/team11.html)
10. [Improving MMA judging with consensus scoring (arXiv)](https://arxiv.org/pdf/2401.03280)
11. [WarrierRajeev/UFC-Predictions (GitHub)](https://github.com/WarrierRajeev/UFC-Predictions)
12. [How Predictive Analytics Is Changing UFC Betting in 2026 (Fight Matrix)](https://www.fightmatrix.com/2025/12/17/how-predictive-analytics-is-changing-ufc-betting-in-2026/) — note: prediction-market-style source, specific win-rate figures here are lower-confidence than the academic sources above.

## Empirical check: does our Apify actor supply this? (not web research — tested directly)

Tested three call shapes against `automation-lab/ufc-events-fights-fighters`
directly (real calls, real fighter: Dan Hooker). **No single call satisfies
the research above — it takes a combination of the actor's own modes at
increasing depth:**

| Data need (from research) | `events` mode | `fighters` mode | `fights` mode (on one specific completed fight URL) |
|---|---|---|---|
| Physical stats, stance, age | — | ✅ | — |
| Career-average SLpM/SApM/Str Acc/Def/TD stats | — | ✅ (career-long only, **not rolling**) | — |
| Win/loss/method per past fight | — | ✅ (totals only) | ✅ |
| Strike breakdown by target (head/body/leg) & position (distance/clinch/ground) | ❌ | ❌ | ✅ |
| Takedown %, control time | ❌ | ❌ | ✅ |
| Method detail (e.g. "Punches to Head From Mount"), referee | ❌ | ❌ | ✅ |
| Per-fight date (for recency/layoff) | ✅ (for the event itself) | ❌ | ❌ (came back `null` here — but see correction below) |
| Current win/loss streak | — | derivable ourselves (fightHistory is ordered) | — |
| Title-bout flag, opponent quality/ranking-at-time | ❌ | ❌ | ❌ |
| Red/blue corner assignment | ❌ | ❌ | ❌ (only "W"/"L" per fighter, no corner label) |

**The concrete discovery:** `fighters` mode's embedded `fightHistory` is a
*trimmed summary* — confirmed by exhaustively diffing keys across every
record in the archive, no location/control-time data exists there. But
calling `fights` mode again on one specific **completed** fight's URL (e.g.
Hooker vs. Saint Denis, `http://ufcstats.com/fight-details/a7ae8f6eb5fc3a79`)
returns the full breakdown research says matters most: head/body/leg
landed-of-attempted, distance/clinch/ground, TD%, control time. That data
genuinely exists on this source; the fighter-level summary just doesn't
carry it forward.

**Second confirmed instance of the same bug pattern (2026-09-01):**
`weightClass` inside `fighters` mode's embedded `fightHistory` also always
comes back `null` — verified across every entry for two fighters (Jacob
Malkoun: 9 fights, Torrez Finney: 5 fights), zero exceptions. Same fix as
the date bug: the real value is available from `events` mode (their bout
was correctly tagged `"weightClass": "Middleweight"` in the UFC 325 card
pull) or from a direct `fights`-mode call on that fight's URL. **General
rule going forward: treat `fighters` mode's embedded fight-history summary
as identity/result-only — pull date and weight class from `events` or
`fights` mode instead whenever they matter.**

**Correction (2026-09-01):** per-fight date is *not* actually a hard gap.
The `null` above is a bug specific to the nested `event` object inside a
`fights`-mode response. Calling `events` mode directly on that same event's
URL returns a real date every time (verified: UFC 325 → `"date":
"2026-01-31"`, not null). And it's cheap in practice: a completed event's
date is a **permanent fact**, so once fetched it can be cached forever
(no staleness window needed, unlike the upcoming-events list) — and it's
**per unique event, not per fight**, so it's shared across every fighter
who fought on that card. Once our local DB has an event cached, layoff time
for any fighter's fight there is free.

### Architectural implications, before designing the deterministic pipeline

1. **No single call gets everything.** Design needs to be: `fighters` mode
   as the index (identity, career averages, list of past fight IDs) → then
   a *bounded* number of `fights`-mode enrichment calls for the fights we
   actually want deep stats on (e.g. last 3–5, not all 24 — cost scales
   linearly per fight, and research says recent form matters more than deep
   career history anyway, so the cost constraint and the research
   recommendation point the same direction).
2. **Layoff-time needs one more call type, not zero.** When enriching a
   fighter's recent fights, if the referenced event isn't already in our
   local cache, pull its date once via `events` mode (permanent, no
   re-fetch ever) — don't trust the date embedded in a `fights`-mode
   response.
3. **Some research-identified predictors are simply unavailable from this
   source at all**: title-bout flag, opponent quality/ranking-at-time-of-
   fight, corner assignment. The MD instructions for the non-deterministic
   report need to either work around these gaps or explicitly flag them as
   unknown rather than have the LLM hallucinate values for them.
4. **"Career average" ≠ "recent form."** The actor's `careerStatistics`
   field is career-long — exactly the metric research says overstates
   predictive power. Recent-form stats need to be computed by us from the
   last N fights' `fightHistory` entries, not read off a pre-computed field.

## Signal-by-signal picture (consolidated)

**Strong signal, available for free** (already in `fighters` mode, zero extra calls):

| Predictor | Field |
|---|---|
| Strikes absorbed (CS229's #1 feature) | `careerStatistics.SApM` |
| Striking accuracy/defense | `Str. Acc.`, `Str. Def.` |
| Takedown accuracy | `TD Acc.` |
| Age | `dateOfBirth` (computed) |
| Win/loss streaks | derived by scanning `fightHistory` order |
| Career win/loss counts | `record` string |
| Finish-method history (KO/TKO %, decision %, sub %) | tallied from `method` per `fightHistory` entry |

**Strong signal, requires a `fights`-mode enrichment call per specific past fight:**

| Predictor | Field |
|---|---|
| Strike-location breakdown (head/body/leg, distance/clinch/ground) | `significantStrikes.{...}` |
| Total strikes landed (not just significant) | `totals.{fighter}.Total str.` |
| Takedown %, control time per fight | `totals.{fighter}.{Td %, Ctrl}` |
| Exact per-fight date (layoff/recency) | via a follow-up `events`-mode call on that fight's event URL (permanently cacheable) |

**Weak signal per research, but available for free anyway** — don't over-weight: reach (barely beats a coin flip outside heavyweight).

**Real gaps, unavailable from this actor at any depth**: title-bout flag,
opponent quality/ranking-at-time-of-fight, red/blue corner assignment.

## Alternative Apify actors investigated (dead ends)

Checked whether other UFC-data actors on Apify might fill these gaps or
offer a better source. Most (`parseforge/ufcstats-scraper`,
`jungle_synthesizer/ufcstats-mma-historical-fight-stats-scraper`,
`superapis/ufc-stats`, `fetchfinch/ufc-stats-scraper`) just re-scrape
ufcstats.com with the same limitations, and most had no documented input
schema at all (placeholder `{helloWorld: 123}` example input) — lower
confidence than what we've already verified.

**`jenko_systems/ufc-historical-stats`** looked genuinely different on paper
(proprietary composite metrics — JFI/JSP/JGD/JCG/JDS/JKR — plus multi-
promotion coverage: UFC/Bellator/PFL/Invicta/Rizin, and a `matchup` mode
built for exactly our head-to-head use case). Tested it directly with a
real matchup request (Hooker vs. Poirier, `include_jenko`/`jenko_full`
true) — **it silently ignored our input and ran an unrelated default query
instead** (`jenko_ranking` top-10, nobody we asked about). Its own log also
revealed it runs off a bundled, only-occasionally-refreshed SQLite
database rather than scraping live, and the log output is inconsistently
localized (English/Portuguese mixed) — signs of a low-effort, unreliable
actor. Rejected; not worth further spend debugging it.

## Blind-test run #1: Malkoun vs. Finney (2026-09-01)

Ran the pipeline concept live: pulled both fighters' `fighters`-mode
profiles, computed pre-fight recent-form from prior fights only (no
leakage from the target bout), had the user predict blind, then revealed
the real result and — separately — pulled `fights`-mode enrichment on each
fighter's last 2 fights to see if the granular detail would have helped.

- **User predicted:** Finney by unanimous decision.
- **Actual result:** Malkoun won by unanimous decision, 117–27 significant
  strikes, decisively — the opposite of what every summary-level signal
  suggested (Finney had the better streak, lower recent SApM, and was
  younger).
- **What the enrichment revealed that the summary didn't:** Finney's clean
  recent-form numbers were built on takedown/control-time volume, not
  output — his most recent win (vs. Valentin) had 13:16 of control time
  in a 15-minute fight but only 4 significant strikes landed, and still
  came out a **split** decision, not unanimous. That's a real, visible
  crack in an otherwise "undefeated, low SApM" profile that the
  aggregate stats alone completely hid. It wouldn't have flipped the pick
  to a confident Malkoun call, but it's exactly the kind of caveat a
  scouting report should surface instead of over-trusting a clean streak.
- **Takeaway:** the enrichment detail is worth the extra calls — it
  surfaces qualitative texture (how a fighter wins, not just that they
  win) that the top-line predictors miss, even when it doesn't change the
  final pick.

## Blind-test run #2: Micallef vs. Elliott (2026-09-03)

First run using the new standard depth (last 3 fights per fighter — though
Micallef only had 2 on record — each mapped to its own event for a real
date, per the decisions below).

- **User predicted:** Micallef by submission.
- **Actual result:** Correct on both counts — Micallef won by submission,
  round 2, 3:31.
- **What called it:** not an aggregate stat — a single prior-fight detail.
  In Micallef's win over Mohamed Ado, he was losing on every surface stat
  (25% striking accuracy vs. Ado's 83%, behind on control time) and still
  won via a triangle choke, with a submission attempt and a reversal on
  his own line. That's a live finishing/scramble instinct that doesn't
  show up anywhere in a career-average view.
- **Also surfaced by the new event-date mapping:** Micallef carried an
  **11.7-month layoff** into this fight (2025-02-08 → 2026-01-31) — the
  first real data point from the fight-frequency check we added this
  round.

## Blind-test run #3: Rowston vs. Brundage (2026-09-03)

- **User predicted:** Rowston by unanimous decision, ahead on significant
  strikes.
- **Actual result:** Rowston won (correct) — but by **KO/TKO, round 2,
  4:08**, not a decision. Significant strikes were 57–29 in Rowston's
  favor, matching the striking lean called — the fight just ended before
  it reached the scorecards.
- **Signals that pointed the right way:** Rowston entered on a clean
  2-fight win streak (both first-round finishes); Brundage entered with
  no win in his last two (a muddled technical draw, then a **split**
  decision loss despite out-controlling his opponent on takedowns and
  control time) — the same "control time without decisive credit" caution
  from run #1 showed up again, this time correctly flagging the weaker
  fighter.
- **Running tally: 2-of-3 correct winners, 2-of-3 correct methods too**
  (run #1 wrong on both, run #2 right on both, run #3 right on winner,
  wrong on method — decision predicted, finish happened).

## Decisions

- **Enrichment depth: last 3 fights per fighter**, going forward (the
  Malkoun/Finney test used 2 as a quick check; 3 is the standard depth).
- **Next run, also map each enriched fight to its event and pull that
  event's date** (via `events` mode — permanent, cacheable per the
  layoff-time correction above). This lets us compute each fighter's
  actual **average time between fights** (fight frequency / layoff
  pattern), not just recency-by-list-order.

## Emerging app shape

A clearer picture of the whole pipeline is forming:

1. **Deterministic step**: pull full enrichment (career profile + last 3
   fights per fighter, each mapped to its event for a real date) via
   Apify → this is the stored, factual "artifact."
2. **Non-deterministic step**: Claude predicts the fight — but **grounded
   only in that deterministic artifact**, explicitly instructed not to be
   "clever" or bring in outside knowledge/priors. This step's instructions
   live in an MD file (not yet created). Every time we discover something
   new and useful to check for, or a red-flag pattern worth watching, that
   *isn't* already part of the enrichment schema, it gets added to that MD
   file — so it's an evolving prediction-methodology doc, built up from
   real test runs like the one above, not written speculatively upfront.
3. **The actual "meat" of the app is visualization** — how both the
   deterministic report and Claude's prediction get presented to the user.
   The Dan Hooker scouting-report artifact from earlier in this session is
   the liked reference point for that visual style.

## Candidate signals for the future prediction MD file

Not part of the Apify enrichment schema — patterns discovered by testing
that should seed the eventual prediction-instructions MD file once it's
created (see "Emerging app shape" above):

- **Control-time without output is a weaker signal than it looks.** A
  fighter's clean recent record/streak built mainly on takedown/control
  volume rather than landed strikes deserves a discount — check whether
  those wins were unanimous or split despite big control-time numbers
  (Malkoun vs. Finney, run #1: 13:16 control time, only 4 strikes landed,
  still a split decision).
- **A finish despite losing every surface stat is a real "live finishing
  instinct" tell.** If a fighter won a prior fight via KO/TKO or
  submission while behind on striking accuracy and control time up to
  that point, weight that heavily — it showed up as the single most
  load-bearing signal in run #2 (Micallef's submission win over Ado,
  down 25%-to-83% on accuracy).

## Immediate next steps (resuming later)

- Research how to best visualize this data — building on the Dan Hooker
  artifact style already liked.
- Run this blind-prediction exercise a few more times with full 3-fight
  enrichment (+ event-date fight-frequency) per fighter, to keep
  sharpening the deterministic side before formalizing the prediction MD
  file.

## Not yet decided

- The stored "artifact" schema itself (what a deterministic per-fighter/
  per-matchup record looks like once fetched) — this is the next thing to
  design, and the MD instructions for the non-deterministic report get
  written against that schema once it exists.
