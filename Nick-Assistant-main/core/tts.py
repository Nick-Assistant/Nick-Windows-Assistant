"""
Text-to-Speech модуль с использованием нейросетевой генерации Silero TTS
"""
import os
import torch
torch.set_num_threads(4)

import sounddevice as sd
import threading
import queue

import time

def get_base_path():
    import sys
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class TextToSpeech:
    def __init__(self, config_path="config.json"):
        self.base_path = get_base_path()
        self.gui = None
        self.server = None
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.sample_rate = 48000
        self.output_device_index = self.find_virtual_cable()

        # --- МУЛЬТИЯЗЫЧНАЯ БАЗА ---
        self.models = {}
        self.current_lang = "ru"
        self.speaker = "eugene" 

        # Настройки, актуальные только для русской модели v5_5_ru
        self.put_accent = True
        self.put_yo = True
        self.put_stress_homo = True
        self.put_yo_homo = True
        
        # Очередь и запуск внутреннего потока
        self.speech_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._speech_worker, daemon=True)
        self.worker_thread.start()
        
        # Загружаем базовый русский язык при старте
        self.set_language("ru", "eugene")

    def find_virtual_cable(self):
        import sounddevice as sd
        devices = sd.query_devices()
        preferred_apis = ['MME', 'Windows DirectSound', 'WASAPI']
        
        for api in preferred_apis:
            for i, dev in enumerate(devices):
                if 'CABLE Input' in dev['name'] and dev['max_output_channels'] > 0:
                    host_api_name = sd.query_hostapis(dev['hostapi'])['name']
                    if api in host_api_name:
                        return i
                        
        for i, dev in enumerate(devices):
            if 'CABLE Input' in dev['name'] and dev['max_output_channels'] > 0:
                host_api_name = sd.query_hostapis(dev['hostapi'])['name']
                if 'WDM-KS' not in host_api_name:
                    return i
        return None

    def set_language(self, lang="ru", speaker=None):
        if speaker:
            self.speaker = speaker
            
        if lang not in self.models:
            print(f"⏳ Загрузка модели Silero TTS ({lang})...")
            try:
                model_version = 'v5_5_ru' if lang == "ru" else 'v3_en'
                
                model, _ = torch.hub.load(
                    repo_or_dir='snakers4/silero-models',
                    model='silero_tts',
                    language=lang,
                    speaker=model_version,
                )
                
                # ЖЕЛЕЗНАЯ ПРИВЯЗКА К ВИДЕОКАРТЕ
                model.to(self.device)
                
                self.models[lang] = model
                print(f"✅ Модель {lang} успешно загружена на {self.device}.")
            except Exception as e:
                print(f"❌ Ошибка загрузки модели {lang}: {e}")
                return
                
        self.current_lang = lang

    def set_gui(self, gui):
        self.gui = gui

    def speak(self, text):
        if not text:
            return
            
        print(f"🔊 Assistant ({self.current_lang}): {text}")
        
        if self.gui:
            self.gui.signals.jarvis_response.emit(text)
            self.gui.signals.log_message.emit(f"Ник: {text}")

        # ВАЖНО: Кладем в очередь текст ВМЕСТЕ с текущим языком и голосом!
        self.speech_queue.put((text, self.current_lang, self.speaker))

    def _speech_worker(self):
        while True:
            try:
                task = self.speech_queue.get()
                if task is None:
                    self.speech_queue.task_done()
                    continue

                text, task_lang, task_speaker = task
                task_model = self.models.get(task_lang)
                
                if not task_model:
                    print(f"⚠️ Модель для языка {task_lang} не найдена.")
                    self.speech_queue.task_done()
                    continue

                if hasattr(self, 'server') and self.server:
                    self.server.send_to_avatar(text)

                # Базовые аргументы для любой модели
                kwargs = {
                    "speaker": task_speaker,
                    "sample_rate": self.sample_rate,
                }

                # Добавляем спец-аргументы ТОЛЬКО если это русская модель
                if task_lang == "ru":
                    kwargs.update({
                        "put_accent": self.put_accent,
                        "put_yo": self.put_yo,
                        "put_stress_homo": self.put_stress_homo,
                        "put_yo_homo": self.put_yo_homo
                    })

                start_gen = time.time()

                # Генерация звука
                if "<speak>" in text:
                    audio = task_model.apply_tts(ssml_text=text, **kwargs)
                else:
                    audio = task_model.apply_tts(text=text, **kwargs)
                
                print(f"⏱️ Генерация заняла: {time.time() - start_gen:.3f} сек.")

                start_play = time.time()
                audio_np = audio.cpu().numpy()
                sd.play(audio_np, self.sample_rate, device=self.output_device_index) 
                sd.wait()
                print(f"⏱️ Воспроизведение заняло: {time.time() - start_play:.3f} сек.")

                self.speech_queue.task_done()
                
            except Exception as e:
                print(f"❌ Ошибка генерации речи: {e}")
                self.speech_queue.task_done()

if __name__ == "__main__":
    tts = TextToSpeech()
    # Тест русского
    tts.speak("Привет! Я Ник. Системы работают в штатном режиме.")
    
    # Тест мгновенного переключения на английский
    tts.set_language("en", "en_0")
    tts.speak("Translator systems are fully operational. Voice en zero is active.")
    
    tts.speech_queue.join()