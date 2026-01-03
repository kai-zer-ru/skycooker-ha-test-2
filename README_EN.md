# SkyCooker - HomeAssistant Integration

Integration for managing Redmond RMC-M40S multicooker via Bluetooth in HomeAssistant.

## Features

- Power on/off control
- Cooking program selection and launch
- Temperature control
- Cooking time management
- Keep warm time management
- Current state display
- Current temperature display
- Usage statistics

## Supported Devices

- RMC-M40S
- RMC-M800S
- RMC-M223S
- RMC-M92S
- RMC-M92S-E

## Requirements

- HomeAssistant 2025.12.5 or newer
- Bluetooth adapter on the device running HomeAssistant
- Redmond RMC-M40S multicooker (or other supported model)

## Installation

### Through HACS (recommended)

1. Install HACS if it's not already installed
2. Go to HACS → Integrations
3. Click the "+" button in the bottom right corner
4. Find "SkyCooker" in the list of integrations
5. Click "Install"
6. Restart HomeAssistant
7. Go to Settings → Integrations
8. Click "Add Integration" and select "SkyCooker"
9. Follow the on-screen instructions

### Manually

1. Copy the `custom_components/skycooker` folder to the `custom_components` folder of your HomeAssistant
2. Restart HomeAssistant
3. Go to Settings → Integrations
4. Click "Add Integration" and select "SkyCooker"
5. Follow the on-screen instructions

## Configuration

### Through HomeAssistant Interface

1. Go to Settings → Integrations
2. Click "Add Integration"
3. Select "SkyCooker"
4. Enter your multicooker's MAC address
5. Enter password (16 characters in HEX format)
6. Configure scan interval (default 60 seconds)
7. Click "Confirm"

### Pairing Mode

Before adding the integration, make sure your multicooker is in pairing mode:
1. Turn off the multicooker
2. Hold the power button for several seconds until the indicators start blinking
3. Add the integration in HomeAssistant

## Cooking Programs

The integration supports the following programs:

- Rice
- Slow cooking
- Pilaf
- Frying vegetables
- Frying fish
- Frying meat
- Stewing vegetables
- Stewing fish
- Stewing meat
- Pasta
- Milk porridge
- Soup
- Yogurt
- Baking
- Steaming (vegetables, fish, meat)
- Hot

## Entities

The integration creates the following entities:

### Sensors
- `sensor.skycooker_status` - Multicooker status
- `sensor.skycooker_mode` - Operating mode
- `sensor.skycooker_temperature` - Current temperature
- `sensor.skycooker_target_temperature` - Target temperature
- `sensor.skycooker_program_hours` - Program hours
- `sensor.skycooker_program_minutes` - Program minutes
- `sensor.skycooker_timer_hours` - Timer hours
- `sensor.skycooker_timer_minutes` - Timer minutes
- `sensor.skycooker_power_consumption` - Power consumption
- `sensor.skycooker_working_time` - Working time
- `sensor.skycooker_starts_count` - Number of starts
- `sensor.skycooker_last_update` - Last update time

### Switches
- `switch.skycooker_power` - Multicooker power
- `switch.skycooker_program` - Program start

### Number Entities
- `number.skycooker_target_temperature` - Target temperature control
- `number.skycooker_program_hours` - Program hours control
- `number.skycooker_program_minutes` - Program minutes control
- `number.skycooker_timer_hours` - Timer hours control
- `number.skycooker_timer_minutes` - Timer minutes control

### Program Selection
- `select.skycooker_program` - Cooking program selection

## Automation

Example automation to start rice cooking:

```yaml
automation:
  - alias: "Start rice cooking"
    trigger:
      - platform: state
        entity_id: switch.skycooker_power
        to: 'on'
    action:
      - service: select.select_option
        target:
          entity_id: select.skycooker_program
        data:
          option: rice
```

## Support

If you have any problems or questions:
1. Check HomeAssistant logs for errors
2. Make sure the Bluetooth adapter is working correctly
3. Make sure the multicooker is in pairing mode
4. Create an issue in the repository: https://github.com/kai-zer-ru/skycooker-ha-test-2/issues

## License

This project is licensed under the MIT License.

## Acknowledgments

Thanks to the developers of existing integrations for inspiration and code examples:
- https://github.com/XNicON/hassio-r4s
- https://github.com/mavrikkk/ha_kettler
- https://github.com/ClusterM/skykettle-ha

## Русская версия

[Читать документацию на русском](README.md)