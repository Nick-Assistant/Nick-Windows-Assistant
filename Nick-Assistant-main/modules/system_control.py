import os
import re
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume

KEYWORDS = [
    "громкость", "яркость", "звук", "громче", "тише", "ярче", "темнее",
    "сделай громче", "сделай тише", "увеличь громкость", "уменьши громкость",
    "выключи компьютер", "выруби комп", "перезагрузи", "ребут", "перезагрузка",
    "спящий режим", "сон", "заблокируй", "блокировка", "выйди из системы",
    "батарея", "заряд", "аккумулятор"
]

# Словарь для преобразования слов в числа
WORD_TO_NUM = {
    "ноль": 0, "один": 1, "два": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
    "восемнадцать": 18, "девятнадцать": 19, "двадцать": 20,
    "тридцать": 30, "сорок": 40, "пятьдесят": 50, "шестьдесят": 60,
    "семьдесят": 70, "восемьдесят": 80, "девяносто": 90, "сто": 100
}

def parse_number(text):
    """Извлекает число из текста (цифры или слова)"""
    # Сначала ищем цифры
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    
    # Ищем слова-числа
    total = 0
    found = False
    for word, num in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        if word in text:
            total += num
            found = True
            text = text.replace(word, "", 1)
    
    return total if found else None

