@echo off
title Sistema IoT Horta Comunitaria
color 0A

:: Garante execucao na pasta do projeto
cd /d "%~dp0"

echo ===============================================================
echo   SISTEMA DE MONITORAMENTO IOT - HORTA COMUNITARIA
echo ===============================================================
echo.
echo [1/2] Iniciando Servidor de Ingestao API (Porta 8000)...
start "API FastAPI - Ingestao IoT" cmd /k "cd /d ""%~dp0"" && python server.py"

timeout /t 2 /nobreak >nul

echo [2/2] Iniciando Dashboard Analitico (Porta 8501)...
start "Dashboard Streamlit - Horta IoT" cmd /k "cd /d ""%~dp0"" && python -m streamlit run dashboard.py"

timeout /t 3 /nobreak >nul

:: Abre o navegador automaticamente no dashboard
start http://localhost:8501

echo.
echo ===============================================================
echo   TUDO PRONTO!
echo   - Dashboard no navegador: http://localhost:8501
echo   - Documentacao da API:    http://localhost:8000/docs
echo ===============================================================
echo.
timeout /t 5
