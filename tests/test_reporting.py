from ufc_predictor.models import FighterEnrichment, MatchupArtifact, PriorFight
from ufc_predictor.reporting import format_matchup_artifact


def _prior_fight(
    opponent_name="Andre Petroski",
    result="win",
    method="U-DEC",
    method_details=None,
    round_=3,
    time="5:00",
    fighter_name="Jacob Malkoun",
):
    return PriorFight(
        fight_id="edff38661bf2866b",
        opponent_name=opponent_name,
        opponent_id="6ac9bc2953c47345",
        event_id="ufc285",
        event_name="UFC 285",
        event_date="2023-03-04",
        result=result,
        method=method,
        method_details=method_details,
        round=round_,
        time=time,
        weight_class="Middleweight",
        totals={
            fighter_name: {"sig_str": "45 of 90", "td": "3 of 5"},
            opponent_name: {"sig_str": "32 of 65", "td": "0 of 2"},
        },
        significant_strikes={
            fighter_name: {"head": "20", "body": "15", "leg": "10"},
            opponent_name: {"head": "18", "body": "10", "leg": "4"},
        },
    )


def _fighter(
    name="Jacob Malkoun",
    nickname="",
    prior_fights=None,
    layoff_days_entering=126,
    streak_entering=("win", 1),
):
    return FighterEnrichment(
        fighter_id="d4270315cbcf2569",
        name=name,
        nickname=nickname,
        height="6'1\"",
        reach="74\"",
        stance="Orthodox",
        age_at_fight=27,
        record_entering="4-3",
        streak_entering=streak_entering,
        prior_fights=prior_fights if prior_fights is not None else [_prior_fight()],
        recent_form={
            "fights_considered": 5,
            "slpm": 4.44,
            "sapm": 2.66,
            "td_avg_per_15": 6.28,
            "kd_total": 0,
            "finishes": 1,
        },
        layoff_days_entering=layoff_days_entering,
    )


def _artifact(fighter_a=None, fighter_b=None):
    return MatchupArtifact(
        event_id="event123",
        event_name="UFC Fight Night: Hooker vs. Parnasse",
        event_date="2026-09-05",
        weight_class="Lightweight",
        fighter_a=fighter_a if fighter_a is not None else _fighter(),
        fighter_b=fighter_b
        if fighter_b is not None
        else _fighter(
            name="Torrez Finney",
            nickname="Money",
            streak_entering=("win", 4),
            prior_fights=[
                _prior_fight(
                    opponent_name="Jacob Malkoun",
                    result="loss",
                    method="SUB",
                    method_details="rear-naked choke",
                    round_=2,
                    time="3:12",
                    fighter_name="Torrez Finney",
                )
            ],
        ),
        fetched_at="2026-09-04T12:00:00Z",
    )


def test_includes_event_header_details():
    report = format_matchup_artifact(_artifact())
    assert "UFC Fight Night: Hooker vs. Parnasse" in report
    assert "2026-09-05" in report
    assert "Lightweight" in report


def test_includes_both_fighter_names_and_nicknames():
    report = format_matchup_artifact(_artifact())
    assert "Jacob Malkoun" in report
    assert "Torrez Finney" in report
    assert "Money" in report


def test_includes_vitals_and_record():
    report = format_matchup_artifact(_artifact())
    assert "6'1\"" in report
    assert '74"' in report
    assert "Orthodox" in report
    assert "4-3" in report


def test_includes_streak_formatting():
    report = format_matchup_artifact(_artifact())
    assert "1-fight win streak" in report
    assert "4-fight win streak" in report


def test_no_streak_when_length_zero():
    report = format_matchup_artifact(
        _artifact(fighter_a=_fighter(streak_entering=("none", 0)))
    )
    assert "no streak" in report


def test_includes_layoff_days_when_present():
    report = format_matchup_artifact(_artifact())
    assert "126 days since last fight" in report


def test_layoff_unknown_when_none():
    report = format_matchup_artifact(
        _artifact(fighter_a=_fighter(layoff_days_entering=None))
    )
    assert "unknown" in report


def test_includes_recent_form_numbers():
    report = format_matchup_artifact(_artifact())
    assert "4.44" in report
    assert "2.66" in report
    assert "6.28" in report
    assert "Finishes: 1" in report


def test_includes_prior_fight_opponent_and_method():
    report = format_matchup_artifact(_artifact())
    assert "Andre Petroski" in report
    assert "U-DEC" in report
    assert "Rd 3" in report
    assert "5:00" in report


def test_includes_method_details_when_present():
    report = format_matchup_artifact(_artifact())
    assert "rear-naked choke" in report
    assert "SUB" in report


def test_includes_significant_strike_totals_for_both_fighters():
    report = format_matchup_artifact(_artifact())
    assert "sig_str: 45 of 90" in report
    assert "sig_str: 32 of 65" in report


def test_empty_prior_fights_does_not_crash():
    report = format_matchup_artifact(_artifact(fighter_a=_fighter(prior_fights=[])))
    assert "No prior fights on record." in report


def test_no_nickname_fighter_does_not_crash_and_omits_quotes():
    fighter = _fighter(name="Solo Fighter", nickname="")
    report = format_matchup_artifact(_artifact(fighter_a=fighter))
    assert "Solo Fighter" in report


def test_returns_a_string_and_is_nonempty():
    report = format_matchup_artifact(_artifact())
    assert isinstance(report, str)
    assert len(report) > 0
