from ufc_predictor.models import Bout, Event


def test_bout_from_dict_reads_fighters_array():
    bout = Bout.from_dict(
        {
            "fighters": [
                {"id": "193b9d1858bc4df3", "name": "Dan Hooker"},
                {"id": "b3cb9dfccff3be76", "name": "Salahdine Parnasse"},
            ],
            "weightClass": "Lightweight",
        }
    )
    assert bout.fighter_a == "Dan Hooker"
    assert bout.fighter_b == "Salahdine Parnasse"
    assert bout.weight_class == "Lightweight"


def test_bout_from_dict_falls_back_on_missing_keys():
    bout = Bout.from_dict({})
    assert bout.fighter_a == "?"
    assert bout.fighter_b == "?"
    assert bout.weight_class == ""


def test_event_from_dict_reads_known_keys_and_nested_bouts():
    event = Event.from_dict(
        {
            "name": "UFC Fight Night: Hooker vs. Parnasse",
            "date": "2026-09-05",
            "location": "Paris, Ile-de-France, France",
            "url": "http://ufcstats.com/event-details/2144954270be834d",
            "bouts": [
                {
                    "fighters": [{"name": "Dan Hooker"}, {"name": "Salahdine Parnasse"}],
                    "weightClass": "Lightweight",
                }
            ],
        }
    )
    assert event.name == "UFC Fight Night: Hooker vs. Parnasse"
    assert event.date == "2026-09-05"
    assert event.venue == "Paris, Ile-de-France, France"
    assert event.url == "http://ufcstats.com/event-details/2144954270be834d"
    assert len(event.bouts) == 1
    assert event.bouts[0].fighter_a == "Dan Hooker"


def test_event_from_dict_falls_back_on_missing_keys():
    event = Event.from_dict({})
    assert event.name == "Unknown event"
    assert event.date == ""
    assert event.url == ""
    assert event.bouts == []
