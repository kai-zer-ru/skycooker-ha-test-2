#!/usr/local/bin/python3
# coding: utf-8

import logging
import secrets
import traceback

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import (CONF_DEVICE, CONF_FRIENDLY_NAME, CONF_MAC,
                                 CONF_PASSWORD, CONF_SCAN_INTERVAL)
from homeassistant.core import callback

from .const import DOMAIN, SUPPORTED_DEVICES, MIN_TEMP, MAX_TEMP, CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION

_LOGGER = logging.getLogger(__name__)

CONF_USE_BACKLIGHT = 'use_backlight'

DATA_SCHEMA_USER = vol.Schema({
    vol.Required(CONF_MAC): str,
    vol.Required(CONF_PASSWORD): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
    vol.Optional(CONF_USE_BACKLIGHT, default=False): bool,
})

DATA_SCHEMA_BLUETOOTH = vol.Schema({
    vol.Required(CONF_MAC): cv.string,
})


class SkyCookerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SkyCooker."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        """Get the options flow for this handler."""
        return SkyCookerOptionsFlowHandler(entry=entry)

    def __init__(self, entry=None):
        """Initialize a new SkyCookerConfigFlow."""
        self.entry = entry
        self.config = {} if not entry else dict(entry.data.items())

    async def init_mac(self, mac):
        mac = mac.upper()
        mac = mac.replace(':', '').replace('-', '').replace(' ', '')
        mac = ':'.join([mac[p*2:(p*2)+2] for p in range(6)])
        id = f"{DOMAIN}-{mac}"
        self._abort_if_unique_id_configured()
        self.config[CONF_MAC] = mac
        # Generate random password
        self.config[CONF_PASSWORD] = list(secrets.token_bytes(8))
        return True

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        _LOGGER.debug("🔍 Начало user шага")
        return await self.async_step_scan()

    async def async_step_scan(self, user_input=None):
        """Handle the scan step - выбор из списка устройств."""
        _LOGGER.debug("📡 Начало сканирования устройств SkyCooker")
        errors = {}
        if user_input is not None:
            try:
                spl = user_input[CONF_MAC].split(' ', maxsplit=1)
                mac = spl[0]
                name = None
                
                # Извлекаем имя устройства из скобок
                if len(spl) >= 2:
                    name_part = spl[1].strip()
                    if name_part.startswith('(') and name_part.endswith(')'):
                        name = name_part[1:-1]
                    else:
                        name = name_part
                
                _LOGGER.debug("🔍 Выбрано устройство: MAC=%s, Имя=%s", mac, name)
                
                if name and name not in SUPPORTED_DEVICES:
                    # Model is not supported
                    _LOGGER.error("❌ Устройство не поддерживается: %s", name)
                    return self.async_abort(reason='unsupported_device')
                if not await self.init_mac(mac):
                    # This cooker already configured
                    _LOGGER.warning("⚠️  Устройство уже настроено: %s", mac)
                    return self.async_abort(reason='already_configured')
                if name:
                    self.config[CONF_FRIENDLY_NAME] = name
                # Continue to parameters step
                _LOGGER.info("✅ Устройство %s выбрано для настройки", name or mac)
                return await self.async_step_parameters()
            except Exception as ex:
                _LOGGER.error("❌ Ошибка обработки выбора устройства: %s", ex)
                _LOGGER.exception(ex)
                return self.async_abort(reason='unknown')

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                _LOGGER.debug("🔍 Сканер Bluetooth инициализирован")
                
                # Проверяем, есть ли вообще устройства
                discovered_devices = scanner.discovered_devices
                _LOGGER.debug("🔍 Всего найдено устройств: %s", len(discovered_devices))
                
                for device in discovered_devices:
                    _LOGGER.debug("🔍 Найдено устройство: %s - %s", device.address, device.name)
                    if device.name:
                        _LOGGER.debug("🔍 Устройство %s (%s) - проверка на поддержку: %s",
                                    device.name, device.address, device.name in SUPPORTED_DEVICES)
                    
            except Exception as ex:
                _LOGGER.error("❌ Bluetooth интеграция не работает: %s", ex)
                return self.async_abort(reason='no_bluetooth')
            
            # Фильтруем устройства по поддерживаемым моделям
            _LOGGER.debug("🔍 Поддерживаемые модели: %s", list(SUPPORTED_DEVICES.keys()))
            devices_filtered = [device for device in discovered_devices
                              if device.name and device.name in SUPPORTED_DEVICES]
            _LOGGER.debug("🔍 Отфильтровано устройств SkyCooker: %s", len(devices_filtered))
            
            # Логируем все найденные устройства для отладки
            for device in devices_filtered:
                _LOGGER.debug("✅ Поддерживаемое устройство: %s - %s", device.address, device.name)
            
            if len(devices_filtered) == 0:
                _LOGGER.warning("⚠️  Устройства SkyCooker не найдены")
                return self.async_abort(reason='cooker_not_found')
            
            # Создаем список для выбора
            mac_list = [f"{r.address} ({r.name})" for r in devices_filtered]
            _LOGGER.debug("🔍 Список доступных устройств: %s", mac_list)
            
            schema = vol.Schema({
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception as ex:
            _LOGGER.error("❌ Ошибка сканирования: %s", traceback.format_exc())
            return self.async_abort(reason='unknown')

        _LOGGER.info("📡 Найдено %s устройств SkyCooker", len(devices_filtered))
        _LOGGER.debug("📡 Подготовка формы с %s устройствами", len(mac_list))
        
        _LOGGER.debug("📡 Отправка формы с данными: %s", schema)
        return self.async_show_form(
            step_id="scan",
            errors=errors,
            data_schema=schema
        )

    async def async_step_parameters(self, user_input=None):
        """Handle the parameters step - выбор необходимых параметров."""
        errors = {}
        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            
            # Валидация пароля
            if not password or len(password) != 16:
                errors["password"] = "invalid_password"
            else:
                try:
                    # Проверяем, что пароль состоит из 16 шестнадцатеричных символов
                    bytes.fromhex(password)
                    self.config[CONF_PASSWORD] = list(bytes.fromhex(password))
                    self.config[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
                    self.config[CONF_USE_BACKLIGHT] = user_input[CONF_USE_BACKLIGHT]
                    # Continue to instructions step
                    _LOGGER.info("✅ Параметры настроены для устройства: %s", self.config.get(CONF_FRIENDLY_NAME, 'SkyCooker'))
                    return await self.async_step_instructions()
                except ValueError:
                    errors["password"] = "invalid_password"

        schema = vol.Schema({
            vol.Required(CONF_PASSWORD, default=""): str,
            vol.Required(CONF_SCAN_INTERVAL, default=60): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            vol.Optional(CONF_USE_BACKLIGHT, default=False): bool,
        })

        return self.async_show_form(
            step_id="parameters",
            errors=errors,
            data_schema=schema
        )

    async def async_step_instructions(self, user_input=None):
        """Handle the instructions step - инструкции по переводу мультиварки в режим сопряжения."""
        errors = {}
        if user_input is not None:
            # Continue to connect step
            _LOGGER.info("✅ Пользователь прочитал инструкции, переходим к подключению")
            return await self.async_step_connect()

        return self.async_show_form(
            step_id="instructions",
            errors=errors,
            data_schema=vol.Schema({
                vol.Optional("continue", default=True): bool
            })
        )

    async def async_step_connect(self, user_input=None):
        """Handle the connect step - непосредственно подключение к мультиварке."""
        errors = {}
        
        # Если пользователь нажал кнопку "Продолжить", начинаем подключение
        if user_input is not None and user_input.get("continue", False):
            _LOGGER.info("🔌 Начинаем подключение к мультиварке...")
            
            try:
                # Импортируем BTLEConnection для подключения
                from .btle import BTLEConnection
                
                # Создаем соединение
                connection = BTLEConnection(self.hass, self.config[CONF_MAC], self.config[CONF_PASSWORD])
                
                # Подключаемся к устройству
                await connection.connect()
                
                # Отправляем команду аутентификации
                await connection.send_auth()
                
                # Устанавливаем имя и тип устройства
                await connection.setNameAndType()
                
                # Проверяем доступность устройства по имени и типу
                if connection.name and connection.type:
                    _LOGGER.info("✅ Устройство найдено и готово к подключению: %s", connection.name)
                    # Сохраняем MAC-адрес для последующего использования
                    self.config['mac_address'] = self.config[CONF_MAC]
                    return await self.async_step_init()
                else:
                    errors["base"] = "device_not_found"
                    _LOGGER.error("❌ Устройство не найдено или не поддерживается: %s", self.config[CONF_MAC])
                    
            except Exception as ex:
                _LOGGER.error("❌ Ошибка подключения к мультиварке: %s", ex)
                errors["base"] = "connection_failed"

        # Показываем форму с кнопкой для подключения
        _LOGGER.debug("📡 Показываем форму подключения")
        return self.async_show_form(
            step_id="connect",
            errors=errors,
            data_schema=vol.Schema({
                vol.Optional("continue", default=True): bool
            })
        )

    async def async_step_init(self, user_input=None):
        """Handle the options step."""
        errors = {}
        if user_input is not None:
            self.config[CONF_PERSISTENT_CONNECTION] = user_input[CONF_PERSISTENT_CONNECTION]
            self.config[CONF_SCAN_INTERVAL] = user_input[CONF_SCAN_INTERVAL]
            self.config[CONF_USE_BACKLIGHT] = user_input[CONF_USE_BACKLIGHT]
            fname = f"{self.config.get(CONF_FRIENDLY_NAME, 'SkyCooker')} ({self.config[CONF_MAC]})"
            _LOGGER.info("✅ Конфигурация сохранена для устройства: %s", fname)
            if self.entry:
                self.hass.config_entries.async_update_entry(self.entry, data=self.config)
            return self.async_create_entry(
                title=fname, data=self.config if not self.entry else {}
            )

        schema = vol.Schema({
            vol.Required(CONF_PERSISTENT_CONNECTION, default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)): cv.boolean,
            vol.Required(CONF_SCAN_INTERVAL, default=self.config.get(CONF_SCAN_INTERVAL, 60)):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            vol.Required(CONF_USE_BACKLIGHT, default=self.config.get(CONF_USE_BACKLIGHT, False)): bool,
        })

        return self.async_show_form(
            step_id="init",
            errors=errors,
            data_schema=schema
        )


class SkyCookerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SkyCooker options."""

    def __init__(self, entry):
        """Initialize options flow."""
        self.entry = entry
        self.config = dict(entry.data.items())

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.entry.options
        data_schema = vol.Schema({
            vol.Optional(
                CONF_PERSISTENT_CONNECTION,
                default=options.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION)
            ): cv.boolean,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=options.get(CONF_SCAN_INTERVAL, 60)
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            vol.Optional(
                CONF_USE_BACKLIGHT,
                default=options.get(CONF_USE_BACKLIGHT, False)
            ): bool,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )