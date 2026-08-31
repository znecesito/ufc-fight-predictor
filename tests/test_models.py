from ufc_predictor.models import Bout, Event


def test_event_from_dict_reads_known_keys():
    event = Event.from_dict(
        {
            "name": "UFC 300",
            "date": "2026-09-13",
            "venue": "T-Mobile Arena",
            "url": "http://ufcstats.com/event-details/abc123",
        }
    )
    assert event.name == "UFC 300"
    assert event.date == "2026-09-13"
    assert event.venue == "T-Mobile Arena"
    assert event.url == "http://ufcstats.com/event-details/abc123"


def test_event_from_dict_falls_back_on_missing_keys():
    event = Event.from_dict({})
    assert event.name == "Unknown event"
    assert event.date == ""
    assert event.url == ""


def test_bout_from_dict_reads_known_keys():
    bout = Bout.from_dict(
        {
            "fighterAName": "Max Holloway",
            "fighterBName": "Ilia Topuria",
            "weightClass": "Featherweight",
        }
    )
    assert bout.fighter_a == "Max Holloway"
    assert bout.fighter_b == "Ilia Topuria"
    assert bout.weight_class == "Featherweight"


def test_bout_from_dict_falls_back_on_missing_keys():
    bout = Bout.from_dict({})
    assert bout.fighter_a == "?"
    assert bout.fighter_b == "?"
