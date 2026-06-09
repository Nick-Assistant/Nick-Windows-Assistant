"""
Модуль таймеров и напоминаний
"""
import threading
import time
import re
import winsound

KEYWORDS = [
    "таймер", "поставь таймер", "засеки", "секундомер",
    "напомни через", "напоминание", "будильник",
    "отмени таймер", "сколько осталось", "таймер на"
]

# Активные таймеры
active_timers = {}
timer_counter = 0
gui_ref = None  # Ссылка на GUI для обновления

# Словарь для преобразования слов в числа
WORD_TO_NUM = {
    "один": "1", "одну": "1", "одна": "1",
    "два": "2", "две": "2", "двух": "2",
    "три": "3", "трёх": "3", "трех": "3",
    "четыре": "4", "четырёх": "4", "четырех": "4",
    "пять": "5", "пяти": "5",
    "шесть": "6", "шести": "6",
    "семь": "7", "семи": "7",
    "восемь": "8", "восьми": "8",
    "девять": "9", "девяти": "9",
    "десять": "10", "десяти": "10",
    "пятнадцать": "15", "двадцать": "20", "тридцать": "30",
    "сорок": "40", "пятьдесят": "50", "шестьдесят": "60",
    "полчаса": "30 минут", "полминуты": "30 секунд"
}

def words_to_numbers(text):
    """Преобразует слова-числа в цифры"""
    result = text
    for word, num in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, num)
    return result

def parse_time(text):
    """Извлекает время из текста (минуты, секунды, часы)"""
    # Сначала преобразуем слова в числа
    text = words_to_numbers(text)
    print(f"Timer parse_time: '{text}'")
    
    total_seconds = 0
    
    # Часы
    hours_match = re.search(r'(\d+)\s*(час|часа|часов|ч\b)', text)
    if hours_match:
        total_seconds += int(hours_match.group(1)) * 3600
    
    # Минуты
    minutes_match = re.search(r'(\d+)\s*(минут|минуты|минуту|мин\b)', text)
    if minutes_match:
        total_seconds += int(minutes_match.group(1)) * 60
    
    # Секунды
    seconds_match = re.search(r'(\d+)\s*(секунд|секунды|секунду|сек\b)', text)
    if seconds_match:
        total_seconds += int(seconds_match.group(1))
    
    # Если просто число без единиц - считаем минутами
    if total_seconds == 0:
        number_match = re.search(r'(\d+)', text)
        if number_match:
            total_seconds = int(number_match.group(1)) * 60
    
    print(f"Timer total_seconds: {total_seconds}")
    return total_seconds

def update_gui_timer():
    """Обновляет отображение таймера в GUI"""
    global gui_ref, active_timers
    if gui_ref and active_timers:
        for tid, data in active_timers.items():
            remaining = data['end_time'] - time.time()
            if remaining > 0:
                gui_ref.signals.timer_update.emit(f"Таймер: {format_time(int(remaining))}")
                return
    if gui_ref:
        gui_ref.signals.timer_update.emit("")

def timer_callback(timer_id, tts, message=""):
    """Вызывается когда таймер срабатывает"""
    global active_timers, gui_ref
    
    # Звуковой сигнал
    try:
        for _ in range(3):
            winsound.Beep(1000, 500)
            time.sleep(0.2)
    except:
        pass
    
    if tts:
        if message:
            tts.speak(f"Напоминание: {message}")
        else:
            tts.speak("Таймер сработал! Время вышло.")
    
    # Удаляем таймер из активных
    if timer_id in active_timers:
        del active_timers[timer_id]
    
    # Обновляем GUI
    update_gui_timer()

def format_time(seconds):
    """Форматирует секунды в читаемый вид"""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} час{'а' if 1 < hours < 5 else 'ов' if hours >= 5 else ''} {minutes} минут"
    elif seconds >= 60:
        minutes = seconds // 60
        secs = seconds % 60
        if secs > 0:
            return f"{minutes} минут {secs} секунд"
        return f"{minutes} минут"
    else:
        return f"{seconds} секунд"

