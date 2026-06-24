import os, json, re, threading, time, webbrowser, sys, traceback, urllib.request, subprocess, io, base64
from PIL import Image

if getattr(sys, 'frozen', False):
    DATA_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GestorOfertasProveesur')
else:
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))

os.makedirs(DATA_DIR, exist_ok=True)

TIENDA = "pintureria_cliente"

LOG = os.path.join(DATA_DIR, 'app.log')

def log(msg):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')

log('=== App iniciada ===')

from flask import Flask, request, jsonify
from config_manager import load as load_config, save as save_config, load_published, save_published, add_published, remove_published
from github_api import test_connection, get_file_contents, put_file_contents, delete_file, list_files_in_dir
from card_generator import generate_card_html, insert_card_in_html, update_index_html, remove_card_by_id, inject_expiry_script, extract_card_by_id

app = Flask(__name__, static_folder=None)
PORT = 3456

DRAFTS_DIR = os.path.join(DATA_DIR, 'drafts')
os.makedirs(DRAFTS_DIR, exist_ok=True)

# ─── Quitar fondo con Pillow ───────────────────────

def quitar_fondo_pillow(imagen, threshold=50):
    """Remove background using color distance. threshold (10-150): lower = gentler, higher = more aggressive."""
    img = imagen.convert('RGBA')
    pixels = img.load()
    w, h = img.size

    sample_colors = []
    for x in range(0, w, max(1, w // 20)):
        for y in range(0, h, max(1, h // 20)):
            if x < 3 or y < 3 or x >= w - 3 or y >= h - 3:
                c = pixels[x, y][:3]
                sample_colors.append(c)
    if not sample_colors:
        return img

    bg_r = sum(c[0] for c in sample_colors) / len(sample_colors)
    bg_g = sum(c[1] for c in sample_colors) / len(sample_colors)
    bg_b = sum(c[2] for c in sample_colors) / len(sample_colors)

    for x in range(w):
        for y in range(h):
            r, g, b, a = pixels[x, y]
            dist = ((r - bg_r) ** 2 + (g - bg_g) ** 2 + (b - bg_b) ** 2) ** 0.5
            if dist < threshold:
                pixels[x, y] = (r, g, b, 0)

    return img

# ─── Shutdown endpoint ────────────────────────────

SHUTDOWN_FILE = os.path.join(DATA_DIR, '.cerrar')
if os.path.exists(SHUTDOWN_FILE):
    os.remove(SHUTDOWN_FILE)

def _read_static(name):
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = os.path.join(sys._MEIPASS, 'static')
    else:
        base = os.path.join(DATA_DIR, 'static')
    path = os.path.join(base, name)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    return '/* not found */'

CSS = _read_static('styles.css')
JS = _read_static('app.js')
HTML_BODY = _read_static('index.html')

HTML_HEAD = f'<!DOCTYPE html>\n<html lang="es-AR">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Gestor de Ofertas &middot; {TIENDA}</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">\n<style>\n' + CSS + '\n</style>\n</head>\n<body>\n'
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

# ─── Imagen ─────────────────────────────────────────

MAX_IMG_W = 800
IMG_QUALITY = 85

@app.route('/api/imagen/procesar', methods=['POST'])
def api_procesar_imagen():
    data = request.json
    b64 = data.get('imagen', '')
    if not b64:
        return jsonify({'ok': False, 'error': 'Falta imagen'}), 400

    threshold = data.get('threshold', 50)
    try:
        threshold = int(threshold)
        threshold = max(10, min(150, threshold))
    except (ValueError, TypeError):
        threshold = 50

    try:
        header, encoded = b64.split(',', 1) if ',' in b64 else ('', b64)
        raw = base64.b64decode(encoded)

        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        if w > MAX_IMG_W:
            ratio = MAX_IMG_W / w
            img = img.resize((MAX_IMG_W, int(h * ratio)), Image.LANCZOS)

        img = quitar_fondo_pillow(img, threshold=threshold)

        out_buf = io.BytesIO()
        img.save(out_buf, format='PNG')
        result = base64.b64encode(out_buf.getvalue()).decode('utf-8')
        result_b64 = 'data:image/png;base64,' + result

        return jsonify({'ok': True, 'imagen': result_b64})
    except Exception as e:
        log(f'Error procesando imagen: {e}')
        log(traceback.format_exc())
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/imagen/solo_optimizar', methods=['POST'])
def api_optimizar_imagen():
    data = request.json
    b64 = data.get('imagen', '')
    if not b64:
        return jsonify({'ok': False, 'error': 'Falta imagen'}), 400

    try:
        header, encoded = b64.split(',', 1) if ',' in b64 else ('', b64)
        raw = base64.b64decode(encoded)

        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        if w > MAX_IMG_W:
            ratio = MAX_IMG_W / w
            img = img.resize((MAX_IMG_W, int(h * ratio)), Image.LANCZOS)

        out_buf = io.BytesIO()
        img.save(out_buf, format='JPEG', quality=IMG_QUALITY)
        result = base64.b64encode(out_buf.getvalue()).decode('utf-8')
        result_b64 = 'data:image/jpeg;base64,' + result

        return jsonify({'ok': True, 'imagen': result_b64})
    except Exception as e:
        log(f'Error optimizando: {e}')
        return jsonify({'ok': False, 'error': str(e)}), 500

# ─── Shutdown ───────────────────────────────────────

@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    with open(SHUTDOWN_FILE, 'w') as f:
        f.write('cerrar')
    return jsonify({'ok': True})

@app.route('/api/rembg/status', methods=['GET'])
def api_rembg_status():
    return jsonify({'disponible': True, 'metodo': 'pillow'})

# ─── Diagnostic ─────────────────────────────────────

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
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)

def _wait_flask():
    for _ in range(30):
        try:
            urllib.request.urlopen(f'http://127.0.0.1:{PORT}/')
            return True
        except Exception:
            time.sleep(0.3)
    return False

def _chrome_app(url):
    candidates = [
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
    ]
    for p in candidates:
        if os.path.exists(p):
            log(f'Chrome encontrado en: {p}')
            subprocess.Popen([p, f'--app={url}'], shell=False)
            return True
    log('Chrome no encontrado en rutas conocidas')
    return False

if __name__ == '__main__':
    if '--uninstall' in sys.argv:
        sys.exit(0)

    threading.Thread(target=start_server, daemon=True).start()
    ready = _wait_flask()
    log(f'Flask ready={ready}')

    url = f'http://localhost:{PORT}'
    log(f'Abriendo ventana app en {url}')

    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0
        )

    if not _chrome_app(url):
        log('Usando navegador por defecto')
        webbrowser.open(url)

    while True:
        if os.path.exists(SHUTDOWN_FILE):
            log('Shutdown solicitado')
            break
        time.sleep(1)
