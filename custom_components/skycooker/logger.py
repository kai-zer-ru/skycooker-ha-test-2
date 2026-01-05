"""
Модуль логгирования для интеграции SkyCooker с иконками
"""

import logging
import sys
from datetime import datetime

# Настройка уровня логгирования
LOG_LEVEL = logging.DEBUG

# Иконки для разных типов сообщений
ICONS = {
    "DEBUG": "🐛",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🚨",
    "SUCCESS": "✅",
    "CONNECT": "🔌",
    "DISCONNECT": "🔌",
    "AUTH": "🔑",
    "BLUETOOTH": "📡",
    "STATUS": "📊",
    "COMMAND": "📤",
    "RESPONSE": "📥",
    "SENSOR": "🌡️",
    "DEVICE": "📱"
}

class SkyCookerLogger:
    """Логгер с иконками для SkyCooker"""
    
    def __init__(self):
        # self.logger = logging.getLogger("custom_components.skycooker")
        self.logger = logging.getLogger(__name__)
        
        self.logger.setLevel(LOG_LEVEL)
        
        # Если логгер уже настроен, не настраиваем заново
        if self.logger.hasHandlers():
            return
            
        # Создаем форматтер с иконками
        formatter = logging.Formatter(
            fmt='%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Создаем обработчик для консоли
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(formatter)
        
        # Добавляем обработчик к логгеру
        self.logger.addHandler(console_handler)
    
    def _add_icon(self, level, message):
        """Добавляет иконку к сообщению в зависимости от уровня"""
        icon = ICONS.get(level, "ℹ️")
        if level == "CONNECT":
            icon = "🔌"
        elif level == "DISCONNECT":
            icon = "🔌"
        elif level == "AUTH":
            icon = "🔑"
        elif level == "BLUETOOTH":
            icon = "📡"
        elif level == "STATUS":
            icon = "📊"
        elif level == "COMMAND":
            icon = "📤"
        elif level == "RESPONSE":
            icon = "📥"
        elif level == "SENSOR":
            icon = "🌡️"
        elif level == "DEVICE":
            icon = "📱"
        elif level == "SUCCESS":
            icon = "✅"
            
        return f"{icon} {message}"
    
    def debug(self, message):
        """Вывод отладочного сообщения"""
        message_with_icon = self._add_icon("DEBUG", message)
        self.logger.debug(message_with_icon)
    
    def info(self, message):
        """Вывод информационного сообщения"""
        message_with_icon = self._add_icon("INFO", message)
        self.logger.info(message_with_icon)
    
    def warning(self, message):
        """Вывод предупреждения"""
        message_with_icon = self._add_icon("WARNING", message)
        self.logger.warning(message_with_icon)
    
    def error(self, message):
        """Вывод ошибки"""
        message_with_icon = self._add_icon("ERROR", message)
        self.logger.error(message_with_icon)
    
    def critical(self, message):
        """Вывод критической ошибки"""
        message_with_icon = self._add_icon("CRITICAL", message)
        self.logger.critical(message_with_icon)
    
    def success(self, message):
        """Вывод сообщения об успехе"""
        message_with_icon = self._add_icon("SUCCESS", message)
        self.logger.info(message_with_icon)
    
    def connect(self, message):
        """Вывод сообщения о подключении"""
        message_with_icon = self._add_icon("CONNECT", message)
        self.logger.info(message_with_icon)
    
    def disconnect(self, message):
        """Вывод сообщения об отключении"""
        message_with_icon = self._add_icon("DISCONNECT", message)
        self.logger.info(message_with_icon)
    
    def auth(self, message):
        """Вывод сообщения об аутентификации"""
        message_with_icon = self._add_icon("AUTH", message)
        self.logger.info(message_with_icon)
    
    def bluetooth(self, message):
        """Вывод сообщения о Bluetooth"""
        message_with_icon = self._add_icon("BLUETOOTH", message)
        self.logger.info(message_with_icon)
    
    def status(self, message):
        """Вывод сообщения о статусе"""
        message_with_icon = self._add_icon("STATUS", message)
        self.logger.info(message_with_icon)
    
    def command(self, message):
        """Вывод сообщения о команде"""
        message_with_icon = self._add_icon("COMMAND", message)
        self.logger.info(message_with_icon)
    
    def response(self, message):
        """Вывод сообщения о ответе"""
        message_with_icon = self._add_icon("RESPONSE", message)
        self.logger.info(message_with_icon)
    
    def sensor(self, message):
        """Вывод сообщения о сенсоре"""
        message_with_icon = self._add_icon("SENSOR", message)
        self.logger.info(message_with_icon)
    
    def device(self, message):
        """Вывод сообщения об устройстве"""
        message_with_icon = self._add_icon("DEVICE", message)
        self.logger.info(message_with_icon)

# Глобальный логгер
logger = SkyCookerLogger()