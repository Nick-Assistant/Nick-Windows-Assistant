import os
import sys
import threading
import queue

# Убеждаемся, что Python видит модули проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.tts import TextToSpeech
from core.processor import CommandProcessor
from browser import BrowserManager 

class ConsoleGeminiWorker:
    """Правильный заменитель BrowserWorker с изолированным потоком и очередью"""
    def __init__(self, tts):
        self.tts = tts
        self.query_queue = queue.Queue()
        self.is_running = True
        
        # Запускаем единственный фоновый поток
        self.thread = threading.Thread(target=self._run_browser_loop, daemon=True)
        self.thread.start()
        
    def _run_browser_loop(self):
        # ВАЖНО: Инициализация браузера происходит ВНУТРИ рабочего потока
        self.manager = BrowserManager()
        
        while self.is_running:
            try:
                # Ждем новую команду (таймаут нужен, чтобы поток мог плавно завершиться)
                query = self.query_queue.get(timeout=0.5)
                
                if query == "CMD_TOGGLE_BROWSER":
                    self.manager.toggle_browser()
                elif query == "CMD_STOP":
                    break
                else:
                    response = self.manager.send_query(query)
                    print(f"\n🤖 Ник (Gemini): {response}")
                    
                    # Оборачиваем в SSML
                    tts_text = response
                    if "<speak>" not in tts_text:
                        tts_text = f"<speak>{tts_text}</speak>"
                        
                    self.tts.speak(tts_text)
                    print("\nТы: ", end="", flush=True)
                    
                self.query_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"\n❌ Ошибка в потоке браузера: {e}")
                print("\nТы: ", end="", flush=True)

    def execute_query(self, query):
        """Просто кладем запрос в очередь, поток заберет его сам"""
        self.query_queue.put(query)
        
    def setting(self):
        self.query_queue.put("CMD_TOGGLE_BROWSER")
        
    def stop(self):
        self.is_running = False
        self.query_queue.put("CMD_STOP")
        self.thread.join()
        if hasattr(self, 'manager'):
            self.manager.close()

def main():
    print("⏳ Инициализация систем (Консольный режим отладки)...")
    
    tts = TextToSpeech("config.json")
    gemini_worker = ConsoleGeminiWorker(tts)
    processor = CommandProcessor(config_path="config.json", tts=tts, gemini_worker=gemini_worker)
    
    print("\n✅ Система готова. Вводи команды с клавиатуры (или 'выход' для завершения).")
    
    while True:
        try:
            user_input = input("\nТы: ").strip()
            
            if user_input.lower() in ['выход', 'exit', 'quit']:
                print("Завершение работы...")
                gemini_worker.stop()
                break
            
            if not user_input:
                continue
                
            processor.process(user_input)
            
        except KeyboardInterrupt:
            print("\nПринудительная остановка.")
            gemini_worker.stop()
            break

if __name__ == "__main__":
    main()