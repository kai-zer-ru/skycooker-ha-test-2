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
        if id in self._async_current_ids():
            return False
        await self.async_set_unique_id(id)
        self.config[CONF_MAC] = mac
        # Generate random password
        self.config[CONF_PASSWORD] = list(secrets.token_bytes(8))
        return True

    async def async_step_user(self, user_input=None):
        """Handle the user step."""
        return await self.async_step_scan()

    async def async_step_scan(self, user_input=None):
        """Handle the scan step."""
        errors = {}
        if user_input is not None:
            spl = user_input[CONF_MAC].split(' ', maxsplit=1)
            mac = spl[0]
            name = spl[1][1:-1] if len(spl) >= 2 else None
            if name not in SUPPORTED_DEVICES:
                # Model is not supported
                _LOGGER.error("❌ Устройство не поддерживается: %s", name)
                return self.async_abort(reason='unsupported_device')
            if not await self.init_mac(mac):
                # This cooker already configured
                _LOGGER.warning("⚠️  Устройство уже настроено: %s", mac)
                return self.async_abort(reason='already_configured')
            if name:
                self.config[CONF_FRIENDLY_NAME] = name
            # Continue to connect step
            _LOGGER.info("✅ Устройство %s готово к подключению", name)
            return await self.async_step_connect()

        try:
            try:
                scanner = bluetooth.async_get_scanner(self.hass)
                for device in scanner.discovered_devices:
                    _LOGGER.debug("🔍 Найдено устройство: %s - %s", device.address, device.name)
            except Exception as ex:
                _LOGGER.error("❌ Bluetooth интеграция не работает: %s", ex)
                return self.async_abort(reason='no_bluetooth')
            
            devices_filtered = [device for device in scanner.discovered_devices
                              if device.name and device.name in SUPPORTED_DEVICES]
            if len(devices_filtered) == 0:
                _LOGGER.warning("⚠️  Устройства SkyCooker не найдены")
                return self.async_abort(reason='cooker_not_found')
            
            mac_list = [f"{r.address} ({r.name})" for r in devices_filtered]
            schema = vol.Schema({
                vol.Required(CONF_MAC): vol.In(mac_list)
            })
        except Exception as ex:
            _LOGGER.error("❌ Ошибка сканирования: %s", traceback.format_exc())
            return self.async_abort(reason='unknown')

        _LOGGER.info("📡 Найдено %s устройств SkyCooker", len(mac_list))
        return self.async_show_form(
            step_id="scan",
            errors=errors,
            data_schema=schema
        )

    async def async_step_connect(self, user_input=None):
        """Handle the connect step."""
        errors = {}
        if user_input is not None:
            # Here we would try to connect to the cooker
            # For now, we'll just proceed to init step
            _LOGGER.info("🔌 Подключение к мультиварке...")
            return await self.async_step_init()

        return self.async_show_form(
            step_id="connect",
            errors=errors,
            description_placeholders={
                "message": "✅ Устройство готово к подключению. Переведите мультиварку в режим сопряжения (удерживайте кнопку питания 3 секунды, пока не загорится синий индикатор)"
            },
            data_schema=vol.Schema({})
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
            vol.Required(CONF_PERSISTENT_CONNECTION, default=self.config.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION),
                         description="Постоянное подключение",
                         description_placeholders={"description": "Сохранять постоянное подключение к мультиварке для более быстрого реагирования"}): cv.boolean,
            vol.Required(CONF_SCAN_INTERVAL, default=self.config.get(CONF_SCAN_INTERVAL, 60),
                         description="Интервал опроса (секунды)",
                         description_placeholders={"description": "Интервал опроса состояния мультиварки в секундах (10-300)"}):
                vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            vol.Required(CONF_USE_BACKLIGHT, default=self.config.get(CONF_USE_BACKLIGHT, False),
                         description="Подсветка экрана",
                         description_placeholders={"description": "Включать подсветку экрана мультиварки при управлении"}): bool,
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
                default=options.get(CONF_PERSISTENT_CONNECTION, DEFAULT_PERSISTENT_CONNECTION),
                description="Постоянное подключение",
                description_placeholders={"description": "Сохранять постоянное подключение к мультиварке для более быстрого реагирования"}
            ): cv.boolean,
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=options.get(CONF_SCAN_INTERVAL, 60),
                description="Интервал опроса (секунды)",
                description_placeholders={"description": "Интервал опроса состояния мультиварки в секундах (10-300)"}
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
            vol.Optional(
                CONF_USE_BACKLIGHT,
                default=options.get(CONF_USE_BACKLIGHT, False),
                description="Подсветка экрана",
                description_placeholders={"description": "Включать подсветку экрана мультиварки при управлении"}
            ): bool,
        })

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )