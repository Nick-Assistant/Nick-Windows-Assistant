"""
Модуль умного ассистента - ответы на вопросы, время, дата, калькулятор, заметки
"""
import datetime
import math
import re
import json
import os
import requests

KEYWORDS = [
    "который час", "сколько времени", "время", "дата", "какой день", "какое число",
    "посчитай", "сколько будет", "калькулятор", "вычисли",
    "погода", "какая погода", "температура",
    "запомни", "заметка", "что запомнил", "мои заметки",
    "кто ты", "как тебя зовут", "что ты умеешь", "помощь",
    "привет", "здравствуй", "доброе утро", "добрый день", "добрый вечер", "спокойной ночи",
    "спасибо", "благодарю", "молодец", "хорошо",
    "пока", "до свидания", "выход",
    "как дела", "что нового", "расскажи анекдот", "шутка"
]

# Словарь для преобразования слов в числа
WORD_TO_NUM = {
    "ноль": 0, "один": 1, "два": 2, "три": 3, "четыре": 4,
    "пять": 5, "шесть": 6, "семь": 7, "восемь": 8, "девять": 9,
    "десять": 10, "одиннадцать": 11, "двенадцать": 12, "тринадцать": 13,
    "четырнадцать": 14, "пятнадцать": 15, "шестнадцать": 16, "семнадцать": 17,
    "восемнадцать": 18, "девятнадцать": 19, "двадцать": 20,
    "тридцать": 30, "сорок": 40, "пятьдесят": 50, "шестьдесят": 60,
    "семьдесят": 70, "восемьдесят": 80, "девяносто": 90, "сто": 100,
    "двести": 200, "триста": 300, "четыреста": 400, "пятьсот": 500,
    "тысяча": 1000
}

NOTES_FILE = "jarvis_notes.json"

def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_notes(notes):
    with open(NOTES_FILE, 'w', encoding='utf-8') as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

def words_to_number(text):
    """Преобразует слова-числа в цифры"""
    result = text
    for word, num in sorted(WORD_TO_NUM.items(), key=lambda x: -len(x[0])):
        result = result.replace(word, str(num))
    return result

def calculate(expression):
    """Безопасный калькулятор с поддержкой слов"""
    try:
        expr = expression.lower()
        
        # Преобразуем слова в числа
        expr = words_to_number(expr)
        
        # Заменяем операторы
        expr = expr.replace("плюс", "+").replace("минус", "-")
        expr = expr.replace("умножить на", "*").replace("умножить", "*")
        expr = expr.replace("разделить на", "/").replace("делить на", "/").replace("делить", "/")
        expr = expr.replace("в степени", "**").replace("степень", "**")
        expr = expr.replace(",", ".")
        
        # Убираем лишние слова но оставляем числа и операторы
        expr = re.sub(r'[^\d+\-*/().\s]', ' ', expr)
        expr = ' '.join(expr.split())  # нормализуем пробелы
        expr = expr.replace(' ', '')  # убираем пробелы между числами
        
        # Исправляем случаи типа "15+5" -> работает, "15 + 5" -> работает
        expr = re.sub(r'(\d)\s+(\d)', r'\1\2', expr)  # склеиваем разделённые числа
        
        if expr and re.search(r'\d', expr):
            result = eval(expr, {"__builtins__": {}, "math": math})
            return result
    except Exception as e:
        print(f"Calculate error: {e}, expr: {expression}")
    return None

