@echo off
title ELEVATE ECOM - Relatorios Shopee
cd /d "%~dp0"
if not exist "logs" mkdir logs

:MENU
cls
echo.
echo  =====================================================
echo    ELEVATE ECOM - RELATORIOS SHOPEE
echo  =====================================================
echo.
echo    [1] Todos os clientes
echo    [2] Um cliente especifico
echo    [3] Verificar sessoes
echo    [4] Sair
echo.
set "OPCAO="
set /p OPCAO=  Escolha:
echo.

if /i "%OPCAO%"=="1" goto TODOS
if /i "%OPCAO%"=="2" goto UM_CLIENTE
if /i "%OPCAO%"=="3" goto VERIFICAR
if /i "%OPCAO%"=="4" goto SAIR
goto MENU

:TODOS
set "HOJE=%date:~6,4%-%date:~3,2%-%date:~0,2%"
set "HORA=%time:~0,2%%time:~3,2%"
set "HORA=%HORA: =0%"
set "LOG=logs\todos_%HOJE%_%HORA%.log"
echo  Rodando para TODOS os clientes...
echo  Log: %LOG%
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py > "%LOG%" 2>&1
set "COD=%ERRORLEVEL%"
type "%LOG%"
goto FIM

:UM_CLIENTE
set "CLIENTE="
set /p CLIENTE=  Nome do cliente:
if "%CLIENTE%"=="" goto MENU
set "HOJE=%date:~6,4%-%date:~3,2%-%date:~0,2%"
set "HORA=%time:~0,2%%time:~3,2%"
set "HORA=%HORA: =0%"
set "LOG=logs\%CLIENTE%_%HOJE%_%HORA%.log"
echo.
echo  Rodando para: %CLIENTE%
echo  Log: %LOG%
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py --cliente "%CLIENTE%" > "%LOG%" 2>&1
set "COD=%ERRORLEVEL%"
type "%LOG%"
goto FIM

:VERIFICAR
echo  Verificando sessoes...
echo.
"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 verificar_sessoes.py
echo.
pause
goto MENU

:FIM
echo.
echo  =====================================================
echo    Concluido: %date% %time%
echo    Codigo de saida: %COD%
echo  =====================================================
echo.
if "%COD%"=="0" goto SUCESSO
echo  ERRO detectado. Verifique o log: %LOG%
echo  O PC nao sera suspenso.
echo.
pause
goto MENU

:SUCESSO
echo  Sucesso! PC sera suspenso em 60 segundos.
echo  Pressione qualquer tecla para cancelar.
echo.
pause >nul
timeout /t 60 /nobreak >nul
rundll32.exe powrprof.dll,SetSuspendState 0,1,0
goto MENU

:SAIR
exit
