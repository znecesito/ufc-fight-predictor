"""End-to-end tests for assembly.py's orchestration of apify_source + enrichment.

No real Apify calls are made: apify_source.get_fighter_profile,
apify_source.get_fight_detail, and apify_source.get_event_detail are all
monkeypatched with small hand-built fixtures shaped like real actor
responses (see apify_source.py's docstrings and tests/fixtures/*.json for
the real shapes this mirrors).
"""

from __future__ import annotations

import pytest

from ufc_predictor import apify_source, assembly
from ufc_predictor.models import FighterEnrichment, MatchupArtifact, PriorFight

# --- Fake fighters -----------------------------------------------------

ALPHA_URL = "http://ufcstats.com/fighter-details/alpha"
BRAVO_URL = "http://ufcstats.com/fighter-details/bravo"
CHARLIE_URL = "http://ufcstats.com/fighter-details/charlie"
DELTA_URL = "http://ufcstats.com/fighter-details/delta"
ECHO_URL = "http://ufcstats.com/fighter-details/echo"

EVENT_URL = "http://ufcstats.com/event-details/main-event"

FIGHT_AB_URL = "http://ufcstats.com/fight-details/ab"  # alpha vs bravo (the matchup itself)
FIGHT_A_CHARLIE_URL = "http://ufcstats.com/fight-details/a-charlie"
FIGHT_A_DELTA_URL = "http://ufcstats.com/fight-details/a-delta"
FIGHT_B_ECHO_URL = "http://ufcstats.com/fight-details/b-echo"
FIGHT_B_CHARLIE_URL = "http://ufcstats.com/fight-details/b-charlie"

EVENT_PRIOR_1_URL = "http://ufcstats.com/event-details/prior-1"
EVENT_PRIOR_2_URL = "http://ufcstats.com/event-details/prior-2"
EVENT_PRIOR_3_URL = "http://ufcstats.com/event-details/prior-3"


def _fighter_ref(name: str, url: str) -> dict:
    fighter_id = url.rsplit("/", 1)[-1]
    return {"id": fighter_id, "name": name, "url": url}


ALPHA_PROFILE = {
    "sourceId": "alpha",
    "name": "Alpha Fighter",
    "nickname": "The Alpha",
    "height": "5' 11\"",
    "reach": "76\"",
    "stance": "Orthodox",
    "dateOfBirth": "1993-01-15",
    "fightHistory": [
        {
            "id": "fight-a-vs-bravo",
            "url": FIGHT_AB_URL,
            "fighters": [_fighter_ref("Alpha Fighter", ALPHA_URL), _fighter_ref("Bravo Fighter", BRAVO_URL)],
            "result": ["win", "loss"],
            "knockdowns": ["0", "0"],
            "significantStrikes": ["10", "5"],
            "takedowns": ["1", "0"],
            "submissionAttempts": ["0", "0"],
            "weightClass": None,
            "method": "U-DEC",
            "round": 3,
            "time": "5:00",
        },
        {
            "id": "fight-a-vs-charlie",
            "url": FIGHT_A_CHARLIE_URL,
            "fighters": [_fighter_ref("Alpha Fighter", ALPHA_URL), _fighter_ref("Charlie Fighter", CHARLIE_URL)],
            "result": ["win", "loss"],
            "knockdowns": ["1", "0"],
            "significantStrikes": ["40", "20"],
            "takedowns": ["2", "0"],
            "submissionAttempts": ["0", "0"],
            "weightClass": None,
            "method": "KO/TKO",
            "round": 2,
            "time": "3:12",
        },
        {
            "id": "fight-a-vs-delta",
            "url": FIGHT_A_DELTA_URL,
            "fighters": [_fighter_ref("Alpha Fighter", ALPHA_URL), _fighter_ref("Delta Fighter", DELTA_URL)],
            "result": ["loss", "win"],
            "knockdowns": ["0", "0"],
            "significantStrikes": ["15", "30"],
            "takedowns": ["0", "1"],
            "submissionAttempts": ["0", "0"],
            "weightClass": None,
            "method": "U-DEC",
            "round": 3,
            "time": "5:00",
        },
    ],
}

