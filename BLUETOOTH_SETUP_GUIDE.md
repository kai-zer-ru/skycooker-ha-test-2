# Руководство по настройке Bluetooth для SkyCoocker

## Проблема

Если вы видите ошибки типа:
```
Bluetooth адаптер исчерпал лимит соединений
No backend with an available connection slot
The proxy/adapter is out of connection slots
```

Это означает, что Bluetooth интеграция в Home Assistant не настроена правильно.

## Решение

### 1. Проверка Bluetooth интеграции

Убедитесь, что Bluetooth интеграция включена в Home Assistant:

1. Перейдите в **Настройки → Устройства и службы**
2. Найдите **Bluetooth** в списке интеграций
3. Если её нет, добавьте через **Добавить интеграцию → Bluetooth**

### 2. Настройка Bluetooth адаптера

#### Вариант A: Встроенный Bluetooth адаптер (рекомендуется для Raspberry Pi)

1. Убедитесь, что Bluetooth включен в системе:
   ```bash
   sudo systemctl enable bluetooth
   sudo systemctl start bluetooth
   ```

2. Проверьте, что адаптер обнаружен:
   ```bash
   hciconfig -a
   ```

3. Убедитесь, что Home Assistant имеет права на Bluetooth:
   ```bash
   sudo usermod -aG bluetooth homeassistant
   sudo systemctl restart home-assistant
   ```

#### Вариант B: Внешний Bluetooth адаптер

1. Подключите USB Bluetooth адаптер (рекомендуется на чипе CSR или Broadcom)
2. Проверьте, что он обнаружен:
   ```bash
   lsusb
   hciconfig -a
   ```

3. Убедитесь, что Home Assistant имеет права на устройство

### 3. Настройка Bluetooth прокси (рекомендуется)

Для стабильной работы используйте ESPHome Bluetooth прокси:

1. Установите ESPHome добавку в Home Assistant
2. Создайте новое устройство с конфигурацией:
   ```yaml
   esp32:
     board: esp32dev
     framework:
       type: arduino
   
   # Enable logging
   logger:
   
   # Enable Home Assistant API
   api:
     encryption:
       key: "YOUR_ENCRYPTION_KEY"
   
   ota:
     password: "YOUR_OTA_PASSWORD"
   
   wifi:
     ssid: !secret wifi_ssid
     password: !secret wifi_password
   
   # Enable Bluetooth Proxy
   bluetooth_proxy:
     active: true
   ```

3. Загрузите прошивку на ESP32 устройство
4. Разместите прокси рядом с мультиваркой (в пределах 5 метров)

### 4. Проверка Bluetooth в Home Assistant

1. Перейдите в **Настройки → Устройства и службы → Bluetooth**
2. Убедитесь, что ваш адаптер или прокси отображается в списке
3. Проверьте, что устройство доступно для сканирования

### 5. Настройка SkyCoocker интеграции

1. Убедитесь, что мультиварка включена и находится в режиме сопряжения
2. В настройках интеграции SkyCoocker:
   - Укажите правильный MAC адрес (например, `DA:D8:9F:9E:0B:4C`)
   - Используйте стандартный ключ `0000000000000000` для RMC-M40S
   - Убедитесь, что мультиварка находится рядом с Bluetooth адаптером/прокси

### 6. Диагностика проблем

Если проблемы сохраняются:

1. Проверьте логи Home Assistant:
   ```bash
   journalctl -u home-assistant -f
   ```

2. Ищите ошибки типа:
   - `Bluetooth adapter not found`
   - `No available connection slots`
   - `Device not reachable`

3. Попробуйте перезагрузить Bluetooth службу:
   ```bash
   sudo systemctl restart bluetooth
   sudo systemctl restart home-assistant
   ```

4. Проверьте, что нет других устройств, занимающих все слоты Bluetooth

## Дополнительные ресурсы

- [Официальная документация ESPHome Bluetooth Proxy](https://esphome.github.io/bluetooth-proxies/)
- [Home Assistant Bluetooth интеграция](https://www.home-assistant.io/integrations/bluetooth/)
- [Устранение неполадок Bluetooth](https://www.home-assistant.io/integrations/bluetooth/#troubleshooting)

## Важно

- Bluetooth адаптер должен поддерживать BLE (Bluetooth Low Energy)
- Мультиварка должна находиться в пределах 5-10 метров от адаптера
- Убедитесь, что нет помех от других Bluetooth/WiFi устройств
- Для стабильной работы рекомендуется использовать выделенный Bluetooth прокси