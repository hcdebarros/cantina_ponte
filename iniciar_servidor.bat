@echo off
echo ============================================
echo   Cantina da Igreja - Iniciando servidor...
echo ============================================
echo.
echo Acesse no navegador:
echo   Kiosk (cliente):  http://localhost:5000
echo   Caixa:            http://localhost:5000/caixa
echo   Admin:            http://localhost:5000/admin
echo   Senha admin:      admin123
echo.

REM Descobre qual Python usar (py launcher tem prioridade)
set PYCMD=
where py >nul 2>&1
if not errorlevel 1 ( set PYCMD=py & goto run )
python -c "import pip" >nul 2>&1
if not errorlevel 1 ( set PYCMD=python & goto run )
python3 -c "import pip" >nul 2>&1
if not errorlevel 1 ( set PYCMD=python3 & goto run )

echo ERRO: Python com pip nao encontrado. Execute instalar.bat primeiro.
pause
exit /b 1

:run
REM Verifica se Flask esta instalado
%PYCMD% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask nao encontrado. Instalando dependencias...
    %PYCMD% -m pip install flask python-escpos Pillow
    echo.
)

%PYCMD% app.py
pause
