@echo off
chcp 65001 >nul
title HakimAgent - Lanceur Global
setlocal enabledelayedexpansion

:: Repertoire du projet sans antislash de fin
set "ROOT_DIR=%~dp0"
if "%ROOT_DIR:~-1%"=="\" set "ROOT_DIR=%ROOT_DIR:~0,-1%"
cd /d "%ROOT_DIR%"

cls
echo ======================================================================
echo           HAKIMAGENT / APEX v4.0 - DEMARRAGE COMPLET
echo ======================================================================
echo.
echo Repertoire du projet : %ROOT_DIR%
echo.

:: 1. Verification de l'environnement virtuel Python
if not exist "%ROOT_DIR%\backend\.venv\Scripts\python.exe" (
    echo [ERREUR] L'environnement virtuel Python est introuvable :
    echo         %ROOT_DIR%\backend\.venv\Scripts\python.exe
    echo.
    echo Veuillez verifier que le venv existe.
    echo.
    pause
    exit /b 1
)

:: 2. Verification de Node.js / node_modules
if not exist "%ROOT_DIR%\frontend\node_modules" (
    echo [INFO] node_modules introuvable. Installation des dependances...
    cd /d "%ROOT_DIR%\frontend"
    call npm install
    cd /d "%ROOT_DIR%"
)

:: Configuration LLM OmniRoute & Routage Intelligent
set "HAKIM_LLM_PROVIDER=omniroute"
set "HAKIM_LLM_BASE_URL=http://127.0.0.1:20128/v1"
set "HAKIM_LLM_API_KEY=d83a770394c0a1a5b8da99b37e8b19decd0915760bc50efaaaffbbfd5818400e"
set "OMNIROUTE_BASE_URL=http://127.0.0.1:20128/v1"
set "OMNIROUTE_API_KEY=d83a770394c0a1a5b8da99b37e8b19decd0915760bc50efaaaffbbfd5818400e"
set "HAKIM_LLM_MODEL=omniroute/auto/best-coding"
set "HAKIM_MODEL_SUPERVISOR=omniroute/auto/best-reasoning"
set "HAKIM_MODEL_CODE=omniroute/auto/best-coding"
set "HAKIM_MODEL_REVIEWER=omniroute/auto/best-reasoning"
set "HAKIM_MODEL_RESEARCH=omniroute/auto/best-fast"
set "HAKIM_MODEL_CHAT=omniroute/auto/best-chat"

:: 3. Verification de la Passerelle OmniRoute (Port 20128)
echo [1/4] Verification de la passerelle OmniRoute (Port 20128)...
powershell -ExecutionPolicy Bypass -NoProfile -Command "$conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 20128 -WarningAction SilentlyContinue; if (-not $conn.TcpTestSucceeded) { Write-Host '   [OMNIROUTE] Demarrage automatique de la passerelle...'; Start-Process -FilePath 'node.exe' -ArgumentList '--dns-result-order=ipv4first --max-old-space-size=4096 \"$env:APPDATA\npm\node_modules\omniroute\dist\server-ws.mjs\"' -WindowStyle Hidden; Start-Sleep -Seconds 3 } else { Write-Host '   [OMNIROUTE] Passerelle operationnelle sur 127.0.0.1:20128 (780+ modeles)' }"

:: 4. Liberation prealable des ports 8000 et 3000 pour eviter les conflits
echo [2/4] Verification et liberation securisee des ports 8000 et 3000...
powershell -ExecutionPolicy Bypass -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000,3000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { $p = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; if ($p -and ($p.ProcessName -match 'python|node|uvicorn')) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Write-Host ('   [CLEANUP] Processus precedent termine sur le port ' + $_.LocalPort + ' (' + $p.ProcessName + ')') } }"
ping 127.0.0.1 -n 2 >nul

:: 4. Lancement du Backend dans sa propre fenetre
echo [2/3] Demarrage du Backend FastAPI (Port 8000)...
start "HakimAgent - Backend (Port 8000)" cmd /k "title HakimAgent - Backend (8000) && cd /d "%ROOT_DIR%" && set "PYTHONPATH=backend;backend\.venv\Lib\site-packages" && py -3.11 -m uvicorn axiom.api.main:app --host 127.0.0.1 --port 8000 --reload || .\backend\.venv\Scripts\python.exe -m uvicorn axiom.api.main:app --host 127.0.0.1 --port 8000 --reload"

echo     Attente de l'initialisation du Backend...
ping 127.0.0.1 -n 4 >nul

:: 5. Lancement du Frontend dans sa propre fenetre
echo [3/3] Demarrage du Frontend Next.js (Port 3000)...
start "HakimAgent - Frontend (Port 3000)" cmd /k "title HakimAgent - Frontend (3000) && cd /d "%ROOT_DIR%\frontend" && npm run dev"

echo     Attente du demarrage du Frontend...
ping 127.0.0.1 -n 5 >nul

echo.
echo ======================================================================
echo               TOUS LES SERVICES SONT EN ROUTE !
echo.
echo   - Frontend Web : http://localhost:3000
echo   - Page Login   : http://localhost:3000/login/
echo   - OpenBot      : http://localhost:3000/coworkers/
echo   - Backend API  : http://127.0.0.1:8000
echo   - Swagger Docs : http://127.0.0.1:8000/docs
echo ======================================================================
echo.
echo Ouverture automatique de http://localhost:3000 dans votre navigateur...
start http://localhost:3000
echo.
echo IMPORTANT :
echo   - Deux fenetres ont ete ouvertes : "Backend (8000)" et "Frontend (3000)".
echo   - Gardez ces fenetres ouvertes pendant que vous utilisez l'application.
echo   - Pour arreter completement les serveurs, fermez ces deux fenetres.
echo.
pause