def get_volume_interface():
    """Получение интерфейса управления громкостью"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except Exception as e:
        print(f"Pycaw error: {e}")
        return None

def handle_command(text, tts, config, **kwargs):
    text = text.lower().strip()
    
    # === БЛОК ПЕРЕХВАТА QWEN ===
    qwen_data = config.pop('qwen_context', None)
    if qwen_data:
        action = qwen_data.get("action", "").lower()
        target = str(qwen_data.get("target", ""))
        
        try:
            if "громкость" in action or "звук" in action:
                volume = get_volume_interface()
                import pyautogui  # Запасной метод
                
                if volume:
                    if target.isdigit():
                        volume.SetMasterVolumeLevelScalar(int(target) / 100, None)
                    elif "увелич" in action:
                        current = volume.GetMasterVolumeLevelScalar() * 100
                        volume.SetMasterVolumeLevelScalar(min(current + 10, 100) / 100, None)
                    elif "уменьш" in action:
                        current = volume.GetMasterVolumeLevelScalar() * 100
                        volume.SetMasterVolumeLevelScalar(max(current - 10, 0) / 100, None)
                else:
                    # РЕЗЕРВНЫЙ ВАРИАНТ (сработает, раз Pycaw выдает ошибку)
                    if "увелич" in action or "громче" in action:
                        pyautogui.press('volumeup', presses=5)
                    elif "уменьш" in action or "тише" in action:
                        pyautogui.press('volumedown', presses=5)
                
                if tts: tts.speak("Выполнил")
                
            elif "яркость" in action:
                if target.isdigit():
                    sbc.set_brightness(int(target))
                    if tts: tts.speak(f"Яркость {target}")
            elif "выключ" in action and "комп" in action:
                os.system("shutdown /s /t 5")
                if tts: tts.speak("Выключаю")
            elif "перезагруз" in action:
                os.system("shutdown /r /t 3")
            elif "сон" in action or "спящ" in action:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        except Exception as e:
            print(f"Ошибка Qwen в system_control: {e}")
        return True
    # === КОНЕЦ БЛОКА QWEN ===

    # Выключение
    if "выключи компьютер" in text or "выруби комп" in text:
        if tts:
            tts.speak("Выключаю компьютер через 5 секунд.")
        os.system("shutdown /s /t 5")
        return
    
    # Перезагрузка
    if "перезагрузи" in text or "ребут" in text or "перезагрузка" in text:
        if tts:
            tts.speak("Перезагружаю систему.")
        os.system("shutdown /r /t 3")
        return
    
    # Спящий режим
    if "спящий режим" in text or "режим сна" in text or text == "сон":
        if tts:
            tts.speak("Перехожу в спящий режим.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return
    
    # Блокировка
    if "заблокируй" in text or "блокировка" in text or "заблокировать" in text:
        if tts:
            tts.speak("Блокирую компьютер.")
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return
    
    # Выход из системы
    if "выйди из системы" in text or "выйти из системы" in text or "логаут" in text:
        if tts:
            tts.speak("Выхожу из системы.")
        os.system("shutdown /l")
        return
    
    # Информация о батарее
    if "батарея" in text or "заряд" in text or "аккумулятор" in text:
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = "на зарядке" if battery.power_plugged else "от батареи"
                if tts:
                    tts.speak(f"Заряд батареи {percent} процентов, работаю {plugged}")
            else:
                if tts:
                    tts.speak("Батарея не обнаружена, вероятно это стационарный компьютер")
        except ImportError:
            if tts:
                tts.speak("Для проверки батареи установите библиотеку psutil")
        except Exception as e:
            print(f"Battery check error: {e}")
            if tts:
                tts.speak("Не удалось проверить батарею")
        return
    
    # Проверяем команды громкости - расширенные условия
    volume_keywords = ["громкость", "звук", "громче", "тише", "сделай громче", "сделай тише", "увеличь громкость", "уменьши громкость"]
    is_volume_command = any(kw in text for kw in volume_keywords)
    
    if is_volume_command:
        try:
            volume = get_volume_interface()
            if volume is None:
                # Fallback: используем клавиши
                import pyautogui
                if "громче" in text or "повысь" in text or "увеличь" in text:
                    pyautogui.press('volumeup', presses=5)
                    if tts: tts.speak("Громкость увеличена")
                elif "тише" in text or "понизь" in text or "уменьши" in text:
                    pyautogui.press('volumedown', presses=5)
                    if tts: tts.speak("Громкость уменьшена")
                elif "выключи звук" in text or "без звука" in text:
                    pyautogui.press('volumemute')
                    if tts: tts.speak("Звук выключен")
                return
            
            current_vol = volume.GetMasterVolumeLevelScalar() * 100
            
            # Проверяем конкретное значение громкости (цифры или слова)
            # "громкость 70" или "громкость семьдесят"
            target_vol = parse_number(text)
            if target_vol is not None and 0 <= target_vol <= 100:
                # Убеждаемся что это команда установки, а не изменения
                if not any(word in text for word in ["громче", "тише", "повысь", "понизь", "увеличь", "уменьши"]):
                    volume.SetMasterVolumeLevelScalar(target_vol / 100, None)
                    if tts: tts.speak(f"Громкость {target_vol} процентов")
                    return
            
            if "громче" in text or "повысь" in text or "увеличь" in text:
                new_vol = min(current_vol + 10, 100)
                volume.SetMasterVolumeLevelScalar(new_vol / 100, None)
                if tts: tts.speak(f"Громкость {int(new_vol)} процентов")
                return
                
            elif "тише" in text or "понизь" in text or "уменьши" in text:
                new_vol = max(current_vol - 10, 0)
                volume.SetMasterVolumeLevelScalar(new_vol / 100, None)
                if tts: tts.speak(f"Громкость {int(new_vol)} процентов")
                return
                
            elif "максимум" in text:
                volume.SetMasterVolumeLevelScalar(1.0, None)
                if tts: tts.speak("Громкость на максимум")
                return
                
            elif "выключи звук" in text or "без звука" in text:
                volume.SetMute(1, None)
                if tts: tts.speak("Звук выключен")
                return
                
            elif "включи звук" in text:
                volume.SetMute(0, None)
                if tts: tts.speak("Звук включен")
                return
        except Exception as e:
            print(f"Error changing volume: {e}")
            # Fallback на клавиши
            try:
                import pyautogui
                if "громче" in text:
                    pyautogui.press('volumeup', presses=5)
                    if tts: tts.speak("Громкость увеличена")
                elif "тише" in text:
                    pyautogui.press('volumedown', presses=5)
                    if tts: tts.speak("Громкость уменьшена")
                return
            except:
                if tts: tts.speak("Не удалось изменить громкость")
            return

    # Проверяем команды яркости
    brightness_keywords = ["яркость", "ярче", "темнее"]
    is_brightness_command = any(kw in text for kw in brightness_keywords)
    
    if is_brightness_command:
        try:
            current_brightness = sbc.get_brightness()
            if isinstance(current_brightness, list):
                current_brightness = current_brightness[0]
            
            # Проверяем конкретное значение яркости
            # "яркость 50" или "яркость пятьдесят"
            target_brightness = parse_number(text)
            if target_brightness is not None and 0 <= target_brightness <= 100:
                if not any(word in text for word in ["ярче", "темнее", "повысь", "понизь", "увеличь", "уменьши"]):
                    sbc.set_brightness(target_brightness)
                    if tts: tts.speak(f"Яркость {target_brightness} процентов")
                    return
                
            if "ярче" in text or "повысь" in text or "увеличь" in text:
                new_brightness = min(current_brightness + 10, 100)
                sbc.set_brightness(new_brightness)
                if tts: tts.speak(f"Яркость {new_brightness} процентов")
                return
                
            elif "темнее" in text or "понизь" in text or "уменьши" in text:
                new_brightness = max(current_brightness - 10, 0)
                sbc.set_brightness(new_brightness)
                if tts: tts.speak(f"Яркость {new_brightness} процентов")
                return
        except Exception as e:
            print(f"Error changing brightness: {e}")
            if tts: tts.speak("Не удалось изменить яркость")
            return