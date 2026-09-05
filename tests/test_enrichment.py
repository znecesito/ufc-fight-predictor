import json
from pathlib import Path

import pytest

from ufc_predictor.enrichment import (
    compute_layoff_days,
    compute_record_entering,
    compute_recent_form,
    compute_streak_entering,
    find_prior_fights,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fight_history(filename: str) -> list[dict]:
    with open(FIXTURES / filename) as f:
        record = json.load(f)[0]
    return record["fightHistory"]


@pytest.fixture
def malkoun_history():
    return _load_fight_history("malkoun_fighter.json")


@pytest.fixture
def finney_history():
    return _load_fight_history("finney_fighter.json")


def test_find_prior_fights_default_limit(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney")
    assert len(prior) == 3
    assert [f["fighters"][1]["name"] for f in prior] == [
        "Andre Petroski",
        "Cody Brundage",
        "Nick Maximov",
    ]


def test_find_prior_fights_opponent_not_found_falls_back_to_most_recent(malkoun_history):
    # A real bug found by an actual live run: when the two fighters haven't
    # fought yet (the real product case - an upcoming matchup), the opponent
    # never appears in either fighter's history, so there's no index to skip
    # past. It must fall back to the fighter's most recent `limit` fights,
    # not silently return nothing.
    prior = find_prior_fights(malkoun_history, "Nobody Realname", limit=3)
    assert len(prior) == 3
    assert prior == malkoun_history[:3]


def test_find_prior_fights_opponent_not_found_and_empty_history_returns_empty():
    assert find_prior_fights([], "Nobody Realname") == []


def test_find_prior_fights_returns_fewer_than_limit_when_not_enough_exist(finney_history):
    prior = find_prior_fights(finney_history, "Jacob Malkoun", limit=10)
    assert len(prior) == 4


def test_compute_record_entering_malkoun(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney", limit=10)
    assert compute_record_entering("Jacob Malkoun", prior) == "4-3"


def test_compute_record_entering_finney(finney_history):
    prior = find_prior_fights(finney_history, "Jacob Malkoun", limit=10)
    assert compute_record_entering("Torrez Finney", prior) == "4-0"


def test_compute_streak_entering_malkoun(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney", limit=10)
    assert compute_streak_entering("Jacob Malkoun", prior) == ("win", 1)


def test_compute_streak_entering_finney(finney_history):
    prior = find_prior_fights(finney_history, "Jacob Malkoun", limit=10)
    assert compute_streak_entering("Torrez Finney", prior) == ("win", 4)


def test_compute_streak_entering_empty_history_returns_none():
    assert compute_streak_entering("Anyone", []) == ("none", 0)


def test_compute_recent_form_malkoun_last_five(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney", limit=5)
    assert len(prior) == 5
    form = compute_recent_form("Jacob Malkoun", prior)
    assert form["fights_considered"] == 5
    assert form["slpm"] == pytest.approx(4.44, abs=0.01)
    assert form["sapm"] == pytest.approx(2.66, abs=0.01)
    assert form["td_avg_per_15"] == pytest.approx(6.28, abs=0.01)
    assert form["kd_total"] == 0
    assert form["finishes"] == 1


def test_compute_recent_form_finney_only_four_available(finney_history):
    prior = find_prior_fights(finney_history, "Jacob Malkoun", limit=5)
    assert len(prior) == 4
    form = compute_recent_form("Torrez Finney", prior)
    assert form["fights_considered"] == 4
    assert form["slpm"] == pytest.approx(1.77, abs=0.01)
    assert form["sapm"] == pytest.approx(1.74, abs=0.01)
    assert form["td_avg_per_15"] == pytest.approx(9.31, abs=0.01)
    assert form["kd_total"] == 0
    assert form["finishes"] == 2


def test_compute_recent_form_empty_prior_fights_returns_zeros():
    form = compute_recent_form("Anyone", [])
    assert form == {
        "fights_considered": 0,
        "slpm": 0.0,
        "sapm": 0.0,
        "td_avg_per_15": 0.0,
        "kd_total": 0,
        "finishes": 0,
    }


def test_compute_layoff_days_returns_reasonable_positive_int(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney", limit=3)
    most_recent_fight_id = prior[0]["id"]
    event_dates = {most_recent_fight_id: "2022-10-15"}
    layoff = compute_layoff_days(prior, "2023-06-24", event_dates)
    assert isinstance(layoff, int)
    assert layoff > 0


def test_compute_layoff_days_empty_prior_fights_returns_none():
    assert compute_layoff_days([], "2023-06-24", {}) is None


def test_compute_layoff_days_missing_event_date_returns_none(malkoun_history):
    prior = find_prior_fights(malkoun_history, "Torrez Finney", limit=3)
    assert compute_layoff_days(prior, "2023-06-24", {}) is None
