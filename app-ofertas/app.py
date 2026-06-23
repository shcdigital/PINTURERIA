import os, json, re, threading, time, webbrowser
from flask import Flask, request, jsonify, send_from_directory
from config_manager import load as load_config, save as save_config
from github_api import test_connection, get_file_contents, put_file_contents
from card_generator import generate_card_html, insert_card_in_html, update_index_html

app = Flask(__name__, static_folder='static')
PORT = 3456
DRAFTS_DIR = os.path.join(os.path.dirname(__file__), 'drafts')

os.makedirs(DRAFTS_DIR, exist_ok=True)

# ─── Config ─────────────────────────────────────────────

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        c = load_config()
        return jsonify({'token': c['token'][:8] + '••••' if c['token'] else '', 'repo': c['repo'], 'has_token': bool(c['token'])})
    data = request.json
    save_config({'token': data['token'], 'repo': data['repo']})
    return jsonify({'ok': True})

@app.route('/api/test', methods=['POST'])
def api_test():
    data = request.json
    ok, code = test_connection(data['token'], data['repo'])
    return jsonify({'ok': ok, 'status': code})

# ─── Borradores locales ────────────────────────────────

@app.route('/api/ofertas', methods=['GET'])
def api_list_ofertas():
    drafts = []
    if os.path.exists(DRAFTS_DIR):
        for fname in sorted(os.listdir(DRAFTS_DIR), reverse=True):
            if fname.endswith('.json'):
                with open(os.path.join(DRAFTS_DIR, fname), 'r') as f:
                    draft = json.load(f)
                    draft['tipo'] = 'borrador'
                    draft['archivo'] = fname
                    drafts.append(draft)

    publicadas = []
    cfg = load_config()
    if cfg['token'] and cfg['repo']:
        html, _, _ = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
        if html:
            cards = re.findall(r'<div class="offer-card reveal">(.*?)</div>', html, re.DOTALL)
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

# ─── Publicar en GitHub ─────────────────────────────────

@app.route('/api/ofertas/publicar', methods=['POST'])
def api_publicar():
    data = request.json
    cfg = load_config()
    if not cfg['token'] or not cfg['repo']:
        return jsonify({'ok': False, 'error': 'Configurá el token y repo primero'}), 400

    foto = data.get('foto', '')
    nombre = data.get('nombre', 'Producto')
    desc = data.get('descripcion', '')
    precio = data.get('precio_original', '0')
    descuento = data.get('descuento', '0')

    card_html = generate_card_html(foto, nombre, desc, precio, descuento)

    # Actualizar ofertas.html
    ofertas_html, sha_ofertas, err = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
    if err:
        return jsonify({'ok': False, 'error': f'No se pudo leer ofertas.html: {err}'}), 500

    nuevo_ofertas = insert_card_in_html(ofertas_html, card_html)
    ok, err = put_file_contents(cfg['token'], cfg['repo'], 'ofertas.html', nuevo_ofertas, f'Agregar oferta: {nombre}')
    if not ok:
        return jsonify({'ok': False, 'error': f'Error al actualizar ofertas.html: {err}'}), 500

    # Actualizar index.html (solo las 3 primeras ofertas)
    index_html, sha_index, err = get_file_contents(cfg['token'], cfg['repo'], 'index.html')
    if not err:
        todas_cards = re.findall(r'<div class="offer-card reveal">.*?</div>', nuevo_ofertas, re.DOTALL)
        if todas_cards:
            nuevo_index = update_index_html(index_html, todas_cards, max_cards=3)
            if nuevo_index != index_html:
                put_file_contents(cfg['token'], cfg['repo'], 'index.html', nuevo_index, 'Actualizar ofertas destacadas')

    # Borrar borrador si se publicó desde uno
    archivo = data.get('archivo_borrador')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        if os.path.exists(path):
            os.remove(path)

    return jsonify({'ok': True})

# ─── Eliminar ────────────────────────────────────────────

@app.route('/api/ofertas/eliminar', methods=['POST'])
def api_eliminar():
    data = request.json
    archivo = data.get('archivo_borrador')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        if os.path.exists(path):
            os.remove(path)
    return jsonify({'ok': True})

# ─── Frontend ────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

def open_browser():
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    print(f'🔧 Gestor de Ofertas Proveesur')
    print(f'📋 Abrí http://localhost:{PORT} en tu navegador')
    app.run(host='127.0.0.1', port=PORT, debug=False)
