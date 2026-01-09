#!/usr/local/bin/python3
"""Test for parsing new status format."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_connection import SkyCookerConnection
from custom_components.skycooker.const import MODELS


class TestNewStatus:
    """Test class for new status parsing."""

    @pytest.mark.asyncio
    async def test_parse_new_status(self):
        """Test parsing of the new status format."""
        # Create a mock SkyCookerConnection instance
        mac = "AA:BB:CC:DD:EE:FF"
        key = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
        skycooker = SkyCookerConnection(mac, key, persistent=True, model="RMC-M40S")
        
        # New status data to parse: 55D40605006400230023010100000000000000AA
        # Clean data (without header/footer): 05 00 64 00 23 00 23 01 01 00 00 00 00 00 00 00
        test_status_data = bytes([0x05, 0x00, 0x64, 0x00, 0x23, 0x00, 0x23, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        skycooker.command = AsyncMock(return_value=test_status_data)
        
        # Call get_status
        status = await skycooker.get_status()
        
        # Print all parsed values
        print(f"Parsed status values:")
        print(f"  mode: {status.mode}")
        print(f"  subprog: {status.subprog}")
        print(f"  target_temp: {status.target_temp}")
        print(f"  target_boil_hours: {status.target_boil_hours}")
        print(f"  target_boil_minutes: {status.target_boil_minutes}")
        print(f"  target_delayed_start_hours: {status.target_delayed_start_hours}")
        print(f"  target_delayed_start_minutes: {status.target_delayed_start_minutes}")
        print(f"  auto_warm: {status.auto_warm}")
        print(f"  is_on: {status.is_on}")
        print(f"  sound_enabled: {status.sound_enabled}")

        # Verify the parsed status
        assert status.mode == 5
        assert status.subprog == 0
        assert status.target_temp == 100
        assert status.target_boil_hours == 0
        assert status.target_boil_minutes == 35
        assert status.target_delayed_start_hours == 0
        assert status.target_delayed_start_minutes == 35
        assert status.auto_warm == 1
        assert status.is_on == True
        assert status.sound_enabled == False

        print(f"\nStatus parsing test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])