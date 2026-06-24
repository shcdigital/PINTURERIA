@echo off
chcp 65001 >nul
pushd "%~dp0"
set INNO_DIR=%~dp0innosetup
set ISCC_EXE=%INNO_DIR%\ISCC.exe
echo ============================================
echo  Creando instalador de Gestor de Ofertas
echo  Desarrollado por SHC Digital
echo ============================================
echo.

REM Verificar si ISCC ya esta disponible
where ISCC >nul 2>&1
if %errorlevel% equ 0 (
    set ISCC_EXE=ISCC
    goto :COMPILAR
)

REM Verificar si ya tenemos portable
if exist "%ISCC_EXE%" goto :COMPILAR

echo Inno Setup no encontrado. Descargando portable...
echo.

REM Descargar Inno Setup
powershell -Command "& {Invoke-WebRequest -Uri 'https://jrsoftware.org/download.php/is.exe' -OutFile '%TEMP%\innosetup_dl.exe'}"
if %errorlevel% neq 0 (
    echo ERROR: No se pudo descargar Inno Setup.
    echo Descargalo manualmente de: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo Instalando Inno Setup portable...
REM Instalar en modo portable (sin admin)
start /wait "" "%TEMP%\innosetup_dl.exe" /PORTABLE=1 /DIR="%INNO_DIR%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
del "%TEMP%\innosetup_dl.exe" 2>nul

if not exist "%ISCC_EXE%" (
    echo ERROR: No se pudo instalar Inno Setup portable.
    pause
    exit /b 1
)

echo Inno Setup portable instalado en: %INNO_DIR%
echo.

:COMPILAR
REM Verificar que existe el .exe compilado
if not exist "%~dp0..\dist\GestorOfertas.exe" (
    echo ERROR: Primero ejecuta build.bat para compilar el .exe
    pause
    exit /b 1
)

REM Compilar instalador
echo Compilando instalador...
"%ISCC_EXE%" setup.iss

if exist "%~dp0..\dist\GestorOfertas_Installer.exe" (
    echo ============================================
    echo  LISTO!
    echo  Instalador: %~dp0..\dist\GestorOfertas_Installer.exe
    echo.
    echo  %~dp0..\dist\GestorOfertas_Installer.exe
    echo  se puede copiar a cualquier PC.
    echo  El usuario final solo hace doble click e instala.
    echo ============================================
) else (
    echo ERROR: No se genero el instalador.
    echo Fijate el mensaje de arriba para ver que fallo.
)

pause
