import os, json, re, threading, time, webbrowser, sys, shutil
from flask import Flask, request, jsonify
from config_manager import load as load_config, save as save_config
from github_api import test_connection, get_file_contents, put_file_contents
from card_generator import generate_card_html, insert_card_in_html, update_index_html

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
PORT = 3456

DRAFTS_DIR = os.path.join(BASE_DIR, 'drafts')
os.makedirs(DRAFTS_DIR, exist_ok=True)

# ─── CSS incrustado ─────────────────────────────────
CSS = """:root {
  --cream: #FBF7F1; --cream-deep: #F3ECE0; --rose-soft: #FBE6E4;
  --sky-soft: #E4EEFB; --mint-soft: #E2F3EA; --sun-soft: #FBF1D2;
  --ink: #1A1A1F; --ink-soft: #4B4B55; --red: #E63946; --blue: #2E6FE6;
  --yellow: #F5B800; --green: #2E9E6B;
  --shadow-soft: 0 10px 30px -12px rgba(26,26,31,0.12);
  --shadow-lift: 0 20px 50px -20px rgba(26,26,31,0.25);
}
* { -webkit-font-smoothing: antialiased; box-sizing: border-box; }
body {
  font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
  background: var(--cream); color: var(--ink);
  margin: 0; padding: 0; font-size: 16px;
}
.app-header {
  background: rgba(251,247,241,0.92);
  backdrop-filter: saturate(180%) blur(12px);
  border-bottom: 1px solid var(--cream-deep);
  padding: 1.25rem 2rem;
  display: flex; align-items: center;
  justify-content: space-between;
  position: sticky; top: 0; z-index: 50;
}
.logo-text { font-family: 'Caveat', cursive; font-weight: 700; font-size: 1.8rem; letter-spacing: -0.5px; line-height: 1; }
.logo-text .l1 { color: var(--red); }
.logo-text .l2 { color: var(--blue); }
.logo-text .l3 { color: var(--yellow); }
.logo-text .l4 { color: var(--green); }
.container { max-width: 1100px; margin: 0 auto; padding: 2rem; }
.card { background: white; border-radius: 1.25rem; box-shadow: var(--shadow-soft); padding: 1.75rem; }
.btn {
  display: inline-flex; align-items: center; gap: 0.5rem;
  padding: 0.8rem 1.5rem; border-radius: 999px; font-weight: 600;
  font-size: 1rem; border: none; cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  text-decoration: none; line-height: 1.3;
}
.btn:hover { transform: translateY(-2px); }
.btn:active { transform: translateY(0); }
.btn-primary { background: linear-gradient(135deg, var(--red), #D62839); color: white; box-shadow: 0 8px 20px -6px rgba(230,57,70,0.4); }
.btn-secondary { background: var(--cream-deep); color: var(--ink); }
.btn-green { background: #25D366; color: white; box-shadow: 0 8px 20px -6px rgba(37,211,102,0.4); }
.btn-sm { padding: 0.55rem 1.2rem; font-size: 0.9rem; }
.btn-danger { background: var(--red); color: white; }
.btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none !important; }
.form-field {
  width: 100%; padding: 0.85rem 1.1rem; border: 2px solid var(--cream-deep);
  border-radius: 0.85rem; background: white; font-family: inherit;
  font-size: 1rem; transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.form-field:focus { outline: none; border-color: var(--blue); box-shadow: 0 0 0 4px rgba(46,111,230,0.12); }
.form-label { display: block; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.4rem; }
.dropzone {
  border: 2px dashed var(--cream-deep); border-radius: 1rem;
  padding: 2.5rem 2rem; text-align: center; cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease; background: white;
}
.dropzone:hover, .dropzone.dragover { border-color: var(--blue); background: var(--sky-soft); }
.dropzone img { max-height: 180px; border-radius: 0.75rem; margin-top: 0.5rem; }
.offer-card-preview {
  background: white; border-radius: 1.25rem; box-shadow: var(--shadow-soft);
  overflow: hidden; position: relative; max-width: 380px;
}
.offer-card-preview .offer-badge {
  position: absolute; top: 12px; left: 12px; width: 56px; height: 56px;
  border-radius: 50%; background: var(--red); color: white; font-weight: 800;
  font-size: 0.9rem; display: flex; align-items: center;
  justify-content: center; z-index: 2;
  box-shadow: 0 4px 12px rgba(230,57,70,0.4);
}
.offer-card-preview img { width: 100%; height: 200px; object-fit: cover; display: block; }
.offer-card-preview .card-body { padding: 1.25rem; }
.offer-card-preview h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.4rem; }
.offer-card-preview p { font-size: 0.95rem; color: var(--ink-soft); margin-bottom: 0.75rem; }
.old-price { font-size: 1rem; color: var(--ink-soft); text-decoration: line-through; margin-right: 0.5rem; }
.offer-price { font-size: 1.35rem; font-weight: 800; color: var(--red); }
.section-title { font-size: 1.4rem; font-weight: 700; margin-bottom: 1.25rem; }
.badge {
  display: inline-flex; align-items: center; gap: 0.35rem;
  padding: 0.3rem 0.85rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600;
}
.badge-draft { background: var(--sun-soft); color: #8A6A00; }
.badge-published { background: var(--mint-soft); color: var(--green); }
.offer-list-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 1.25rem; border-bottom: 1px solid var(--cream-deep); gap: 1rem;
}
.offer-list-item:last-child { border-bottom: none; }
.offer-list-item strong { font-size: 1rem; }
.empty-state { text-align: center; padding: 2.5rem 2rem; color: var(--ink-soft); font-size: 1rem; }
.spinner {
  display: inline-block; width: 1.2em; height: 1.2em;
  border: 2px solid rgba(255,255,255,0.3); border-top-color: white;
  border-radius: 50%; animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.toast {
  position: fixed; top: 20px; right: 20px; padding: 1rem 1.5rem;
  background: white; border-left: 4px solid var(--green);
  border-radius: 0.5rem; box-shadow: var(--shadow-lift); z-index: 100;
  transform: translateX(120%); transition: transform 0.4s ease; font-size: 1rem;
}
.toast.show { transform: translateX(0); }
.toast.error { border-left-color: var(--red); }
.cta-bar {
  display: flex; gap: 0.75rem; flex-wrap: wrap;
  margin-top: 1.25rem; padding-top: 1.25rem;
  border-top: 1px solid var(--cream-deep);
}
.hidden { display: none !important; }
@media (max-width: 640px) { .container { padding: 1rem; } }
"""

