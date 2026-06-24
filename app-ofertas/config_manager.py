import json, os, sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')
PUBLICADAS_PATH = os.path.join(BASE_DIR, 'publicadas.json')

def load():
    if not os.path.exists(CONFIG_PATH):
        return {'token': '', 'repo': ''}
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_published():
    if not os.path.exists(PUBLICADAS_PATH):
        return []
    with open(PUBLICADAS_PATH, 'r') as f:
        return json.load(f)

def save_published(data):
    with open(PUBLICADAS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def add_published(entry):
    pub = load_published()
    pub.insert(0, entry)
    save_published(pub)

def remove_published(card_id):
    pub = load_published()
    pub = [p for p in pub if p['id'] != card_id]
    save_published(pub)
