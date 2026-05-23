@echo off
REM Abre o Google Chrome em modo quiosque (tela cheia, sem botoes, sem fechar)
REM O servidor precisa estar rodando antes de abrir este arquivo.

echo Abrindo Kiosk em modo quiosque...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --kiosk --app=http://localhost:5000 --disable-translate --no-first-run --disable-infobars

REM Se o Chrome nao estiver no caminho acima, tente:
REM start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --kiosk --app=http://localhost:5000
