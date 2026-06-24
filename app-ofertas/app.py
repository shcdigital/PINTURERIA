import os, json, re, threading, time, webbrowser, sys, shutil
from flask import Flask, request, jsonify
from config_manager import load as load_config, save as save_config
from github_api import test_connection, get_file_contents, put_file_contents
from card_generator import generate_card_html, insert_card_in_html, update_index_html

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    APP_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = BASE_DIR

app = Flask(__name__)
PORT = 3456

DRAFTS_DIR = os.path.join(BASE_DIR, 'drafts')
os.makedirs(DRAFTS_DIR, exist_ok=True)

if APP_DIR != BASE_DIR and not os.listdir(DRAFTS_DIR):
    bundled_drafts = os.path.join(APP_DIR, 'drafts')
    if os.path.exists(bundled_drafts):
        for fname in os.listdir(bundled_drafts):
            if fname.endswith('.json'):
                shutil.copy2(os.path.join(bundled_drafts, fname), os.path.join(DRAFTS_DIR, fname))

# ─── Embeber CSS + JS en el HTML ────────────────────
def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

try:
    css = _read(os.path.join(APP_DIR, 'static', 'styles.css'))
    js = _read(os.path.join(APP_DIR, 'static', 'app.js'))
    html_raw = _read(os.path.join(APP_DIR, 'static', 'index.html'))
except FileNotFoundError:
    css = _read(os.path.join(BASE_DIR, 'static', 'styles.css'))
    js = _read(os.path.join(BASE_DIR, 'static', 'app.js'))
    html_raw = _read(os.path.join(BASE_DIR, 'static', 'index.html'))

# Quitar referencias externas e inyectar CSS/JS inline
html = html_raw \
    .replace('<link rel="stylesheet" href="/static/styles.css" />', '') \
    .replace('<script src="/static/app.js"></script>', '')
html = html.replace('</head>', f'<style>{css}</style></head>')
html = html.replace('</body>', f'<script>{js}</script></body>')

# ─── API ────────────────────────────────────────────

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        c = load_config()
        return jsonify({'token': c['token'][:8] + '\u2022\u2022\u2022\u2022' if c['token'] else '', 'repo': c['repo'], 'has_token': bool(c['token'])})
    data = request.json
    save_config({'token': data['token'], 'repo': data['repo']})
    return jsonify({'ok': True})

@app.route('/api/test', methods=['POST'])
def api_test():
    data = request.json
    ok, code = test_connection(data['token'], data['repo'])
    return jsonify({'ok': ok, 'status': code})

@app.route('/api/ofertas', methods=['GET'])
def api_list_ofertas():
    drafts = []
    if os.path.exists(DRAFTS_DIR):
        for fname in sorted(os.listdir(DRAFTS_DIR), reverse=True):
            if fname.endswith('.json'):
                with open(os.path.join(DRAFTS_DIR, fname)) as f:
                    draft = json.load(f)
                    draft['tipo'] = 'borrador'
                    draft['archivo'] = fname
                    drafts.append(draft)

    publicadas = []
    cfg = load_config()
    if cfg['token'] and cfg['repo']:
        content, _, _ = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
        if content:
            cards = re.findall(r'<div class="offer-card reveal">(.*?)</div>', content, re.DOTALL)
            for card in cards:
                nombre = re.search(r'<h3>(.*?)</h3>', card)
                precio = re.search(r'class="offer-price">\$(.*?)</span>', card)
                publicadas.append({
                    'tipo': 'publicada',
                    'nombre': nombre.group(1) if nombre else 'Sin nombre',
                    'precio_oferta': precio.group(1) if precio else '0',
                })

    return jsonify({'borradores': drafts, 'publicadas': publicadas})

@app.route('/api/ofertas/borrador', methods=['POST'])
def api_save_borrador():
    data = request.json
    fname = f"borrador_{int(time.time())}.json"
    with open(os.path.join(DRAFTS_DIR, fname), 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'ok': True, 'archivo': fname})

@app.route('/api/ofertas/publicar', methods=['POST'])
def api_publicar():
    data = request.json
    cfg = load_config()
    if not cfg['token'] or not cfg['repo']:
        return jsonify({'ok': False, 'error': 'Configur\u00e1 el token y repo primero'}), 400

    foto = data.get('foto', '')
    nombre = data.get('nombre', 'Producto')
    desc = data.get('descripcion', '')
    precio = data.get('precio_original', '0')
    descuento = data.get('descuento', '0')

    card_html = generate_card_html(foto, nombre, desc, precio, descuento)

    ofertas_html, sha_ofertas, err = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
    if err:
        return jsonify({'ok': False, 'error': f'No se pudo leer ofertas.html: {err}'}), 500

    nuevo_ofertas = insert_card_in_html(ofertas_html, card_html)
    ok, err = put_file_contents(cfg['token'], cfg['repo'], 'ofertas.html', nuevo_ofertas, f'Agregar oferta: {nombre}')
    if not ok:
        return jsonify({'ok': False, 'error': f'Error al actualizar ofertas.html: {err}'}), 500

    index_html, sha_index, err = get_file_contents(cfg['token'], cfg['repo'], 'index.html')
    if not err:
        todas_cards = re.findall(r'<div class="offer-card reveal">.*?</div>', nuevo_ofertas, re.DOTALL)
        if todas_cards:
            nuevo_index = update_index_html(index_html, todas_cards, max_cards=3)
            if nuevo_index != index_html:
                put_file_contents(cfg['token'], cfg['repo'], 'index.html', nuevo_index, 'Actualizar ofertas destacadas')

    archivo = data.get('archivo_borrador')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        if os.path.exists(path):
            os.remove(path)

    return jsonify({'ok': True})

@app.route('/api/ofertas/eliminar', methods=['POST'])
def api_eliminar():
    data = request.json
    archivo = data.get('archivo_borrador')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        if os.path.exists(path):
            os.remove(path)
    return jsonify({'ok': True})

@app.route('/')
def index():
    return html

def open_browser():
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    print(f'Gestor de Ofertas Proveesur')
    print(f'Abr\u00ed http://localhost:{PORT} en tu navegador')
    app.run(host='127.0.0.1', port=PORT, debug=False)
