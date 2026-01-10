#!/usr/local/bin/python3
"""Tests for cooking time preservation when user sets custom values."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.skycooker.skycooker_connection import SkyCookerConnection
from custom_components.skycooker.const import MODE_DATA


class TestCookingTimePreservation:
    """Test class for cooking time preservation."""

    @pytest.mark.asyncio
    async def test_start_respects_user_cooking_time(self):
        """Test that start() method respects user-set cooking time instead of using MODE_DATA defaults."""
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
        
        # Mock the connected property to return True
        connection._client = MagicMock()
        connection._client.is_connected = True
        
        # Mock the _status attribute
        connection._status = MagicMock()
        connection._status.mode = 16  # MODE_STANDBY
        connection._status.is_on = False
        connection._status.target_temp = 100
        
        # Set user custom cooking time (1 minute instead of default 35 minutes for mode 5)
        connection._target_boil_hours = 0
        connection._target_boil_minutes = 1
        
        # Set target mode to 5 (Steam mode which has default 35 minutes in MODE_DATA)
        connection._target_mode = 5
        
        await connection.start()
        
        # Verify that set_main_mode was called with user's custom time (0 hours, 1 minute)
        # not the MODE_DATA default (0 hours, 35 minutes)
        set_main_mode_calls = connection.set_main_mode.call_args_list
        assert len(set_main_mode_calls) >= 1
        
        # Check the arguments passed to set_main_mode
        for call in set_main_mode_calls:
            args = call.args
            # args should be: mode, subprog, temp, boil_hours, boil_minutes, delayed_hours, delayed_minutes, auto_warm
            if len(args) >= 5:
                boil_hours = args[3]
                boil_minutes = args[4]
                # Should be user's custom time (0, 1), not MODE_DATA default (0, 35)
                assert boil_hours == 0, f"Expected boil_hours=0, got {boil_hours}"
                assert boil_minutes == 1, f"Expected boil_minutes=1, got {boil_minutes}"
                break
        else:
            pytest.fail("set_main_mode was not called with expected arguments")

    @pytest.mark.asyncio
    async def test_select_mode_preserves_user_cooking_time(self):
        """Test that select_mode() preserves user-set cooking time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Set user custom cooking time
        connection._target_boil_hours = 0
        connection._target_boil_minutes = 5
        
        # Mock MODE_DATA to return a list with enough elements
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Mock the command method to return a success response
        async def mock_command(command, params=None):
            return bytes([0x01])
        connection.command = mock_command
        
        # Call select_mode - it should preserve user's cooking time
        try:
            await connection.select_mode(5)
        except Exception:
            pass  # We expect a connection error, but that's fine
        
        # Verify that user's cooking time was preserved
        # Mode 5 in MODE_DATA has default 35 minutes, but user set 5 minutes
        assert connection._target_boil_hours == 0
        assert connection._target_boil_minutes == 5
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_set_target_mode_preserves_user_cooking_time(self):
        """Test that set_target_mode() preserves user-set cooking time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Set user custom cooking time
        connection._target_boil_hours = 0
        connection._target_boil_minutes = 10
        
        # Mock MODE_DATA to return a list with enough elements
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Call set_target_mode - it should preserve user's cooking time
        await connection.set_target_mode(5)
        
        # Verify that user's cooking time was preserved
        # Mode 5 in MODE_DATA has default 35 minutes, but user set 10 minutes
        assert connection._target_boil_hours == 0
        assert connection._target_boil_minutes == 10
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)

    @pytest.mark.asyncio
    async def test_set_target_temp_preserves_user_cooking_time(self):
        """Test that set_target_temp() preserves user-set cooking time."""
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        connection = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # Set user custom cooking time
        connection._target_boil_hours = 0
        connection._target_boil_minutes = 15
        
        # Mock MODE_DATA to return a list with enough elements
        original_mode_data = MODE_DATA.copy()
        MODE_DATA[3] = [
            [100, 0, 30, 15], [101, 0, 30, 7], [100, 1, 0, 7], [165, 0, 18, 5],
            [100, 1, 0, 7], [100, 0, 35, 7], [100, 0, 8, 4], [98, 3, 0, 7],
            [100, 0, 40, 7], [140, 1, 0, 7], [100, 0, 25, 7], [110, 1, 0, 7],
            [40, 8, 0, 6], [145, 0, 20, 7], [140, 3, 0, 7],
            [0, 0, 0, 0], [62, 2, 30, 6]
        ]
        
        # Call set_target_temp - it should preserve user's cooking time
        await connection.set_target_temp(100)
        
        # Verify that user's cooking time was preserved
        # The mode that matches 100°C (mode 0) has default 30 minutes, but user set 15 minutes
        assert connection._target_boil_hours == 0
        assert connection._target_boil_minutes == 15
        
        # Restore original MODE_DATA
        MODE_DATA.update(original_mode_data)