BRAVO_PROFILE = {
    "sourceId": "bravo",
    "name": "Bravo Fighter",
    "nickname": "",
    "height": "6' 0\"",
    "reach": "74\"",
    "stance": "Southpaw",
    "dateOfBirth": "1991-06-20",
    "fightHistory": [
        {
            "id": "fight-b-vs-alpha",
            "url": FIGHT_AB_URL,
            "fighters": [_fighter_ref("Bravo Fighter", BRAVO_URL), _fighter_ref("Alpha Fighter", ALPHA_URL)],
            "result": ["loss", "win"],
            "knockdowns": ["0", "0"],
            "significantStrikes": ["5", "10"],
            "takedowns": ["0", "1"],
            "submissionAttempts": ["0", "0"],
            "weightClass": None,
            "method": "U-DEC",
            "round": 3,
            "time": "5:00",
        },
        {
            "id": "fight-b-vs-echo",
            "url": FIGHT_B_ECHO_URL,
            "fighters": [_fighter_ref("Bravo Fighter", BRAVO_URL), _fighter_ref("Echo Fighter", ECHO_URL)],
            "result": ["win", "loss"],
            "knockdowns": ["0", "1"],
            "significantStrikes": ["25", "10"],
            "takedowns": ["3", "0"],
            "submissionAttempts": ["1", "0"],
            "weightClass": None,
            "method": "SUB",
            "round": 1,
            "time": "4:00",
        },
        {
            "id": "fight-b-vs-charlie",
            "url": FIGHT_B_CHARLIE_URL,
            "fighters": [_fighter_ref("Bravo Fighter", BRAVO_URL), _fighter_ref("Charlie Fighter", CHARLIE_URL)],
            "result": ["win", "loss"],
            "knockdowns": ["0", "0"],
            "significantStrikes": ["18", "12"],
            "takedowns": ["1", "0"],
            "submissionAttempts": ["0", "0"],
            "weightClass": None,
            "method": "U-DEC",
            "round": 3,
            "time": "5:00",
        },
    ],
}

FIGHTER_PROFILES = {
    ALPHA_URL: ALPHA_PROFILE,
    BRAVO_URL: BRAVO_PROFILE,
}


def _fight_detail(
    winner_name: str,
    loser_name: str,
    event_url: str,
    method: str = "U-DEC",
    method_details: str | None = None,
    round_: int = 3,
    time_: str = "5:00",
    weight_class: str = "Middleweight",
) -> dict:
    return {
        "event": {"id": None, "name": None, "date": None, "url": event_url},
        "fighters": [
            {"name": winner_name, "result": "W"},
            {"name": loser_name, "result": "L"},
        ],
        "totals": {
            winner_name: {"knockdowns": "0", "sigStrikes": "40", "takedowns": "2"},
            loser_name: {"knockdowns": "0", "sigStrikes": "20", "takedowns": "0"},
        },
        "significantStrikes": {
            winner_name: {"Head": "20", "Body": "10", "Leg": "10", "Distance": "30", "Clinch": "5", "Ground": "5"},
            loser_name: {"Head": "10", "Body": "5", "Leg": "5", "Distance": "15", "Clinch": "3", "Ground": "2"},
        },
        "method": method,
        "methodDetails": method_details,
        "round": round_,
        "time": time_,
        "weightClass": weight_class,
    }


