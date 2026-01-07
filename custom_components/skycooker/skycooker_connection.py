#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic

from bleak_retry_connector import establish_connection, BleakClientWithServiceCache

from homeassistant.components import bluetooth

from .const import *
from .skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


class SkyCookerConnection(SkyCooker):

    def __init__(self, mac, key, persistent=True, adapter=None, hass=None, model=None):
        super().__init__(model)
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
        self._target_boil_time = None
        self._status = None
        self._stats = None
        self._disposed = False
        self._last_data = None

    async def command(self, command, params=None):
        if params is None:
            params = []
        if self._disposed:
            raise DisposedError()
        if not self._client or not self._client.is_connected:
            raise IOError("🔌 Не подключено")
        self._iter = (self._iter + 1) % 256
        _LOGGER.debug(f"📤 Отправка команды {command:02x}, данные: [{' '.join([f'{c:02x}' for c in params])}]")
        data = bytes([0x55, self._iter, command] + list(params) + [0xAA])
        self._last_data = None
        try:
            await self._client.write_gatt_char(UUID_TX, data)
            _LOGGER.debug(f"📋 Отправленный пакет: {data.hex().upper()}")
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка отправки команды: {e}")
            raise IOError(f"Ошибка отправки команды: {e}")
        timeout_time = monotonic() + BLE_RECV_TIMEOUT
        while True:
            await asyncio.sleep(0.05)
            if self._last_data:
                r = self._last_data
                _LOGGER.debug(f"📥 Получен сырой ответ: {r.hex().upper()}")
                if len(r) < 4 or r[0] != 0x55 or r[-1] != 0xAA:
                    _LOGGER.error(f"❌ Некорректный формат ответа: {r.hex().upper()}")
                    raise IOError("Некорректный формат ответа")
                if r[1] == self._iter:
                    _LOGGER.debug(f"✅ Правильный идентификатор запроса {self._iter} в ответе")
                    break
                else:
                    _LOGGER.warning(f"⚠️  Неправильный идентификатор запроса в ответе: ожидалось {self._iter}, получено {r[1]}")
                    _LOGGER.warning(f"💡 Это может быть ответ на предыдущий запрос или от другого устройства")
                    self._last_data = None
            if monotonic() >= timeout_time:
                _LOGGER.error(f"⏱️  Таймаут приема ответа на команду {command:02x}")
                raise IOError("Таймаут приема")
        if r[2] != command:
            _LOGGER.error(f"❌ Некорректная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            raise IOError("Некорректная команда ответа")
        clean = bytes(r[3:-1])
        _LOGGER.debug(f"📥 Очищенные данные ответа: {' '.join([f'{c:02x}' for c in clean])}")
        return clean

    def _rx_callback(self, sender, data):
        self._last_data = data

    async def _connect(self):
        if self._disposed:
            raise DisposedError()
        if self._client and self._client.is_connected:
            _LOGGER.debug("✅ Уже подключено к мультиварке")
            return
        try:
            # Очистка предыдущих подключений
            await self._cleanup_previous_connections()
            
            self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
            if not self._device:
                _LOGGER.error("❌ Устройство %s не найдено", self._mac)
                raise IOError(f"Устройство {self._mac} не найдено")
            _LOGGER.info("🔌 Подключение к мультиварке %s (%s)...", self._mac, self._device.name)
            self._client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self._device.name or "Unknown Device",
                max_attempts=5
            )
            _LOGGER.info("✅ Успешно подключено к мультиварке %s", self._mac)
            await self._client.start_notify(UUID_RX, self._rx_callback)
            _LOGGER.info("📡 Подписка на уведомления от мультиварки")
        except Exception as e:
            _LOGGER.error("❌ Ошибка подключения к мультиварке: %s", e)
            _LOGGER.error("💡 Проверьте, что устройство находится в режиме сопряжения и рядом с адаптером")
            if "out of connection slots" in str(e).lower():
                _LOGGER.error("💡 Bluetooth адаптер исчерпал лимит соединений. Попробуйте:")
                _LOGGER.error("   1. Перезагрузите Bluetooth адаптер")
                _LOGGER.error("   2. Уменьшите количество активных Bluetooth устройств")
                _LOGGER.error("   3. Используйте дополнительный Bluetooth прокси")
                _LOGGER.error("   4. Проверьте, что мультиварка находится в режиме сопряжения")
            raise

    async def auth(self):
        """Authenticate with the multicooker using correct key format."""
        try:
            _LOGGER.info("🔑 Начало аутентификации...")
            _LOGGER.debug(f"🔑 Ключ аутентификации: {self._key}")
            
            # Convert key to bytes if it's a string
            if isinstance(self._key, str):
                key_bytes = list(bytes.fromhex(self._key))
            elif isinstance(self._key, list):
                key_bytes = self._key
            else:
                key_bytes = list(self._key)
            
            _LOGGER.debug(f"🔑 Ключ в формате байтов: {key_bytes}")
            
            auth_data = await self.command(COMMAND_AUTH, key_bytes)
            if auth_data and auth_data[0] == 0x01:
                _LOGGER.info("🔐 Аутентификация успешна")
                return True
            else:
                _LOGGER.error(f"🚫 Аутентификация не удалась. Код ответа: {auth_data[0] if auth_data else 'None'}")
                return False
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка аутентификации: {e}")
            return False

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

    async def _disconnect(self):
        try:
            if self._client:
                was_connected = self._client.is_connected
                await self._client.disconnect()
                if was_connected: _LOGGER.debug("Disconnected")
        finally:
            self._auth_ok = False
            self._device = None
            self._client = None

    async def disconnect(self):
        try:
            await self._disconnect()
        except:
            pass

    async def _connect_if_need(self):
        if self._client and not self._client.is_connected:
            _LOGGER.warning("⚠️  Подключение к мультиварке потеряно")
            await self.disconnect()
        if not self._client or not self._client.is_connected:
            try:
                await self._connect()
                self._last_connect_ok = True
            except Exception as ex:
                await self.disconnect()
                self._last_connect_ok = False
                _LOGGER.error(f"🚫 Ошибка подключения к мультиварке: {ex}")
                raise ex
        if not self._auth_ok:
            self._last_auth_ok = self._auth_ok = await self.auth()
            if not self._auth_ok:
                _LOGGER.error("🚫 Ошибка аутентификации. Необходимо включить режим сопряжения на мультиварке.")
                raise AuthError("Ошибка аутентификации")
            _LOGGER.info("✅ Аутентификация успешна")
            self._sw_version = await self.get_version()
            await self.sync_time()

    async def _disconnect_if_need(self):
        if not self.persistent:
            await self.disconnect()

    async def update(self, tries=MAX_TRIES, force_stats=False, extra_action=None, commit=False):
        try:
            async with self._update_lock:
                if self._disposed: return None
                _LOGGER.info("🔄 Обновление состояния мультиварки")
                if not self.available: force_stats = True
                await self._connect_if_need()

                if extra_action: await extra_action

                self._status = await self.get_status()
                boil_time = self._status.boil_time
                if self._target_boil_time is not None and self._target_boil_time != boil_time:
                    try:
                        _LOGGER.info(f"🔥 Необходимо обновить время кипения с {boil_time} на {self._target_boil_time}")
                        boil_time = self._target_boil_time
                        if self._target_state is None:
                            self._target_state = self._status.mode if self._status.is_on else None, self._status.target_temp
                            self._last_set_target = monotonic()
                        if self._status.is_on:
                            await self.turn_off()
                            await asyncio.sleep(0.2)
                        await self.set_main_mode(self._status.mode, self._status.target_temp, boil_time)
                        _LOGGER.info(f"✅ Время кипения успешно установлено на {boil_time}")
                    except Exception as ex:
                        _LOGGER.error(f"❌ Не удалось обновить время кипения ({type(ex).__name__}): {str(ex)}")
                    self._status = await self.get_status()
                self._target_boil_time = None

                if commit: await self.commit()

                if self._target_state is not None:
                    target_mode, target_temp = self._target_state
                    if target_mode is None and self._status.is_on:
                        _LOGGER.info(f"🔄 Состояние: {self._status} -> {self._target_state}")
                        _LOGGER.info("🔌 Необходимо выключить мультиварку...")
                        await self.turn_off()
                        _LOGGER.info("✅ Мультиварка выключена")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode is not None and not self._status.is_on:
                        _LOGGER.info(f"🔄 Состояние: {self._status} -> {self._target_state}")
                        _LOGGER.info("🔌 Необходимо установить режим и включить мультиварку...")
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("✅ Режим установлен")
                        await self.turn_on()
                        _LOGGER.info("✅ Мультиварка включена")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode is not None and (
                            target_mode != self._status.mode or
                            target_temp != self._status.target_temp):
                        _LOGGER.info(f"🔄 Состояние: {self._status} -> {self._target_state}")
                        _LOGGER.info("🔌 Необходимо переключить режим мультиварки и перезапустить её")
                        await self.turn_off()
                        _LOGGER.info("✅ Мультиварка выключена")
                        await asyncio.sleep(0.2)
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("✅ Режим установлен")
                        await self.turn_on()
                        _LOGGER.info("✅ Мультиварка включена")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    else:
                        _LOGGER.debug(f"📊 Нет необходимости обновлять состояние")
                    self._target_state = None

                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            if self._target_state is not None and self._last_set_target + TARGET_TTL < monotonic():
                _LOGGER.warning(f"⚠️  Не удалось установить режим {self._target_state} в течение {TARGET_TTL} секунд, прекращаю попытки")
                self._target_state = None
            if type(ex) == AuthError: return None
            self.add_stat(False)
            if tries > 1 and extra_action is None:
                _LOGGER.debug(f"🚫 {type(ex).__name__}: {str(ex)}, повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1, force_stats=force_stats, extra_action=extra_action, commit=commit)
            else:
                _LOGGER.warning(f"⚠️  Не удалось обновить состояние, {type(ex).__name__}: {str(ex)}")
                _LOGGER.debug(traceback.format_exc())
            return False

    def add_stat(self, value):
        self._successes.append(value)
        if len(self._successes) > 100: self._successes = self._successes[-100:]

    @property
    def success_rate(self):
        if len(self._successes) == 0: return 0
        return int(100 * len([s for s in self._successes if s]) / len(self._successes))

    async def _set_target_state(self, target_mode, target_temp = 0):
        self._target_state = target_mode, target_temp
        self._last_set_target = monotonic()
        await self.update()

    async def commit(self):
        """Commit changes to the device."""
        _LOGGER.debug("Committing changes")
        await self.update(commit=True)

    async def cancel_target(self):
        self._target_state = None

    def stop(self):
        if self._disposed: return
        self._disconnect()
        self._disposed = True
        _LOGGER.info("Stopped.")

    @property
    def available(self):
        return self._last_connect_ok and self._last_auth_ok

    @property
    def last_connect_ok(self):
        return self._last_connect_ok

    @property
    def last_auth_ok(self):
        return self._last_auth_ok

    @property
    def current_temp(self):
        if self._status:
            return self._status.current_temp
        return None

    @property
    def current_mode(self):
        if self._status and self._status.is_on:
            return self._status.mode
        return None

    @property
    def target_temp(self):
        if self._target_state:
            target_mode, target_temp = self._target_state
            if target_mode in [0, 1]:
                return target_temp
            if target_mode == 2:
                return 100
            if target_mode is None:
                return 25
        if self._status:
            if self._status.is_on:
                if self._status.mode in [0, 1]:
                    return self._status.target_temp
                if self._status.mode == 2:
                    return 100
            else:
                return 25
        return None

    @property
    def target_mode(self):
        if self._target_state:
            target_mode, target_temp = self._target_state
            return target_mode
        else:
            if self._status and self._status.is_on:
                return self._status.mode
        return None

    @property
    def connected(self):
        return True if self._client and self._client.is_connected else False

    @property
    def auth_ok(self):
        return self._auth_ok

    @property
    def sw_version(self):
        return self._sw_version

    @property
    def sound_enabled(self):
        if not self._status: return None
        return self._status.sound_enabled

    @property
    def color_interval(self):
        if not self._status: return None
        return self._status.color_interval

    @property
    def boil_time(self):
        if not self._status: return None
        return self._status.boil_time

    async def set_boil_time(self, value):
        value = int(value)
        _LOGGER.info(f"Setting boil time to {value}")
        self._target_boil_time = value
        await self.update(commit=True)

    async def set_target_temp(self, target_temp, operation_mode = None):
        if target_temp == self.target_temp: return
        _LOGGER.info(f"Setting target temperature to {target_temp}")
        target_mode = self.target_mode
        
        # Get model type from model_code
        model_type = self.model_code.split('_')[1] if self.model_code else None
        if model_type is None:
            _LOGGER.error("Unknown model type")
            return
        
        model_type = int(model_type)
        
        # Find the appropriate mode based on temperature
        if target_temp < 35:
            target_mode = None
        else:
            # Find the mode that matches the target temperature
            for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                if mode_data[0] == target_temp:
                    target_mode = mode_idx
                    break
            
            # If no exact match found, use the closest mode
            if target_mode is None:
                closest_diff = float('inf')
                for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                    diff = abs(mode_data[0] - target_temp)
                    if diff < closest_diff:
                        closest_diff = diff
                        target_mode = mode_idx
        
        if target_mode != self.current_mode:
            _LOGGER.info(f"Mode autoswitched to {target_mode}")
        await self._set_target_state(target_mode, target_temp)

    async def set_target_mode(self, operation_mode):
        if operation_mode == self.target_mode: return
        _LOGGER.info(f"Setting target mode to {operation_mode}")
        target_mode = operation_mode
        target_temp = self.target_temp
        if target_mode in [2]:
            target_temp = 0
        elif target_mode in [3, 4]:
            target_temp = 85
        elif target_temp is None:
            target_temp = 90
        else:
            if target_temp > 90:
                target_temp = 90
            elif target_temp < 35:
                target_temp = 35
        if target_temp != self.target_temp:
            _LOGGER.info(f"Target temperature autoswitched to {target_temp}")
        await self._set_target_state(target_mode, target_temp)


class AuthError(Exception):
    pass

class DisposedError(Exception):
    pass
