import json

from constants import DATA_DIR


def load_metadata_json(date_str):
    with open(DATA_DIR.joinpath(f'metadata_{date_str}.json'), 'r') as in_file:
        return json.load(in_file)
