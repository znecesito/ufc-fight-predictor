import pytest

from ufc_predictor import assembly, cli, reporting
from ufc_predictor.apify_source import ApifySourceError
from ufc_predictor.models import Event, FighterEnrichment, MatchupArtifact

RAW_EVENT = {
    "name": "UFC Fight Night: Hooker vs. Parnasse",
    "date": "2026-09-05",
    "location": "Paris, Ile-de-France, France",
    "url": "http://ufcstats.com/event-details/event1",
    "bouts": [
        {
            "fighters": [
                {"id": "a1", "name": "Dan Hooker", "url": "http://ufcstats.com/fighter/a1"},
                {"id": "b1", "name": "Salahdine Parnasse", "url": "http://ufcstats.com/fighter/b1"},
            ],
            "weightClass": "Lightweight",
        },
        {
            "fighters": [
                {"id": "a2", "name": "Fighter Three", "url": "http://ufcstats.com/fighter/a2"},
                {"id": "b2", "name": "Fighter Four", "url": "http://ufcstats.com/fighter/b2"},
            ],
            "weightClass": "Welterweight",
        },
    ],
}


def _dummy_artifact() -> MatchupArtifact:
    fe = FighterEnrichment(
        fighter_id="x",
        name="x",
        nickname="",
        height="",
        reach="",
        stance="",
        age_at_fight=30,
        record_entering="0-0-0",
        streak_entering=("win", 1),
        prior_fights=[],
        recent_form={},
        layoff_days_entering=None,
    )
    return MatchupArtifact(
        event_id="e",
        event_name="e",
        event_date="2026-01-01",
        weight_class="Lightweight",
        fighter_a=fe,
        fighter_b=fe,
        fetched_at="2026-01-01T00:00:00Z",
    )


def _feed_inputs(monkeypatch, values):
    values_iter = iter(values)
    monkeypatch.setattr("builtins.input", lambda *_args, **_kwargs: next(values_iter))


def test_run_skips_matchup_when_bout_choice_blank(monkeypatch, capsys):
    monkeypatch.setattr(cli.apify_source, "get_upcoming_events", lambda limit=5: [RAW_EVENT])
    _feed_inputs(monkeypatch, ["1", ""])

    called = []
    monkeypatch.setattr(assembly, "build_matchup_artifact", lambda *a: called.append(a))

    cli.run()

    assert called == []
    out = capsys.readouterr().out
    assert "Fight card" in out


def test_run_skips_matchup_when_bout_choice_is_s(monkeypatch, capsys):
    monkeypatch.setattr(cli.apify_source, "get_upcoming_events", lambda limit=5: [RAW_EVENT])
    _feed_inputs(monkeypatch, ["1", "s"])

    called = []
    monkeypatch.setattr(assembly, "build_matchup_artifact", lambda *a: called.append(a))

    cli.run()

    assert called == []


def test_run_builds_and_prints_matchup_for_picked_bout(monkeypatch, capsys):
    monkeypatch.setattr(cli.apify_source, "get_upcoming_events", lambda limit=5: [RAW_EVENT])
    _feed_inputs(monkeypatch, ["1", "2"])

    captured_args = {}

    def fake_build(fighter_a_url, fighter_b_url, event_url):
        captured_args["args"] = (fighter_a_url, fighter_b_url, event_url)
        return _dummy_artifact()

    monkeypatch.setattr(assembly, "build_matchup_artifact", fake_build)
    monkeypatch.setattr(reporting, "format_matchup_artifact", lambda artifact: "FORMATTED-OUTPUT")

    cli.run()

    assert captured_args["args"] == (
        "http://ufcstats.com/fighter/a2",
        "http://ufcstats.com/fighter/b2",
        "http://ufcstats.com/event-details/event1",
    )
    out = capsys.readouterr().out
    assert "FORMATTED-OUTPUT" in out


def test_run_handles_apify_source_error_from_build_matchup_artifact(monkeypatch, capsys):
    monkeypatch.setattr(cli.apify_source, "get_upcoming_events", lambda limit=5: [RAW_EVENT])
    _feed_inputs(monkeypatch, ["1", "1"])

    def fake_build(*_args):
        raise ApifySourceError("boom")

    monkeypatch.setattr(assembly, "build_matchup_artifact", fake_build)

    cli.run()

    out = capsys.readouterr().out
    assert "boom" in out
    assert "Couldn't build the matchup" in out


def test_run_returns_without_prompting_bout_when_no_bouts(monkeypatch, capsys):
    raw_event_no_bouts = dict(RAW_EVENT, bouts=[])
    monkeypatch.setattr(cli.apify_source, "get_upcoming_events", lambda limit=5: [raw_event_no_bouts])
    _feed_inputs(monkeypatch, ["1"])

    cli.run()

    out = capsys.readouterr().out
    assert "No bouts found." in out
