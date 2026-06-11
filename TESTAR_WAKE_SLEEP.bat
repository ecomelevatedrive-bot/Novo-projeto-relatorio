@echo off
chcp 65001 >nul
title TESTE - Acordar e Suspender PC

echo.
echo =====================================================
echo   TESTE: ACORDAR E SUSPENDER PC
echo =====================================================
echo.

:: Usa PowerShell para calcular horario daqui 3 minutos (evita bug de espacos no %time%)
for /f %%T in ('powershell -NoProfile -Command "(Get-Date).AddMinutes(3).ToString(\"HH:mm\")"') do set HORARIO=%%T
for /f %%D in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd"') do set HOJE=%%D

echo  Horario atual:  %time%
echo  Tarefa vai rodar as: %HORARIO%
echo.

:: Cria arquivo XML temporario com WakeToRun=true
set XMLFILE=%TEMP%\teste_wake_relatorio.xml
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>^<Description^>Teste Wake Relatorio^</Description^>^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<TimeTrigger^>
echo       ^<StartBoundary^>%HOJE%T%HORARIO%:00^</StartBoundary^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</TimeTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<WakeToRun^>true^</WakeToRun^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<ExecutionTimeLimit^>PT2H^</ExecutionTimeLimit^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>cmd.exe^</Command^>
echo       ^<Arguments^>/c "C:\Users\User\Desktop\Novo projeto para relatorios\RODAR_RELATORIO.bat"^</Arguments^>
echo       ^<WorkingDirectory^>C:\Users\User\Desktop\Novo projeto para relatorios^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%XMLFILE%"

echo  [1/3] Registrando tarefa com WakeToRun...
schtasks /create /tn "TESTE_Wake_Relatorio" /xml "%XMLFILE%" /f

if %errorlevel% == 0 (
    echo  [OK] Tarefa criada para %HORARIO% com WakeToRun ativado!
) else (
    echo  [ERRO] Falha ao criar tarefa. Execute como Administrador.
    pause
    exit /b 1
)

echo.
echo  [2/3] Aguardando 5 segundos antes de suspender...
timeout /t 5 /nobreak

echo.
echo  [3/3] Suspendendo o PC...
echo        Ele deve acordar automaticamente as %HORARIO%
echo.
timeout /t 3 /nobreak

rundll32.exe powrprof.dll,SetSuspendState 0,1,0
