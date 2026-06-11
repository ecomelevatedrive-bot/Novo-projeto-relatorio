@echo off
chcp 65001 >nul
title ELEVATE ECOM - Verificar Sessoes Shopee
cd /d "%~dp0"

echo.
echo  =====================================================
echo    ELEVATE ECOM ^| VERIFICAR SESSOES SHOPEE
echo  =====================================================
echo.
echo  Verificando quais perfis estao logados...
echo  Aguarde — abre e fecha cada perfil rapidamente.
echo.

"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 verificar_sessoes.py 2>&1

echo.
pause
