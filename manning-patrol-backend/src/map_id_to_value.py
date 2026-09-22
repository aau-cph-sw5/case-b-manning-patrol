# Make a function that takes the mapping.json file and returns a dictionary with the Id as the key and the Station or Train as the value.
import json
from pathlib import Path
from models import BeaconToStation # Imports the pydantic model from models.py

BASE_DIR = Path(__file__).resolve().parent.parent
MAPPING_PATH = BASE_DIR / "fixtures" / "mapping.json"
def load_mapping():
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    mapping = {}
    for item in data:
        validated_item = BeaconToStation(**item)  # Validate the item using the pydantic model

        if validated_item.station:
            mapping[validated_item.beacon_id] = validated_item.station
        elif validated_item.train:
            mapping[validated_item.beacon_id] = validated_item.train
    
    return mapping

# Make a function that takes an id of the mapping and returns the corresponding Station or Train.
def get_mapping_value(item_id):
    mapping = load_mapping()
    return mapping.get(item_id, None)

# Make a function that takes get_mapping_value and logs it into a file called mapping.log
def log_mapping_value(item_id):
    value = get_mapping_value(item_id)
    with (BASE_DIR / "fixtures" / "mapping.log").open("a", encoding="utf-8") as f:
        f.write(f'Id: {item_id}, Value: {value}\n')

if __name__ == '__main__':
    # Test the functions
    print ("Loading mapping ..")
    mapping = load_mapping()
    print(mapping)

    print("Value for Id 2:", get_mapping_value('2'))  # Should return 'VAN'
    log_mapping_value("2")

    print("Value for Id 50:", get_mapping_value('50'))  # Should return 'M1-8'
    log_mapping_value("50")

    print ("Done. Check mapping.log")
