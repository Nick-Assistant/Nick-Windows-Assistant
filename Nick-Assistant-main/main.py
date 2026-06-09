import os 
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

import sys
import json
import threading
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal # Добавлены модули для потоков

from core.tts import TextToSpeech
from core.stt import SpeechToText
from core.processor import CommandProcessor
from ui.gui import AssistantGUI
from avatar_server import AvatarServer

# Импортируем наш новый модуль браузера
from browser import BrowserManager 

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

class BrowserWorker(QThread):
    """Фоновый поток для работы с Gemini через Playwright, чтобы не тормозить интерфейс"""
    response_ready = pyqtSignal(str)

    def __init__(self, tts=None):
        super().__init__()
        self.manager = None
        self._query_queue = []
        self.is_running = True
        self.tts = tts
        self.current_profile_name = "default"

    def run(self):
        self.manager = BrowserManager()
        self.current_profile_name = self.manager.current_profile_name

        while self.is_running:
            if self._query_queue:
                query = self._query_queue.pop(0)
                
                if query == "CMD_TOGGLE_BROWSER":
                    self.manager.toggle_browser()
                    
                # ОБНОВЛЕННЫЙ БЛОК ПЕРЕКЛЮЧЕНИЯ
                elif str(query).startswith("CMD_SWITCH_PROFILE"):
                    # Вытаскиваем цель (translator, --- или cycle)
                    target = query.split(":")[1] if ":" in query else "cycle"
                    
                    # Браузер меняет папку и возвращает название нового режима
                    new_profile_name = self.manager.switch_profile(target)
                    
                    # ----------------------------------------------------
                    self.current_profile_name = new_profile_name
                    # ----------------------------------------------------
                    if new_profile_name == "nika":
                        self.tts.set_language("ru", "kseniya") # Голос ---
                        self.tts.speak(f"<speak>Разврат  <break time=\"500ms\"/> эм... <break time=\"300ms\"/> всмыысссль+э <break time=\"200ms\"/> *возвр+ат*... <break time=\"200ms\"/> к настройкам к+ошко жен+ы.</speak>")
                        
                    elif new_profile_name == "translator":
                        # Здесь в будущем ты можешь переключить TTS на английскую модель (например, v3_en)
                        self.tts.set_language("en", "en_0")
                        self.tts.speak("<speak>Translator mode has been enabled.</speak>")
                        
                    else: # default
                        self.tts.set_language("ru", "eugene") # Обычный голос Ника
                        self.tts.speak("<speak>Возврат к стандартным настройкам. Я готов.</speak>")
                        
                else:
                    # ----------------------------------------------------
                    # МЕСТО ДЛЯ БУДУЩЕЙ ИНТЕГРАЦИИ API
                    # ----------------------------------------------------
                    # Если активен профиль переводчика, мы можем проигнорировать браузер
                    # и отправить запрос напрямую в API:
                    # if self.manager.current_profile_name == "translator":
                    #     response = my_api_translator.translate(query)
                    # else:
                    
                    # Обычный запрос через браузер
                    response = self.manager.send_query(query)
                    self.response_ready.emit(response)
                    
            self.msleep(100)

    def execute_query(self, query):
        self._query_queue.append(query)
        
    def stop(self):
        self.is_running = False
        if self.manager:
            self.manager.close()

    def setting(self):
        self._query_queue.append("CMD_TOGGLE_BROWSER")

