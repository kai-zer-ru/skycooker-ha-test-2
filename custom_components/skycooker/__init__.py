#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import time
from datetime import (timedelta)
from enum import Enum

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_MAC,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .btle import BTLEConnection

DOMAIN = "skycooker"
SUPPORTED_DOMAINS = [
    "sensor",
    "switch",
    "number",
    "select"
]
SIGNAL_UPDATE_DATA = 'skycooker_update'

CONF_USE_BACKLIGHT = 'use_backlight'

CONF_MIN_TEMP = 35
CONF_MAX_TEMP = 200

STATUS_OFF = '00'
STATUS_ON = '02'

COOKER_STATUS_PROGRAM = '01'
COOKER_STATUS_KEEP_WARM = '04'
COOKER_STATUS_DELAYED_START = '05'

MODE_MANUAL = '00'
MODE_AUTO = '01'

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the SkyCooker component."""
    # Проверка минимальной версии HomeAssistant
    from homeassistant.const import __version__ as HA_VERSION
    from packaging import version
    
    min_ha_version = "2025.12.5"
    if version.parse(HA_VERSION) < version.parse(min_ha_version):
        _LOGGER.error("❌ Требуется HomeAssistant версии %s или выше. У вас установлена версия %s",
                     min_ha_version, HA_VERSION)
        return False
    
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.info("✅ SkyCooker интеграция загружена. Версия HA: %s", HA_VERSION)
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    config = config_entry.data
    mac = str(config.get(CONF_MAC)).upper()
    password = config.get(CONF_PASSWORD)
    scan_delta = timedelta(seconds=config.get(CONF_SCAN_INTERVAL))
    backlight = config.get(CONF_USE_BACKLIGHT)

    cooker = SkyCooker(hass, mac, password, backlight)
    await cooker.setNameAndType()

    try:
        _LOGGER.info("🔧 Попытка подключения к мультиварке %s...", mac)
        await cooker.firstConnect()
        _LOGGER.info("✅ Успешное подключение к мультиварке %s", mac)
    except BaseException as ex:
        _LOGGER.error("❌ Ошибка подключения к мультиварке %s: %s", mac, ex)
        _LOGGER.exception(ex)
        return False

    hass.data[DOMAIN][config_entry.entry_id] = cooker

    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={
            (DOMAIN, config_entry.unique_id)
        },
        connections={
            (dr.CONNECTION_NETWORK_MAC, mac)
        },
        manufacturer="Redmond",
        model=cooker._name,
        name=cooker._name,
        sw_version=cooker._firmware_ver
    )

    async_track_time_interval(hass, hass.data[DOMAIN][config_entry.entry_id].update, scan_delta)

    for component in SUPPORTED_DOMAINS:
        hass.async_create_task(hass.config_entries.async_forward_entry_setup(config_entry, component))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    try:
        for component in SUPPORTED_DOMAINS:
            await hass.config_entries.async_forward_entry_unload(entry, component)
        hass.data[DOMAIN].pop(entry.entry_id)
    except ValueError:
        pass
    return True


class RedmondCommand(Enum):
    AUTH = 'ff'
    VERSION = '01'
    RUN_CURRENT_MODE = '03'
    STOP_CURRENT_MODE = '04'
    SET_STATUS_MODE = '05'
    GET_STATUS_MODE = '06'
    SET_DELAY = '08'
    SET_COLOR = '32'
    GET_COLOR = '33'
    SET_BACKLIGHT_MODE = '37'
    SET_SOUND = '3c'
    SET_LOCK_BUTTONS = '3e'
    GET_STATISTICS_WATT = '47'
    GET_STARTS_COUNT = '50'
    SET_TIME = '6e'
    SET_IONIZATION = '1b'
    SET_TEMPERATURE = '0b'
    SET_TIME_COOKER = '0c'

    def __str__(self):
        return str(self.value)


class SkyCooker:
    def __init__(self, hass, addr, key, backlight):
        self.hass = hass
        self._type = None
        self._name = None
        self._mac = addr
        self._key = key
        self._use_backlight = backlight
        self._tgtemp = CONF_MIN_TEMP
        self._temp = 0
        self._Watts = 0
        self._alltime = 0
        self._times = 0
        self._firmware_ver = None
        self._time_upd = '00:00'
        self._nightlight_brightness = 255
        self._rgb1 = (0, 0, 255)
        self._rgb2 = (255, 0, 0)
        self._mode = MODE_MANUAL
        self._status = STATUS_OFF
        self._prog = '00'
        self._sprog = '00'
        self._ph = 0
        self._pm = 0
        self._th = 0
        self._tm = 0
        self._ion = '00'
        self._conf_sound_on = False
        self._auth = False
        self._conn = BTLEConnection(self.hass, self._mac, self._key)
        self._available = False
        
        # Счетчики для отслеживания успешности команд
        self._total_commands = 0
        self._successful_commands = 0
        self._success_rate = 100.0
        
        self.initCallbacks()

    async def setNameAndType(self):
        _LOGGER.debug("🔍 Определение типа устройства и имени...")
        await self._conn.setNameAndType()
        self._type = self._conn._type
        self._name = self._conn._name
        self._available = self._conn._available
        _LOGGER.info("🏷️  Устройство: %s, Тип: %s, Доступность: %s", self._name, self._type, self._available)

    def initCallbacks(self):
        self._conn.setConnectAfter(lambda: self.sendAuth(self._conn))
        self._conn.setCallback(RedmondCommand.AUTH, self.responseAuth)
        self._conn.setCallback(RedmondCommand.VERSION, self.responseGetVersion)
        self._conn.setCallback(RedmondCommand.GET_STATUS_MODE, self.responseStatus)
        self._conn.setCallback(RedmondCommand.GET_STATISTICS_WATT, self.responseStat)
        self._conn.setCallback(RedmondCommand.GET_STARTS_COUNT, self.responseStat)

    def hexToRgb(self, hexa: str):
        return tuple(int(hexa[i:i + 2], 16) for i in (0, 2, 4))

    def rgbToHex(self, rgb):
        return '%02x%02x%02x' % rgb

    @staticmethod
    def hexToDec(hexChr: str) -> int:
        return BTLEConnection.hexToDec(hexChr)

    @staticmethod
    def decToHex(num: int) -> str:
        return BTLEConnection.decToHex(num)

    def getHexNextIter(self) -> str:
        return self._conn.getHexNextIter()

    async def sendAuth(self, conn):
        self._type = conn._type
        self._name = conn._name

        await conn.sendRequest(RedmondCommand.AUTH, self._key)
        await asyncio.sleep(1.5)

        if self._auth is False:
            raise Exception('error auth')

        return True

    def responseAuth(self, arrayHex):
        if self._type == 5 and arrayHex[3] == '01':
            self._auth = True
        else:
            self._auth = False

        return self._auth

    async def sendGetVersion(self, conn):
        return await conn.sendRequest(RedmondCommand.VERSION)

    def responseGetVersion(self, arrHex):
        self._firmware_ver = str(self.hexToDec(arrHex[3])) + '.' + str(self.hexToDec(arrHex[4]))

    async def sendOn(self, conn):
        if self._type == 5:
            return await conn.sendRequest(RedmondCommand.RUN_CURRENT_MODE)
        return False

    async def sendOff(self, conn):
        return await conn.sendRequest(RedmondCommand.STOP_CURRENT_MODE)

    async def sendSyncDateTime(self, conn):
        if self._type == 5:
            now = self.decToHex(int(time.time()))
            offset = self.decToHex(time.timezone * -1)
            return await conn.sendRequest(RedmondCommand.SET_TIME, now + offset + '0000')
        return False

    async def sendStat(self, conn):
        if await conn.sendRequest(RedmondCommand.GET_STATISTICS_WATT, '00'):
            if await conn.sendRequest(RedmondCommand.GET_STARTS_COUNT, '00'):
                return True
        return False

    def responseStat(self, arrHex):
        if arrHex[2] == '47':
            self._Watts = self.hexToDec(str(arrHex[9] + arrHex[10] + arrHex[11]))
            self._alltime = round(self._Watts / 2200, 1)
        elif arrHex[2] == '50':
            self._times = self.hexToDec(str(arrHex[6] + arrHex[7]))

    async def sendStatus(self, conn):
        if await conn.sendRequest(RedmondCommand.GET_STATUS_MODE):
            return True
        return False

    def responseStatus(self, arrHex):
        if self._type == 5:
            self._prog = arrHex[3]
            self._sprog = arrHex[4]
            self._temp = self.hexToDec(arrHex[5])

            if arrHex[5] != '00':
                self._tgtemp = self.hexToDec(arrHex[5])

            self._ph = self.hexToDec(arrHex[6])
            self._pm = self.hexToDec(arrHex[7])
            self._th = self.hexToDec(arrHex[8])
            self._tm = self.hexToDec(arrHex[9])
            self._mode = arrHex[10]
            self._status = arrHex[11]

        self._time_upd = time.strftime("%H:%M")
        async_dispatcher_send(self.hass, SIGNAL_UPDATE_DATA)

    async def sendModeCook(self, conn, prog, sprog, temp, hours, minutes, dhours, dminutes, heat):
        if self._type == 5:
            str2b = prog + sprog + temp + hours + minutes + dhours + dminutes + heat
            return await conn.sendRequest(RedmondCommand.SET_STATUS_MODE, str2b)
        else:
            return True

    async def sendKeepWarmTime(self, conn, hours, minutes):
        """Отправка команды установки времени поддержания температуры."""
        if self._type == 5:
            # Команда для установки времени поддержания температуры
            # Формат: часы + минуты
            return await conn.sendRequest(RedmondCommand.SET_TIME_COOKER, hours + minutes)
        else:
            return True

    async def sendTimerCook(self, conn, hours, minutes):
        if self._type == 5:
            return await conn.sendRequest(RedmondCommand.SET_TIME_COOKER, hours + minutes)
        else:
            return True

    async def sendTemperature(self, conn, temp: str):
        if self._type == 5:
            return await conn.sendRequest(RedmondCommand.SET_TEMPERATURE, temp)
        else:
            return True

    async def modeOnCook(self, prog, sprog, temp, hours, minutes, dhours='00', dminutes='00', heat='01'):
        try:
            _LOGGER.info("🍲 Запуск программы приготовления: %s, Температура: %s°C, Время: %s:%s",
                        prog, temp, hours, minutes)
            async with self._conn as conn:
                if self._status != STATUS_OFF:
                    _LOGGER.debug("🔌 Мультиварка включена, выключаем перед запуском программы...")
                    await self.sendOff(conn)

                if await self.sendModeCook(conn, prog, sprog, temp, hours, minutes, dhours, dminutes, heat):
                    _LOGGER.debug("⚙️  Отправка команды запуска программы...")
                    if await self.sendOn(conn):
                        _LOGGER.debug("📡 Запрос состояния после запуска...")
                        if await self.sendStatus(conn):
                            _LOGGER.info("✅ Программа приготовления успешно запущена")
                            return True
        except Exception as e:
            _LOGGER.error("❌ Ошибка запуска программы приготовления: %s", e)

        return False

    async def modeTempCook(self, temp):
        try:
            _LOGGER.info("🌡️  Установка температуры: %s°C", temp)
            async with self._conn as conn:
                if await self.sendTemperature(conn, temp) and await self.sendStatus(conn):
                    _LOGGER.info("✅ Температура успешно установлена")
                    return True
        except Exception as e:
            _LOGGER.error("❌ Ошибка установки температуры: %s", e)

        return False

    async def modeTimeCook(self, hours, minutes):
        try:
            async with self._conn as conn:
                if await self.sendTimerCook(conn, hours, minutes) and await self.sendStatus(conn):
                    return True
        except:
            pass

        return False

    async def modeKeepWarmTime(self, hours, minutes):
        """Установка времени поддержания температуры после приготовления."""
        try:
            _LOGGER.info("⏰ Установка времени поддержания температуры: %s:%s", hours, minutes)
            async with self._conn as conn:
                if await self.sendKeepWarmTime(conn, hours, minutes) and await self.sendStatus(conn):
                    _LOGGER.info("✅ Время поддержания температуры успешно установлено")
                    return True
        except Exception as e:
            _LOGGER.error("❌ Ошибка установки времени поддержания температуры: %s", e)

        return False

    async def modeOff(self):
        try:
            _LOGGER.info("🔌 Выключение мультиварки...")
            async with self._conn as conn:
                if await self.sendOff(conn):
                    _LOGGER.debug("📡 Запрос состояния после выключения...")
                    if await self.sendStatus(conn):
                        _LOGGER.info("✅ Мультиварка успешно выключена")
                        return True
        except Exception as e:
            _LOGGER.error("❌ Ошибка выключения мультиварки: %s", e)

        return False

    async def setTemperatureHeat(self, temp: int = CONF_MIN_TEMP):
        temp = CONF_MIN_TEMP if temp < CONF_MIN_TEMP else temp
        temp = CONF_MAX_TEMP if temp > CONF_MAX_TEMP else temp
        self._tgtemp = temp

        try:
            async with self._conn as conn:
                if await self.sendTemperature(conn, self.decToHex(temp)):
                    return True
        except:
            pass

        return False

    async def update(self, now, **kwargs) -> bool:
        try:
            _LOGGER.debug("🔄 Обновление данных с мультиварки...")
            async with self._conn as conn:
                if await self.sendSyncDateTime(conn) and await self.sendStatus(conn) and await self.sendStat(conn):
                    _LOGGER.debug("📊 Данные успешно обновлены")
                    return True
        except Exception as e:
            _LOGGER.error("❌ Ошибка обновления данных: %s", e)

        return False

    def update_success_rate(self, success: bool):
        """Обновление процента успешных команд."""
        self._total_commands += 1
        if success:
            self._successful_commands += 1
        
        if self._total_commands > 0:
            self._success_rate = round((self._successful_commands / self._total_commands) * 100, 1)
        
        _LOGGER.debug("📈 Статистика команд: %s/%s (%.1f%%)",
                     self._successful_commands, self._total_commands, self._success_rate)

    async def firstConnect(self):
        _LOGGER.debug('FIRST CONNECT')

        async with self._conn as conn:
            if await self.sendGetVersion(conn):
                if await self.update(1):
                    return True

        self._available = False

        return False

    @property
    def success_rate(self):
        """Процент успешных команд."""
        return self._success_rate

    @property
    def total_commands(self):
        """Общее количество отправленных команд."""
        return self._total_commands

    @property
    def successful_commands(self):
        """Количество успешных команд."""
        return self._successful_commands