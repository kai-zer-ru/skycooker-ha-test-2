#!/usr/local/bin/python3
"""Tests for SkyCooker number entities."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.const import CONF_FRIENDLY_NAME, UnitOfTemperature, UnitOfTime
from custom_components.skycooker.number import SkyCookerNumber
from custom_components.skycooker.const import *


class TestSkyCookerNumber:
    """Test class for SkyCookerNumber."""

    @pytest.mark.asyncio
    async def test_number_initialization(self):
        """Test that the number entity initializes correctly."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {CONF_FRIENDLY_NAME: "Test Device"}
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        assert number.hass == hass
        assert number.entry == entry
        assert number.number_type == NUMBER_TYPE_TEMPERATURE

    @pytest.mark.asyncio
    async def test_number_unique_id(self):
        """Test that the number entity returns the correct unique ID."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        assert number.unique_id == "test_entry_temperature"

    @pytest.mark.asyncio
    async def test_number_name_russian(self):
        """Test that the number entity returns the correct name in Russian."""
        hass = MagicMock()
        hass.config.language = "ru"
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {CONF_FRIENDLY_NAME: "Test Device"}
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        assert number.name == "SkyCooker Test Device температура"

    @pytest.mark.asyncio
    async def test_number_name_english(self):
        """Test that the number entity returns the correct name in English."""
        hass = MagicMock()
        hass.config.language = "en"
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {CONF_FRIENDLY_NAME: "Test Device"}
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        assert number.name == "SkyCooker Test Device temperature"

    @pytest.mark.asyncio
    async def test_number_icon(self):
        """Test that the number entity returns the correct icon."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.icon == "mdi:thermometer"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        assert number.icon == "mdi:timer"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_HOURS)
        assert number.icon == "mdi:timer-sand"

    @pytest.mark.asyncio
    async def test_number_available(self):
        """Test that the number entity returns the correct availability."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.available = True
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.available == True

    @pytest.mark.asyncio
    async def test_number_native_value_temperature(self):
        """Test that the number entity returns the correct native value for temperature."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        mock_connection.model_code = 3
        mock_connection.target_state = (1, 100)
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.native_value == 100

    @pytest.mark.asyncio
    async def test_number_native_value_cooking_time_hours(self):
        """Test that the number entity returns the correct native value for cooking time hours."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        mock_connection.model_code = 3
        mock_connection.target_boil_time = 90
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.native_value == 1

    @pytest.mark.asyncio
    async def test_number_native_value_cooking_time_minutes(self):
        """Test that the number entity returns the correct native value for cooking time minutes."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_MINUTES)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        mock_connection.model_code = 3
        mock_connection.target_boil_time = 90
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.native_value == 30

    @pytest.mark.asyncio
    async def test_number_native_value_delayed_start_hours(self):
        """Test that the number entity returns the correct native value for delayed start hours."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_HOURS)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        mock_connection.model_code = 3
        mock_connection.target_delayed_start_hours = 2
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.native_value == 2

    @pytest.mark.asyncio
    async def test_number_native_value_delayed_start_minutes(self):
        """Test that the number entity returns the correct native value for delayed start minutes."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_MINUTES)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        mock_connection.model_code = 3
        mock_connection.target_delayed_start_minutes = 30
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        assert number.native_value == 30

    @pytest.mark.asyncio
    async def test_number_native_min_value(self):
        """Test that the number entity returns the correct native min value."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.native_min_value == 35
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        assert number.native_min_value == 0

    @pytest.mark.asyncio
    async def test_number_native_max_value(self):
        """Test that the number entity returns the correct native max value."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.native_max_value == 100
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        assert number.native_max_value == 24

    @pytest.mark.asyncio
    async def test_number_native_step(self):
        """Test that the number entity returns the correct native step."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.native_step == 1

    @pytest.mark.asyncio
    async def test_number_native_unit_of_measurement(self):
        """Test that the number entity returns the correct native unit of measurement."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.native_unit_of_measurement == UnitOfTemperature.CELSIUS
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        assert number.native_unit_of_measurement == UnitOfTime.HOURS

    @pytest.mark.asyncio
    async def test_number_mode(self):
        """Test that the number entity returns the correct mode."""
        hass = MagicMock()
        entry = MagicMock()
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        assert number.mode == "auto"

    @pytest.mark.asyncio
    async def test_number_async_set_native_value_temperature(self):
        """Test that the number entity correctly sets the temperature value."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_TEMPERATURE)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.status = MagicMock()
        mock_connection.status.mode = 1
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        await number.async_set_native_value(100)
        
        assert mock_connection.target_state == (1, 100)
        assert mock_connection.target_temperature == 100

    @pytest.mark.asyncio
    async def test_number_async_set_native_value_cooking_time_hours(self):
        """Test that the number entity correctly sets the cooking time hours value."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_HOURS)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.target_boil_time = 30
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        await number.async_set_native_value(2)
        
        assert mock_connection.target_boil_time == 150

    @pytest.mark.asyncio
    async def test_number_async_set_native_value_cooking_time_minutes(self):
        """Test that the number entity correctly sets the cooking time minutes value."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_COOKING_TIME_MINUTES)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        mock_connection.target_boil_time = 120
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        await number.async_set_native_value(30)
        
        assert mock_connection.target_boil_time == 150

    @pytest.mark.asyncio
    async def test_number_async_set_native_value_delayed_start_hours(self):
        """Test that the number entity correctly sets the delayed start hours value."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_HOURS)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        await number.async_set_native_value(2)
        
        assert mock_connection.target_delayed_start_hours == 2

    @pytest.mark.asyncio
    async def test_number_async_set_native_value_delayed_start_minutes(self):
        """Test that the number entity correctly sets the delayed start minutes value."""
        hass = MagicMock()
        entry = MagicMock()
        entry.entry_id = "test_entry"
        
        number = SkyCookerNumber(hass, entry, NUMBER_TYPE_DELAYED_START_MINUTES)
        
        # Mock the skycooker connection
        mock_connection = MagicMock()
        hass.data = {DOMAIN: {"test_entry": {DATA_CONNECTION: mock_connection}}}
        
        await number.async_set_native_value(30)
        
        assert mock_connection.target_delayed_start_minutes == 30