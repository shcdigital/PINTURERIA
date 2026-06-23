import json, os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load():
    if not os.path.exists(CONFIG_PATH):
        return {'token': '', 'repo': ''}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
