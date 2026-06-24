@echo off
chcp 65001 >nul
pushd "%~dp0"
echo ============================================
echo  Creando instalador de Gestor de Ofertas
echo  Desarrollado por SHC Digital
echo ============================================
echo.

REM Verificar que existe ISCC
where ISCC >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Inno Setup no encontrado.
    echo Instalalo desde: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM Verificar que existe el .exe compilado
if not exist "..\dist\GestorOfertas.exe" (
    echo ERROR: Primero ejecuta build.bat para compilar el .exe
    pause
    exit /b 1
)

REM Compilar instalador
echo Compilando instalador...
ISCC setup.iss

if exist "..\dist\GestorOfertas_Installer.exe" (
    echo ============================================
    echo  LISTO!
    echo  Instalador: ..\dist\GestorOfertas_Installer.exe
    echo ============================================
) else (
    echo ERROR: No se genero el instalador.
)

pause
