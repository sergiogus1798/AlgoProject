@echo off
rem algoui.cmd - abre la ventana en Windows. Doble clic, o esto desde cualquier sitio.
rem El equivalente de bin/algoui; alli el xcb de Qt, aqui el modo UTF-8 de Python, sin el
rem cual cualquier open() sin encoding lee y escribe en cp1252.
cd /d "%~dp0.."
set PYTHONUTF8=1
python -m ui.desktop.launch %*
if errorlevel 1 pause
