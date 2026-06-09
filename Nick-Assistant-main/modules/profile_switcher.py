KEYWORDS = [
    "смени режим на", "поменяй режим на", "переключи профиль на", "смени профиль на", 
    "стань", "поменяйся на", "переключись на", "режим"
]

def handle_command(text, tts, config, gemini_worker=None, **kwargs):
    print("🧠 Выполнение: Смена профиля ассистента")
    
    # Определяем целевой профиль по ключевым словам
    target = "cycle" # По умолчанию - просто переключение по кругу
    if any(w in text for w in ["да"]):
        target = "nika"
    elif any(w in text for w in ["перевод", "translator", "переводчиком", "переводчика"]):
        target = "translator"
    elif any(w in text for w in ["обычный", "стандарт", "ник", "ника", "ником", "ника", "обычным", "обычного"]):
        target = "default"

    if tts: 
        tts.set_language("ru")
        tts.speak("<speak>Меняю конфигурацию систем. Секунду.</speak>")
        
    if gemini_worker:
        # Отправляем команду вместе с параметром (например: CMD_SWITCH_PROFILE:translator)
        gemini_worker.execute_query(f"CMD_SWITCH_PROFILE:{target}")
    else:
        print("⚠️ Ошибка: Нет доступа к потоку браузера.")