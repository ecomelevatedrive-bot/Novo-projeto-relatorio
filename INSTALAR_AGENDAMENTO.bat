@echo off
chcp 65001 >nul
title Instalar Agendamentos - Elevate Ecom
cd /d "%~dp0"

echo.
echo =====================================================
echo   INSTALANDO TAREFAS AGENDADAS
echo   Relatorios Shopee - Toda Sexta as 06:00
echo =====================================================
echo.

echo [1/2] Instalando tarefa grupo Shopee...
schtasks /create /tn "Elevate Ecom - Relatorio Shopee" /xml "%~dp0tarefa_shopee.xml" /f

if %errorlevel% == 0 (
    echo  [OK] Grupo Shopee agendado com sucesso!
) else (
    echo  [ERRO] Falha ao criar tarefa Shopee. Execute como Administrador.
)

echo.
echo [2/2] Instalando tarefa grupo Jaguar...
schtasks /create /tn "Elevate Ecom - Relatorio Jaguar" /xml "%~dp0tarefa_jaguar.xml" /f

if %errorlevel% == 0 (
    echo  [OK] Grupo Jaguar agendado com sucesso!
) else (
    echo  [ERRO] Falha ao criar tarefa Jaguar. Execute como Administrador.
)

echo.
echo =====================================================
echo   Tarefas instaladas! Proxima execucao: sexta 06:00
echo   Para verificar: Agendador de Tarefas ^> Biblioteca
echo     - "Elevate Ecom - Relatorio Shopee"
echo     - "Elevate Ecom - Relatorio Jaguar"
echo =====================================================
echo.
pause
