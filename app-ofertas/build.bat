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

REM Compilar
echo.
pyinstaller --onefile --windowed --name "GestorOfertas" ^
  --add-data="drafts;drafts" ^
  --distpath dist ^
  --workpath build ^
  --clean app.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo  LISTO!
    echo  Ejecutable: %~dp0dist\GestorOfertas.exe
    echo  Tamano: %~z0dist\GestorOfertas.exe bytes
    echo.
    echo  Ahora podes:
    echo  1. Hacer doble click en GestorOfertas.exe
    echo  2. Se te va a abrir el navegador
    echo  3. Anda a ⚙️ Configuracion
    echo  4. Pega el token, repo: shcdigital/PINTURERIA
    echo  5. Guarda y proba conexion
    echo ============================================
) else (
    echo.
    echo ERROR: No se pudo compilar.
    echo Fijate el mensaje de arriba para ver que fallo.
    echo.
    echo Si dice "Access is denied": cerra GestorOfertas.exe si esta abierto.
)

pause
