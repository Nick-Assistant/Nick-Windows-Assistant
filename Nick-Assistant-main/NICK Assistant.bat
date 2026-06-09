@echo off
title NICK ASSISTANT
cd /d "%~dp0"

echo Проверка сервера Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo Ollama уже работает.
) else (
    echo Сервер не найден. Запускаю Ollama...
    start /B ollama serve > NUL 2>&1
    timeout /t 3 /nobreak > NUL
)

echo Запуск ассистента из виртуального окружения...
py main.py
pause