FIGHT_DETAILS = {
    FIGHT_AB_URL: _fight_detail("Alpha Fighter", "Bravo Fighter", EVENT_PRIOR_1_URL, method="U-DEC"),
    FIGHT_A_CHARLIE_URL: _fight_detail(
        "Alpha Fighter", "Charlie Fighter", EVENT_PRIOR_2_URL, method="KO/TKO", method_details="Punches"
    ),
    FIGHT_A_DELTA_URL: _fight_detail("Delta Fighter", "Alpha Fighter", EVENT_PRIOR_3_URL, method="U-DEC"),
    FIGHT_B_ECHO_URL: _fight_detail(
        "Bravo Fighter", "Echo Fighter", EVENT_PRIOR_1_URL, method="SUB", method_details="Rear-naked choke"
    ),
    FIGHT_B_CHARLIE_URL: _fight_detail("Bravo Fighter", "Charlie Fighter", EVENT_PRIOR_2_URL, method="U-DEC"),
}

EVENT_DETAILS = {
    EVENT_PRIOR_1_URL: {
        "id": "evt-1",
        "sourceId": "evt-1-src",
        "name": "UFC Prior One",
        "date": "2024-01-20",
        "location": "Las Vegas, Nevada, USA",
        "status": "completed",
        "url": EVENT_PRIOR_1_URL,
    },
    EVENT_PRIOR_2_URL: {
        "id": "evt-2",
        "sourceId": "evt-2-src",
        "name": "UFC Prior Two",
        "date": "2024-06-15",
        "location": "New York, New York, USA",
        "status": "completed",
        "url": EVENT_PRIOR_2_URL,
    },
    EVENT_PRIOR_3_URL: {
        "id": "evt-3",
        "sourceId": "evt-3-src",
        "name": "UFC Prior Three",
        "date": "2024-11-02",
        "location": "Miami, Florida, USA",
        "status": "completed",
        "url": EVENT_PRIOR_3_URL,
    },
    EVENT_URL: {
        "id": "evt-main",
        "sourceId": "evt-main-src",
        "name": "UFC Main Event",
        "date": "2025-03-08",
        "location": "Los Angeles, California, USA",
        "status": "upcoming",
        "url": EVENT_URL,
        "bouts": [
            {
                "fighters": [
                    _fighter_ref("Alpha Fighter", ALPHA_URL),
                    _fighter_ref("Bravo Fighter", BRAVO_URL),
                ],
                "weightClass": "Middleweight",
            },
            {
                "fighters": [
                    _fighter_ref("Charlie Fighter", CHARLIE_URL),
                    _fighter_ref("Delta Fighter", DELTA_URL),
                ],
                "weightClass": "Lightweight",
            },
        ],
    },
}


@pytest.fixture(autouse=True)
def _mock_apify(monkeypatch):
    monkeypatch.setattr(
        apify_source, "get_fighter_profile", lambda url: FIGHTER_PROFILES[url]
    )
    monkeypatch.setattr(
        apify_source, "get_fight_detail", lambda url: FIGHT_DETAILS[url]
    )
    monkeypatch.setattr(
        apify_source, "get_event_detail", lambda url: EVENT_DETAILS[url]
    )


# --- Tests ---------------------------------------------------------------


def test_build_fighter_enrichment_populates_core_fields():
    enrichment = assembly.build_fighter_enrichment(
        ALPHA_URL, opponent_name="Bravo Fighter", target_event_date="2025-03-08"
    )

    assert isinstance(enrichment, FighterEnrichment)
    assert enrichment.name == "Alpha Fighter"
    assert enrichment.nickname == "The Alpha"
    assert enrichment.fighter_id == "alpha"
    assert enrichment.height == "5' 11\""
    assert enrichment.reach == "76\""
    assert enrichment.stance == "Orthodox"
    assert enrichment.age_at_fight == 32  # dob 1993-01-15, target 2025-03-08


