@echo off
title Сборка MONO Assistant EXE
color 0A
cd /d "%~dp0"

echo.
echo ========================================
echo    СБОРКА MONO ASSISTANT
echo ========================================
echo.

:: Устанавливаем PyInstaller
echo [1/4] Устанавливаю PyInstaller...
pip install pyinstaller pillow --quiet

:: Создаём иконку
echo [2/4] Создаю иконку...
python create_icon.py

:: Находим путь к vosk
echo [3/4] Ищу библиотеку Vosk...
for /f "delims=" %%i in ('python -c "import vosk; import os; print(os.path.dirname(vosk.__file__))"') do set VOSK_PATH=%%i
echo Vosk найден: %VOSK_PATH%

:: Собираем EXE
echo [4/4] Собираю EXE файл...
echo Это займёт 2-5 минут...
echo.

pyinstaller --noconfirm --onedir --windowed ^
    --name "MONO Assistant" ^
    --icon "mono.ico" ^
    --add-data "config.json;." ^
    --add-data "sounds;sounds" ^
    --add-data "model;model" ^
    --add-data "modules;modules" ^
    --add-data "core;core" ^
    --add-data "ui;ui" ^
    --additional-hooks-dir "." ^
    --hidden-import "pyttsx3.drivers" ^
    --hidden-import "pyttsx3.drivers.sapi5" ^
    --hidden-import "pygame" ^
    --hidden-import "vosk" ^
    --hidden-import "pycaw" ^
    --hidden-import "pycaw.pycaw" ^
    --hidden-import "comtypes" ^
    --hidden-import "comtypes.client" ^
    --hidden-import "screen_brightness_control" ^
    --hidden-import "fuzzywuzzy" ^
    --hidden-import "Levenshtein" ^
    --hidden-import "pyautogui" ^
    --hidden-import "pyperclip" ^
    --hidden-import "psutil" ^
    --hidden-import "requests" ^
    --hidden-import "modules.smart_assistant" ^
    --hidden-import "modules.system_control" ^
    --hidden-import "modules.app_control" ^
    --hidden-import "modules.media_control" ^
    --hidden-import "modules.web_control" ^
    --hidden-import "modules.input_control" ^
    --hidden-import "modules.timer_control" ^
    --collect-all "vosk" ^
    --collect-binaries "vosk" ^
    main.py

echo.
echo ========================================
if exist "dist\MONO Assistant\MONO Assistant.exe" (
    echo    ГОТОВО!
    echo ========================================
    echo.
    echo EXE файл: dist\MONO Assistant\MONO Assistant.exe
    echo.
    echo Скопируй всю папку "dist\MONO Assistant" 
    echo и раздавай друзьям!
) else (
    echo    ОШИБКА СБОРКИ
    echo ========================================
)
echo.
pause
