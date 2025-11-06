@echo off
echo === ACTUALIZANDO REPOSITORIO ===

git add .
set /p msg=Escribe el mensaje del commit: 
git commit -m "%msg%"
git push origin main
echo === CAMBIOS SUBIDOS CON EXITO ===
pause