def test_build_fighter_enrichment_prior_fights_are_populated():
    enrichment = assembly.build_fighter_enrichment(
        ALPHA_URL, opponent_name="Bravo Fighter", target_event_date="2025-03-08"
    )

    # find_prior_fights looks *after* the opponent match in fightHistory, so
    # only the two fights following the alpha-vs-bravo entry are "prior".
    assert len(enrichment.prior_fights) == 2
    for pf in enrichment.prior_fights:
        assert isinstance(pf, PriorFight)
        assert pf.event_id
        assert pf.event_name
        assert pf.event_date
        assert pf.method
        assert pf.weight_class
        assert pf.totals
        assert pf.significant_strikes
        assert pf.result in ("win", "loss", "draw", "no_contest")

    first, second = enrichment.prior_fights
    assert first.opponent_name == "Charlie Fighter"
    assert first.event_name == "UFC Prior Two"
    assert first.event_date == "2024-06-15"
    assert first.method == "KO/TKO"
    assert first.method_details == "Punches"

    assert second.opponent_name == "Delta Fighter"
    assert second.result == "loss"
    assert second.event_name == "UFC Prior Three"
    assert second.event_date == "2024-11-02"


def test_build_fighter_enrichment_record_streak_and_form_are_consistent():
    enrichment = assembly.build_fighter_enrichment(
        ALPHA_URL, opponent_name="Bravo Fighter", target_event_date="2025-03-08"
    )

    assert enrichment.record_entering == "1-1"
    # Most recent prior fight (Charlie) was a win, then the streak breaks at
    # the next-most-recent (Delta, a loss).
    assert enrichment.streak_entering == ("win", 1)
    assert enrichment.recent_form["fights_considered"] == 2
    assert enrichment.recent_form["finishes"] == 1


def test_build_fighter_enrichment_layoff_days_is_positive_int():
    enrichment = assembly.build_fighter_enrichment(
        ALPHA_URL, opponent_name="Bravo Fighter", target_event_date="2025-03-08"
    )

    assert isinstance(enrichment.layoff_days_entering, int)
    assert enrichment.layoff_days_entering > 0
    # Most recent prior fight (Charlie) was on 2024-06-15; target is 2025-03-08.
    from datetime import date

    expected = (date(2025, 3, 8) - date(2024, 6, 15)).days
    assert enrichment.layoff_days_entering == expected


def test_build_fighter_enrichment_no_prior_fights_when_opponent_not_in_history():
    enrichment = assembly.build_fighter_enrichment(
        ALPHA_URL, opponent_name="Nobody Realname", target_event_date="2025-03-08"
    )

    assert enrichment.prior_fights == []
    assert enrichment.record_entering == "0-0"
    assert enrichment.streak_entering == ("none", 0)
    assert enrichment.layoff_days_entering is None


def test_build_matchup_artifact_end_to_end():
    artifact = assembly.build_matchup_artifact(ALPHA_URL, BRAVO_URL, EVENT_URL)

    assert isinstance(artifact, MatchupArtifact)
    assert artifact.event_id == "evt-main"
    assert artifact.event_name == "UFC Main Event"
    assert artifact.event_date == "2025-03-08"
    assert artifact.weight_class == "Middleweight"
    assert artifact.fetched_at  # non-empty ISO timestamp

    assert artifact.fighter_a.name == "Alpha Fighter"
    assert artifact.fighter_b.name == "Bravo Fighter"

    # Each side's prior fights were built against the *other* fighter as the
    # opponent-name anchor, so both sides should have prior fights populated.
    assert len(artifact.fighter_a.prior_fights) == 2
    assert len(artifact.fighter_b.prior_fights) == 2

    assert artifact.fighter_a.record_entering == "1-1"
    # Bravo's fightHistory has both prior fights (vs Echo, vs Charlie) as
    # wins once the Alpha match itself is skipped.
    assert artifact.fighter_b.record_entering == "2-0"


def test_build_matchup_artifact_raises_when_bout_not_found():
    with pytest.raises(ValueError, match="No bout found"):
        assembly.build_matchup_artifact(ALPHA_URL, ECHO_URL, EVENT_URL)
