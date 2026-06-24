import json, os, sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def load():
    if not os.path.exists(CONFIG_PATH):
        return {'token': '', 'repo': ''}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)
