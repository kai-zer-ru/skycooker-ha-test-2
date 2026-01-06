"""Multicooker connection for SkyCoocker."""
import asyncio
import logging
import traceback
from time import monotonic

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache
from bleak.exc import BleakOutOfConnectionSlotsError

from homeassistant.components import bluetooth

from .const import *

_LOGGER = logging.getLogger(__name__)


class MulticookerConnection:
    """Main class for multicooker connection."""
    
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
        
        # Get UUIDs for the specific model
        if model and model in SUPPORTED_MODELS:
            model_config = SUPPORTED_MODELS[model]
            self.UUID_SERVICE = model_config["uuid_service"]
            self.UUID_TX = model_config["uuid_tx"]
            self.UUID_RX = model_config["uuid_rx"]
        else:
            # Default to RMC-M40S
            self.UUID_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
            self.UUID_TX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
            self.UUID_RX = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

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
        await self._client.write_gatt_char(self.UUID_TX, data)
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
        _LOGGER.debug(f"📥 Получено: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        """Callback for receiving data."""
        self._last_data = data

    async def _connect(self):
        """Connect to the multicooker with better error handling."""
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected: return
        
        # Ensure any previous connection is properly cleaned up
        await self._cleanup_previous_connections()
        
        try:
            self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            _LOGGER.debug("🔌 Подключение к мультиварке...")
            
            # Use fewer connection attempts to avoid slot exhaustion
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=2,  # Reduced from 3 to 2
                disconnected_callback=self._handle_disconnect
            )
            _LOGGER.debug("✅ Подключено к мультиварке")
            
            # Start notifications with timeout
            try:
                await asyncio.wait_for(
                    self._client.start_notify(self.UUID_RX, self._rx_callback),
                    timeout=5.0
                )
                _LOGGER.debug("🔔 Подписано на уведомления")
            except asyncio.TimeoutError:
                _LOGGER.error("⏱️  Таймаут при подписке на уведомления")
                await self._disconnect()
                raise
                
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка подключения: {e}")
            await self._disconnect()
            raise

    async def _cleanup_previous_connections(self):
        """Clean up any previous connections to free up slots."""
        try:
            if self._client:
                if self._client.is_connected:
                    _LOGGER.debug("🧹 Очистка предыдущего соединения...")
                    await self._client.disconnect()
                self._client = None
            self._device = None
        except Exception as e:
            _LOGGER.warning(f"⚠️  Ошибка очистки предыдущего соединения: {e}")

    def _handle_disconnect(self, client):
        """Handle unexpected disconnections."""
        _LOGGER.warning("⚠️  Неожиданное отключение от мультиварки")
        self._last_connect_ok = False
        self._auth_ok = False

    async def auth(self):
        """Authenticate with the multicooker."""
        try:
            auth_data = await self.command(COMMAND_AUTH, list(self._key))
            if auth_data and auth_data[0] == 0x01:
                _LOGGER.info("🔐 Аутентификация успешна")
                return True
            else:
                _LOGGER.error("🚫 Аутентификация не удалась")
                return False
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка аутентификации: {e}")
            return False

    async def _disconnect(self):
        """Disconnect from the multicooker."""
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.debug("🔌 Отключено")
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
        """Connect if needed with better error handling."""
        if self._client and not self._client.is_connected:
            _LOGGER.debug("🔌 Подключение потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except BleakOutOfConnectionSlotsError as ex:
                _LOGGER.error("🚫 Bluetooth адаптер исчерпал лимит соединений. Попробуйте:")
                _LOGGER.error("   1. Перезагрузите Bluetooth адаптер")
                _LOGGER.error("   2. Уменьшите количество активных Bluetooth устройств")
                _LOGGER.error("   3. Используйте дополнительный Bluetooth прокси")
                _LOGGER.error("   4. Проверьте, что мультиварка находится в режиме сопряжения")
                await self.disconnect()
                self._last_connect_ok = False
                raise
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
            data = await self.command(COMMAND_GET_STATUS)
            if len(data) >= 11:
                mode = data[0]
                temperature = data[2]
                hours = data[3]
                minutes = data[4]
                remaining_hours = data[5]
                remaining_minutes = data[6]
                auto_warm = data[7]
                status = data[8]
                
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
                    'status': status
                }
            return None
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка получения статуса: {e}")
            return None

    async def set_mode(self, mode_id):
        """Set the cooking mode."""
        try:
            await self.command(COMMAND_SET_MODE, [mode_id])
            _LOGGER.info(f"✅ Режим установлен: {mode_id}")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка установки режима: {e}")
            return False

    async def start(self):
        """Start the cooking program."""
        try:
            await self.command(COMMAND_START)
            _LOGGER.info("✅ Программа запущена")
            return True
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка запуска программы: {e}")
            return False

    async def stop(self):
        """Stop the cooking program."""
        try:
            await self.command(COMMAND_STOP)
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
                await self._connect_if_need()
                
                # Get current status
                self._status = await self.get_status()
                
                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            self.add_stat(False)
            if tries > 1:
                _LOGGER.debug(f"🚫 {type(ex).__name__}: {str(ex)}, повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1)
            else:
                _LOGGER.warning(f"🚫 Не удалось обновить статус, {type(ex).__name__}: {str(ex)}")
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
        return self._last_connect_ok and self._last_auth_ok

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

    def stop_connection(self):
        """Stop the connection."""
        if self._disposed: return
        self._disconnect()
        self._disposed = True
        _LOGGER.info("🛑 Соединение остановлено")


class AuthError(Exception):
    """Authentication error."""
    pass


class DisposedError(Exception):
    """Connection disposed error."""
    pass