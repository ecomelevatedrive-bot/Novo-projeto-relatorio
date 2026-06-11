@echo off
chcp 65001 >nul
title Teste - Foreli

cd /d "%~dp0"

echo.
echo =====================================================
echo   TESTE - FORELI
echo =====================================================
echo.

"C:\Users\User\AppData\Local\Python\bin\python.exe" main.py --cliente "Foreli"

echo.
echo =====================================================
echo   Pressione qualquer tecla para fechar...
echo =====================================================
pause >nul
