"""Plain-text formatting for a fully-populated MatchupArtifact.

This module has exactly one job: turn a `MatchupArtifact` (already built by
assembly.py from live Apify data) into a readable report a person can read in
a terminal via `print()`. No network calls, no other module knowledge beyond
the dataclass shapes in models.py - pure string formatting.

The layout mirrors how fight breakdowns were manually written out in this
project's scratch research during testing: event header, then one section per
fighter covering vitals/record/form, then a numbered rundown of their last
few fights with enough per-fight detail (method, round/time, who led on
significant strikes) to see the story behind the numbers, not just totals.
"""

from __future__ import annotations

import textwrap

from ufc_predictor.models import FighterEnrichment, MatchupArtifact, PriorFight

_RULE_WIDTH = 78
_WRAP_WIDTH = 78


def format_matchup_artifact(artifact: MatchupArtifact) -> str:
    lines: list[str] = []
    lines.extend(_format_header(artifact))
    lines.append("")
    lines.extend(_format_fighter_section(artifact.fighter_a))
    lines.append("")
    lines.extend(_format_fighter_section(artifact.fighter_b))
    return "\n".join(lines)


def _format_header(artifact: MatchupArtifact) -> list[str]:
    rule = "=" * _RULE_WIDTH
    return [
        rule,
        artifact.event_name,
        f"{artifact.event_date}  |  {artifact.weight_class}",
        rule,
    ]


def _format_fighter_section(fighter: FighterEnrichment) -> list[str]:
    rule = "-" * _RULE_WIDTH
    title = fighter.name
    if fighter.nickname:
        title = f'{fighter.name} "{fighter.nickname}"'

    lines = [rule, title, rule]
    lines.append(f"Age at fight time: {fighter.age_at_fight}")
    lines.append(
        f"Height: {fighter.height}  |  Reach: {fighter.reach}  |  Stance: {fighter.stance}"
    )
    lines.append(f"Record entering: {fighter.record_entering}")
    lines.append(f"Streak entering: {_format_streak(fighter.streak_entering)}")
    lines.append(f"Layoff entering: {_format_layoff(fighter.layoff_days_entering)}")
    lines.append("")
    lines.append("Recent form:")
    lines.extend(_format_recent_form(fighter.recent_form))
    lines.append("")
    lines.append("Prior fights:")
    lines.extend(_format_prior_fights(fighter.prior_fights))
    return lines


def _format_streak(streak_entering: tuple[str, int]) -> str:
    streak_type, length = streak_entering
    if length <= 0:
        return "no streak"
    return f"{length}-fight {streak_type} streak"


def _format_layoff(layoff_days_entering: int | None) -> str:
    if layoff_days_entering is None:
        return "unknown"
    return f"{layoff_days_entering} days since last fight"


def _format_recent_form(recent_form: dict[str, float | int]) -> list[str]:
    fights_considered = recent_form.get("fights_considered")
    slpm = recent_form.get("slpm", 0.0)
    sapm = recent_form.get("sapm", 0.0)
    td_avg_per_15 = recent_form.get("td_avg_per_15", 0.0)
    kd_total = recent_form.get("kd_total", 0)
    finishes = recent_form.get("finishes", 0)

    basis = (
        f"  (based on last {fights_considered} fight"
        f"{'s' if fights_considered != 1 else ''})"
        if fights_considered
        else ""
    )
    return [
        f"  SLpM: {slpm:.2f}{basis}",
        f"  SApM: {sapm:.2f}",
        f"  TD avg per 15 min: {td_avg_per_15:.2f}",
        f"  Knockdowns (total): {kd_total}",
        f"  Finishes: {finishes}",
    ]


def _format_prior_fights(prior_fights: list[PriorFight]) -> list[str]:
    if not prior_fights:
        return ["  No prior fights on record."]

    lines: list[str] = []
    for i, fight in enumerate(prior_fights, start=1):
        lines.extend(_format_single_prior_fight(i, fight))
    return lines


def _format_single_prior_fight(index: int, fight: PriorFight) -> list[str]:
    method = fight.method
    if fight.method_details:
        method = f"{method} ({fight.method_details})"

    headline = (
        f"{index}. vs. {fight.opponent_name} — {fight.result} by {method}, "
        f"Rd {fight.round} ({fight.time}) — {fight.event_name} ({fight.event_date})"
    )
    wrapped_headline = textwrap.wrap(
        headline,
        width=_WRAP_WIDTH,
        initial_indent="  ",
        subsequent_indent="     ",
    ) or ["  " + headline]

    strikes_line = _format_totals_line(fight.totals)
    wrapped_strikes = textwrap.wrap(
        strikes_line,
        width=_WRAP_WIDTH,
        initial_indent="     ",
        subsequent_indent="       ",
    ) or ["     " + strikes_line]

    return [*wrapped_headline, *wrapped_strikes]


def _format_totals_line(totals: dict[str, dict[str, str]]) -> str:
    if not totals:
        return "no strike totals available"

    parts = []
    for fighter_name, stats in totals.items():
        if stats:
            stat_str = ", ".join(f"{key}: {value}" for key, value in stats.items())
            parts.append(f"{fighter_name} — {stat_str}")
        else:
            parts.append(fighter_name)
    return "  |  ".join(parts)
