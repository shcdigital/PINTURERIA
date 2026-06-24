@echo off
chcp 65001 >nul
echo ============================================
echo  Compilando Gestor de Ofertas Proveesur...
echo ============================================
echo.

REM Verificar que las carpetas existen
if not exist static (
    echo ERROR: Falta la carpeta static/
    pause
    exit /b 1
)

if exist drafts\*.json (
    echo OK: drafts/ contiene archivos JSON
) else (
    echo Advertencia: drafts/ esta vacio, creando placeholder...
    echo ^{"tipo":"placeholder"^} > drafts\.placeholder.json
)

REM Compilar
pyinstaller --onefile --windowed --name "GestorOfertas" ^
  --add-data="static;static" ^
  --add-data="drafts;drafts" app.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  LISTO!
    echo  Ejecutable: %~dp0dist\GestorOfertas.exe
    echo.
    echo  Ahora podes:
    echo  1. Hacer doble click en GestorOfertas.exe
    echo  2. Se te va a abrir el navegador
    echo  3. Configura tu token de GitHub
    echo ============================================
) else (
    echo.
    echo ERROR: No se pudo compilar.
    echo Fijate el mensaje de arriba para ver que fallo.
)

pause
