"""
Реализация устройства мультиварки для интеграции SkyCooker.
"""

import asyncio
from bleak import BleakClient, BleakError
from bleak_retry_connector import establish_connection

from .logger import logger
from .const import get_device_constants, SERVICE_UUID, CHAR_RX_UUID, CHAR_TX_UUID

class SkyCookerDevice:
    """Основной класс устройства для мультиварки Redmond."""
    
    def __init__(self, device_type, device_address, device_name):
        """Инициализация устройства."""
        self.device_type = device_type
        self.device_address = device_address
        self.device_name = device_name
        self.client = None
        self.rx_char = None
        self.tx_char = None
        self.constants = get_device_constants(device_type)
        self.connected = False
        self.status_data = {}
        self.command_success_rate = 100.0
        self.total_commands = 0
        self.successful_commands = 0
    
    async def connect(self):
        """Подключение к мультиварке."""
        logger.bluetooth(f"📡 Подключение к {self.device_name} ({self.device_address})...")
        
        try:
            # Установка соединения с повторными попытками
            self.client = await establish_connection(
                BleakClientWithServiceCache,
                self.device_address,
                self.device_name or "Unknown Device",
                max_attempts=3
            )
            
            logger.connect(f"🔌 Подключено к {self.device_name}")
            self.connected = True
            
            # Настройка уведомлений
            await self.client.start_notify(CHAR_TX_UUID, self._rx_callback)
            logger.info("🔔 Подписан на уведомления")
            
            # Поиск сервисов
            await self._discover_services()
            
            # Аутентификация
            await self._authenticate()
            
            return True
            
        except BleakError as e:
            logger.error(f"❌ Не удалось подключиться к {self.device_name}: {e}")
            await self.disconnect()
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка подключения к {self.device_name}: {e}")
            await self.disconnect()
            return False
    
    async def _discover_services(self):
        """Поиск BLE сервисов и характеристик."""
        logger.device(f"📱 Поиск сервисов для {self.device_name}...")
        
        try:
            # Получение сервисов
            services = self.client.services
            
            # Проверяем, что сервисы доступны (service discovery выполнен)
            if not services:
                logger.error("❌ Сервисы не найдены, service discovery не выполнен")
                return False
            
            # Ищем Nordic UART Service
            target_service = None
            self.rx_char = None
            self.tx_char = None
            
            # Сначала ищем Nordic UART Service
            for service in services.services.values():
                if str(service.uuid) == SERVICE_UUID:
                    target_service = service
                    logger.device(f"📱 Найден Nordic UART Service: {service.uuid}")
                    
                    # Ищем характеристики
                    for char in service.characteristics:
                        logger.device(f"📱 Характеристика {char.uuid}: свойства={char.properties}")
                        
                        # Ищем RX характеристику (для записи данных в устройство)
                        if str(char.uuid) == CHAR_RX_UUID:
                            self.rx_char = char
                            logger.device(f"✅ Найдена RX характеристика: {char.uuid}")
                        
                        # Ищем TX характеристику (для чтения данных от устройства)
                        elif str(char.uuid) == CHAR_TX_UUID:
                            self.tx_char = char
                            logger.device(f"✅ Найдена TX характеристика: {char.uuid}")
                    
                    break
            
            # Если не нашли Nordic UART Service, пытаемся найти сервис автоматически
            if not target_service:
                logger.warning("⚠️ Nordic UART Service не найден, ищем сервис автоматически...")
                for service in services.services.values():
                    logger.device(f"📱 Проверка сервиса: {service.uuid}")
                    
                    # Собираем все характеристики сервиса
                    chars = list(service.characteristics)
                    logger.device(f"📊 Найдено характеристик: {len(chars)}")
                    
                    if len(chars) >= 2:
                        # Пытаемся определить RX и TX характеристики
                        for char in chars:
                            logger.device(f"📱 Характеристика {char.uuid}: свойства={char.properties}")
                            
                            # Ищем характеристику для записи (RX)
                            if 'write' in char.properties and self.rx_char is None:
                                self.rx_char = char
                                logger.device(f"✅ Найдена RX характеристика: {char.uuid}")
                            
                            # Ищем характеристику для чтения/уведомлений (TX)
                            elif ('read' in char.properties or 'notify' in char.properties) and self.tx_char is None:
                                self.tx_char = char
                                logger.device(f"✅ Найдена TX характеристика: {char.uuid}")
                        
                        # Если нашли обе характеристики, используем этот сервис
                        if self.rx_char and self.tx_char:
                            target_service = service
                            logger.device(f"✅ Выбран сервис: {service.uuid}")
                            break
            
            if target_service and self.rx_char and self.tx_char:
                logger.device("✅ Найдены необходимые сервис и характеристики")
                logger.device(f"📊 Service UUID: {target_service.uuid}")
                logger.device(f"📊 RX UUID: {self.rx_char.uuid}")
                logger.device(f"📊 TX UUID: {self.tx_char.uuid}")
                return True
            else:
                logger.error("❌ Не найдены необходимые сервис и характеристики")
                return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка поиска сервисов: {e}")
            return False
    
    async def _authenticate(self):
        """Аутентификация устройства."""
        logger.auth(f"🔑 Аутентификация с {self.device_name}...")
        
        try:
            # Создаем пакет аутентификации
            auth_packet = self._create_packet(self.constants["COMMAND_AUTH"])
            
            # Отправляем команду аутентификации
            await self.client.write_gatt_char(self.rx_char.uuid, auth_packet)
            logger.command(f"📤 Отправлена команда аутентификации: {auth_packet.hex()}")
            
            # Ждем ответ
            await asyncio.sleep(1.0)
            
            # Читаем ответ
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Получен ответ аутентификации: {response.hex()}")
            
            # Проверяем успешность аутентификации
            if response and len(response) >= 4 and response[0] == 0x55 and response[-1] == 0xAA:
                if response[2] == self.constants["COMMAND_AUTH"] and response[3] == 0x01:
                    logger.auth("🔑 Аутентификация успешна!")
                    return True
            
            logger.warning("⚠️ Аутентификация не удалась")
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка аутентификации: {e}")
            return False
    
    def _rx_callback(self, sender, data):
        """Обработчик уведомлений от устройства."""
        logger.response(f"📥 Получено уведомление: {data.hex()}")
        
        # Парсим входящие данные
        if data and len(data) >= 4 and data[0] == 0x55 and data[-1] == 0xAA:
            # Это валидный пакет R4S
            command = data[2]
            
            # Парсим данные статуса
            status_data = self._parse_status_response(data)
            if status_data:
                # Проверяем, изменилось ли состояние
                if (not self.status_data or
                    self.status_data.get('mode') != status_data.get('mode') or
                    self.status_data.get('status') != status_data.get('status') or
                    self.status_data.get('temperature') != status_data.get('temperature')):
                    
                    self.status_data = status_data
                    self._update_success_rate()
                    logger.status(f"📊 Изменение состояния: {status_data}")
        
    def _create_packet(self, command, data=None, iteration=0):
        """Создание пакета по протоколу R4S."""
        packet = bytearray()
        packet.append(0x55)  # Стартовый байт
        packet.append(iteration & 0xFF)  # Счетчик итераций
        packet.append(command & 0xFF)  # Команда
        
        if data:
            packet.extend(data)
        
        packet.append(0xAA)  # Конечный байт
        return bytes(packet)
    
    async def get_status(self):
        """Получение текущего статуса мультиварки."""
        logger.status(f"📊 Запрос статуса от {self.device_name}...")
        
        if not self.connected:
            logger.error("❌ Устройство не подключено")
            return None
        
        try:
            # Создаем пакет запроса статуса
            status_packet = self._create_packet(self.constants["COMMAND_GET_STATUS"])
            
            # Отправляем команду
            await self.client.write_gatt_char(self.rx_char.uuid, status_packet)
            logger.command(f"📤 Отправлен запрос статуса: {status_packet.hex()}")
            self.total_commands += 1
            
            # Ждем ответ через уведомления (callback)
            # Ответ придет в _rx_callback и обновит self.status_data
            await asyncio.sleep(1.0)
            
            # Возвращаем текущие данные статуса
            if self.status_data:
                self.successful_commands += 1
                self._update_success_rate()
                logger.status(f"📊 Обновлены сенсоры: {self.status_data}")
                return self.status_data
            
            logger.warning("⚠️ Не получен ответ статуса")
            self._update_success_rate()
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            self._update_success_rate()
            return None
    
    def _parse_status_response(self, response):
        """Парсинг ответа статуса от устройства."""
        if not response or len(response) < 15:
            logger.warning(f"⚠️ Некорректная длина ответа статуса: {len(response)}")
            return None
        
        # Проверка формата пакета
        if response[0] != 0x55 or response[-1] != 0xAA:
            logger.warning(f"⚠️ Некорректный формат пакета: {response.hex()}")
            return None
        
        # Извлечение данных
        mode = response[3]
        status = response[11]
        temperature = response[5]
        hours = response[6]
        minutes = response[7]
        remaining_hours = response[8]
        remaining_minutes = response[9]
        auto_warm = response[10]
        
        return {
            "mode": mode,
            "mode_name": self.constants["MODES"].get(mode, f"Unknown ({mode})"),
            "status": status,
            "status_text": self.constants["STATUS_CODES"].get(status, f"Unknown ({status})"),
            "temperature": temperature,
            "time_hours": hours,
            "time_minutes": minutes,
            "time_total": hours * 60 + minutes,
            "remaining_hours": remaining_hours,
            "remaining_minutes": remaining_minutes,
            "remaining_time_total": remaining_hours * 60 + remaining_minutes,
            "auto_warm_enable": bool(auto_warm)
        }
    
    async def set_mode(self, mode):
        """Установка режима готовки."""
        logger.command(f"🍲 Установка режима {mode} ({self.constants['MODES'].get(mode, 'Unknown')})")
        
        if not self.connected:
            logger.error("❌ Устройство не подключено")
            return False
        
        try:
            # Создаем пакет установки режима
            mode_packet = self._create_packet(self.constants["COMMAND_SET_MODE"], bytes([mode]))
            
            # Отправляем команду
            await self.client.write_gatt_char(self.rx_char.uuid, mode_packet)
            logger.command(f"📤 Отправлена команда установки режима: {mode_packet.hex()}")
            self.total_commands += 1
            
            # Ждем ответ
            await asyncio.sleep(1.0)
            
            # Читаем ответ
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Получен ответ установки режима: {response.hex()}")
            
            # Проверяем успешность
            if response and len(response) >= 4 and response[3] == 0x01:
                self.successful_commands += 1
                self._update_success_rate()
                
                # После успешной установки режима запрашиваем статус
                await self.get_status()
                return True
            
            logger.warning("⚠️ Установка режима может быть неудачной")
            self._update_success_rate()
            return False
        
        except Exception as e:
            logger.error(f"❌ Ошибка установки режима: {e}")
            self._update_success_rate()
            return False
    
    async def start(self):
        """Запуск программы готовки."""
        logger.command(f"🚀 Запуск программы готовки на {self.device_name}")
        
        if not self.connected:
            logger.error("❌ Устройство не подключено")
            return False
        
        try:
            # Создаем пакет запуска
            start_packet = self._create_packet(self.constants["COMMAND_START"])
            
            # Отправляем команду
            await self.client.write_gatt_char(self.rx_char.uuid, start_packet)
            logger.command(f"📤 Отправлена команда запуска: {start_packet.hex()}")
            self.total_commands += 1
            
            # Для команды запуска может не быть ответа или он может быть другим
            # Поэтому считаем успешным, если не было исключений
            self.successful_commands += 1
            self._update_success_rate()
            
            # После успешного запуска запрашиваем статус
            await self.get_status()
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска программы: {e}")
            self._update_success_rate()
            return False
    
    async def stop(self):
        """Остановка программы готовки."""
        logger.command(f"🛑 Остановка программы готовки на {self.device_name}")
        
        if not self.connected:
            logger.error("❌ Устройство не подключено")
            return False
        
        try:
            # Создаем пакет остановки
            stop_packet = self._create_packet(self.constants["COMMAND_STOP"])
            
            # Отправляем команду
            await self.client.write_gatt_char(self.rx_char.uuid, stop_packet)
            logger.command(f"📤 Отправлена команда остановки: {stop_packet.hex()}")
            self.total_commands += 1
            
            # Ждем ответ
            await asyncio.sleep(1.0)
            
            # Читаем ответ
            response = await self.client.read_gatt_char(self.tx_char.uuid)
            logger.response(f"📥 Получен ответ остановки: {response.hex()}")
            
            # Проверяем успешность
            if response and len(response) >= 4 and response[3] == 0x01:
                self.successful_commands += 1
                self._update_success_rate()
                
                # После успешной остановки запрашиваем статус
                await self.get_status()
                return True
            
            logger.warning("⚠️ Команда остановки может быть неудачной")
            self._update_success_rate()
            return False
        
        except Exception as e:
            logger.error(f"❌ Ошибка остановки программы: {e}")
            self._update_success_rate()
            return False
    
    def _update_success_rate(self):
        """Обновление процента успешных команд."""
        if self.total_commands > 0:
            self.command_success_rate = (self.successful_commands / self.total_commands) * 100.0
            logger.status(f"📊 Процент успешных команд: {self.command_success_rate:.1f}%")
    
    async def disconnect(self):
        """Отключение от мультиварки."""
        logger.disconnect(f"🔌 Отключение от {self.device_name}...")
        
        try:
            if self.client and self.connected:
                await self.client.disconnect()
                self.connected = False
                logger.disconnect(f"🔌 Отключено от {self.device_name}")
        except Exception as e:
            logger.error(f"❌ Ошибка отключения: {e}")
        finally:
            self.client = None
            self.rx_char = None
            self.tx_char = None