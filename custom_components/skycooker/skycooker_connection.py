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
            await self._client.write_gatt_char(SkyCookerConnection.UUID_TX, data)
            _LOGGER.debug(f"📋 Отправленный пакет: {data.hex().upper()}")
        except Exception as e:
            _LOGGER.error(f"🚫 Ошибка отправки команды: {e}")
            raise IOError(f"Ошибка отправки команды: {e}")
        timeout_time = monotonic() + SkyCookerConnection.BLE_RECV_TIMEOUT
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
        if self._client and self._client.is_connected: return
        self._device = bluetooth.async_ble_device_from_address(self.hass, self._mac)
        _LOGGER.debug("Connecting to the SkyCooker...")
        self._client = await establish_connection(
            BleakClientWithServiceCache,
            self._device,
            self._device.name or "Unknown Device",
            max_attempts=3
        )
        _LOGGER.debug("Connected to the SkyCooker")
        await self._client.start_notify(SkyCookerConnection.UUID_RX, self._rx_callback)
        _LOGGER.debug("Subscribed to RX")

    auth = lambda self: super().auth(self._key)

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
            _LOGGER.debug("Connection lost")
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
                _LOGGER.error(f"Auth failed. You need to enable pairing mode on the SkyCooker.")
                raise AuthError("Auth failed")
            _LOGGER.debug("Auth ok")
            self._sw_version = await self.get_version()
            await self.sync_time()

    async def _disconnect_if_need(self):
        if not self.persistent:
            await self.disconnect()

    async def update(self, tries=MAX_TRIES, force_stats=False, extra_action=None, commit=False):
        try:
            async with self._update_lock:
                if self._disposed: return None
                _LOGGER.debug(f"Updating")
                if not self.available: force_stats = True
                await self._connect_if_need()

                if extra_action: await extra_action

                self._status = await self.get_status()
                boil_time = self._status.boil_time
                if self._target_boil_time is not None and self._target_boil_time != boil_time:
                    try:
                        _LOGGER.debug(f"Need to update boil time from {boil_time} to {self._target_boil_time}")
                        boil_time = self._target_boil_time
                        if self._target_state is None:
                            self._target_state = self._status.mode if self._status.is_on else None, self._status.target_temp
                            self._last_set_target = monotonic()
                        if self._status.is_on:
                            await self.turn_off()
                            await asyncio.sleep(0.2)
                        await self.set_main_mode(self._status.mode, self._status.target_temp, boil_time)
                        _LOGGER.info(f"Boil time is successfully set to {boil_time}")
                    except Exception as ex:
                        _LOGGER.error(f"Can't update boil time ({type(ex).__name__}): {str(ex)}")
                    self._status = await self.get_status()
                self._target_boil_time = None

                if commit: await self.commit()

                if self._target_state is not None:
                    target_mode, target_temp = self._target_state
                    if target_mode is None and self._status.is_on:
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to turn off the SkyCooker...")
                        await self.turn_off()
                        _LOGGER.info("The SkyCooker was turned off")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode is not None and not self._status.is_on:
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to set mode and turn on the SkyCooker...")
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("New mode was set")
                        await self.turn_on()
                        _LOGGER.info("The SkyCooker was turned on")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    elif target_mode is not None and (
                            target_mode != self._status.mode or
                            target_temp != self._status.target_temp):
                        _LOGGER.info(f"State: {self._status} -> {self._target_state}")
                        _LOGGER.info("Need to switch mode of the SkyCooker and restart it")
                        await self.turn_off()
                        _LOGGER.info("The SkyCooker was turned off")
                        await asyncio.sleep(0.2)
                        await self.set_main_mode(target_mode, target_temp, boil_time)
                        _LOGGER.info("New mode was set")
                        await self.turn_on()
                        _LOGGER.info("The SkyCooker was turned on")
                        await asyncio.sleep(0.2)
                        self._status = await self.get_status()
                    else:
                        _LOGGER.debug(f"There is no reason to update state")
                    self._target_state = None

                await self._disconnect_if_need()
                self.add_stat(True)
                return True

        except Exception as ex:
            await self.disconnect()
            if self._target_state is not None and self._last_set_target + SkyCookerConnection.TARGET_TTL < monotonic():
                _LOGGER.warning(f"Can't set mode to {self._target_state} for {SkyCookerConnection.TARGET_TTL} seconds, stop trying")
                self._target_state = None
            if type(ex) == AuthError: return None
            self.add_stat(False)
            if tries > 1 and extra_action is None:
                _LOGGER.debug(f"{type(ex).__name__}: {str(ex)}, retry #{SkyCookerConnection.MAX_TRIES - tries + 1}")
                await asyncio.sleep(SkyCookerConnection.TRIES_INTERVAL)
                return await self.update(tries=tries-1, force_stats=force_stats, extra_action=extra_action, commit=commit)
            else:
                _LOGGER.warning(f"Can't update status, {type(ex).__name__}: {str(ex)}")
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
