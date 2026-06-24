@echo off
chcp 65001 >nul
pushd "%~dp0"
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
echo Instalando dependencias...
pip install "rembg[cpu]" Pillow --quiet
echo.

REM Compilar
echo.
pyinstaller --onefile --windowed --name "GestorOfertas" ^
  --add-data="static;static" ^
  --add-data="drafts;drafts" ^
  --add-data="installer\icon.ico;." ^
  --hidden-import=rembg ^
  --hidden-import=onnxruntime ^
  --hidden-import=PIL ^
  --collect-all=rembg ^
  --collect-all=onnxruntime ^
  --distpath dist ^
  --workpath build ^
  --clean app.py

if exist dist\GestorOfertas.exe (
    copy installer\icon.ico dist\ /y >nul
    echo.
    echo ============================================
    echo  LISTO!
    echo  Ejecutable: dist\GestorOfertas.exe
    echo.
    echo  Ahora podes:
    echo  1. Hacer doble click en GestorOfertas.exe
    echo  2. Se abre Chrome modo app (sin interfaz de navegador)
    echo  3. Anda a Configuracion ^(arriba a la derecha^)
    echo  4. Pega el token, repo: shcdigital/PINTURERIA
    echo  5. Guarda y proba conexion
    echo.
    echo  Para crear el instalador: package.bat (en carpeta installer/)
    echo ============================================
) else (
    echo.
    echo ERROR: No se genero el .exe.
    echo Fijate el mensaje de arriba para ver que fallo.
)

pause
