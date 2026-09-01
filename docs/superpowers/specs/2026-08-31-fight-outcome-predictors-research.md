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
| Per-fight date (for recency/layoff) | ✅ (for the event itself) | ❌ | ❌ (came back `null` even here) |
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

### Architectural implications, before designing the deterministic pipeline

1. **No single call gets everything.** Design needs to be: `fighters` mode
   as the index (identity, career averages, list of past fight IDs) → then
   a *bounded* number of `fights`-mode enrichment calls for the fights we
   actually want deep stats on (e.g. last 3–5, not all 24 — cost scales
   linearly per fight, and research says recent form matters more than deep
   career history anyway, so the cost constraint and the research
   recommendation point the same direction).
2. **Recency/layoff-time is a real gap.** Per-fight dates aren't reliably
   available even via the enrichment call (came back `null`). Options:
   approximate recency by fight order (we know sequence, not exact days),
   accept the gap, or spend an extra `events`-mode call per historical event
   to backfill real dates — a cost/precision tradeoff to decide explicitly.
3. **Some research-identified predictors are simply unavailable from this
   source at all**: title-bout flag, opponent quality/ranking-at-time-of-
   fight, corner assignment. The MD instructions for the non-deterministic
   report need to either work around these gaps or explicitly flag them as
   unknown rather than have the LLM hallucinate values for them.
4. **"Career average" ≠ "recent form."** The actor's `careerStatistics`
   field is career-long — exactly the metric research says overstates
   predictive power. Recent-form stats need to be computed by us from the
   last N fights' `fightHistory` entries, not read off a pre-computed field.

## Not yet decided

- Exactly how many past fights to enrich in full detail (cost vs. recency
  tradeoff)
- Whether to spend the extra `events`-mode calls to backfill real dates, or
  live with order-only recency
- The stored "artifact" schema itself (what a deterministic per-fighter/
  per-matchup record looks like once fetched) — this is the next thing to
  design, and the MD instructions for the non-deterministic report get
  written against that schema once it exists.
