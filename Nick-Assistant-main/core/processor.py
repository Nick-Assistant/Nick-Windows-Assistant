import os
import importlib
import json
import sys

def get_base_path():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class CommandProcessor:
    def __init__(self, config_path="config.json", tts=None, gemini_worker=None):
        self.base_path = get_base_path()
        self.config = {}
        self.load_config(config_path)
        self.modules = []
        self.tts = tts
        self.gemini_worker = gemini_worker # Ссылка на поток браузера
        self.load_modules()

    def load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def load_modules(self):
        # Загрузка модулей остается такой же, как в твоем оригинальном коде
        modules_path = os.path.join(self.base_path, "modules")
        if not os.path.exists(modules_path):
            return
        sys.path.insert(0, self.base_path)
        module_priority = ['debug_tools', 'profile_switcher', 'system_control', 'app_control', 'media_control']
        loaded_names = set()
        
        for module_name in module_priority:
            self._load_module(module_name)
            loaded_names.add(module_name)
            
        try:
            for filename in os.listdir(modules_path):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = filename[:-3]
                    if module_name not in loaded_names:
                        self._load_module(module_name)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def _load_module(self, module_name):
        try:
            module = importlib.import_module(f"modules.{module_name}")
            if hasattr(module, "handle_command") and hasattr(module, "KEYWORDS"):
                self.modules.append(module)
        except Exception:
            pass

    def process(self, text):
        text = text.lower().strip()
        if not text:
            return False
            
        # ПЕРЕМЕННАЯ ЗДЕСЬ, ОНА ВСЕГДА БУДЕТ ДОСТУПНА
        whitelist_modules = ["modules.simulation_scene", "modules.debug_tools", "modules.profile_switcher"]
        
        print(f"\n🎤 Услышано: '{text}'")
        clean_text = text.replace("ник ", "", 1).strip() if text.startswith("ник ") else text
        current_mode = getattr(self.gemini_worker, 'current_profile_name', 'default')
        
        for module in self.modules:
            if module.__name__ in whitelist_modules:
                if any(kw in clean_text for kw in getattr(module, 'KEYWORDS', [])):
                    if module.handle_command(clean_text, tts=self.tts, config=self.config, gemini_worker=self.gemini_worker) is True:
                        return True

        # 2. РЕЖИМ ПЕРЕВОДЧИКА
        if current_mode == "translator":
            print("🧠 Маршрут: Прямой перевод (Gemini)")
            if self.gemini_worker:
                self.gemini_worker.execute_query(clean_text)
            return True

        # 3. ОБЫЧНЫЙ РЕЖИМ
        gemini_triggers = ["расскажи", "объясни", "что такое", "кто такой", "почему", "зачем", "как ", "скажи", "когда", "найди", "перескажи"]
        if any(clean_text.startswith(t) for t in gemini_triggers):
            print("🧠 Маршрут: Облачная генерация (Gemini)")
            if self.tts: self.tts.speak("Секунду, ищу информацию...")
            if self.gemini_worker:
                self.gemini_worker.execute_query(clean_text)
            return True
            
        print("🧠 Маршрут: Локальные модули управления")
        for module in self.modules:
            if module.__name__ in whitelist_modules: continue
            if any(kw in clean_text for kw in getattr(module, 'KEYWORDS', [])):
                module.handle_command(clean_text, tts=self.tts, config=self.config, gemini_worker=self.gemini_worker)
                return True