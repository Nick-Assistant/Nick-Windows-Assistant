"""
Модуль управления приложениями - запуск программ и сайтов
"""
import os
import webbrowser
import subprocess

#####################################################################
                                                                    #
KEYWORDS = [                                                        #
    "открой", "запусти", "включи", "закрой",                        #
    "youtube", "ютуб", "ютюб",                                      #
    "google", "гугл",                                               #
    "chatgpt", "чатгпт", "чат гпт",                                 #
    "браузер", "хром", "chrome",                                    #
    "discord", "дискорд",                                           #
    "steam", "стим",                                                #
    "spotify", "спотифай",                                          #
    "telegram", "телеграм", "телега",                               #
    "vscode", "код", "редактор",                                    #
    "блокнот", "notepad",                                           #
    "калькулятор", "calculator",                                    #
    "диспетчер задач", "task manager"                               #
]                                                                   #
                                                                    #
# Маппинг русских названий на ключи конфига и системные приложения  #
APP_ALIASES = {                                                     #
    # Браузеры                                                      #
    "хром": "chrome",                                               #
    "браузер": "chrome",                                            #
    "chrome": "chrome",                                             #
    "гугл хром": "chrome",                                          #
    # Мессенджеры                                                   #
    "дискорд": "discord",                                           #
    "discord": "discord",                                           #
    "дис корд": "discord",                                          #
    "телеграм": "telegram",                                         #
    "телеграмм": "telegram",                                        #
    "телега": "telegram",                                           #
    "telegram": "telegram",                                         #
    # Игры/Развлечения                                              #
    "стим": "steam",                                                #  Ключеывые слова для активации.
    "steam": "steam",                                               #
    "с тим": "steam",  # распознавание с пробелом                   #
    "сти м": "steam",                                               #
    "спотифай": "spotify",                                          #
    "spotify": "spotify",                                           #
    "спотифи": "spotify",                                           #
    # Разработка                                                    #
    "vscode": "vscode",                                             #
    "vs code": "vscode",                                            #
    "код": "vscode",                                                #
    "редактор": "vscode",                                           #
    "visual studio": "vscode",                                      #
    # Системные                                                     #
    "блокнот": "notepad",                                           #
    "notepad": "notepad",                                           #
    "калькулятор": "calculator",                                    #
    "calculator": "calculator"                                      #
}                                                                   #
                                                                    #
# Системные приложения Windows (не требуют путей)                   #
SYSTEM_APPS = {                                                     #
    "notepad": "notepad.exe",                                       #
    "calculator": "calc.exe",                                       #
    "paint": "mspaint.exe",                                         #
    "explorer": "explorer.exe",                                     #
    "cmd": "cmd.exe",                                               #
    "powershell": "powershell.exe"                                  #
}                                                                   #  
                                                                    #
#####################################################################

#############################################################################################
                                                                                            #
def launch_app(app_path, tts, app_name):                                                    #
    """Запуск приложения с обработкой ошибок"""                                             #
    try:                                                                                    #
        if " " in app_path and ("--" in app_path or "/" in app_path):                       #
            subprocess.Popen(app_path, shell=True)                                          #
        else:                                                                               #
            subprocess.Popen(app_path)                                                      #
        if tts:                                                                             #
            tts.speak(f"Запускаю {app_name}")                                               #   Заглушка на случай не предвиденной команды.
        return True                                                                         #
    except FileNotFoundError:                                                               #
        if tts:                                                                             #
            tts.speak(f"Приложение {app_name} не найдено. Проверьте путь в настройках.")    #
        return False                                                                        #
    except Exception as e:                                                                  #
        print(f"Error launching {app_name}: {e}")                                           #
        if tts:                                                                             #
            tts.speak(f"Не удалось запустить {app_name}")                                   #
        return False                                                                        #
                                                                                            #
#############################################################################################

