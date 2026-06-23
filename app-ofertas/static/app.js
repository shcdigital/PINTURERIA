let ofertasData = { borradores: [], publicadas: [] };
let fotoBase64 = null;

// ─── Toast ──────────────────────────────────────────
function showToast(text, type = 'success') {
  const t = document.getElementById('toast');
  const txt = document.getElementById('toast-text');
  txt.textContent = text;
  t.className = 'toast' + (type === 'error' ? ' error' : '');
  t.classList.add('show');
  clearTimeout(t._timer);
  t._timer = setTimeout(() => t.classList.remove('show'), 3500);
}

// ─── Navegación SPA ────────────────────────────────
function showView(id) {
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  document.getElementById(id).classList.remove('hidden');
}

// ─── Dashboard ─────────────────────────────────────
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
    draftList.innerHTML = '<div class="empty-state">No tenés borradores.</div>';
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
          <button class="btn btn-danger btn-sm" onclick="eliminarBorrador('${d.archivo}')">✕</button>
        </div>
      </div>
    `).join('');
  }

  if (ofertasData.publicadas.length === 0) {
    pubList.innerHTML = '<div class="empty-state">Todavía no publicaste ofertas.</div>';
  } else {
    pubList.innerHTML = ofertasData.publicadas.map(p => `
      <div class="offer-list-item">
        <div>
          <strong>${p.nombre}</strong>
          <div><span class="badge badge-published">Publicada · $${p.precio_oferta}</span></div>
        </div>
        <a href="ofertas.html" target="_blank" class="btn btn-secondary btn-sm">Ver online</a>
      </div>
    `).join('');
  }

  document.getElementById('draft-count').textContent = ofertasData.borradores.length;
  document.getElementById('published-count').textContent = ofertasData.publicadas.length;
}

// ─── Nueva Oferta ──────────────────────────────────
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

// ─── Drag & Drop ───────────────────────────────────
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
  if (!file.type.startsWith('image/')) return showToast('Solo imágenes (JPG, PNG)', 'error');
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

// ─── Preview en vivo ───────────────────────────────
function actualizarPreview() {
  const nombre = document.getElementById('offer-name').value || 'Nombre del producto';
  const desc = document.getElementById('offer-desc').value || 'Descripción breve del producto.';
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

// ─── Guardar borrador ──────────────────────────────
async function guardarBorrador() {
  const data = getFormData();
  if (!data.nombre) return showToast('Completá el nombre del producto.', 'error');

  const r = await fetch('/api/ofertas/borrador', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (r.ok) {
    showToast('Borrador guardado ✅');
    loadDashboard();
  } else {
    showToast('Error al guardar', 'error');
  }
}

// ─── Publicar ──────────────────────────────────────
async function publicarOferta(archivoBorrador) {
  const confirmar = confirm('¿Publicar esta oferta en GitHub? Aparecerá en la web en ~1-2 minutos.');
  if (!confirmar) return;

  let data;
  if (archivoBorrador) {
    const d = ofertasData.borradores.find(b => b.archivo === archivoBorrador);
    if (!d) return;
    data = { ...d, archivo_borrador: archivoBorrador };
  } else {
    data = getFormData();
    if (!data.nombre) return showToast('Completá el nombre del producto.', 'error');
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
      showToast('✅ Oferta publicada. En ~1 min está online.');
      loadDashboard();
    } else {
      showToast('Error: ' + (res.error || 'desconocido'), 'error');
    }
  } catch {
    showToast('Error de conexión con el servidor', 'error');
  }

  btn.disabled = false;
  btn.innerHTML = '🌐 Publicar';
}

async function eliminarBorrador(archivo) {
  if (!confirm('¿Eliminar este borrador?')) return;
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

// ─── Configuración ─────────────────────────────────
async function loadConfig() {
  const r = await fetch('/api/config');
  const cfg = await r.json();
  document.getElementById('config-token').value = '';
  document.getElementById('config-repo').value = cfg.repo || 'pablo/PINTURERIA';
  document.getElementById('config-status').innerHTML = cfg.has_token
    ? '<span style="color:var(--green)">✅ Token configurado</span>'
    : '<span style="color:var(--ink-soft)">⚠️ Todavía no configuraste el token</span>';
}

async function testConnection() {
  const token = document.getElementById('config-token').value.trim();
  const repo = document.getElementById('config-repo').value.trim();
  if (!token || !repo) return showToast('Completá token y repo', 'error');

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
    document.getElementById('config-status').innerHTML = '<span style="color:var(--green)">✅ Conexión exitosa — acceso al repo</span>';
    showToast('✅ Conexión exitosa');
  } else {
    document.getElementById('config-status').innerHTML = `<span style="color:var(--red)">❌ Error ${res.status}: revisá token y nombre del repo</span>`;
    showToast('Error de conexión', 'error');
  }

  btn.disabled = false;
  btn.textContent = 'Probar conexión';
}

async function saveConfig() {
  const token = document.getElementById('config-token').value.trim();
  const repo = document.getElementById('config-repo').value.trim();
  if (!token || !repo) return showToast('Completá token y repo', 'error');

  await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, repo }),
  });
  showToast('Configuración guardada ✅');
  loadConfig();
}

// ─── Init ──────────────────────────────────────────
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
