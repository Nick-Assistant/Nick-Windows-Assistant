import time
import os
from playwright.sync_api import sync_playwright

class BrowserManager:
    def __init__(self):
        self.playwright = sync_playwright().start()
        self.browser = None
        self.page = None
        self.is_browser_visible = False

        self.profiles = {
            "default": "3",    # Обычный Ник
            "nika": "2",      # ---
            "translator": "4"  # НОВЫЙ: Переводчик
        }
        
        # Задаем профиль по умолчанию
        self.current_profile_name = "default"
        self.current_profile_id = self.profiles[self.current_profile_name]
        self.setup_profile_path()

        self.edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        self.start_browser(headless=True)

    def setup_profile_path(self):
        """Формирует путь к папке профиля и создает её при необходимости"""
        appdata_path = os.getenv('APPDATA')
        self.user_data_dir = os.path.join(appdata_path, "GeminiBar", f"browser_profile_{self.current_profile_id}")
        
        if not os.path.exists(self.user_data_dir):
            os.makedirs(self.user_data_dir)

    def switch_profile(self, target="cycle"):
        """Закрывает браузер, меняет профиль и перезапускает"""
        if self.browser:
            self.browser.close()
            
        # Логика переключения
        if target in self.profiles:
            # Если запросили конкретный режим
            self.current_profile_name = target
        else:
            # Если просто сказали "смени режим", переключаем между дефолтом и --- (или по кругу)
            if self.current_profile_name == "default":
                self.current_profile_name = "nika"
            else:
                self.current_profile_name = "default"
                
        self.current_profile_id = self.profiles[self.current_profile_name]
        self.setup_profile_path()
        
        # Запускаем браузер заново
        self.start_browser(headless=not self.is_browser_visible)
        
        # Возвращаем ИМЯ профиля, чтобы main.py понял, какой голос ставить
        return self.current_profile_name

    def start_browser(self, headless=True):
        if self.browser:
            self.browser.close()

        self.browser = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            executable_path=self.edge_path,
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
        self.page.goto("https://gemini.google.com/u/1/app?hl=ru&pli=1", wait_until="domcontentloaded")

    def _wait_for_new_response(self, old_message_count, old_message_text, timeout=60):
        start = time.time()
        last_text = None
        stable_since = None

        while time.time() - start < timeout:
            try:
                message_count = self.page.locator('model-response').count()
            except Exception:
                message_count = 0

            if message_count > 0:
                last_message = self.page.locator('model-response').nth(message_count - 1)
                try:
                    # Читаем текст ответа напрямую из элемента страницы
                    current_text = last_message.locator('message-content').text_content(timeout=1000) or ''
                    current_text = current_text.strip()
                except Exception:
                    current_text = ''

                is_new = message_count > old_message_count or current_text != old_message_text
                
                # Ждем, пока текст перестанет печататься (стабилизируется на 0.4 секунды)
                if is_new and current_text:
                    if current_text == last_text:
                        if stable_since is None:
                            stable_since = time.time()
                        elif time.time() - stable_since >= 2.0:
                            return current_text
                    else:
                        last_text = current_text
                        stable_since = None
                else:
                    stable_since = None

            time.sleep(0.1)

        return ''

    def send_query(self, query):
        try:
            input_selector = 'div[contenteditable="true"]'
            self.page.locator(input_selector).first.focus(timeout=5000)

            old_message_count = self.page.locator('model-response').count()
            old_message_text = ''
            if old_message_count:
                try:
                    old_message_text = self.page.locator('model-response').nth(old_message_count - 1).locator('message-content').text_content(timeout=1000) or ''
                    old_message_text = old_message_text.strip()
                except Exception:
                    old_message_text = ''

            self.page.keyboard.type(query)
            self.page.keyboard.press("Enter")

            response_text = self._wait_for_new_response(old_message_count, old_message_text, timeout=60)
            if response_text:
                return response_text

            message_content_selector = 'model-response:last-of-type message-content'
            try:
                response_text = self.page.locator(message_content_selector).last.text_content(timeout=5000)
                if response_text:
                    response_text = response_text.strip()
                    if response_text and response_text != old_message_text:
                        return response_text
            except Exception:
                pass

            return "Запрос отправлен в браузер. Не удалось найти ответный блок."
        except Exception as e:
            return f"Сбой браузера: {str(e)}"

    def new_chat(self):
        pass

    def toggle_browser(self):
        if self.browser:
            self.browser.close()

        if self.is_browser_visible:
            self.start_browser(headless=True)
            self.is_browser_visible = False
        else:
            self.start_browser(headless=False)
            self.is_browser_visible = True

    def close(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()