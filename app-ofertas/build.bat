@echo off
echo ============================================
echo  Compilando Gestor de Ofertas Proveesur...
echo ============================================
echo.

pyinstaller --onefile --windowed --name "GestorOfertas" --add-data "static;static" --add-data "drafts;drafts" app.py

echo.
echo ============================================
echo  Listo! El ejecutable esta en:
echo  dist\GestorOfertas.exe
echo ============================================
pause
