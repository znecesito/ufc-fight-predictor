import pytest

from ufc_predictor import apify_source


def test_get_upcoming_events_requires_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(apify_source.ApifySourceError, match="APIFY_API_TOKEN"):
        apify_source.get_upcoming_events()


def test_get_fighter_profile_requires_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(apify_source.ApifySourceError, match="APIFY_API_TOKEN"):
        apify_source.get_fighter_profile("https://example.com/fighter/1")


def test_get_fight_detail_requires_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(apify_source.ApifySourceError, match="APIFY_API_TOKEN"):
        apify_source.get_fight_detail("https://example.com/fight/1")


def test_get_event_detail_requires_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(apify_source.ApifySourceError, match="APIFY_API_TOKEN"):
        apify_source.get_event_detail("https://example.com/event/1")
