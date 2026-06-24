@echo off
chcp 65001 >nul
echo ============================================
echo  Compilando Gestor de Ofertas Proveesur...
echo ============================================
echo.

if exist drafts\*.json (
    echo OK: drafts/ contiene archivos JSON
) else (
    echo Advertencia: drafts/ esta vacio, creando placeholder...
    echo ^{"tipo":"placeholder"^} > drafts\.placeholder.json
)

REM Intentar borrar el .exe anterior por si esta bloqueado
if exist dist\GestorOfertas.exe (
    del /f /q dist\GestorOfertas.exe 2>nul
    if exist dist\GestorOfertas.exe (
        echo.
        echo ERROR: No se puede borrar dist\GestorOfertas.exe
        echo Cerra el programa si esta abierto y volve a ejecutar build.bat
        echo.
        pause
        exit /b 1
    )
)

REM Limpiar builds anteriores
if exist build rmdir /s /q build
if exist *.spec del /q *.spec

REM Instalar dependencias
echo Instalando pywebview...
pip install pywebview
if %errorlevel% neq 0 (
    echo ERROR: No se pudo instalar pywebview.
    echo Asegurate de tener pip actualizado: python -m pip install --upgrade pip
    pause
    exit /b 1
)

REM Verificar que se pueda importar
python -c "import webview; print('pywebview OK')"
if %errorlevel% neq 0 (
    echo ERROR: pywebview instalado pero no se puede importar.
    pause
    exit /b 1
)

REM Compilar
echo.
pyinstaller --onefile --windowed --name "GestorOfertas" ^
  --add-data="static;static" ^
  --add-data="drafts;drafts" ^
  --hidden-import=webview ^
  --hidden-import=clr ^
  --distpath dist ^
  --workpath build ^
  --clean app.py

if exist "%~dp0dist\GestorOfertas.exe" (
    echo.
    echo ============================================
    echo  LISTO!
    echo  Ejecutable: %~dp0dist\GestorOfertas.exe
    echo.
    echo  Ahora podes:
    echo  1. Hacer doble click en GestorOfertas.exe
    echo  2. Se abre una ventana nativa (sin Chrome)
    echo  3. Anda a Configuracion (arriba a la derecha)
    echo  4. Pega el token, repo: shcdigital/PINTURERIA
    echo  5. Guarda y proba conexion
    echo ============================================
) else (
    echo.
    echo ERROR: No se genero el .exe.
    echo Fijate el mensaje de arriba para ver que fallo.
)

pause
