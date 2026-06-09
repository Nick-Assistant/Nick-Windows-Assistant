import os

KEYWORDS = ["создай", "запрограммируй", "напиши код", "напиши скрипт"]

def handle_command(text, tts, config, gemini_worker=None, **kwargs):
    print("🧠 Выполнение: Локальный код (Interpreter)")
    if tts: tts.speak("<speak>Запускаю локальную сред+у. Выполняю...</speak>")
    
    try:
        os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
        from interpreter import interpreter
        
        interpreter.messages = [] 
        interpreter.offline = True
        interpreter.llm.model = "ollama/my-assistant" 
        interpreter.llm.api_base = "http://127.0.0.1:11434"
        interpreter.auto_run = True 
        interpreter.chat(text)
        
        if tts: tts.speak("Код успешно выполнен.")
    except Exception as e:
        print(f"❌ Ошибка Interpreter: {e}")
        if tts: tts.speak("Произошла ошибка при выполнении кода.")