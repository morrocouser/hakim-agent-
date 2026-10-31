@echo off
chcp 65001 >nul
echo ======================================================================
echo 🚀 HAKIMAGENT - SUITE DE VALIDATION QA AUTOMATISÉE COMPLÈTE
echo ======================================================================

set PYTHONPATH=%~dp0backend
set PYTHONIOENCODING=utf-8
set QT_QPA_PLATFORM=offscreen
set VENV_PYTHON=%~dp0backend\.venv\Scripts\python.exe

if not exist "%VENV_PYTHON%" (
    echo ❌ Environnement virtuel Python introuvable sous backend\.venv
    pause
    exit /b 1
)

echo [1/7] Diagnostic de l'Environnement et des Services (Healthcheck)...
"%VENV_PYTHON%" tests\healthcheck.py
if errorlevel 1 (
    echo ❌ Échec du Healthcheck
    pause
    exit /b 1
)

echo.
echo [2/7] Tests Unitaires de Routage et Délégation Multi-Agents...
"%VENV_PYTHON%" tests\test_routing.py
if errorlevel 1 (
    echo ❌ Échec des tests de routage
    pause
    exit /b 1
)

echo.
echo [3/7] Tests de Résilience et Gestion d'Erreurs...
"%VENV_PYTHON%" tests\test_resilience.py
if errorlevel 1 (
    echo ❌ Échec des tests de résilience
    pause
    exit /b 1
)

echo.
echo [4/7] Tests End-to-End de l'API FastAPI et Gouvernance...
"%VENV_PYTHON%" tests\test_api_e2e.py
if errorlevel 1 (
    echo ❌ Échec des tests API
    pause
    exit /b 1
)

echo.
echo [5/7] Tests Desktop PySide6 et UI Web...
"%VENV_PYTHON%" tests\test_desktop_and_ui.py
if errorlevel 1 (
    echo ❌ Échec des tests Desktop/UI
    pause
    exit /b 1
)

echo.
echo [6/7] Tests MCP E2E et Découverte d'Outils Stdio...
"%VENV_PYTHON%" tests\test_mcp_e2e.py
if errorlevel 1 (
    echo ❌ Échec des tests MCP
    pause
    exit /b 1
)

echo.
echo [7/7] Test d'Exécution Réelle E2E (Conception -> Code -> QA)...
"%VENV_PYTHON%" tests\test_e2e_task_execution.py
if errorlevel 1 (
    echo ❌ Échec du test E2E de tâche réelle
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo 🎉 TOUS LES 7 MODULES DE TESTS SONT AU VERT ! HAKIMAGENT EST 100%% OPÉRATIONNEL.
echo ======================================================================
pause
