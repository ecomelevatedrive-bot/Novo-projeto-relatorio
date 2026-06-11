@echo off
cd /d "%~dp0"
if not exist "logs" mkdir logs

set "HOJE=%date:~6,4%-%date:~3,2%-%date:~0,2%"
set "HORA=%time:~0,2%%time:~3,2%"
set "HORA=%HORA: =0%"
set "LOG=logs\auto_shopee_%HOJE%_%HORA%.log"

"C:\Users\User\AppData\Local\Python\bin\python.exe" -X utf8 main.py >> "%LOG%" 2>&1

if %ERRORLEVEL% == 0 (
    echo [%date% %time%] Shopee: SUCESSO >> logs\historico.log
) else (
    echo [%date% %time%] Shopee: ERRO - veja %LOG% >> logs\historico.log
)