def handle_command(text, tts, config, **kwargs):                      #
    text = text.lower().strip()                             # инициализация
    apps = config.get("modules", {}).get("apps", {})        #
    
     ####################################################################################################################
                                                                                                                        #
    qwen_data = config.pop('qwen_context', None)                                                                        #
                                                                                                                        #
    if qwen_data:                                                                                                       #
        target = qwen_data.get("target")                                                                                #
        action = qwen_data.get("action", "")                                                                            #
                                                                                                                        #
        if target:                                                                                                      #
            try:                                                                                                        #
                # 1. Если Qwen передал точный путь к папке или файлу (из твоего config.json)                            #
                if os.path.exists(target):                                                                              #
                    print(f"📂 Qwen: Открываю путь -> {target}")                                                        #
                    os.startfile(target)                                                                                #
                    if tts: tts.speak("Открываю")                                                                       #
                    return True                                                                                         #
                                                                                                                        #
                # 2. Если Qwen понял, что это сайт, и передал ссылку                                                    #
                elif target.startswith("http"):                                                                         #
                    print(f"🌐 Qwen: Открываю ссылку -> {target}")                                                      # Блок извлечения Qwen (старый код, сейчас не активен)
                    webbrowser.open(target)                                                                             # возможно позже верну в цикл, но пока идей нет
                    if tts: tts.speak("Открываю страницу")                                                              #
                    return True                                                                                         #
                                                                                                                        #
                # 3. Если Qwen передал системное имя приложения (например, "notepad" или "chrome")                      #
                else:                                                                                                   #
                    if target in apps:                                                                                  #
                        launch_app(apps[target], tts, target)                                                           #
                        return True                                                                                     #
                    elif target in SYSTEM_APPS:                                                                         #
                        launch_app(SYSTEM_APPS[target], tts, target)                                                    #
                        return True                                                                                     #
            except Exception as e:                                                                                      #
                print(f"❌ Ошибка выполнения инструкции Qwen: {e}")                                                     #
                if tts: tts.speak("Не удалось открыть запрошенный путь")                                                #
                                                                                                                        #
            return True # Завершаем работу                                                                              #
                                                                                                                        #
     ####################################################################################################################

     ####################################################################
                                                                        #
    # Диспетчер задач                                                   #
    if "диспетчер задач" in text or "task manager" in text:             #
        subprocess.Popen("taskmgr.exe")                                 #
        if tts:                                                         #
            tts.speak("Открываю диспетчер задач")                       #
        return                                                          #
                                                                        #
    # Панель управления                                                 #
    if "панель управления" in text:                                     #
        subprocess.Popen("control.exe")                                 #
        if tts:                                                         #
            tts.speak("Открываю панель управления")                     #
        return                                                          #
                                                                        #
    # Настройки Windows                                                 #
    if "настройки" in text and "windows" in text:                       #
        subprocess.Popen("ms-settings:", shell=True)                    #
        if tts:                                                         #
            tts.speak("Открываю настройки Windows")                     #
        return                                                          #
                                                                        #
    # Сайты                                                             #
    if "youtube" in text or "ютуб" in text or "ютюб" in text:           #
        webbrowser.open("https://www.youtube.com")                      #
        if tts:                                                         #
            tts.speak("Открываю YouTube")                               # Блок выбора действия.
        return                                                          #
                                                                        #
    if "chatgpt" in text or "чатгпт" in text or "чат гпт" in text:      #
        webbrowser.open("https://chat.openai.com")                      #
        if tts:                                                         #
            tts.speak("Открываю ChatGPT")                               #
        return                                                          #
                                                                        #
    if "google" in text or "гугл" in text:                              #
        webbrowser.open("https://www.google.com")                       #
        if tts:                                                         #
            tts.speak("Открываю Google")                                #
        return                                                          #
                                                                        #
    # Приложения из конфига и системные                                 #
    for alias, app_key in APP_ALIASES.items():                          #
        if alias in text:                                               #
            # Сначала проверяем конфиг                                  #
            if app_key in apps:                                         #
                launch_app(apps[app_key], tts, alias)                   #
                return                                                  #
            # Затем системные приложения                                #
            elif app_key in SYSTEM_APPS:                                #
                launch_app(SYSTEM_APPS[app_key], tts, alias)            #
                return                                                  #
                                                                        #
    # Fallback для браузера                                             #
    if "браузер" in text or "интернет" in text:                         #
        webbrowser.open("https://google.com")                           #
        if tts:                                                         #
            tts.speak("Открываю браузер")                               #
        return                                                          #
                                                                        #
    #####################################################################