def handle_command(text, tts, config, **kwargs):
    global active_timers, timer_counter, gui_ref
    text = text.lower().strip()
    
    # === БЛОК ПЕРЕХВАТА QWEN ===
    global active_timers, timer_counter, gui_ref
    qwen_data = config.pop('qwen_context', None)
    if qwen_data:
        action = str(qwen_data.get("action", "")).lower()
        target = str(qwen_data.get("target", ""))
        
        if "отмен" in action:
            if active_timers:
                last_id = max(active_timers.keys())
                active_timers[last_id]['timer'].cancel()
                del active_timers[last_id]
                if tts: tts.speak("Таймер отменён")
            else:
                if tts: tts.speak("Нет активных таймеров")
            return True
            
        seconds = int(target) if target.isdigit() else parse_time(target)
            
        if seconds > 0:
            timer_counter += 1
            timer_id = timer_counter
            message = action if "напомн" in action else ""
            
            timer = threading.Timer(seconds, timer_callback, args=[timer_id, tts, message])
            timer.daemon = True
            timer.start()
            
            active_timers[timer_id] = {'timer': timer, 'end_time': time.time() + seconds, 'message': message}
            if tts: tts.speak(f"Таймер установлен на {format_time(seconds)}")
            
            if gui_ref:
                def update_loop():
                    while timer_id in active_timers:
                        update_gui_timer()
                        time.sleep(1)
                    update_gui_timer()
                threading.Thread(target=update_loop, daemon=True).start()
        return True
    # === КОНЕЦ БЛОКА QWEN ===

    # Получаем ссылку на GUI через TTS
    if tts and hasattr(tts, 'gui') and tts.gui:
        gui_ref = tts.gui
    
    # Отмена таймера
    if "отмени таймер" in text or "останови таймер" in text:
        if active_timers:
            # Отменяем последний таймер
            last_id = max(active_timers.keys())
            active_timers[last_id]['timer'].cancel()
            del active_timers[last_id]
            if tts:
                tts.speak("Таймер отменён")
        else:
            if tts:
                tts.speak("Нет активных таймеров")
        return
    
    # Сколько осталось
    if "сколько осталось" in text:
        if active_timers:
            for tid, data in active_timers.items():
                remaining = data['end_time'] - time.time()
                if remaining > 0:
                    if tts:
                        tts.speak(f"До таймера осталось {format_time(int(remaining))}")
                    return
        if tts:
            tts.speak("Нет активных таймеров")
        return
    
    # Установка таймера
    if any(word in text for word in ["таймер", "засеки", "напомни через"]):
        seconds = parse_time(text)
        
        if seconds <= 0:
            if tts:
                tts.speak("Не понял время. Скажите например: таймер на 5 минут")
            return
        
        # Извлекаем сообщение напоминания если есть
        message = ""
        if "напомни" in text:
            # Пытаемся извлечь что напомнить
            parts = text.split("напомни")
            if len(parts) > 1:
                msg_part = parts[1]
                # Убираем временные слова
                for word in ["через", "минут", "минуты", "секунд", "час", "часа", "часов"]:
                    msg_part = re.sub(rf'\d*\s*{word}\w*', '', msg_part)
                message = msg_part.strip()
        
        timer_counter += 1
        timer_id = timer_counter
        
        timer = threading.Timer(seconds, timer_callback, args=[timer_id, tts, message])
        timer.daemon = True
        timer.start()
        
        active_timers[timer_id] = {
            'timer': timer,
            'end_time': time.time() + seconds,
            'message': message
        }
        
        if tts:
            tts.speak(f"Таймер установлен на {format_time(seconds)}")
        
        # Запускаем обновление GUI
        if gui_ref:
            def update_loop():
                while timer_id in active_timers:
                    update_gui_timer()
                    time.sleep(1)
                update_gui_timer()  # Финальное обновление
            
            update_thread = threading.Thread(target=update_loop, daemon=True)
            update_thread.start()
        
        return
