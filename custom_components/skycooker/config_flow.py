#!/usr/local/bin/python3
# coding: utf-8

import logging
from homeassistant import config_entries
from homeassistant.const import CONF_MAC, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import SUPPORTED_DEVICES, MIN_TEMP, MAX_TEMP

_LOGGER = logging.getLogger(__name__)

DOMAIN = "skycooker"

DATA_SCHEMA_USER = {
    CONF_MAC: str,
    CONF_PASSWORD: str,
    CONF_SCAN_INTERVAL: int,
    CONF_USE_BACKLIGHT: bool,
}

DATA_SCHEMA_BLUETOOTH = {
    CONF_MAC: str,
}


class SkyCookerConfigFlow(config_entries.ConfigFlow):
    """Config flow for SkyCooker."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLLING
    DOMAIN = "skycooker"

    def __init__(self):
        """Initialize."""
        self.device_name = None
        self.device_mac = None

    async def async_step_user(
        self, user_input=None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        _LOGGER.info("🔧 Начало настройки интеграции SkyCooker")
        errors = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].upper()
            password = user_input[CONF_PASSWORD]
            scan_interval = user_input[CONF_SCAN_INTERVAL]
            use_backlight = user_input.get('use_backlight', False)

            _LOGGER.debug("📝 Введены параметры: MAC=%s, Пароль=%s, Интервал=%s, Подсветка=%s",
                         mac, password, scan_interval, use_backlight)

            # Validate password format (8 hex characters)
            if len(password) != 16 or not all(c in '0123456789abcdefABCDEF' for c in password):
                _LOGGER.error("❌ Неверный формат пароля")
                errors["base"] = "wrong_password"
            else:
                # Check if device is supported
                try:
                    _LOGGER.info("🔍 Проверка поддерживаемого устройства: %s", mac)
                    device_name = f"RMC-M40S_{mac[-5:].replace(':', '')}"
                    
                    if device_name in SUPPORTED_DEVICES or any(mac.startswith(prefix) for prefix in ['AA', 'BB', 'CC', 'DD', 'EE', 'FF']):
                        # Check if already configured
                        await self.async_set_unique_id(device_name)
                        self._abort_if_unique_id_configured()

                        _LOGGER.info("✅ Интеграция успешно настроена для устройства: %s", device_name)
                        return self.async_create_entry(
                            title=device_name,
                            data={
                                CONF_MAC: mac,
                                CONF_PASSWORD: password,
                                CONF_SCAN_INTERVAL: scan_interval,
                                'use_backlight': use_backlight,
                            }
                        )
                    else:
                        _LOGGER.error("❌ Устройство не поддерживается: %s", device_name)
                        errors["base"] = "unsupported_device"
                except Exception as ex:
                    _LOGGER.error("❌ Ошибка настройки интеграции: %s", ex)
                    errors["base"] = "setup_failed"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_USER,
            errors=errors,
        )

    async def async_step_bluetooth(self, discovery_info):
        """Handle bluetooth discovery."""
        mac = discovery_info.address
        name = discovery_info.name

        _LOGGER.info("📡 Обнаружено Bluetooth устройство: %s (%s)", name, mac)

        if name not in SUPPORTED_DEVICES:
            _LOGGER.warning("❌ Устройство не поддерживается: %s", name)
            return self.async_abort(reason="unsupported_device")

        await self.async_set_unique_id(name)
        self._abort_if_unique_id_configured({CONF_MAC: mac})

        self.device_name = name
        self.device_mac = mac

        _LOGGER.info("✅ Bluetooth устройство %s готово к настройке", name)
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(self, user_input=None):
        """Confirm bluetooth setup."""
        if user_input is not None:
            _LOGGER.info("✅ Подтверждение настройки Bluetooth устройства: %s", self.device_name)
            return await self.async_step_user({
                CONF_MAC: self.device_mac,
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_SCAN_INTERVAL: 60,
                'use_backlight': False,
            })

        _LOGGER.info("📡 Ожидание подтверждения Bluetooth устройства: %s", self.device_name)
        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema={CONF_PASSWORD: str},
            description_placeholders={
                "name": self.device_name,
                "mac": self.device_mac,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return SkyCookerOptionsFlowHandler(config_entry)


class SkyCookerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle SkyCooker options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        data_schema = {
            CONF_SCAN_INTERVAL: int,
            'use_backlight': bool,
        }

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )