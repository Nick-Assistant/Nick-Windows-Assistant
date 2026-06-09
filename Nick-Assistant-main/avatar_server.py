import socket

class AvatarServer:
    def __init__(self, ip="127.0.0.1", port=39540):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"🔗 Канал связи (UDP) с Unity открыт на {ip}:{port}")

    def send_command(self, command: str):
        """Отправляет текстовую команду в Unity"""
        self.sock.sendto(command.encode('utf-8'), (self.ip, self.port))

    def send_to_avatar(self, message: str):
        if not message:
            return

        text = message.lower()
        
        # Сбрасываем эмоции
        self.send_command("EMOTION:Neutral")

        # Триггеры эмоций (отправляем простые строки)
        if any(word in text for word in ["привет", "рад", "отлично", "успешно", "готово"]):
            self.send_command("EMOTION:Joy")
        elif any(word in text for word in ["ошибка", "проблема", "сбой", "увы"]):
            self.send_command("EMOTION:Sorrow")
            
        # Можно добавить триггер анимации разговора
        self.send_command("ANIM:Talk")