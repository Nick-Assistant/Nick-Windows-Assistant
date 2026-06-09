KEYWORDS = ["открой настройку евгения", "закрой настройку евгения"]

def handle_command(text, tts, config, gemini_worker=None, **kwargs):
    print("🧠 Выполнение: Открытие отладочного окна")
    if tts: 
        tts.speak("<speak>Выво+жу на экран...</speak>")
        
    if gemini_worker:
        gemini_worker.setting()