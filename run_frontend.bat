@echo off
title HakimAgent - Frontend (Port 3000)
cd /d "%~dp0frontend"
echo ========================================================
echo   HakimAgent - Serveur Frontend (Next.js)
echo ========================================================
echo.
npm run dev
echo.
echo Le serveur Frontend s'est arrete.
pause
