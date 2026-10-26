@echo off
title DR Motor Analytics Launcher
cls

echo ===================================================
echo   Starting DR Motor Analytics Dashboard...
echo ===================================================

REM Запускаємо Docker-контейнер
docker start dr_motor_dashboard

echo [INFO] Waiting 2 seconds for container to spin up...
timeout /t 2 >nul

echo [INFO] Opening dashboard in your default browser...
start http://localhost:8501

echo ===================================================
echo   Done! Dashboard is live. You can close this window.
echo ===================================================
pause