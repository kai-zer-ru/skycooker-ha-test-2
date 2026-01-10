"""Поддержка карточки SkyCooker."""
import logging

from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Настройка компонента карточки SkyCooker."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("Интеграция карточки SkyCooker загружена")
    return True


async def async_setup_entry(hass: HomeAssistant, entry):
    """Настройка карточки SkyCooker из конфигурационного входа."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry):
    """Выгрузка конфигурационного входа."""
    return True