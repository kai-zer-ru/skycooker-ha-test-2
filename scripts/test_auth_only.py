#!/usr/bin/env python3
"""
Тестирование только аутентификации без отправки команд управления.
Этот скрипт поможет понять, проходит ли аутентификация и получаем ли мы ответы от устройства.
"""

import asyncio
import logging
import sys
from bleak import BleakClient
from bleak.exc import BleakError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# UUID для Nordic UART Service (NUS)
NUS_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # RX Characteristic
WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"   # TX Characteristic

class AuthTester:
    def __init__(self, mac_address, password):
        self.mac_address = mac_address
        self.password = password
        self._client = None
        self._notifications_received = []
        
    async def connect(self):
        """Подключение к устройству."""
        logger.info("🔌 Подключение к устройству: %s", self.mac_address)
        self._client = BleakClient(self.mac_address)
        await self._client.connect()
        logger.info("✅ Успешное подключение к %s", self.mac_address)
        
        # Включаем уведомления
        await self._client.start_notify(NOTIFY_UUID, self._notification_handler)
        logger.info("📡 Уведомления включены через характеристику %s", NOTIFY_UUID)
        
    async def disconnect(self):
        """Отключение от устройства."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info("🔌 Отключение от устройства: %s", self.mac_address)
            
    def _notification_handler(self, sender, data):
        """Обработчик уведомлений от устройства."""
        logger.info("📡 Получены данные от %s: %s", self.mac_address, data.hex())
        self._notifications_received.append(data)
        
    async def send_auth(self):
        """Отправка команды аутентификации."""
        logger.info("🔑 Отправка команды аутентификации")
        
        # Конвертируем пароль в список байтов
        if isinstance(self.password, str):
            # Если пароль передан как hex строка, конвертируем в список байтов
            key_bytes = [int(self.password[i:i+2], 16) for i in range(0, len(self.password), 2)]
        elif isinstance(self.password, list):
            # Если пароль уже список байтов, используем как есть
            key_bytes = self.password
        else:
            # В других случаях пытаемся конвертировать
            key_bytes = list(self.password)
        
        # Проверяем, что пароль имеет правильную длину (8 байт)
        if len(key_bytes) != 8:
            logger.warning("⚠️  Неправильная длина пароля: %s (ожидается 8 байт)", len(key_bytes))
        
        # Формируем команду аутентификации
        # Формат: 55 01 01 [пароль] AA
        packet = [0x55, 0x01, 0x01] + key_bytes + [0xAA]
        packet_bytes = bytes(packet)
        
        logger.info("📤 Отправка команды аутентификации: %s", packet_bytes.hex())
        await self._client.write_gatt_char(WRITE_UUID, packet_bytes)
        logger.info("✅ Команда аутентификации отправлена")
        
    async def wait_for_response(self, timeout=5):
        """Ожидание ответа от устройства."""
        logger.info("⏳ Ожидание ответа от устройства (%s секунд)...", timeout)
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            if self._notifications_received:
                logger.info("🎉 Получен ответ от устройства!")
                return True
            await asyncio.sleep(0.1)
            
        logger.warning("⏰ Таймаут ожидания ответа")
        return False
        
    async def test_authentication(self):
        """Тестирование аутентификации."""
        try:
            await self.connect()
            
            # Отправляем команду аутентификации
            await self.send_auth()
            
            # Ждём ответа от устройства
            response_received = await self.wait_for_response(10)
            
            if response_received:
                logger.info("🎉 Аутентификация прошла успешно и получен ответ!")
                return True
            else:
                logger.warning("⚠️  Аутентификация отправлена, но ответ не получен")
                return False
                
        except Exception as e:
            logger.error("❌ Ошибка при аутентификации: %s", e)
            logger.exception(e)
            return False
        finally:
            await self.disconnect()

async def main():
    """Основная функция."""
    logger.info("🚀 Запуск тестирования аутентификации мультиварки")
    
    # MAC-адрес устройства
    mac_address = "DA:D8:9F:9E:0B:4C"
    
    # Тестовые пароли
    test_passwords = [
        "5b5b12868d0e8d12",  # hex строка
        [91, 91, 18, 134, 141, 14, 141, 18],  # список байтов
    ]
    
    for i, password in enumerate(test_passwords, 1):
        logger.info("🧪 Тест %s: %s (тип: %s)", i, password, type(password))
        
        tester = AuthTester(mac_address, password)
        success = await tester.test_authentication()
        
        if success:
            logger.info("✅ Тест %s прошёл успешно!", i)
            break
        else:
            logger.error("❌ Тест %s не удался", i)
            
    logger.info("🏁 Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main())