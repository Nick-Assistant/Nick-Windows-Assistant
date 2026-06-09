import json
import os
import sys
import pyaudio
from vosk import Model, KaldiRecognizer

def get_base_path():
    """Возвращает базовый путь для ресурсов"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SpeechToText:
    def __init__(self, config_path="config.json"):
        self.base_path = get_base_path()
        self.config = {}
        self.load_config(config_path)
        
        # Путь к модели относительно базового пути
        model_name = self.config.get("stt", {}).get("model_path", "model")
        self.model_path = os.path.join(self.base_path, model_name)
        
        self.model = None
        self.recognizer = None
        self.pa = pyaudio.PyAudio()
        self.stream = None
        
        self.initialize_model()

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def initialize_model(self):
        if not os.path.exists(self.model_path):
            print(f"Error: Vosk model not found at '{self.model_path}'")
            return

        try:
            print(f"Loading Vosk model from {self.model_path}...")
            self.model = Model(self.model_path)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("Vosk model loaded successfully.")
        except Exception as e:
            print(f"Failed to load model: {e}")

    def get_device_index(self):
        """Ищем Bluetooth, затем USB-микрофон. Если нет, возвращаем None (устройство по умолчанию)"""
        bluetooth_index = None
        usb_index = None
        VoiceMeeter_index = None
        
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            # Проверяем, что это устройство ввода (микрофон)
            if info.get('maxInputChannels') > 0:
                name = info.get('name', '').upper()
                
                if ('VoiceMeeter' in name or 'VoiceMeeter Output' in name) and VoiceMeeter_index is None:
                    VoiceMeeter_index = i
                # Ищем Bluetooth (в Windows часто помечается как Hands-Free)
                elif ('BLUETOOTH' in name or 'HANDS-FREE' in name or 'HANDSFREE' in name) and bluetooth_index is None:
                    bluetooth_index = i
                # Ищем USB
                elif 'USB' in name and usb_index is None:
                    usb_index = i
        
        # Строгая иерархия приоритетов:
        if VoiceMeeter_index is not None:
            return VoiceMeeter_index, "VoiceMeeter-микрофон"
        elif bluetooth_index is not None:
            return bluetooth_index, "Bluetooth-микрофон"
        elif usb_index is not None:
            return usb_index, "USB-микрофон"
        
        return None, "Встроенный микрофон (по умолчанию)"

    def start_stream(self):
        if self.stream is None:
            # Получаем индекс и название для логов
            mic_index, device_type = self.get_device_index()
            
            try:
                self.stream = self.pa.open(format=pyaudio.paInt16, 
                                         channels=1, 
                                         rate=16000, 
                                         input=True, 
                                         input_device_index=mic_index,
                                         frames_per_buffer=8000)
                self.stream.start_stream()
                print(f"🎤 Аудиопоток запущен ({device_type})")
                
            except Exception as e:
                print(f"⚠️ Ошибка запуска ({device_type}): {e}")
                print("🔄 Пробую переключиться на микрофон по умолчанию...")
                
                # РЕЗЕРВНЫЙ ЗАПУСК: Если Bluetooth/USB сбоит, принудительно берем дефолтный микрофон
                try:
                    self.stream = self.pa.open(format=pyaudio.paInt16, 
                                             channels=1, 
                                             rate=16000, 
                                             input=True, 
                                             input_device_index=None, # Устройство по умолчанию
                                             frames_per_buffer=8000)
                    self.stream.start_stream()
                    print("🎤 Аудиопоток запущен (Встроенный микрофон)")
                except Exception as fallback_error:
                    print(f"❌ Критическая ошибка аудио: {fallback_error}")
                    self.stream = None

    def stop_stream(self):
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass # Игнорируем ошибки при закрытии уже сломанного потока
            self.stream = None

    def listen(self):
        if not self.model:
            return ""

        if self.stream is None:
            self.start_stream()

        # ЗАЩИТА ОТ БЕСКОНЕЧНОГО СПАМА В КОНСОЛЬ
        if self.stream is None:
            import time
            time.sleep(2) # Делаем паузу, если микрофон вообще не удалось запустить
            return ""

        try:
            # Читаем данные
            data = self.stream.read(4000, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    return text
                    
        except OSError:
            print("⚠️ Устройство записи отключено. Выполняю переподключение...")
            self.stop_stream()
        except Exception as e:
            print(f"Неизвестная ошибка при прослушивании: {e}")
            self.stop_stream() 
            import time
            time.sleep(1) # Защита от спама при других ошибках
        
        return ""

if __name__ == "__main__":
    stt = SpeechToText()
    if stt.model:
        print("Listening... (Press Ctrl+C to stop)")
        try:
            while True:
                text = stt.listen()
                if text:
                    print(f"Recognized: {text}")
        except KeyboardInterrupt:
            print("\nStopped.")