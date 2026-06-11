@echo off
chcp 65001 >nul
title ELEVATE ECOM — RELATORIOS SHOPEE

cd /d "%~dp0"

:MENU
cls
echo.
echo  =====================================================
echo    ELEVATE ECOM ^| RELATORIOS SHOPEE
echo  =====================================================
echo.
echo    [1] Rodar TODOS os clientes (semana atual)
echo    [2] Rodar UM cliente especifico
echo    [3] Rodar com periodo personalizado
echo    [4] Diagnostico
echo    [5] Refresh nos logins de conta
echo    [6] Sair
echo.
set /p OPCAO="  Escolha uma opcao: "

if "%OPCAO%"=="1" goto TODOS
if "%OPCAO%"=="2" goto UM_CLIENTE
if "%OPCAO%"=="3" goto PERIODO
if "%OPCAO%"=="4" goto DIAGNOSTICO
if "%OPCAO%"=="5" goto REFRESH
if "%OPCAO%"=="6" exit
goto MENU

:TODOS
cls
echo.
echo  Rodando para TODOS os clientes...
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py 2>&1
echo.
pause
goto MENU

:UM_CLIENTE
cls
echo.
set /p CLIENTE="  Nome do cliente: "
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py --cliente "%CLIENTE%" 2>&1
echo.
pause
goto MENU

:PERIODO
cls
echo.
set /p DE="  Data inicio (AAAA-MM-DD): "
set /p ATE="  Data fim   (AAAA-MM-DD): "
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py %DE% %ATE% 2>&1
echo.
pause
goto MENU

:DIAGNOSTICO
cls
echo.
echo  Rodando diagnostico...
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 diagnostico.py 2>&1
echo.
pause
goto MENU

:REFRESH
cls
echo.
echo  Refresh de logins — abrindo cada perfil para verificar sessao...
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 refresh_logins.py 2>&1
echo.
pause
goto MENU
