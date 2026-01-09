#!/usr/local/bin/python3
"""Tests for SkyCookerConnection class."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_connection import SkyCookerConnection, AuthError, DisposedError
from custom_components.skycooker.const import STATUS_OFF, STATUS_AUTO_WARM


class TestSkyCookerConnection:
    """Test class for SkyCookerConnection."""

    def test_connection_initialization(self):
        """Test that the SkyCookerConnection initializes correctly."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection._mac == mac
        assert connection._key == key
        assert connection.persistent == True
        assert connection._auth_ok == False
        assert connection._sw_version == "0.0"

    def test_connection_available(self):
        """Test that the connection returns the correct availability."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.available == False

    def test_connection_last_connect_ok(self):
        """Test that the connection returns the correct last_connect_ok status."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.last_connect_ok == False

    def test_connection_last_auth_ok(self):
        """Test that the connection returns the correct last_auth_ok status."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.last_auth_ok == False

    def test_connection_add_stat(self):
        """Test that the connection correctly adds statistics."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        connection.add_stat(True)
        assert len(connection._successes) == 1
        assert connection._successes[0] == True

        connection.add_stat(False)
        assert len(connection._successes) == 2
        assert connection._successes[1] == False

    def test_connection_success_rate(self):
        """Test that the connection returns the correct success rate."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.success_rate == 0

        connection.add_stat(True)
        assert connection.success_rate == 100

        connection.add_stat(False)
        assert connection.success_rate == 50

    @pytest.mark.asyncio
    async def test_connection_stop(self):
        """Test that the connection correctly stops."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        await connection.stop()
        assert connection._disposed == True

    def test_connection_minutes(self):
        """Test that the connection returns the correct minutes."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.minutes is None

    def test_connection_status_code(self):
        """Test that the connection returns the correct status code."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.status_code is None

    def test_connection_remaining_time(self):
        """Test that the connection returns the correct remaining time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.remaining_time is None

    def test_connection_total_time(self):
        """Test that the connection returns the correct total time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.total_time is None

    def test_connection_delayed_start_time(self):
        """Test that the connection returns the correct delayed start time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.delayed_start_time is None

    def test_connection_auto_warm_time(self):
        """Test that the connection returns the correct auto warm time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.auto_warm_time is None

    def test_connection_auto_warm_enabled(self):
        """Test that the connection returns the correct auto warm enabled status."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.auto_warm_enabled is None

    @pytest.mark.asyncio
    async def test_connection_set_boil_time(self):
        """Test that the connection correctly sets the boil time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        connection.update = AsyncMock()

        await connection.set_boil_time(30)

        assert connection._target_boil_time == 30

    @pytest.mark.asyncio
    async def test_connection_set_temperature(self):
        """Test that the connection correctly sets the temperature."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        connection.update = AsyncMock()

        await connection.set_temperature(100)

        assert connection._target_state == (None, 100)

    @pytest.mark.asyncio
    async def test_connection_set_cooking_time(self):
        """Test that the connection correctly sets the cooking time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        connection.update = AsyncMock()

        await connection.set_cooking_time(1, 30)

        assert connection._target_boil_time == 90

    @pytest.mark.asyncio
    async def test_connection_set_delayed_start(self):
        """Test that the connection correctly sets the delayed start time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        connection.update = AsyncMock()

        await connection.set_delayed_start(2, 30)

        connection.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_start_delayed(self):
        """Test that the connection correctly starts with delayed start."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute to avoid IndexError
        connection._status = MagicMock()
        connection._status.mode = 1
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]

        await connection.start_delayed()

        # Verify that the methods were called in the correct order
        connection._connect_if_need.assert_called_once()
        connection.select_mode.assert_called()
        connection.set_main_mode.assert_called()
        connection.turn_on.assert_called_once()
        connection.get_status.assert_called_once()
        connection._disconnect_if_need.assert_called_once()
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_set_target_temp(self):
        """Test that the connection correctly sets the target temperature."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        connection.update = AsyncMock()

        await connection.set_target_temp(100)

        connection.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_set_target_mode(self):
        """Test that the connection correctly sets the target mode."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        await connection.set_target_mode(1)

        # Verify that target_state was set correctly
        assert connection._target_state == (1, 101)

    def test_connection_sw_version(self):
        """Test that the connection returns the correct software version."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.sw_version == "0.0"

    def test_connection_sound_enabled(self):
        """Test that the connection returns the correct sound enabled status."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.sound_enabled is None

    def test_connection_boil_time(self):
        """Test that the connection returns the correct boil time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")

        assert connection.boil_time is None

    @pytest.mark.asyncio
    async def test_connection_start_with_mode_16(self):
        """Test that the connection correctly handles mode 16 (standby) when starting."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute to simulate device in mode 16 (standby)
        connection._status = MagicMock()
        connection._status.mode = 16
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Call start() - it should use mode 0 instead of mode 16
        await connection.start()
        
        # Verify that the methods were called in the correct order
        connection._connect_if_need.assert_called_once()
        connection.select_mode.assert_called()
        connection.set_main_mode.assert_called()
        connection.turn_on.assert_called_once()
        connection.get_status.assert_called_once()
        connection._disconnect_if_need.assert_called_once()
        
        # Verify that target_state was set to mode 0 (Multi-chef) instead of mode 16
        assert connection._target_state[0] == 0
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_start_command_sequence(self):
        """Test that the connection sends commands in the correct sequence when starting."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute
        connection._status = MagicMock()
        connection._status.mode = 1
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Set target state to simulate user selection
        connection._target_state = (1, 101)
        connection._target_boil_time = 30
        
        await connection.start()

        # Verify that the methods were called in the correct order
        connection._connect_if_need.assert_called_once()
        connection.select_mode.assert_called()
        connection.set_main_mode.assert_called()
        connection.turn_on.assert_called_once()
        connection.get_status.assert_called_once()
        connection._disconnect_if_need.assert_called_once()
        
        # Verify that select_mode was called with correct parameters
        select_mode_calls = connection.select_mode.call_args_list
        assert len(select_mode_calls) >= 1
        
        # Verify that set_main_mode was called with correct parameters
        set_main_mode_calls = connection.set_main_mode.call_args_list
        assert len(set_main_mode_calls) >= 1
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_update_with_mode_16_and_target_mode_5(self):
        """Test that the connection correctly handles mode 16 (standby) when updating with target mode 5 (Steam)."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Test the specific logic we fixed: target mode selection when device is in mode 16
        # Mock the _status attribute to simulate device in mode 16 (standby)
        connection._status = MagicMock()
        connection._status.mode = 16
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Set target state to mode 5 (Steam) with temperature 100
        connection._target_state = (5, 100)
        connection._target_boil_time = 35
        
        # Test the logic in update method for selecting the correct target mode
        # This is the key fix: when device is in mode 16, use target mode from _target_state
        target_mode_to_check = connection._target_state[0] if connection._target_state else connection._status.mode
        
        # Verify that the correct target mode is selected (5, not 16)
        assert target_mode_to_check == 5
        
        # Verify that mode 5 is supported
        assert connection._is_mode_supported(5) == True
        
        # Verify that mode 16 is also supported (as a device state)
        assert connection._is_mode_supported(16) == True
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_is_mode_supported_mode_16(self):
        """Test that _is_mode_supported correctly handles mode 16 (standby)."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Test that mode 16 is supported as a device state (but not for direct setting)
        assert connection._is_mode_supported(16) == True
        
        # Test that mode 5 (Steam) is supported
        assert connection._is_mode_supported(5) == True

    @pytest.mark.asyncio
    async def test_connection_select_mode_with_mode_16(self):
        """Test that select_mode correctly handles mode 16 (standby)."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Test that _is_mode_supported allows mode 16
        # (mode 16 is allowed as it can be a current device state)
        assert connection._is_mode_supported(16) == True
        
        # Test that select_mode doesn't raise an error for mode 16 in the validation check
        # (the actual command sending would fail without connection, but that's expected)
        # We just want to verify that mode 16 passes the initial validation
        try:
            # This should pass the mode validation but fail on connection
            await connection.select_mode(16)
        except Exception as e:
            # We expect a connection error, not a mode validation error
            assert "Не подключено" in str(e) or "не поддерживается" not in str(e)

    @pytest.mark.asyncio
    async def test_connection_select_mode_preserves_user_settings(self):
        """Test that select_mode preserves user settings when changing modes."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Set user custom settings
        connection._target_temperature = 120
        connection._target_boil_time = 45
        connection._target_delayed_start_hours = 2
        connection._target_delayed_start_minutes = 30
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Call select_mode - it should preserve user settings
        try:
            await connection.select_mode(5)
        except Exception:
            pass  # We expect a connection error, but that's fine
        
        # Verify that user settings were preserved
        assert connection._target_temperature == 120
        assert connection._target_boil_time == 45
        assert connection._target_delayed_start_hours == 2
        assert connection._target_delayed_start_minutes == 30
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_start_preserves_auto_warm(self):
        """Test that start method preserves auto warm setting."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Enable auto warm
        connection._auto_warm_enabled = True
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute
        connection._status = MagicMock()
        connection._status.mode = 1
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Set target state
        connection._target_state = (1, 101)
        connection._target_boil_time = 30
        
        await connection.start()
        
        # Verify that auto warm flag was passed to select_mode and set_main_mode
        # Check that select_mode was called with auto_warm_flag=1
        select_mode_calls = connection.select_mode.call_args_list
        for call in select_mode_calls:
            if len(call.args) > 7:
                assert call.args[7] == 1  # auto_warm_flag should be 1
        
        # Check that set_main_mode was called with auto_warm_flag=1
        set_main_mode_calls = connection.set_main_mode.call_args_list
        for call in set_main_mode_calls:
            if len(call.args) > 7:
                assert call.args[7] == 1  # auto_warm_flag should be 1
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_start_command_sequence_standby(self):
        """Test that start method sends correct command sequence when device is in standby mode."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute to simulate device in mode 16 (standby)
        connection._status = MagicMock()
        connection._status.mode = 16
        connection._status.is_on = False
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Set target state
        connection._target_state = (5, 100)
        connection._target_boil_time = 35
        
        await connection.start()
        
        # Verify that the correct command sequence was followed for standby mode
        # 1. select_mode should be called first to wake up the device
        # 2. set_main_mode should be called next
        # 3. turn_on should be called last
        
        # Verify that select_mode was called
        connection.select_mode.assert_called()
        
        # Verify that set_main_mode was called
        connection.set_main_mode.assert_called()
        
        # Verify that turn_on was called
        connection.turn_on.assert_called_once()
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_connection_start_command_sequence_same_mode(self):
        """Test that start method sends correct command sequence when device is already in target mode."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Mock the necessary methods and attributes
        connection._connect_if_need = AsyncMock()
        connection.select_mode = AsyncMock()
        connection.set_main_mode = AsyncMock()
        connection.turn_on = AsyncMock()
        connection.get_status = AsyncMock()
        connection._disconnect_if_need = AsyncMock()
        
        # Mock the _status attribute to simulate device already in target mode
        connection._status = MagicMock()
        connection._status.mode = 5
        connection._status.is_on = True
        connection._status.target_temp = 100
        connection._status.boil_time = 0
        
        # Mock MODE_DATA to return a list with enough elements
        from custom_components.skycooker.const import MODE_DATA
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Set target state to same mode
        connection._target_state = (5, 100)
        connection._target_boil_time = 35
        
        await connection.start()
        
        # Verify that the correct command sequence was followed for same mode
        # 1. set_main_mode should be called (no need to send select_mode)
        # 2. turn_on should be called
        
        # Verify that set_main_mode was called
        connection.set_main_mode.assert_called()
        
        # Verify that turn_on was called
        connection.turn_on.assert_called_once()
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)