import pytest
from pydantic import ValidationError
from models import BeaconToStation
from map_id_to_value import load_mapping

def test_pydantic_model_structure():
    # Test that the BeaconToStation model has the correct fields and types
    station_data = {"Id": "10", "Station": "Sluseholmen"}
    model = BeaconToStation(**station_data)
    assert model.beacon_id == "10"
    assert model.station == "Sluseholmen"

    # Test valid train data
    train_data = {"Id": "20", "Train": "M1-8"}
    model = BeaconToStation(**train_data)
    assert model.beacon_id == "20"
    assert model.train == "M1-8"

    #Test failing case with missing required field (missing Id)
    invalid_data = {"Station": "Sluseholmen"}
    with pytest.raises(ValidationError):
        BeaconToStation(**invalid_data)

def test_load_mapping_integration():
    # Test that the load_mapping function correctly loads and validates the mapping.json file
    mapping = load_mapping()
    
    # Check that the mapping is a dictionary
    assert isinstance(mapping, dict)
    
    # Check that specific known values are present in the mapping
    assert mapping.get("2") == "VAN"
    assert mapping.get("50") == "M1-8"
    
    # Check that an unknown Id returns None
    assert mapping.get("999") is None