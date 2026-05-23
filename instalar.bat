@echo off
echo ============================================
echo   Instalando dependencias do Cafe Ponte...
echo ============================================
echo.

REM Tenta o launcher "py" do Python oficial (mais confiavel no Windows)
where py >nul 2>&1
if not errorlevel 1 (
    echo Usando: py (Python Launcher)
    py -m pip install flask python-escpos Pillow
    goto done
)

REM Tenta python3 explicitamente
where python3 >nul 2>&1
if not errorlevel 1 (
    python3 -c "import pip" >nul 2>&1
    if not errorlevel 1 (
        echo Usando: python3
        python3 -m pip install flask python-escpos Pillow
        goto done
    )
)

REM Tenta python, mas so se tiver pip
python -c "import pip" >nul 2>&1
if not errorlevel 1 (
    echo Usando: python
    python -m pip install flask python-escpos Pillow
    goto done
)

REM Nenhum Python util encontrado
echo.
echo ERRO: Nao foi possivel encontrar o Python com pip.
echo.
echo Solucao: Instale o Python oficial em https://python.org
echo Marque a opcao "Add Python to PATH" durante a instalacao!
echo.
pause
exit /b 1

:done
echo.
echo Instalacao concluida com sucesso!
pause
