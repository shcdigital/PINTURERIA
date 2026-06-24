import os, json, re, threading, time, webbrowser, sys, traceback

LOG = os.path.join(
    os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)),
    'app.log'
)

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')

log('=== App iniciada ===')

try:
    import webview
    HAS_WEBVIEW = True
    log('webview importado OK')
except ImportError:
    HAS_WEBVIEW = False
    log('webview NO disponible')

from flask import Flask, request, jsonify
from config_manager import load as load_config, save as save_config, load_published, save_published, add_published, remove_published
from github_api import test_connection, get_file_contents, put_file_contents, delete_file, list_files_in_dir
from card_generator import generate_card_html, insert_card_in_html, update_index_html, remove_card_by_id, inject_expiry_script, extract_card_by_id

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)
PORT = 3456

DRAFTS_DIR = os.path.join(BASE_DIR, 'drafts')
os.makedirs(DRAFTS_DIR, exist_ok=True)

def _read_static(name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = os.path.join(sys._MEIPASS, 'static')
    else:
        base = os.path.join(BASE_DIR, 'static')
    path = os.path.join(base, name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return '/* not found */'

CSS = _read_static('styles.css')
JS = _read_static('app.js')
HTML_BODY = _read_static('index.html')

HTML_HEAD = '<!DOCTYPE html>\n<html lang="es-AR">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Gestor de Ofertas &middot; Proveesur</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">\n<style>\n' + CSS + '\n</style>\n</head>\n<body>\n'
HTML_FOOT = '<script>\n' + JS + '\n</script>\n</body>\n</html>'
HTML = HTML_HEAD + HTML_BODY + HTML_FOOT

# ─── API ────────────────────────────────────────────

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    if request.method == 'GET':
        c = load_config()
        hidden = c['token'][:8] + '\u2022\u2022\u2022\u2022' if c['token'] else ''
        return jsonify({'token': hidden, 'repo': c['repo'], 'has_token': bool(c['token'])})
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
                with open(os.path.join(DRAFTS_DIR, fname), encoding='utf-8') as f:
                    draft = json.load(f)
                    draft['tipo'] = 'borrador'
                    draft['archivo'] = fname
                    drafts.append(draft)
    publicadas = load_published()
    return jsonify({'borradores': drafts, 'publicadas': publicadas})

@app.route('/api/ofertas/borrador', methods=['POST'])
def api_save_borrador():
    data = request.json
    archivo = data.get('archivo_borrador', '')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True, 'archivo': archivo})
    fname = f"borrador_{int(time.time())}.json"
    with open(os.path.join(DRAFTS_DIR, fname), 'w', encoding='utf-8') as f:
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
    vencimiento = data.get('vencimiento', '')

    card_id, card_html = generate_card_html(foto, nombre, desc, precio, descuento, vencimiento)

    ofertas_html, sha_ofertas, err = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
    if err:
        return jsonify({'ok': False, 'error': f'No se pudo leer ofertas.html: {err}'}), 500

    nuevo_ofertas = insert_card_in_html(ofertas_html, card_html)
    nuevo_ofertas = inject_expiry_script(nuevo_ofertas)

    ok, err = put_file_contents(cfg['token'], cfg['repo'], 'ofertas.html', nuevo_ofertas, f'Agregar oferta: {nombre}')
    if not ok:
        return jsonify({'ok': False, 'error': f'Error al actualizar ofertas.html: {err}'}), 500

    index_html, sha_index, err = get_file_contents(cfg['token'], cfg['repo'], 'index.html')
    if not err:
        nuevas_cards = re.findall(r'<div class="offer-card reveal".*?</div>', nuevo_ofertas, re.DOTALL)
        if nuevas_cards:
            nuevo_index = update_index_html(index_html, nuevas_cards, max_cards=3)
            if nuevo_index != index_html:
                nuevo_index = inject_expiry_script(nuevo_index)
                put_file_contents(cfg['token'], cfg['repo'], 'index.html', nuevo_index, 'Actualizar ofertas destacadas')

    precio_oferta = int(int(precio) * (100 - int(descuento)) / 100)
    add_published({
        'id': card_id,
        'nombre': nombre,
        'precio_oferta': precio_oferta,
        'precio_original': precio,
        'descuento': descuento,
        'vencimiento': vencimiento,
    })

    archivo = data.get('archivo_borrador')
    if archivo:
        path = os.path.join(DRAFTS_DIR, archivo)
        if os.path.exists(path):
            os.remove(path)

    return jsonify({'ok': True, 'card_id': card_id})