class JarvisAssistant:
    def __init__(self):
        self.config = self.load_config()
        self.tts = TextToSpeech(os.path.join(BASE_PATH, "config.json"))
        self.stt = SpeechToText(os.path.join(BASE_PATH, "config.json"))
        
        # 1. Запускаем поток для Gemini
        self.browser_thread = BrowserWorker(self.tts)
        self.browser_thread.response_ready.connect(self.handle_gemini_response)
        
        self.browser_thread.start()

        # 2. Инициализируем процессор и передаем ему ссылку на поток браузера
        self.processor = CommandProcessor(
            config_path=os.path.join(BASE_PATH, "config.json"), 
            tts=self.tts,
            gemini_worker=self.browser_thread
        )
        
        self.is_listening = False
        self.gui = None
        self.first_start = True

    def handle_gemini_response(self, text):
        """Метод принимает ответ от Gemini, выводит его в окно и озвучивает"""
        if self.gui:
            self.gui.signals.jarvis_response.emit(text)
            self.gui.signals.log_message.emit(f"Gemini: {text}")
        
        # 2. Подготавливаем текст для озвучки
        tts_text = text
        
        # Если Gemini не добавила тег <speak> сама, оборачиваем принудительно
        if "<speak>" not in tts_text:
            tts_text = f"<speak>{tts_text}</speak>"
            
        # 3. Отправляем в TTS
        self.tts.speak(tts_text)

    def load_config(self):
        config_path = os.path.join(BASE_PATH, "config.json")
        example_path = os.path.join(BASE_PATH, "config.example.json")
        
        if not os.path.exists(config_path):
            if os.path.exists(example_path):
                import shutil
                shutil.copy(example_path, config_path)
                print("✅ Создан config.json из шаблона")
            else:
                raise FileNotFoundError("Не найден config.json или config.example.json")
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def start_listening(self):
        self.is_listening = True
        
        if self.gui:
            self.gui.signals.log_message.emit("🚀 Система запущена")
            self.gui.signals.status_update.emit("Слушаю...")
            self.gui.signals.listening_state.emit(True)
        
        if self.first_start and self.config.get("assistant", {}).get("greeting", True):
            name = self.config.get("assistant", {}).get("name", "Ник")
            self.tts.speak(f"<speak>Привет! Я {name} <break time=\"300ms\"/>, к вашим услугам.</speak>")
            self.first_start = False
        
        wake_words = self.config.get("assistant", {}).get("wake_words", ["ник "])
        
        while self.is_listening:
            try:
                text = self.stt.listen()
                if not text:
                    continue
                
                text_lower = text.lower().strip()
                
                # 1. Получаем текущий режим ассистента
                current_mode = self.browser_thread.current_profile_name
                
                command_text = ""
                
                if current_mode == "translator":
                    # В РЕЖИМЕ ПЕРЕВОДЧИКА: Слушаем всё подряд
                    command_text = text_lower
                    # На всякий случай вырезаем слово "ник", чтобы он не переводил его как имя собственное
                    if command_text.startswith("ник "):
                        command_text = command_text[4:].strip()
                        
                    if not command_text:
                        continue
                else:
                    # В ОБЫЧНОМ РЕЖИМЕ: Ищем имя-триггер
                    is_wake_word = False
                    for word in wake_words:
                        if word in text_lower:
                            is_wake_word = True
                            command_text = text_lower.split(word, 1)[-1].strip()
                            break
                    
                    if not is_wake_word:
                        continue
                
                if self.gui:
                    self.gui.signals.log_message.emit(f"Вы: {text}")
                
                # Фразы откликания ("Да, сэр?") используем только в обычном режиме
                if not command_text and current_mode != "translator":
                    responses = ["Да, сэр?", "Слушаю вас", "Чем могу помочь?", "К вашим услугам"]
                    import random
                    self.tts.speak(random.choice(responses))
                    continue

                print(f"\n{'='*50}")
                self.processor.process(command_text)
                        
            except Exception as e:
                print(f"Error in listening loop: {e}")
                time.sleep(0.5)
                
    def stop_listening(self):
        self.is_listening = False
        self.stt.stop_stream()
        
        if self.gui:
            self.gui.signals.status_update.emit("Пауза")
            self.gui.signals.listening_state.emit(False)
            self.gui.signals.log_message.emit("⏸️ Прослушивание остановлено")
            
    def cleanup(self):
        """Корректно закрываем скрытый браузер при выходе"""
        self.stop_listening()
        self.browser_thread.stop()
        self.browser_thread.wait()

def main():
    from PyQt5.QtCore import Qt
    from ui.gui import SplashScreen

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setApplicationName("NICK ASSISTANT")
    app.setStyle("Fusion")
    
    assistant = JarvisAssistant()
    gui = AssistantGUI(assistant)
    assistant.gui = gui
    assistant.tts.set_gui(gui)
    
    splash = SplashScreen()
    server = AvatarServer()
    assistant.tts.server = server
    
    # Привязываем очистку ресурсов браузера к закрытию приложения
    app.aboutToQuit.connect(assistant.cleanup)
    
    def on_splash_finished():
        gui.show()
        gui.start_with_greeting()
    
    splash.finished.connect(on_splash_finished)
    splash.start_animation()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()