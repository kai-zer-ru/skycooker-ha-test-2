"""
Select platform for SkyCooker integration.
"""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .logger import logger
from .multicooker import SkyCookerDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up SkyCooker select entities."""
    logger.info("🎛️ Setting up SkyCooker select entities")
    
    # Get device from hass data
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    
    # Create select entity for cooking programs
    select_entities = [SkyCookerProgramSelect(device)]
    
    async_add_entities(select_entities)
    logger.success("✅ SkyCooker select entities setup complete")

class SkyCookerProgramSelect(SelectEntity):
    """Select entity for choosing cooking programs."""
    
    def __init__(self, device: SkyCookerDevice):
        """Initialize the program select."""
        self._device = device
        self._attr_name = f"{device.device_name} Program"
        self._attr_unique_id = f"{device.device_address}_program_select"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, device.device_address)},
            "name": device.device_name,
            "manufacturer": "Redmond",
            "model": device.device_type,
        }
        
        # Get available modes from device constants
        self._options = list(device.constants["MODES"].values())
        self._mode_values = list(device.constants["MODES"].keys())
    
    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self._device.status_data:
            mode = self._device.status_data.get("mode", 0)
            return self._device.constants["MODES"].get(mode, "Unknown")
        return "Unknown"
    
    @property
    def options(self) -> list[str]:
        """Return a list of available options."""
        return self._options
    
    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        logger.command(f"🍲 Selecting program: {option}")
        
        # Find the mode value for the selected option
        mode_value = None
        for i, opt in enumerate(self._options):
            if opt == option:
                mode_value = self._mode_values[i]
                break
        
        if mode_value is not None:
            # Set the mode on the device
            success = await self._device.set_mode(mode_value)
            if success:
                logger.success(f"✅ Program set to: {option}")
                # Update the current option
                self.async_write_ha_state()
            else:
                logger.error(f"❌ Failed to set program: {option}")
        else:
            logger.error(f"❌ Unknown program: {option}")