@app.route('/api/ofertas/eliminar_publicada', methods=['POST'])
def api_eliminar_publicada():
    data = request.json
    card_id = data.get('id', '')
    if not card_id:
        return jsonify({'ok': False, 'error': 'Falta id'}), 400

    cfg = load_config()
    if not cfg['token'] or not cfg['repo']:
        return jsonify({'ok': False, 'error': 'Configur\u00e1 el token y repo primero'}), 400

    ofertas_html, sha_ofertas, err = get_file_contents(cfg['token'], cfg['repo'], 'ofertas.html')
    if err:
        return jsonify({'ok': False, 'error': f'No se pudo leer ofertas.html: {err}'}), 500

    card_html = extract_card_by_id(ofertas_html, card_id)
    if not card_html:
        return jsonify({'ok': False, 'error': 'Oferta no encontrada en ofertas.html'}), 404

    nuevo_ofertas, removed = remove_card_by_id(ofertas_html, card_id)
    if removed is None:
        return jsonify({'ok': False, 'error': 'No se pudo eliminar la card'}), 500

    ok, err = put_file_contents(cfg['token'], cfg['repo'], 'ofertas.html', nuevo_ofertas, f'Eliminar oferta: {card_id}')
    if not ok:
        return jsonify({'ok': False, 'error': f'Error al actualizar ofertas.html: {err}'}), 500

    bak_filename = f'of_{int(time.time()*1000)}.bak.html'
    bak_path = f'.bak/{bak_filename}'
    ok, err = put_file_contents(cfg['token'], cfg['repo'], bak_path, f'<!-- Backup of {card_id} -->\n' + card_html, f'Backup of deleted offer {card_id}')
    if not ok:
        pass

    bak_files, _ = list_files_in_dir(cfg['token'], cfg['repo'], '.bak')
    if bak_files and len(bak_files) > 10:
        bak_files_sorted = sorted(bak_files, key=lambda x: x['name'])
        for old in bak_files_sorted[:-10]:
            delete_file(cfg['token'], cfg['repo'], f'.bak/{old["name"]}', f'Cleanup old backup: {old["name"]}')

    remove_published(card_id)

    index_html, sha_index, err = get_file_contents(cfg['token'], cfg['repo'], 'index.html')
    if not err:
        cards_en_index = re.findall(r'<div class="offer-card reveal".*?</div>', index_html, re.DOTALL)
        card_ids_in_index = re.findall(r'data-id="(of_\d+)"', index_html)
        if card_id in card_ids_in_index:
            nuevo_index, _ = remove_card_by_id(index_html, card_id)
            if nuevo_index != index_html:
                put_file_contents(cfg['token'], cfg['repo'], 'index.html', nuevo_index, f'Eliminar oferta destacada: {card_id}')

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

@app.route('/check')
def check():
    has_css_ref = 'styles.css' in HTML
    has_js_ref = 'app.js' in HTML
    css_len = len(CSS)
    js_len = len(JS)
    return jsonify({'version': '2026-06-24-filebased', 'has_css_ref': has_css_ref, 'has_js_ref': has_js_ref, 'css_len': css_len, 'js_len': js_len, 'drafts_dir': DRAFTS_DIR})

@app.route('/debug')
def debug():
    return '<pre>' + HTML.replace('&', '&amp;').replace('<', '&lt;') + '</pre>'

@app.route('/')
def index():
    return HTML

def start_server():
    app.run(host='127.0.0.1', port=PORT, debug=False)

if __name__ == '__main__':
    threading.Thread(target=start_server, daemon=True).start()
    time.sleep(1.5)

    if HAS_WEBVIEW:
        log('Intentando abrir ventana nativa...')
        try:
            webview.create_window(
                'Gestor de Ofertas · Proveesur',
                f'http://localhost:{PORT}',
                width=1100, height=750,
                resizable=True,
            )
            log('Ventana cerrada normalmente')
        except Exception as e:
            log(f'ERROR en webview: {e}')
            log(traceback.format_exc())
            webbrowser.open(f'http://localhost:{PORT}')
            log('Fallback a navegador')
            while True:
                time.sleep(1)
    else:
        log('Abriendo navegador (sin pywebview)')
        webbrowser.open(f'http://localhost:{PORT}')
        while True:
            time.sleep(1)
