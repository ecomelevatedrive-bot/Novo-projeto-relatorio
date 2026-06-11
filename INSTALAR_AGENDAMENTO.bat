@echo off
chcp 65001 >nul
title Instalar Agendamento - Elevate Ecom

echo.
echo =====================================================
echo   INSTALANDO TAREFA AGENDADA
echo   Relatorio Shopee - Toda Sexta as 00:00
echo =====================================================
echo.

schtasks /create /tn "Elevate Ecom - Relatorio Shopee" /xml "%~dp0tarefa_agendada.xml" /f

if %errorlevel% == 0 (
    echo.
    echo  [OK] Tarefa agendada com sucesso!
    echo  O script rodara automaticamente toda sexta-feira as 00:00.
    echo.
    echo  Para verificar: Agendador de Tarefas ^> Biblioteca ^> "Elevate Ecom - Relatorio Shopee"
) else (
    echo.
    echo  [ERRO] Falha ao criar tarefa. Verifique se executou como Administrador.
)

echo.
echo =====================================================
pause
