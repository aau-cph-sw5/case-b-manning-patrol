# Make a function that takes the mapping.json file and returns a dictionary with the Id as the key and the Station or Train as the value.
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
MAPPING_PATH = BASE_DIR / "mapping.json"
def load_mapping():
    with MAPPING_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    
    mapping = {}
    for item in data:
        item_id = item['Id']
        if 'Station' in item:
            mapping[item_id] = item['Station']
        elif 'Train' in item:
            mapping[item_id] = item['Train']
    
    return mapping

# Make a function that takes an id of the mapping and returns the corresponding Station or Train.
def get_mapping_value(item_id):
    mapping = load_mapping()
    return mapping.get(item_id, None)

# Make a function that takes get_mapping_value and logs it into a file called mapping.log
def log_mapping_value(item_id):
    value = get_mapping_value(item_id)
    with (BASE_DIR / "mapping.log").open("a", encoding="utf-8") as f:
        f.write(f'Id: {item_id}, Value: {value}\n')

if __name__ == '__main__':
    # Test the functions
    print ("Loading mapping ..")
    mapping = load_mapping()
    print(mapping)

    print("Value for Id 1:", get_mapping_value('1'))  # Should return 'VAN'
    log_mapping_value("1")

    print("Value for Id 50:", get_mapping_value('50'))  # Should return 'M1-8'
    log_mapping_value("50")

    print ("Done. Check mapping.log")
