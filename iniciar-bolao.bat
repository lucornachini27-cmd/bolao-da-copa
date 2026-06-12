@echo off
chcp 65001 >nul
title Bolao da Copa
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo [ERRO] Nao encontrei o ambiente virtual .venv nesta pasta.
  echo Coloque este .bat na pasta do projeto ^(mesma pasta do .venv e da pasta app^).
  echo.
  pause
  exit /b 1
)

echo Iniciando o servidor do Bolao da Copa...
start "Bolao - Servidor (NAO FECHE)" cmd /k ".\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Aguardando o servidor subir...
timeout /t 3 /nobreak >nul

echo Abrindo a tela no navegador...
start "" "http://localhost:8000/"

echo.
echo ===========================================
echo   Servidor: http://localhost:8000
echo   Docs:     http://localhost:8000/docs
echo.
echo   Para PARAR o servidor, feche a janela:
echo     "Bolao - Servidor (NAO FECHE)"
echo ===========================================
echo.
echo Pode fechar ESTA janela; o servidor continua rodando na outra.
pause