# ─── JS incrustado (original, con template literals) ─
JS = """let ofertasData = { borradores: [], publicadas: [] };
let fotoBase64 = null;

function showToast(text, type = 'success') {
  const t = document.getElementById('toast');
  const txt = document.getElementById('toast-text');
  txt.textContent = text;
  t.className = 'toast' + (type === 'error' ? ' error' : '');
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 3500);
}

function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}

async function loadDashboard() {
  showView('view-dashboard');
  try {
    const r = await fetch('/api/ofertas');
    ofertasData = await r.json();
  } catch {
    ofertasData = { borradores: [], publicadas: [] };
  }
  renderDashboard();
}

function renderDashboard() {
  const draftList = document.getElementById('draft-list');
  const pubList = document.getElementById('published-list');

  if (ofertasData.borradores.length === 0) {
    draftList.innerHTML = '<div class="empty-state">No ten\u00e9s borradores.</div>';
  } else {
    draftList.innerHTML = ofertasData.borradores.map(d => `
      <div class="offer-list-item">
        <div>
          <strong>${d.nombre || 'Sin nombre'}</strong>
          <div><span class="badge badge-draft">Borrador</span></div>
        </div>
        <div class="flex" style="display:flex;gap:0.5rem">
          <button class="btn btn-secondary btn-sm" onclick="editarBorrador('${d.archivo}')">Editar</button>
          <button class="btn btn-green btn-sm" onclick="publicarOferta('${d.archivo}')">Publicar</button>
          <button class="btn btn-danger btn-sm" onclick="eliminarBorrador('${d.archivo}')">\u2715</button>
        </div>
      </div>
    `).join('');
  }

  if (ofertasData.publicadas.length === 0) {
    pubList.innerHTML = '<div class="empty-state">Todav\u00eda no publicaste ofertas.</div>';
  } else {
    pubList.innerHTML = ofertasData.publicadas.map(p => `
      <div class="offer-list-item">
        <div>
          <strong>${p.nombre}</strong>
          <div><span class="badge badge-published">Publicada \u00b7 $${p.precio_oferta}</span></div>
        </div>
        <a href="ofertas.html" target="_blank" class="btn btn-secondary btn-sm">Ver online</a>
      </div>
    `).join('');
  }

  document.getElementById('draft-count').textContent = ofertasData.borradores.length;
  document.getElementById('published-count').textContent = ofertasData.publicadas.length;
}

function nuevaOferta() {
  document.getElementById('form-title').textContent = 'Nueva oferta';
  document.getElementById('offer-form').reset();
  fotoBase64 = null;
  document.getElementById('preview-foto').src = '';
  document.getElementById('preview-foto').classList.add('hidden');
  document.getElementById('preview-foto-card').src = '';
  document.getElementById('preview-foto-card').style.display = 'none';
  document.getElementById('preview-placeholder').style.display = 'flex';
  document.getElementById('archivo-borrador').value = '';
  actualizarPreview();
  showView('view-form');
}

function editarBorrador(archivo) {
  const d = ofertasData.borradores.find(b => b.archivo === archivo);
  if (!d) return;
  document.getElementById('form-title').textContent = 'Editar oferta';
  document.getElementById('offer-name').value = d.nombre || '';
  document.getElementById('offer-desc').value = d.descripcion || '';
  document.getElementById('offer-price').value = d.precio_original || '';
  document.getElementById('offer-discount').value = d.descuento || '20';
  document.getElementById('archivo-borrador').value = archivo;
  fotoBase64 = d.foto || null;
  if (fotoBase64) {
    document.getElementById('preview-foto').src = fotoBase64;
    document.getElementById('preview-foto').classList.remove('hidden');
    document.getElementById('preview-foto-card').src = fotoBase64;
    document.getElementById('preview-foto-card').style.display = 'block';
    document.getElementById('preview-placeholder').style.display = 'none';
  }
  actualizarPreview();
  showView('view-form');
}

function setupDropzone() {
  const dz = document.getElementById('dropzone');
  const input = document.getElementById('foto-input');

  dz.addEventListener('click', () => input.click());
  input.addEventListener('change', (e) => {
    if (e.target.files[0]) procesarFoto(e.target.files[0]);
  });

  dz.addEventListener('dragover', (e) => { e.preventDefault(); dz.classList.add('dragover'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
  dz.addEventListener('drop', (e) => {
    e.preventDefault();
    dz.classList.remove('dragover');
    if (e.dataTransfer.files[0]) procesarFoto(e.dataTransfer.files[0]);
  });
}

function procesarFoto(file) {
  if (!file.type.startsWith('image/')) return showToast('Solo im\u00e1genes (JPG, PNG)', 'error');
  const reader = new FileReader();
  reader.onload = (e) => {
    fotoBase64 = e.target.result;
    document.getElementById('preview-foto').src = fotoBase64;
    document.getElementById('preview-foto').classList.remove('hidden');
    document.getElementById('preview-foto-card').src = fotoBase64;
    document.getElementById('preview-foto-card').style.display = 'block';
    document.getElementById('preview-placeholder').style.display = 'none';
    actualizarPreview();
  };
  reader.readAsDataURL(file);
}

function actualizarPreview() {
  const nombre = document.getElementById('offer-name').value || 'Nombre del producto';
  const desc = document.getElementById('offer-desc').value || 'Descripci\u00f3n breve del producto.';
  const precio = document.getElementById('offer-price').value || '10000';
  const descuento = parseInt(document.getElementById('offer-discount').value) || 20;
  const precioOferta = Math.round(parseInt(precio) * (100 - descuento) / 100);

  document.getElementById('preview-nombre').textContent = nombre;
  document.getElementById('preview-desc').textContent = desc;
  document.getElementById('preview-old-price').textContent = '$' + parseInt(precio).toLocaleString();
  document.getElementById('preview-offer-price').textContent = '$' + precioOferta.toLocaleString();
  document.getElementById('preview-badge').textContent = '-' + descuento + '%';

  if (fotoBase64) {
    document.getElementById('preview-foto-card').src = fotoBase64;
    document.getElementById('preview-foto-card').style.display = 'block';
    document.getElementById('preview-placeholder').style.display = 'none';
  } else {
    document.getElementById('preview-foto').src = '';
    document.getElementById('preview-foto').classList.add('hidden');
    document.getElementById('preview-foto-card').style.display = 'none';
    document.getElementById('preview-placeholder').style.display = 'flex';
  }
}

async function guardarBorrador() {
  const data = getFormData();
  if (!data.nombre) return showToast('Complet\u00e1 el nombre del producto.', 'error');

  const r = await fetch('/api/ofertas/borrador', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (r.ok) {
    showToast('Borrador guardado \u2705');
    loadDashboard();
  } else {
    showToast('Error al guardar', 'error');
  }
}

async function publicarOferta(archivoBorrador) {
  const confirmar = confirm('\u00bfPublicar esta oferta en GitHub? Aparecer\u00e1 en la web en ~1-2 minutos.');
  if (!confirmar) return;

  let data;
  if (archivoBorrador) {
    const d = ofertasData.borradores.find(b => b.archivo === archivoBorrador);
    if (!d) return;
    data = { ...d, archivo_borrador: archivoBorrador };
  } else {
    data = getFormData();
    if (!data.nombre) return showToast('Complet\u00e1 el nombre del producto.', 'error');
    data.archivo_borrador = document.getElementById('archivo-borrador').value || null;
  }

  const btn = document.getElementById('btn-publicar');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Publicando...';

  try {
    const r = await fetch('/api/ofertas/publicar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const res = await r.json();
    if (res.ok) {
      showToast('\u2705 Oferta publicada. En ~1 min est\u00e1 online.');
      loadDashboard();
    } else {
      showToast('Error: ' + (res.error || 'desconocido'), 'error');
    }
  } catch {
    showToast('Error de conexi\u00f3n con el servidor', 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '\ud83c\udf10 Publicar';
}

async function eliminarBorrador(archivo) {
  if (!confirm('\u00bfEliminar este borrador?')) return;
  await fetch('/api/ofertas/eliminar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ archivo_borrador: archivo }),
  });
  showToast('Borrador eliminado');
  loadDashboard();
}

function getFormData() {
  return {
    foto: fotoBase64 || '',
    nombre: document.getElementById('offer-name').value.trim(),
    descripcion: document.getElementById('offer-desc').value.trim(),
    precio_original: document.getElementById('offer-price').value || '0',
    descuento: document.getElementById('offer-discount').value || '20',
  };
}

async function loadConfig() {
  const r = await fetch('/api/config');
  const cfg = await r.json();
  document.getElementById('config-token').value = '';
  document.getElementById('config-repo').value = cfg.repo || 'shcdigital/PINTURERIA';
  document.getElementById('config-status').innerHTML = cfg.has_token
    ? '<span style="color:var(--green)">\u2705 Token configurado</span>'
    : '<span style="color:var(--ink-soft)">\u26a0\ufe0f Todav\u00eda no configuraste el token</span>';
}

async function testConnection() {
  const token = document.getElementById('config-token').value.trim();
  const repo = document.getElementById('config-repo').value.trim();
  if (!token || !repo) return showToast('Complet\u00e1 token y repo', 'error');

  const btn = document.getElementById('btn-test');
  btn.disabled = true;
  btn.textContent = 'Probando...';

  const r = await fetch('/api/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, repo }),
  });
  const res = await r.json();

  if (res.ok) {
    document.getElementById('config-status').innerHTML = '<span style="color:var(--green)">\u2705 Conexi\u00f3n exitosa \u2014 acceso al repo</span>';
    showToast('\u2705 Conexi\u00f3n exitosa');
  } else {
    document.getElementById('config-status').innerHTML = `<span style="color:var(--red)">\u274c Error ${res.status}: revis\u00e1 token y nombre del repo</span>`;
    showToast('Error de conexi\u00f3n', 'error');
  }

  btn.disabled = false;
  btn.textContent = 'Probar conexi\u00f3n';
}

async function saveConfig() {
  const token = document.getElementById('config-token').value.trim();
  const repo = document.getElementById('config-repo').value.trim();
  if (!token || !repo) return showToast('Complet\u00e1 token y repo', 'error');

  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, repo }),
  });
  showToast('Configuraci\u00f3n guardada \u2705');
  loadConfig();
}

document.addEventListener('DOMContentLoaded', () => {
  setupDropzone();

  document.querySelectorAll('[data-view]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const view = el.dataset.view;
      if (view === 'dashboard') loadDashboard();
      if (view === 'nueva') nuevaOferta();
      if (view === 'config') { loadConfig(); showView('view-config'); }
    });
  });

  document.getElementById('offer-name').addEventListener('input', actualizarPreview);
  document.getElementById('offer-desc').addEventListener('input', actualizarPreview);
  document.getElementById('offer-price').addEventListener('input', actualizarPreview);
  document.getElementById('offer-discount').addEventListener('change', actualizarPreview);

  document.getElementById('btn-guardar').addEventListener('click', guardarBorrador);
  document.getElementById('btn-publicar').addEventListener('click', () => publicarOferta(null));
  document.getElementById('btn-test').addEventListener('click', testConnection);
  document.getElementById('btn-save-config').addEventListener('click', saveConfig);

  loadDashboard();
});
"""

