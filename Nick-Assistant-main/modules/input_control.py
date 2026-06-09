"""
Модуль управления вводом - клавиатура, мышь, файлы
"""
import os
import pyautogui
import time
import pyperclip

KEYWORDS = [
    "набери", "напиши", "введи", "текст",
    "нажми", "клавиша", "хоткей",
    "копировать", "вставить", "вырезать", "выделить всё",
    "энтер", "enter", "эскейп", "escape", "таб", "tab",
    "отмена", "ctrl z", "повтор", "ctrl y",
    "сохрани", "ctrl s",
    "открой папку",
    "закрыть", "закрой окно"
]

def handle_command(text, tts, config, **kwargs):
    text = text.lower().strip()
    
    # === БЛОК ПЕРЕХВАТА QWEN ===
    qwen_data = config.pop('qwen_context', None)
    if qwen_data:
        action = qwen_data.get("action", "").lower()
        target = qwen_data.get("target", "")
        
        try:
            if "ввод" in action or "напиши" in action or "текст" in action:
                old_clipboard = pyperclip.paste()
                pyperclip.copy(target)
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.1)
                pyperclip.copy(old_clipboard)
                if tts: tts.speak("Написал")
            elif "клавиш" in action or "нажми" in action:
                pyautogui.press(target)
                if tts: tts.speak("Нажал")
            elif "создай" in action and "файл" in action:
                filename = target if "." in target else f"{target}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("")
                if tts: tts.speak("Файл создан")
            elif "удали" in action and "файл" in action:
                if os.path.exists(target):
                    os.remove(target)
                    if tts: tts.speak("Удалил")
        except Exception as e:
            print(f"Ошибка Qwen в input_control: {e}")
        return True
    # === КОНЕЦ БЛОКА QWEN ===

    # Ввод текста (используем буфер обмена для кириллицы)
    if any(word in text for word in ["набери", "напиши", "введи"]):
        content = text
        for word in ["набери", "напиши", "введи"]:
            content = content.replace(word, "")
        content = content.strip()
        
        if content:
            try:
                # Сохраняем текущий буфер
                old_clipboard = pyperclip.paste()
                # Копируем текст в буфер
                pyperclip.copy(content)
                # Вставляем
                time.sleep(0.1)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(0.1)
                # Восстанавливаем буфер
                pyperclip.copy(old_clipboard)
                if tts:
                    tts.speak("Готово")
            except:
                # Fallback на обычный ввод
                pyautogui.write(content, interval=0.05)
                if tts:
                    tts.speak("Напечатал")
        return

    # Быстрые команды клавиш
    if "копировать" in text or "скопируй" in text:
        pyautogui.hotkey('ctrl', 'c')
        if tts:
            tts.speak("Скопировано")
        return
    
    if "вставить" in text or "вставь" in text:
        pyautogui.hotkey('ctrl', 'v')
        if tts:
            tts.speak("Вставлено")
        return
    
    if "вырезать" in text or "вырежи" in text:
        pyautogui.hotkey('ctrl', 'x')
        if tts:
            tts.speak("Вырезано")
        return
    
    if "выделить всё" in text or "выдели всё" in text:
        pyautogui.hotkey('ctrl', 'a')
        if tts:
            tts.speak("Выделено")
        return
    
    if "отмена" in text or "отмени" in text or "ctrl z" in text:
        pyautogui.hotkey('ctrl', 'z')
        if tts:
            tts.speak("Отменено")
        return
    
    if "повтор" in text or "повтори действие" in text or "ctrl y" in text:
        pyautogui.hotkey('ctrl', 'y')
        if tts:
            tts.speak("Повторено")
        return
    
    if "сохрани" in text or "сохранить" in text or "ctrl s" in text:
        pyautogui.hotkey('ctrl', 's')
        if tts:
            tts.speak("Сохранено")
        return

    # Нажатия клавиш
    if "нажми" in text:
        key_cmd = text.replace("нажми", "").strip()
        
        if "энтер" in key_cmd or "enter" in key_cmd or "ввод" in key_cmd:
            pyautogui.press('enter')
        elif "эскейп" in key_cmd or "escape" in key_cmd or "отмена" in key_cmd:
            pyautogui.press('escape')
        elif "таб" in key_cmd or "tab" in key_cmd:
            pyautogui.press('tab')
        elif "пробел" in key_cmd or "space" in key_cmd:
            pyautogui.press('space')
        elif "бэкспейс" in key_cmd or "backspace" in key_cmd or "удалить" in key_cmd:
            pyautogui.press('backspace')
        elif "delete" in key_cmd or "делит" in key_cmd:
            pyautogui.press('delete')
        elif "вверх" in key_cmd:
            pyautogui.press('up')
        elif "вниз" in key_cmd:
            pyautogui.press('down')
        elif "влево" in key_cmd:
            pyautogui.press('left')
        elif "вправо" in key_cmd:
            pyautogui.press('right')
        
        if tts:
            tts.speak("Готово")
        return
    
    # Одиночные команды клавиш
    if text in ["энтер", "enter", "ввод"]:
        pyautogui.press('enter')
        if tts:
            tts.speak("Готово")
        return
    
    if text in ["эскейп", "escape", "отмена"]:
        pyautogui.press('escape')
        if tts:
            tts.speak("Готово")
        return

    # Файловые операции
    if "создай файл" in text:
        filename = text.replace("создай файл", "").strip()
        if not filename:
            filename = "new_file.txt"
        if not "." in filename:
            filename += ".txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("")
            if tts:
                tts.speak(f"Файл {filename} создан")
        except Exception as e:
            print(f"File creation error: {e}")
            if tts:
                tts.speak("Не удалось создать файл")
        return

    if "удалить файл" in text or "удали файл" in text:
        filename = text.replace("удалить файл", "").replace("удали файл", "").strip()
        if os.path.exists(filename):
            os.remove(filename)
            if tts:
                tts.speak(f"Файл удалён")
        else:
            if tts:
                tts.speak("Файл не найден")
        return

    if "открой папку" in text:
        path = text.replace("открой папку", "").strip()
        if not path:
            path = "."
        try:
            os.startfile(os.path.abspath(path))
            if tts:
                tts.speak("Открываю")
        except:
            if tts:
                tts.speak("Папка не найдена")
        return
    
    # Закрытие окна
    if "закрой окно" in text or "закрой это" in text or text == "закрыть":
        pyautogui.hotkey('alt', 'f4')
        if tts:
            tts.speak("Закрываю")
        return