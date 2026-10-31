@echo off
title HakimAgent - Backend (Port 8000)
cd /d "%~dp0"
echo ========================================================
echo   HakimAgent - Serveur Backend (FastAPI / Uvicorn)
echo ========================================================
echo.
set PYTHONPATH=backend
.\backend\.venv\Scripts\python.exe -m uvicorn axiom.api.main:app --host 127.0.0.1 --port 8000 --reload
echo.
echo Le serveur Backend s'est arrete.
pause
