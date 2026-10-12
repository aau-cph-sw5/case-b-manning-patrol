from services.api.src.models.beacon_to_station import BeaconToStation


def test_beacon_to_station_parses_aliases():
    model = BeaconToStation(Id="b1", Station="S1", Train="T1")

    assert model.beacon_id == "b1"
    assert model.station == "S1"
    assert model.train == "T1"


def test_beacon_to_station_defaults_optional_fields():
    model = BeaconToStation(Id="b1")

    assert model.station is None
    assert model.train is None
