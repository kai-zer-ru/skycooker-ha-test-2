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
        self._sw_version = '0.0'
        self._iter = 0
        self._update_lock = asyncio.Lock()
        self._last_set_target = 0
        self._last_get_stats = 0
        self._last_connect_ok = False
        self._last_auth_ok = False
        self._successes = []
        self._target_state = None
        self._target_boil_time = None
        self._target_delayed_start_hours = None
        self._target_delayed_start_minutes = None
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
        # Check if the response command matches the expected command
        # For some commands like SELECT_MODE, the device may send asynchronous status updates
        # In such cases, we should check if the device actually processed the command correctly
        if r[2] != command:
            _LOGGER.warning(f"⚠️  Получена неожиданная команда ответа: ожидалось {command:02x}, получено {r[2]:02x}")
            _LOGGER.warning(f"💡 Это может быть асинхронный ответ от устройства")
            
            # For SELECT_MODE and SET_MAIN_MODE commands, if we get a status update (0x06),
            # it might mean the device processed the command and sent its current status
            if command in [COMMAND_SELECT_MODE, COMMAND_SET_MAIN_MODE] and r[2] == COMMAND_GET_STATUS:
                _LOGGER.info(f"📊 Устройство отправило обновление статуса после команды {command:02x}")
                _LOGGER.info(f"💡 Вероятно, команда была обработана успешно")
                # Return a success response for compatibility
                clean = bytes([0x01])  # Success code
                _LOGGER.debug(f"📥 Очищенные данные ответа: 01 (успех)")
                return clean
            else:
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
                max_attempts=5,
                retry_interval=1.0  # Добавляем задержку между попытками
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

    auth = lambda self: super().auth(self._key)

    async def select_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0, bit_flags=0):
        # Проверяем, поддерживается ли режим устройством
        # Режим 16 (ожидание) не может быть установлен напрямую, но может быть получен как текущий статус
        if mode != 16 and not self._is_mode_supported(mode):
            _LOGGER.error(f"❌ Попытка установить неподдерживаемый режим {mode}")
            raise ValueError(f"Режим {mode} не поддерживается устройством")
        
        # Вызываем метод базового класса для отправки команды
        _LOGGER.debug(f"📤 Отправка команды SELECT_MODE для режима {mode}")
        await super().select_mode(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat, bit_flags)
        
        # При выборе режима устанавливаем Number значения из MODE_DATA для текущего режима
        # Это нужно для того, чтобы при смене режима пользователь видел значения из MODE_DATA
        model_type = self.model_code
        if model_type and model_type in MODE_DATA and mode < len(MODE_DATA[model_type]):
            mode_data = MODE_DATA[model_type][mode]
            
            # Устанавливаем температуру из MODE_DATA
            target_temp_from_mode = mode_data[0]
            if target_temp_from_mode != 0:
                # Сбрасываем целевую температуру, чтобы Number entity показал значение из MODE_DATA
                if hasattr(self, '_target_temperature'):
                    delattr(self, '_target_temperature')
            
            # Устанавливаем время приготовления из MODE_DATA
            cook_hours = mode_data[1]
            cook_minutes = mode_data[2]
            if cook_hours != 0 or cook_minutes != 0:
                # Сбрасываем целевое время приготовления
                self._target_boil_time = None
                if hasattr(self, '_target_cooking_time'):
                    delattr(self, '_target_cooking_time')
            
            # Сбрасываем отложенный старт
            self._target_delayed_start_hours = None
            self._target_delayed_start_minutes = None

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
            _LOGGER.info(f"📋 Версия ПО: {self._sw_version}")
            # try:
            #     await self.sync_time()
            # except Exception as e:
            #     _LOGGER.warning(f"⚠️  Ошибка синхронизации времени: {e}")

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

                try:
                    self._status = await self.get_status()
                except Exception as e:
                    _LOGGER.warning(f"⚠️  Ошибка получения статуса: {e}")
                    self._status = None
                    raise
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
                        
                        # Проверяем, поддерживается ли целевой режим устройством
                        # Если устройство находится в режиме ожидания (16), используем целевой режим из _target_state
                        target_mode_to_check = self._target_state[0] if self._target_state else self._status.mode
                        if not self._is_mode_supported(target_mode_to_check):
                            _LOGGER.error(f"❌ Режим {target_mode_to_check} не поддерживается устройством")
                            self._target_boil_time = None
                            return False
                        
                        # Отправляем команду "Выбор режима" перед установкой режима
                        # Если устройство находится в режиме ожидания (16), используем целевой режим из _target_state
                        target_mode_for_update = self._target_state[0] if self._target_state else self._status.mode
                        _LOGGER.debug(f"📤 Отправка команды SELECT_MODE для режима {target_mode_for_update}")
                        await self.select_mode(target_mode_for_update, 0, self._status.target_temp, boil_time // 60, boil_time % 60)
                        _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE для режима {target_mode_for_update}")
                        await self.set_main_mode(target_mode_for_update, 0, self._status.target_temp, boil_time // 60, boil_time % 60)
                        _LOGGER.info(f"✅ Время кипения успешно установлено на {boil_time}")
                        # После успешной установки времени, получаем актуальный статус
                        self._status = await self.get_status()
                    except Exception as ex:
                        _LOGGER.error(f"❌ Не удалось обновить время кипения ({type(ex).__name__}): {str(ex)}")
                        _LOGGER.debug(f"💡 Сбрасываем _target_boil_time, чтобы избежать циклических попыток")
                        # В случае ошибки, сбрасываем _target_boil_time, чтобы избежать циклических попыток
                        self._target_boil_time = None
                        return False
                self._target_boil_time = None

                # Не вызываем commit() здесь, так как он вызовет повторный update()
                # и может сбросить состояние. Вместо этого продолжим обработку
                # целевого состояния ниже.

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
                        try:
                            # Проверяем, поддерживается ли режим устройством
                            if not self._is_mode_supported(target_mode):
                                _LOGGER.error(f"❌ Режим {target_mode} не поддерживается устройством")
                                self._target_state = None
                                return False
                            
                            # Отправляем команду "Выбор режима" перед установкой режима
                            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE для режима {target_mode}")
                            await self.select_mode(target_mode, 0, target_temp, boil_time // 60, boil_time % 60)
                            _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE для режима {target_mode}")
                            await self.set_main_mode(target_mode, 0, target_temp, boil_time // 60, boil_time % 60)
                            _LOGGER.info("✅ Режим установлен")
                            await self.turn_on()
                            _LOGGER.info("✅ Мультиварка включена")
                            await asyncio.sleep(0.2)
                            self._status = await self.get_status()
                        except Exception as ex:
                            _LOGGER.error(f"❌ Ошибка при установке режима {target_mode}: {str(ex)}")
                            _LOGGER.debug(f"💡 Сбрасываем _target_state, чтобы избежать циклических попыток")
                            self._target_state = None
                            return False
                    elif target_mode is not None and (
                            target_mode != self._status.mode or
                            target_temp != self._status.target_temp):
                        _LOGGER.info(f"🔄 Состояние: {self._status} -> {self._target_state}")
                        _LOGGER.info("🔌 Необходимо переключить режим мультиварки и перезапустить её")
                        try:
                            await self.turn_off()
                            _LOGGER.info("✅ Мультиварка выключена")
                            await asyncio.sleep(0.2)
                            
                            # Проверяем, поддерживается ли режим устройством
                            if not self._is_mode_supported(target_mode):
                                _LOGGER.error(f"❌ Режим {target_mode} не поддерживается устройством")
                                self._target_state = None
                                return False
                            
                            # Отправляем команду "Выбор режима" перед установкой режима
                            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE для режима {target_mode}")
                            await self.select_mode(target_mode, 0, target_temp, boil_time // 60, boil_time % 60)
                            _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE для режима {target_mode}")
                            await self.set_main_mode(target_mode, 0, target_temp, boil_time // 60, boil_time % 60)
                            _LOGGER.info("✅ Режим установлен")
                            await self.turn_on()
                            _LOGGER.info("✅ Мультиварка включена")
                            await asyncio.sleep(0.2)
                            self._status = await self.get_status()
                        except Exception as ex:
                            _LOGGER.error(f"❌ Ошибка при переключении режима {target_mode}: {str(ex)}")
                            _LOGGER.debug(f"💡 Сбрасываем _target_state, чтобы избежать циклических попыток")
                            self._target_state = None
                            return False
                    else:
                        _LOGGER.debug(f"📊 Нет необходимости обновлять состояние")
                    self._target_state = None

                await self._disconnect_if_need()
                self.add_stat(True)
                
                # Если это был вызов с commit=True, сбрасываем состояние
                # после успешного подтверждения
                if commit:
                    await self._reset_target_state_after_success()
                
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

    def _is_mode_supported(self, mode):
        """Проверяет, поддерживается ли режим устройством."""
        model_type = self.model_code
        if model_type and model_type in MODE_DATA:
            if mode >= len(MODE_DATA[model_type]):
                _LOGGER.warning(f"⚠️  Режим {mode} не поддерживается для модели {model_type}")
                return False
            # Режим 16 - это режим ожидания, его нельзя устанавливать напрямую
            # Но он может быть текущим состоянием устройства, поэтому разрешаем его как допустимое состояние
            if mode == 16:
                _LOGGER.debug(f"📋 Режим 16 (ожидание) - это допустимое состояние устройства, но его нельзя устанавливать напрямую")
                return True
        return True

    async def _reset_target_state_after_success(self):
        """Reset target state after successful confirmation."""
        _LOGGER.debug("Resetting target state after successful confirmation")
        self._target_state = None
        self._target_boil_time = None

    async def cancel_target(self):
        self._target_state = None

    async def stop(self):
        if self._disposed: return
        await self._disconnect()
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
    def minutes(self):
        if self._status:
            return self._status.minutes
        return None
    
    @property
    def hours(self):
        if self._status:
            return self._status.hours
        return None
    
    @property
    def dhours(self):
        if self._status:
            return self._status.dhours
        return None
    
    @property
    def dminutes(self):
        if self._status:
            return self._status.dminutes
        return None
    
    @property
    def auto_warm(self):
        if self._status:
            return self._status.auto_warm
        return None
    
    @property
    def subprog(self):
        if self._status:
            return self._status.subprog
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
    def target_state(self):
        """Return the target state."""
        return self._target_state

    @target_state.setter
    def target_state(self, value):
        """Set the target state."""
        self._target_state = value

    @property
    def target_boil_time(self):
        """Return the target boil time."""
        return self._target_boil_time

    @target_boil_time.setter
    def target_boil_time(self, value):
        """Set the target boil time."""
        self._target_boil_time = value

    @property
    def target_delayed_start_hours(self):
        """Return the target delayed start hours."""
        return getattr(self, '_target_delayed_start_hours', None)

    @target_delayed_start_hours.setter
    def target_delayed_start_hours(self, value):
        """Set the target delayed start hours."""
        self._target_delayed_start_hours = value

    @property
    def target_delayed_start_minutes(self):
        """Return the target delayed start minutes."""
        return getattr(self, '_target_delayed_start_minutes', None)

    @target_delayed_start_minutes.setter
    def target_delayed_start_minutes(self, value):
        """Set the target delayed start minutes."""
        self._target_delayed_start_minutes = value

    @property
    def target_temperature(self):
        """Return the target temperature."""
        return self._target_temperature if hasattr(self, '_target_temperature') else None

    @target_temperature.setter
    def target_temperature(self, value):
        """Set the target temperature."""
        self._target_temperature = value

    @property
    def target_cooking_time(self):
        """Return the target cooking time."""
        return self._target_cooking_time if hasattr(self, '_target_cooking_time') else None

    @target_cooking_time.setter
    def target_cooking_time(self, value):
        """Set the target cooking time."""
        self._target_cooking_time = value

    @property
    def status(self):
        return self._status

    @property
    def connected(self):
        return True if self._client and self._client.is_connected else False

    @property
    def auth_ok(self):
        return self._auth_ok

    @property
    def sw_version(self):
        return self._sw_version if self._sw_version else "0.0"

    @property
    def sound_enabled(self):
        if not self._status: return None
        return self._status.sound_enabled

    @property
    def boil_time(self):
        if not self._status: return None
        return self._status.boil_time

    @property
    def status_code(self):
        if not self._status: return None
        return self._status.mode if self._status.is_on else STATUS_OFF

    @property
    def target_temperature(self):
        if not self._status: return None
        return self._status.target_temp

    @property
    def remaining_time(self):
        if not self._status: return None
        # Return boil_time as remaining time
        return self._status.boil_time

    @property
    def total_time(self):
        if not self._status: return None
        # For total time, we need to calculate based on status
        # For now, return boil_time as a placeholder
        # In a real implementation, this should come from the program settings
        return self._status.boil_time

    @property
    def delayed_start_time(self):
        if not self._status: return None
        # For delayed start time, we need to calculate based on status
        # For now, return 0 as a placeholder
        # In a real implementation, this should come from wait_hours and wait_minutes
        return 0

    @property
    def auto_warm_time(self):
        if not self._status: return None
        # For auto warm time, we need to calculate based on status
        # For now, return boil_time if in auto warm mode, else 0
        return self._status.boil_time if self._status.mode == STATUS_AUTO_WARM else 0

    @property
    def auto_warm_enabled(self):
        if not self._status: return None
        return self._status.mode == STATUS_AUTO_WARM

    async def set_boil_time(self, value):
        value = int(value)
        _LOGGER.info(f"Setting boil time to {value}")
        self._target_boil_time = value
        await self.update(commit=True)

    async def set_temperature(self, value):
        """Set target temperature."""
        value = int(value)
        _LOGGER.info(f"Setting target temperature to {value}")
        if self._status and self._status.is_on:
            # If device is on, we need to send temperature command
            # For now, store it and it will be applied on next update
            self._target_state = self._status.mode, value
            await self.update(commit=True)
        else:
            # If device is off, just store the target temperature
            # It will be applied when device is turned on
            if self._target_state:
                target_mode, _ = self._target_state
                self._target_state = target_mode, value
            else:
                self._target_state = self._status.mode if self._status else None, value

    async def set_cooking_time(self, hours, minutes):
        """Set cooking time."""
        hours = int(hours)
        minutes = int(minutes)
        _LOGGER.info(f"Setting cooking time to {hours}:{minutes:02d}")
        # For now, convert to total minutes and store in boil_time
        # In a real implementation, this should send the proper command
        total_minutes = hours * 60 + minutes
        self._target_boil_time = total_minutes
        await self.update(commit=True)

    async def set_delayed_start(self, hours, minutes):
        """Set delayed start time."""
        hours = int(hours)
        minutes = int(minutes)
        _LOGGER.info(f"Setting delayed start time to {hours}:{minutes:02d}")
        # In a real implementation, this should send the proper command
        # For now, we'll just log it
        await self.update(commit=True)

    async def start(self):
        """Start cooking with current settings."""
        _LOGGER.info("Starting cooking with current settings")
        
        # Get the mode that the user has selected (from target_state), not the current device mode
        # If user has selected a mode, use that. Otherwise, use current device mode.
        if self._target_state and self._target_state[0] is not None:
            target_mode = self._target_state[0]
            _LOGGER.info(f"🎯 Используется целевой режим {target_mode} (выбран пользователем)")
        else:
            target_mode = self._status.mode if self._status else 0
            _LOGGER.info(f"🎯 Используется текущий режим устройства {target_mode}")
        
        model_type = self.model_code
        
        # Validate target_mode - if it's invalid (e.g., 16 for MODEL_3), use mode 0 (Multi-chef)
        if model_type and model_type in MODE_DATA and target_mode >= len(MODE_DATA[model_type]):
            _LOGGER.warning(f"⚠️  Некорректный режим {target_mode} для модели {model_type}, использую режим 0 (Multi-chef)")
            target_mode = 0
        
        # Проверяем, поддерживается ли режим устройством
        if not self._is_mode_supported(target_mode):
            _LOGGER.error(f"❌ Режим {target_mode} не поддерживается устройством, использую режим 0 (Multi-chef)")
            target_mode = 0
        
        # Проверяем, поддерживается ли режим устройством
        if not self._is_mode_supported(target_mode):
            _LOGGER.error(f"❌ Режим {target_mode} не поддерживается устройством, использую режим 0 (Multi-chef)")
            target_mode = 0
        
        # Если текущий режим устройства - 16 (ожидание), и пользователь не выбрал режим,
        # используем режим 0 (Multi-chef) вместо режима 16
        if target_mode == 16:
            _LOGGER.warning(f"⚠️  Режим 16 (ожидание) не может быть установлен напрямую, использую режим 0 (Multi-chef)")
            target_mode = 0
        
        # Get current values from the connection (which should be set by Number components)
        # These values may have been modified by the user
        target_temp = self._target_state[1] if self._target_state else None
        cook_hours = self._target_boil_time // 60 if self._target_boil_time else 0
        cook_minutes = self._target_boil_time % 60 if self._target_boil_time else 0
        
        # If user hasn't set custom temperature, use default from MODE_DATA
        if target_temp is None:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_temp = MODE_DATA[model_type][target_mode][0]
        
        # If user hasn't set custom cooking time, use default from MODE_DATA
        if cook_hours == 0 and cook_minutes == 0:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                cook_hours = MODE_DATA[model_type][target_mode][1]
                cook_minutes = MODE_DATA[model_type][target_mode][2]
        
        # Ensure all values are integers (not None)
        cook_hours = cook_hours or 0
        cook_minutes = cook_minutes or 0
        
        _LOGGER.info(f"Starting cooking: mode={target_mode}, temp={target_temp}, time={cook_hours}:{cook_minutes:02d}")
        
        # Check if device is in standby mode (mode 16) or if we need to wake it up
        is_in_standby = self._status and self._status.mode == 16
        
        try:
            # Connect if needed
            await self._connect_if_need()
            
            # If device is in standby mode, send SELECT_MODE first to wake it up
            if is_in_standby:
                _LOGGER.info("🔄 Устройство находится в режиме ожидания, отправляем команду SELECT_MODE для пробуждения")
                await self.select_mode(target_mode, 0, target_temp, cook_hours, cook_minutes)
                await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send SELECT_MODE command to show mode information on device screen
            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE (0x09) для режима {target_mode}")
            await self.select_mode(target_mode, 0, target_temp, cook_hours, cook_minutes)
            await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send SET_MAIN_MODE command with selected parameters
            _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE (0x05) для режима {target_mode}")
            await self.set_main_mode(target_mode, 0, target_temp, cook_hours, cook_minutes)
            await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send TURN_ON command to start cooking
            _LOGGER.debug(f"📤 Отправка команды TURN_ON (0x03)")
            await self.turn_on()
            
            # Update status after starting
            self._status = await self.get_status()
            
            # Set target state for future reference
            self._target_state = (target_mode, target_temp)
            self._target_boil_time = cook_hours * 60 + cook_minutes
            
            _LOGGER.info("✅ Приготовление успешно начато")
            
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при запуске приготовления: {str(ex)}")
            raise
        finally:
            await self._disconnect_if_need()

    async def stop_cooking(self):
        """Stop cooking."""
        _LOGGER.info("Stopping cooking")
        
        # Turn off the device
        await self.turn_off()
        
        # Reset target state
        self._target_state = None
        self._target_boil_time = None
        if hasattr(self, '_target_delayed_start_hours'):
            delattr(self, '_target_delayed_start_hours')
        if hasattr(self, '_target_delayed_start_minutes'):
            delattr(self, '_target_delayed_start_minutes')
        
        # Clear status to force re-read on next start
        self._status = None

    async def start_delayed(self):
        """Start cooking with delayed start."""
        _LOGGER.info("Starting cooking with delayed start")
        
        # Get the mode that the user has selected (from target_state), not the current device mode
        # If user has selected a mode, use that. Otherwise, use current device mode.
        if self._target_state and self._target_state[0] is not None:
            target_mode = self._target_state[0]
            _LOGGER.info(f"🎯 Используется целевой режим {target_mode} (выбран пользователем)")
        else:
            target_mode = self._status.mode if self._status else 0
            _LOGGER.info(f"🎯 Используется текущий режим устройства {target_mode}")
        
        model_type = self.model_code
        
        # Validate target_mode - if it's invalid (e.g., 16 for MODEL_3), use mode 0 (Multi-chef)
        if model_type and model_type in MODE_DATA and target_mode >= len(MODE_DATA[model_type]):
            _LOGGER.warning(f"⚠️  Некорректный режим {target_mode} для модели {model_type}, использую режим 0 (Multi-chef)")
            target_mode = 0
        
        # Get current values from the connection (which should be set by Number components)
        # These values may have been modified by the user
        target_temp = self._target_state[1] if self._target_state else None
        cook_hours = self._target_boil_time // 60 if self._target_boil_time else 0
        cook_minutes = self._target_boil_time % 60 if self._target_boil_time else 0
        
        # Get delayed start time from Number components (not from MODE_DATA)
        # These values should be set by the user through the Number entities
        wait_hours = 0
        wait_minutes = 0
        
        # Check if we have custom delayed start values set through Number components
        # These values are stored in the connection object
        if hasattr(self, '_target_delayed_start_hours'):
            wait_hours = self._target_delayed_start_hours
        if hasattr(self, '_target_delayed_start_minutes'):
            wait_minutes = self._target_delayed_start_minutes
        
        # If user hasn't set custom values, use defaults from MODE_DATA
        if wait_hours == 0 and wait_minutes == 0:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                mode_data = MODE_DATA[model_type][target_mode]
                wait_hours = mode_data[3]
                wait_minutes = mode_data[4]
        
        # If user hasn't set custom temperature, use default from MODE_DATA
        if target_temp is None:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                target_temp = MODE_DATA[model_type][target_mode][0]
        
        # If user hasn't set custom cooking time, use default from MODE_DATA
        if cook_hours == 0 and cook_minutes == 0:
            if model_type and model_type in MODE_DATA and target_mode < len(MODE_DATA[model_type]):
                cook_hours = MODE_DATA[model_type][target_mode][1]
                cook_minutes = MODE_DATA[model_type][target_mode][2]
        
        # Ensure all values are integers (not None)
        cook_hours = cook_hours or 0
        cook_minutes = cook_minutes or 0
        wait_hours = wait_hours or 0
        wait_minutes = wait_minutes or 0
        
        # Calculate total time (as in ESPHome implementation)
        total_hours = wait_hours + cook_hours
        total_minutes = wait_minutes + cook_minutes
        
        if total_minutes >= 60:
            total_hours += 1
            total_minutes -= 60
        
        _LOGGER.info(f"Delayed start: wait {wait_hours}:{wait_minutes:02d}, cook {cook_hours}:{cook_minutes:02d}, total {total_hours}:{total_minutes:02d}")
        
        # Check if device is in standby mode (mode 16) or if we need to wake it up
        is_in_standby = self._status and self._status.mode == 16
        
        try:
            # Connect if needed
            await self._connect_if_need()
            
            # If device is in standby mode, send SELECT_MODE first to wake it up
            if is_in_standby:
                _LOGGER.info("🔄 Устройство находится в режиме ожидания, отправляем команду SELECT_MODE для пробуждения")
                await self.select_mode(target_mode, 0, target_temp, total_hours, total_minutes, wait_hours, wait_minutes)
                await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send SELECT_MODE command to show mode information on device screen
            _LOGGER.debug(f"📤 Отправка команды SELECT_MODE (0x09) для режима {target_mode}")
            await self.select_mode(target_mode, 0, target_temp, total_hours, total_minutes, wait_hours, wait_minutes)
            await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send SET_MAIN_MODE command with selected parameters
            _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE (0x05) для режима {target_mode}")
            await self.set_main_mode(target_mode, 0, target_temp, total_hours, total_minutes, wait_hours, wait_minutes)
            await asyncio.sleep(0.2)  # Small delay between commands
            
            # Send TURN_ON command to start cooking
            _LOGGER.debug(f"📤 Отправка команды TURN_ON (0x03)")
            await self.turn_on()
            
            # Update status after starting
            self._status = await self.get_status()
            
            # Set target state for future reference
            self._target_state = (target_mode, target_temp)
            self._target_boil_time = total_hours * 60 + total_minutes
            
            _LOGGER.info("✅ Отложенный старт успешно настроен")
            
        except Exception as ex:
            _LOGGER.error(f"❌ Ошибка при настройке отложенного старта: {str(ex)}")
            raise
        finally:
            await self._disconnect_if_need()
            
        # Clear delayed start values after successful setup
        if hasattr(self, '_target_delayed_start_hours'):
            delattr(self, '_target_delayed_start_hours')
        if hasattr(self, '_target_delayed_start_minutes'):
            delattr(self, '_target_delayed_start_minutes')

    async def set_target_temp(self, target_temp, operation_mode = None):
        if target_temp == self.target_temp: return
        _LOGGER.info(f"Setting target temperature to {target_temp}")
        target_mode = self.target_mode
        
        # Get model type from model_code
        model_type = self.model_code
        if model_type is None:
            _LOGGER.error("Unknown model type")
            return
        
        # Find the appropriate mode based on temperature
        if target_temp < 35:
            target_mode = None
        else:
            # Find the mode that matches the target temperature
            for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                if mode_data[0] == target_temp:
                    # Проверяем, поддерживается ли режим устройством
                    if self._is_mode_supported(mode_idx):
                        target_mode = mode_idx
                        break
            
            # If no exact match found, use the closest mode
            if target_mode is None:
                closest_diff = float('inf')
                for mode_idx, mode_data in enumerate(MODE_DATA.get(model_type, [])):
                    # Проверяем, поддерживается ли режим устройством
                    if self._is_mode_supported(mode_idx):
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
        
        # Проверяем, поддерживается ли режим устройством
        if not self._is_mode_supported(operation_mode):
            _LOGGER.error(f"❌ Режим {operation_mode} не поддерживается устройством")
            return
        
        # Get MODE_DATA values for the selected mode
        model_type = self.model_code
        if model_type and model_type in MODE_DATA and operation_mode < len(MODE_DATA[model_type]):
            mode_data = MODE_DATA[model_type][operation_mode]
            _LOGGER.info(f"Mode {operation_mode} data: temperature={mode_data[0]}, hours={mode_data[1]}, minutes={mode_data[2]}")
            
            # Set temperature from MODE_DATA
            target_temp = mode_data[0]
            
            # Set cooking time from MODE_DATA
            cook_hours = mode_data[1]
            cook_minutes = mode_data[2]
            
            # Reset custom values so Number entities show MODE_DATA values
            self._target_state = None
            self._target_boil_time = None
            
            # Also reset delayed start values
            self._target_delayed_start_hours = None
            self._target_delayed_start_minutes = None
            
            # Set target state with the new values, but don't start cooking automatically
            self._target_state = (operation_mode, target_temp)
            self._last_set_target = monotonic()
        else:
            # Fallback to old behavior if MODE_DATA is not available
            target_mode = operation_mode
            target_temp = self.target_temp
            if target_mode in [2]:
                target_temp = 0
            elif target_mode in [3, 4]:
                target_temp = 85
            elif target_temp is None:
                target_temp = 90
            else:
                if target_temp < 35:
                    target_temp = 35
            if target_temp != self.target_temp:
                _LOGGER.info(f"Target temperature autoswitched to {target_temp}")
            # Set target state with the new values, but don't start cooking automatically
            self._target_state = (target_mode, target_temp)
            self._last_set_target = monotonic()


class AuthError(Exception):
    pass

class DisposedError(Exception):
    pass