def get_weather(city="Чанша"):
    """Получение погоды через wttr.in"""
    try:
        # Кодируем город для URL
        import urllib.parse
        encoded_city = urllib.parse.quote(city)
        
        # Пробуем wttr.in
        headers = {'User-Agent': 'curl/7.68.0', 'Accept-Language': 'ru'}
        response = requests.get(
            f"https://wttr.in/{encoded_city}?format=%t+%C&lang=ru",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200 and response.text.strip():
            result = response.text.strip()
            if "Unknown" not in result and "Sorry" not in result:
                return result
    except Exception as e:
        print(f"Weather error: {e}")
    return None

def handle_command(text, tts, config, **kwargs):
    text = text.lower().strip()
    
    # === БЛОК ПЕРЕХВАТА QWEN ===
    qwen_data = config.pop('qwen_context', None)
    if qwen_data:
        action = qwen_data.get("action", "").lower()
        target = str(qwen_data.get("target", ""))
        
        if "заметк" in action or "запомни" in action:
            notes = load_notes()
            notes.append({"text": target, "date": datetime.datetime.now().isoformat()})
            save_notes(notes)
            if tts: tts.speak(f"Запомнил: {target}")
            return True
        elif target:
            # Если Qwen сам ответил на вопрос, решил задачу или написал шутку
            if tts: tts.speak(target)
            return True
        return True
    # === КОНЕЦ БЛОКА QWEN ===

    # Приветствия
    if any(word in text for word in ["привет", "здравствуй"]):
        tts.speak("Привет! Чем могу помочь?")
        return
    
    if "доброе утро" in text:
        tts.speak("Доброе утро! Надеюсь, день будет продуктивным.")
        return
    
    if "добрый день" in text:
        tts.speak("Добрый день! Я к вашим услугам.")
        return
    
    if "добрый вечер" in text:
        tts.speak("Добрый вечер! Как прошёл день?")
        return
    
    if "спокойной ночи" in text:
        tts.speak("Спокойной ночи! Приятных снов.")
        return

    # Благодарности
    if any(word in text for word in ["спасибо", "благодарю"]):
        tts.speak("Всегда пожалуйста! Обращайтесь.")
        return
    
    if "молодец" in text or "хорошо" in text:
        tts.speak("Стараюсь быть полезным!")
        return
    
    # Прощания
    if any(word in text for word in ["пока", "до свидания"]):
        tts.speak("До встречи! Буду ждать.")
        return
    
    # О себе
    if "кто ты" in text or "как тебя зовут" in text:
        name = config.get("assistant", {}).get("name", "Ник")
        tts.speak(f"Я {name}, ваш персональный голосовой ассистент. Создан чтобы помогать вам.")
        return
    
    if "что ты умеешь" in text or "помощь" in text:
        tts.speak("Я умею: открывать приложения и сайты, управлять громкостью и яркостью, "
                  "говорить время и дату, считать, запоминать заметки, искать в интернете, "
                  "и многое другое. Просто скажите что нужно!")
        return
    
    if "как дела" in text:
        tts.speak("Отлично! Все системы работают стабильно. А у вас как?")
        return
    
    # Время и дата
    if "который час" in text or "сколько времени" in text or text == "время":
        now = datetime.datetime.now()
        tts.speak(f"Сейчас {now.hour} часов {now.minute} минут")
        return
    
    if "какой день" in text or "какое число" in text or "дата" in text:
        now = datetime.datetime.now()
        days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
        months = ["января", "февраля", "марта", "апреля", "мая", "июня", 
                  "июля", "августа", "сентября", "октября", "ноября", "декабря"]
        tts.speak(f"Сегодня {days[now.weekday()]}, {now.day} {months[now.month-1]} {now.year} года")
        return
    
    # Калькулятор
    if any(word in text for word in ["посчитай", "сколько будет", "вычисли"]):
        expr = text.replace("посчитай", "").replace("сколько будет", "").replace("вычисли", "").strip()
        result = calculate(expr)
        if result is not None:
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            tts.speak(f"Результат: {result}")
        else:
            tts.speak("Не смог вычислить. Попробуйте сказать по-другому.")
        return
    
    # Погода
    if "погода" in text or "температура" in text:
        # Пытаемся извлечь город
        city = "Чанша"
        words = text.split()
        for i, word in enumerate(words):
            if word in ["в", "для"] and i + 1 < len(words):
                city = words[i + 1]
                break
        
        weather = get_weather(city)
        if weather:
            tts.speak(f"Погода в городе {city}: {weather}")
        else:
            tts.speak("Не удалось получить данные о погоде. Проверьте интернет.")
        return
    
    # Заметки
    if "запомни" in text or "заметка" in text:
        note_text = text.replace("запомни", "").replace("заметка", "").strip()
        if note_text:
            notes = load_notes()
            notes.append({
                "text": note_text,
                "date": datetime.datetime.now().isoformat()
            })
            save_notes(notes)
            tts.speak(f"Запомнил: {note_text}")
        else:
            tts.speak("Что нужно запомнить?")
        return
    
    if "что запомнил" in text or "мои заметки" in text:
        notes = load_notes()
        if notes:
            tts.speak(f"У вас {len(notes)} заметок. Последняя: {notes[-1]['text']}")
        else:
            tts.speak("Заметок пока нет.")
        return
    
    # Шутки
    if "анекдот" in text or "шутка" in text or "расскажи" in text:
        jokes = [
            "Программист ставит на тумбочку два стакана. Один с водой — если захочет пить. Второй пустой — если не захочет.",
            "Почему программисты путают Хэллоуин и Рождество? Потому что 31 OCT равно 25 DEC.",
            "Жена программиста просит: Сходи в магазин, купи батон хлеба. Если будут яйца — возьми десяток. Программист вернулся с десятью батонами.",
        ]
        import random
        tts.speak(random.choice(jokes))
        return