# ─── HTML embebido ──────────────────────────────────
HTML_HEAD = '<!DOCTYPE html>\n<html lang="es-AR">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Gestor de Ofertas &middot; Proveesur</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">\n<style>\n' + CSS + '</style>\n</head>\n<body>\n'

HTML_BODY = """\
<div id="toast" class="toast"><div style="display:flex;align-items:center;gap:0.75rem"><span id="toast-text" style="font-weight:500">Mensaje</span></div></div>

<header class="app-header">
<div class="logo-text"><span class="l1">G</span><span class="l2">e</span><span class="l3">s</span><span class="l4">t</span><span style="color:var(--ink)">or</span> <span style="color:var(--ink-soft)">de Ofertas</span></div>
<nav style="display:flex;gap:0.5rem">
<button class="btn btn-secondary btn-sm" data-view="dashboard">\U0001f4cb Dashboard</button>
<button class="btn btn-primary btn-sm" data-view="nueva">+ Nueva</button>
<button class="btn btn-secondary btn-sm" data-view="config">\u2699\ufe0f</button>
</nav>
</header>

<div id="view-dashboard" class="view container">

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem">
<div class="card" style="text-align:center"><div style="font-size:2rem;font-weight:800;color:var(--yellow)"><span id="draft-count">0</span></div><div style="color:var(--ink-soft)">Borradores</div></div>
<div class="card" style="text-align:center"><div style="font-size:2rem;font-weight:800;color:var(--green)"><span id="published-count">0</span></div><div style="color:var(--ink-soft)">Publicadas en web</div></div>
</div>

<div class="card" style="margin-bottom:1rem">
<div class="section-title">\U0001f4dd Borradores</div>
<div id="draft-list"><div class="empty-state">Cargando...</div></div>
</div>

<div class="card">
<div class="section-title">\U0001f310 Publicadas en la web</div>
<div id="published-list"><div class="empty-state">Cargando...</div></div>
</div>

<div style="text-align:center;margin-top:1.5rem;color:var(--ink-soft)">Los cambios en GitHub Pages pueden tardar hasta 2 minutos en verse online.</div>
</div>

<div id="view-form" class="view container hidden">
<button class="btn btn-secondary btn-sm" data-view="dashboard" style="margin-bottom:1rem">&larr; Volver</button>
<h1 id="form-title" class="section-title">Nueva oferta</h1>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">

<div class="card">
<input type="hidden" id="archivo-borrador" value="">
<div class="form-label">Foto del producto</div>
<div id="dropzone" class="dropzone">
<p style="margin:0;color:var(--ink-soft)">\U0001f4f8 Arrastr&aacute; la foto ac&aacute; o click para seleccionar</p>
<p style="margin:0.25rem 0 0;color:var(--ink-soft)">JPG o PNG</p>
<input type="file" id="foto-input" accept="image/*" style="display:none">
<img id="preview-foto" class="hidden" style="max-height:180px;border-radius:0.75rem;margin-top:0.5rem" alt="Preview">
</div>

<div style="margin-top:1rem">
<label class="form-label" for="offer-name">Nombre del producto</label>
<input type="text" id="offer-name" class="form-field" placeholder="Ej: L&aacute;tex interior premium 20L">
</div>

<div style="margin-top:0.75rem">
<label class="form-label" for="offer-desc">Descripci&oacute;n</label>
<textarea id="offer-desc" class="form-field" rows="2" placeholder="Breve descripci&oacute;n del producto..."></textarea>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-top:0.75rem">
<div>
<label class="form-label" for="offer-price">Precio original ($)</label>
<input type="number" id="offer-price" class="form-field" placeholder="45900" min="1">
</div>
<div>
<label class="form-label" for="offer-discount">Descuento (%)</label>
<select id="offer-discount" class="form-field">
<option value="10">10%</option><option value="15">15%</option><option value="20" selected>20%</option>
<option value="25">25%</option><option value="30">30%</option><option value="40">40%</option><option value="50">50%</option>
</select>
</div>
</div>

<div class="cta-bar">
<button id="btn-guardar" class="btn btn-secondary">\U0001f4be Guardar borrador</button>
<button id="btn-publicar" class="btn btn-green">\U0001f310 Publicar</button>
</div>

<p style="margin-top:0.75rem;color:var(--ink-soft)">\U0001f4a1 <strong>Borrador</strong> se guarda en esta PC. <strong>Publicar</strong> lo sube a GitHub y aparece en la web.</p>
</div>

<div>
<div class="form-label">Vista previa</div>
<div class="offer-card-preview">
<div class="offer-badge" id="preview-badge">-20%</div>
<img id="preview-foto-card" src="" alt="Preview" style="display:none">
<div style="background:var(--cream-deep);height:200px;display:flex;align-items:center;justify-content:center;color:var(--ink-soft)" id="preview-placeholder">Sub&iacute; una foto para ver la preview</div>
<div class="card-body">
<h3 id="preview-nombre">Nombre del producto</h3>
<p id="preview-desc">Descripci&oacute;n breve del producto.</p>
<div><span class="old-price" id="preview-old-price">$10,000</span> <span class="offer-price" id="preview-offer-price">$8,000</span></div>
<div style="margin-top:0.75rem"><span class="btn btn-primary btn-sm">\U0001f4ac Consultar</span></div>
</div>
</div>
</div>

</div>
</div>

<div id="view-config" class="view container hidden">
<button class="btn btn-secondary btn-sm" data-view="dashboard" style="margin-bottom:1rem">&larr; Volver</button>
<h1 class="section-title">\u2699\ufe0f Configuraci&oacute;n</h1>
<div class="card" style="max-width:600px">

<p style="color:var(--ink-soft);margin-bottom:1rem">Para que la app pueda publicar ofertas necesit&aacute;s un <strong>token de GitHub</strong> con acceso al repositorio.</p>

<details style="margin-bottom:1rem;color:var(--ink-soft)">
<summary style="cursor:pointer;font-weight:600">\U0001f4d6 &iquest;C&oacute;mo generar el token?</summary>
<ol style="margin-top:0.5rem;padding-left:1.2rem;line-height:1.8">
<li>And&aacute; a <a href="https://github.com/settings/tokens" target="_blank" style="color:var(--blue)">github.com/settings/tokens</a></li>
<li>Click <strong>Generate new token (classic)</strong></li>
<li>Dale un nombre (ej: &quot;Gestor Ofertas&quot;)</li>
<li>Seleccion&aacute; <strong>repo</strong> (todos los permisos)</li>
<li>Click <strong>Generate token</strong></li>
<li>Copi&aacute; el token (es la &uacute;nica vez que lo vas a ver)</li>
<li>Pegalo abajo y guard&aacute;</li>
</ol>
</details>

<div style="margin-bottom:0.75rem">
<label class="form-label" for="config-token">Token de GitHub</label>
<input type="password" id="config-token" class="form-field" placeholder="ghp_xxxxxxxxxxxxxxxxxxxx">
</div>

<div style="margin-bottom:1rem">
<label class="form-label" for="config-repo">Repositorio</label>
<input type="text" id="config-repo" class="form-field" placeholder="pablo/PINTURERIA">
</div>

<div id="config-status" style="margin-bottom:1rem">\u23f3 Cargando...</div>

<div style="display:flex;gap:0.75rem">
<button id="btn-test" class="btn btn-secondary">Probar conexi&oacute;n</button>
<button id="btn-save-config" class="btn btn-primary">Guardar configuraci&oacute;n</button>
</div>

</div>
</div>
"""

HTML_FOOT = '<script>\n' + JS + '\n</script>\n</body>\n</html>'

HTML = HTML_HEAD + HTML_BODY + HTML_FOOT

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
                publicadas.append({'tipo': 'publicada', 'nombre': nombre.group(1) if nombre else 'Sin nombre', 'precio_oferta': precio.group(1) if precio else '0'})

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

@app.route('/check')
def check():
    has_css_ref = 'styles.css' in HTML
    has_js_ref = 'app.js' in HTML
    css_len = len(CSS)
    js_len = len(JS)
    return jsonify({'version': '2026-06-24-embed', 'has_css_ref': has_css_ref, 'has_js_ref': has_js_ref, 'css_len': css_len, 'js_len': js_len})

@app.route('/debug')
def debug():
    return '<pre>' + HTML.replace('&', '&amp;').replace('<', '&lt;') + '</pre>'

@app.route('/')
def index():
    return HTML

def open_browser():
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}')

if __name__ == '__main__':
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host='127.0.0.1', port=PORT, debug=False)
