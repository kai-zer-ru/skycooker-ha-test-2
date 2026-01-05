"""
Модуль логгирования для интеграции SkyCooker
"""

import logging
import sys
from datetime import datetime

# Настройка уровня логгирования
LOG_LEVEL = logging.DEBUG

class SkyCookerLogger:
    """Логгер для SkyCooker"""
    
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

    def debug(self, message):
        """Вывод отладочного сообщения"""
        self.logger.debug(message)
    
    def info(self, message):
        """Вывод информационного сообщения"""
        self.logger.debug(message)
    
    def warning(self, message):
        """Вывод предупреждения"""
        self.logger.warning(message)
    
    def error(self, message):
        """Вывод ошибки"""
        self.logger.error(message)
    
    def critical(self, message):
        """Вывод критической ошибки"""
        self.logger.critical(message)
    
    def success(self, message):
        """Вывод сообщения об успехе"""
        self.logger.debug(message)
    
    def connect(self, message):
        """Вывод сообщения о подключении"""
        self.logger.debug(message)
    
    def disconnect(self, message):
        """Вывод сообщения об отключении"""
        self.logger.debug(message)
    
    def auth(self, message):
        """Вывод сообщения об аутентификации"""
        self.logger.debug(message)
    
    def bluetooth(self, message):
        """Вывод сообщения о Bluetooth"""
        self.logger.debug(message)
    
    def status(self, message):
        """Вывод сообщения о статусе"""
        self.logger.debug(message)
    
    def command(self, message):
        """Вывод сообщения о команде"""
        self.logger.debug(message)
    
    def response(self, message):
        """Вывод сообщения о ответе"""
        self.logger.debug(message)
    
    def sensor(self, message):
        """Вывод сообщения о сенсоре"""
        self.logger.debug(message)
    
    def device(self, message):
        """Вывод сообщения об устройстве"""
        self.logger.debug(message)

# Глобальный логгер
logger = SkyCookerLogger()