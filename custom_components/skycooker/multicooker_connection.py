#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic

from bleak.exc import BleakError
from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import *

_LOGGER = logging.getLogger(__name__)

# Стандартные UUID для R4S устройств
SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NOTIFY_UUID = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"
WRITE_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"


def get_model_constant(model_name, constant_type, key):
    """Get model-specific constant."""
    if model_name not in SUPPORTED_MODELS:
        raise ValueError(f"Model {model_name} not supported")
    
    model_config = SUPPORTED_MODELS[model_name]
    
    if constant_type == "command":
        return model_config["commands"].get(key)
    elif constant_type == "mode":
        # Return the mode name for display
        return model_config["modes"].get(key)
    elif constant_type == "status":
        # Return the status text for display
        return model_config["status_codes"].get(key)
    
    raise ValueError(f"Unknown constant type: {constant_type}")


class MulticookerConnection:
    """Main class for multicooker connection based on working library."""

    def __init__(self, mac, key, persistent=True, adapter=None, hass=None, model=None):
        """Initialize the multicooker connection."""
        self._device = None
        self._client = None
        self._mac = mac
        self._key = key
        self.persistent = persistent
        self.adapter = adapter
        self.hass = hass
        self._auth_ok = False
        self._sw_version = None
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_get_stats = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes = []
        self._target_state = None
        self._status = None
        self._stats = None
        self._disposed = False
        self._last_data = None
        self.model = model

    async def command(self, command, params=[]):
        """Send a command to the multicooker."""
        if self._disposed:
            raise DisposedError()
        if not self._client or not self._client.is_connected:
            raise IOError("🔌 Не подключено")
        self._iter = (self._iter + 1) % 256
        _LOGGER.debug(f"📤 Отправка команды {command:02x}, данные: [{' '.join([f'{c:02x}' for c in params])}]")
        data = bytes([0x55, self._iter, command] + list(params) + [0xAA])
        self._last_data = None
        await self._client.write_gatt_char(WRITE_UUID, data)
        timeout_time = monotonic() + BLE_RECV_TIMEOUT
        while True:
            await asyncio.sleep(0.05)
            if self._last_data:
                r = self._last_data
                if r[0] != 0x55 or r[-1] != 0xAA:
                    raise IOError("❌ Некорректный формат ответа")
                if r[1] == self._iter:
                    break
                else:
                    self._last_data = None
            if monotonic() >= timeout_time: raise IOError("⏱️  Таймаут приема")
        if r[2] != command:
            raise IOError("❌ Некорректная команда ответа")
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        """Callback for receiving data."""
        self._last_data = data

    async def _connect(self):
        """Connect to the multicooker."""
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к %s", self._mac)
            return
        self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
        if not self._device:
            _LOGGER.error("❌ Устройство %s не найдено", self._mac)
            raise BleakError(f"Device {self._mac} not found")
        _LOGGER.info("🔌 Подключение к устройству: %s (%s)", self._device.name, self._mac)
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            self._device,
            self._device.name or "Unknown Device",
            max_attempts=3
        )
        _LOGGER.info("✅ Успешное подключение к %s", self._mac)
        await self._client.start_notify(NOTIFY_UUID, self._rx_callback)
        _LOGGER.info("📡 Уведомления включены для %s", self._mac)

    auth = lambda self: super().auth(self._key)

    async def _disconnect(self):
        """Disconnect from the multicooker."""
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected:
                    _LOGGER.debug("🔌 Отключено")
        finally:
            self._auth_ok = False
            self._device = None
            self._client = None

    async def disconnect(self):
        """Public disconnect method."""
        try:
            await self._disconnect()
        except:
            pass

    async def _connect_if_need(self):
        """Connect if needed."""
        if self._client and not self._client.is_connected:
            _LOGGER.debug("🔌 Подключение потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except Exception as ex:
                await self.disconnect()
                self._last_connect_ok = False
                raise ex
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth()
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Нужно включить режим сопряжения на мультиварке.")
                raise AuthError("Ошибка аутентификации")
            _LOGGER.debug("✅ Аутентификация успешна")

    async def _disconnect_if_need(self):
        """Disconnect if needed."""
        if not self.persistent:
            await self.disconnect()

    async def get_status(self):
        """Get the current status of the multicooker."""
        try:
            # Get the GET_STATUS command code for this specific model
            get_status_command = get_model_constant(self.model, "command", "GET_STATUS") or COMMAND_GET_STATUS
            
            # Add small delay before sending status command
            # Some devices need time after authentication
            await asyncio.sleep(0.5)
            
            data = await self.command(get_status_command)
            if len(data) >= 11:
                mode = data[0]
                temperature = data[2]
                hours = data[3]
                minutes = data[4]
                remaining_hours = data[5]
                remaining_minutes = data[6]
                auto_warm = data[7]
                status = data[8]
                
                # Get status text for logging
                status_text = get_model_constant(self.model, "status", status) or STATUS_CODES.get(status, f"Неизвестно ({status})")
                _LOGGER.debug(f"📊 Статус устройства: {status_text}")
                
                # When device is off, set default values
                if status == STATUS_OFF or status_text == "Выключена":
                    temperature = 0
                    hours = 0
                    minutes = 0
                    remaining_hours = 0
                    remaining_minutes = 0
                
                return {
                    'mode': mode,
                    'temperature': temperature,
                    'time_hours': hours,
                    'time_minutes': minutes,
                    'time_total': hours * 60 + minutes,
                    'remaining_hours': remaining_hours,
                    'remaining_minutes': remaining_minutes,
                    'remaining_time_total': remaining_hours * 60 + remaining_minutes,
                    'auto_warm_enable': bool(auto_warm),
                    'status': status,
                    'status_text': status_text
                }
            return None
        except Exception as e:
            error_str = str(e)
            if "att error" in error_str.lower() or "0x0e" in error_str.lower():
                _LOGGER.error(f"🚫 Ошибка ATT протокола при получении статуса: {e}")
                _LOGGER.error("💡 Устройство может не быть готово к командам. Попробуем позже...")
                return None
            else:
                _LOGGER.error(f"🚫 Ошибка получения статуса: {e}")
                return None

    async def set_mode(self, mode_id):
        """Set the cooking mode."""
        try:
            # Get the SET_MODE command code for this specific model
            set_mode_command = get_model_constant(self.model, "command", "SET_MODE") or COMMAND_SET_MODE
            await self.command(set_mode_command, [mode_id])
            
            # Get the mode name for logging
            mode_name = get_model_constant(self.model, "mode", mode_id) or MODES.get(mode_id, f"Неизвестно ({mode_id})")
            _LOGGER.info(f"✅ Режим установлен: {mode_id} ({mode_name})")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка установки режима: {e}")
            return False

    async def start(self):
        """Start the cooking program."""
        try:
            # Get the START command code for this specific model
            start_command = get_model_constant(self.model, "command", "START") or COMMAND_START
            await self.command(start_command)
            _LOGGER.info("✅ Программа запущена")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка запуска программы: {e}")
            return False

    async def stop(self):
        """Stop the cooking program."""
        try:
            # Get the STOP command code for this specific model
            stop_command = get_model_constant(self.model, "command", "STOP") or COMMAND_STOP
            await self.command(stop_command)
            _LOGGER.info("✅ Программа остановлена")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка остановки программы: {e}")
            return False

    async def update(self, tries=MAX_TRIES):
        """Update the multicooker status."""
        try:
            async with self._update_lock:
                if self._disposed: return
                _LOGGER.debug("🔄 Обновление статуса")
                  
                # Проверяем доступность перед попыткой обновления
                if not self.available:
                    _LOGGER.debug("📡 Устройство недоступно, пытаемся подключиться...")
                  
                try:
                    # Add timeout for connection attempt
                    await asyncio.wait_for(self._connect_if_need(), timeout=30.0)
                except asyncio.TimeoutError:
                    _LOGGER.error("⏱️  Таймаут подключения, устройство не отвечает")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                except Exception as e:
                    _LOGGER.error(f"🚫 Ошибка подключения: {e}")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                  
                # Проверяем, что подключение и авторизация прошли успешно
                if not self.available:
                    _LOGGER.error("🚫 Не удалось подключиться или авторизоваться")
                    await self.disconnect()
                    self.add_stat(False)
                    return False
                  
                _LOGGER.debug("✅ Подключение и авторизация успешны, запрашиваем статус...")
                  
                # Get current status with timeout
                try:
                    self._status = await asyncio.wait_for(self.get_status(), timeout=10.0)
                except asyncio.TimeoutError:
                    _LOGGER.error("⏱️  Таймаут получения статуса")
                    await self._disconnect_if_need()
                    self.add_stat(False)
                    return False
                  
                if self._status:
                    _LOGGER.debug(f"📊 Статус получен: режим={self._status.get('mode')}, температура={self._status.get('temperature')}°C")
                    # Update last successful update time
                    import time
                    self._last_successful_update = time.monotonic()
                else:
                    _LOGGER.warning("⚠️  Не удалось получить статус")
                    
                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            self.add_stat(False)
            error_type = type(ex).__name__
            error_message = str(ex)
            
            # More specific error handling
            if "att error" in error_message.lower() or "0x0e" in error_message.lower():
                _LOGGER.error(f"🚫 Ошибка ATT протокола при обновлении статуса: {error_message}")
                _LOGGER.error("💡 Устройство может не быть готово к командам. Попробуем позже...")
            elif "timeout" in error_message.lower():
                _LOGGER.error(f"⏱️  Таймаут при обновлении статуса: {error_message}")
                _LOGGER.error("💡 Устройство может быть занято или не отвечает. Попробуем позже...")
            elif "connection" in error_message.lower():
                _LOGGER.error(f"🔌 Ошибка подключения при обновлении статуса: {error_message}")
                _LOGGER.error("💡 Проверьте подключение к устройству и попробуйте снова...")
            else:
                _LOGGER.error(f"🚫 Неизвестная ошибка при обновлении статуса: {error_type}: {error_message}")
            
            if tries > 1:
                _LOGGER.debug(f"🔄 Повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1)
            else:
                _LOGGER.warning(f"🚫 Не удалось обновить статус после {MAX_TRIES} попыток")
                _LOGGER.debug(traceback.format_exc())
            return False

    def add_stat(self, value):
        """Add a success/failure statistic."""
        self._successes.append(value)
        if len(self._successes) > 100: self._successes = self._successes[-100:]

    @property
    def success_rate(self):
        """Get the success rate of commands."""
        if len(self._successes) == 0: return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    @property
    def available(self):
        """Check if the multicooker is available."""
        # If we have exceeded the maximum number of reconnection attempts, return False
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            return False
        
        # Consider available if we had at least one successful connection
        # This prevents entities from becoming unavailable immediately after setup
        if self._last_connect_ok and self._last_auth_ok:
            return True
        # If we never connected successfully, check if we're currently trying to connect
        if self._client and self._client.is_connected:
            return True
        # If we have a recent successful update (within the last 2 scan intervals), consider available
        if self._last_successful_update:
            import time
            current_time = time.monotonic()
            # Use 2 * DEFAULT_SCAN_INTERVAL * 60 seconds as timeout (convert minutes to seconds)
            timeout = 2 * DEFAULT_SCAN_INTERVAL * 60
            if current_time - self._last_successful_update < timeout:
                return True
        return False

    @property
    def current_status(self):
        """Get the current status."""
        return self._status

    @property
    def current_mode(self):
        """Get the current mode."""
        if self._status:
            return self._status.get('mode')
        return None

    @property
    def current_temperature(self):
        """Get the current temperature."""
        if self._status:
            return self._status.get('temperature')
        return None

    @property
    def remaining_time(self):
        """Get the remaining time."""
        if self._status:
            return self._status.get('remaining_time_total')
        return None

    @property
    def total_time(self):
        """Get the total cooking time."""
        if self._status:
            return self._status.get('time_total')
        return None

    @property
    def auto_warm_enabled(self):
        """Check if auto warm is enabled."""
        if self._status:
            return self._status.get('auto_warm_enable')
        return None

    @property
    def status_code(self):
        """Get the status code."""
        if self._status:
            return self._status.get('status')
        return None

    async def stop_connection(self):
        """Stop the connection."""
        if self._disposed: return
        await self._disconnect()
        self._disposed = True
        _LOGGER.info("🛑 Соединение остановлено")


class AuthError(Exception):
    """Authentication error."""
    pass


class DisposedError(Exception):
    """Connection disposed error."""
    pass