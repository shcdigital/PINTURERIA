# 🎨 TIENDA_NOMBRE — Sitio web de pinturería

Sitio web estático para una pinturería de barrio, con catálogo de productos, calculadora de pintura, visualizador de colores y sistema de gestión de ofertas conectado a GitHub.

## 🌐 Sitio web

Alojado en **GitHub Pages**: https://shcdigital.github.io/PINTURERIA/

### Páginas

| Página | Archivo | Descripción |
|--------|---------|-------------|
| Landing | `index.html` | Hero, servicios, ofertas destacadas, calculadora, visualizador, testimonios, contacto |
| Ofertas | `ofertas.html` | Catálogo completo con badges de descuento, vencimiento y "OFERTA TERMINADA" |
| Visualizador | `visualizador.html` | Subí una foto de tu pared y probá colores con flood fill (HSV, tolerancia ajustable, deshacer, descargar) |

### Tecnologías

- HTML + CSS + JS vanilla
- [Tailwind CSS v4](https://tailwindcss.com/) (via CDN)
- [Lucide Icons](https://lucide.dev/)
- [Google Fonts](https://fonts.google.com/) (Caveat + Plus Jakarta Sans)
- **Offline-first** con Service Worker (`sw.js`)

### Configuración del sitio

Editar `app.js` → objeto `CONFIG` con nombre, WhatsApp, email, dirección, redes.

Para cambiar el nombre de la tienda en todo el sitio: buscar y reemplazar `TIENDA_NOMBRE`.

---

## 📦 Gestor de Ofertas (`app-ofertas/`)

Aplicación Windows para crear, editar y publicar ofertas en el sitio vía GitHub API.

### Requisitos

- Windows 10+
- Google Chrome (se abre en modo `--app`, sin interfaz de navegador)
- Python 3.13+ (solo para compilar)
- Token de GitHub con permiso `repo`

### Estructura

```
app-ofertas/
├── app.py                  # Servidor Flask (API + frontend)
├── card_generator.py       # Generación de HTML de cards
├── config_manager.py       # Config local (token, repo) + publicadas.json
├── github_api.py           # GitHub API (leer, escribir, eliminar archivos)
├── build.bat               # Script de compilación (PyInstaller)
├── installer/
│   ├── setup.iss           # Inno Setup script
│   ├── package.bat         # Build del installer
│   └── icon.ico            # Ícono personalizado
├── static/
│   ├── index.html          # Frontend del Gestor
│   ├── app.js              # Lógica frontend
│   └── styles.css          # Estilos
└── drafts/                 # Borradores locales (JSON)
```

### Cómo compilar

```bat
git pull
build.bat
```

Genera `dist/GestorOfertas.exe`.

### Cómo crear el instalador

```bat
cd installer
package.bat
```

Genera `dist/GestorOfertas_Installer.exe` (auto-descarga Inno Setup si falta).

### Funcionalidades

- **Crear oferta**: foto (drag & drop), nombre, descripción, precio, descuento, fecha de vencimiento
- **✨ Quitar fondo**: elimina el fondo de la foto con Pillow (umbral ajustable con slider de intensidad)
- **↩ Deshacer**: restaura la foto original antes del último procesamiento
- **💾 Guardar borrador**: guarda localmente en `%APPDATA%\GestorOfertasProveesur\drafts\`
- **🌐 Publicar**: sube la oferta al repositorio GitHub, se inserta al inicio de la grilla. Máximo 30 ofertas simultáneas (10 filas de 3); al llegar a 30, la más antigua se elimina con backup automático en `.bak/`
- **✕ Eliminar**: elimina del sitio, guarda backup en `.bak/` (últimos 10)
- **Badge de vencimiento**: las ofertas vencidas muestran "⚠️ OFERTA TERMINADA"
- **Dashboard**: muestra borradores y ofertas publicadas con su estado

### Almacenamiento de datos

| Dato | Ruta |
|------|------|
| Config (token, repo) | `%APPDATA%\GestorOfertasProveesur\config.json` |
| Publicadas registradas | `%APPDATA%\GestorOfertasProveesur\publicadas.json` |
| Borradores | `%APPDATA%\GestorOfertasProveesur\drafts\` |
| Logs | `%APPDATA%\GestorOfertasProveesur\app.log` |

### API endpoints

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/api/config` | GET/POST | Leer/guardar token y repo |
| `/api/test` | POST | Probar conexión con GitHub |
| `/api/ofertas` | GET | Listar borradores y publicadas |
| `/api/ofertas/borrador` | POST | Guardar borrador |
| `/api/ofertas/publicar` | POST | Publicar oferta en GitHub |
| `/api/ofertas/eliminar_publicada` | POST | Eliminar oferta del sitio |
| `/api/ofertas/eliminar` | POST | Eliminar borrador local |
| `/api/imagen/procesar` | POST | Quitar fondo + redimensionar (umbral configurable) |
| `/api/imagen/solo_optimizar` | POST | Solo redimensionar y comprimir |
| `/api/shutdown` | POST | Cerrar la aplicación |

---

## 🚀 Flujo de trabajo

1. Abrí el Gestor de Ofertas → se abre Chrome en modo app
2. Configurá token y repo en ⚙️
3. Creá oferta con foto → ajustá intensidad si querés quitar fondo
4. Guardá borrador o Publicá directo
5. La oferta aparece en `ofertas.html` (~1-2 min por GitHub Pages)
6. Para eliminar: click ✕ → se borra del sitio y se guarda backup en `.bak/`

---

## 🔧 Personalización

- **Nombre de tienda**: buscá `TIENDA_NOMBRE` en todos los archivos y reemplazalo
- **WhatsApp**: cambiá `WA_NUMBER` en `card_generator.py` y el `CONFIG.whatsapp` en `app.js`
- **Colores**: variables CSS en `styles.css` (`:root`)
- **Icono**: reemplazá `installer/icon.ico`

---

## 📄 Licencia

Desarrollado por **SHC Digital**.
