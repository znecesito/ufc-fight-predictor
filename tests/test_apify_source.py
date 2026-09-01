import pytest

from ufc_predictor import apify_source


def test_get_upcoming_events_requires_token(monkeypatch):
    monkeypatch.delenv("APIFY_API_TOKEN", raising=False)
    with pytest.raises(apify_source.ApifySourceError, match="APIFY_API_TOKEN"):
        apify_source.get_upcoming_events()
