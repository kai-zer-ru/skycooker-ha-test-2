#!/usr/local/bin/python3
# coding: utf-8

import calendar
import logging
import struct
import time
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from struct import pack, unpack

from .const import *

_LOGGER = logging.getLogger(__name__)


class SkyCooker(ABC):
    Status = namedtuple("Status", ["mode", "subprog", "target_temp", "hours", "minutes",
        "dhours", "dminutes", "auto_warm", "is_on", "sound_enabled",
        "parental_control", "error_code", "boil_time"])

    def __init__(self, model):
        _LOGGER.info(f"SkyCooker model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            raise SkyCookerError("Unknown SkyCooker model")

    @staticmethod
    def get_model_code(model):
        if model in MODELS:
            return MODELS[model]
        if model.endswith("-E"):
            return MODELS.get(model[:-2], None)
        return None

    @abstractmethod
    async def command(self, command, params=None):
        pass

    async def auth(self, key):
        r = await self.command(COMMAND_AUTH, key)
        ok = r[0] != 0
        _LOGGER.debug(f"Auth: ok={ok}")
        return ok

    async def get_version(self):
        r = await self.command(COMMAND_GET_VERSION)
        major, minor = unpack("BB", r)
        ver = f"{major}.{minor}"
        _LOGGER.debug(f"Version: {ver}")
        return ver

    async def turn_on(self):
        r = await self.command(COMMAND_TURN_ON)
        if r[0] != 1: raise SkyCookerError("can't turn on")
        _LOGGER.debug(f"Turned on")

    async def turn_off(self):
        r = await self.command(COMMAND_TURN_OFF)
        if r[0] != 1: raise SkyCookerError("can't turn off")
        _LOGGER.debug(f"Turned off")

    async def select_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0, bit_flags=0):
        # В текущей реализации битовые флаги берутся из MODE_DATA
        # Для MODEL_3 битовые флаги не добавляются
        # В будущем, когда будет понятно, как использовать битовые флаги, этот код будет обновлен
        if self.model_code == MODEL_3:
            # bit_flags = 1 # Автоподогрев (1 - включен, 0 выключен)
            data = pack("BBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat))
        else:
            mode_data = MODE_DATA.get(self.model_code, [])
            if mode < len(mode_data) and bit_flags == 0:
                bit_flags = mode_data[mode][3]
            data = pack("BBBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat), int(bit_flags))

        _LOGGER.debug(f"📤 Отправка команды SELECT_MODE (0x09) с данными: {data.hex().upper()}")
        _LOGGER.debug(f"   Параметры: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")

        try:
            r = await self.command(COMMAND_SELECT_MODE, list(data))
            _LOGGER.debug(f"📥 Получен ответ на SELECT_MODE: {r.hex().upper() if r else 'None'}")
            if r and len(r) > 0:
                _LOGGER.debug(f"   Первый байт ответа: {r[0]} (ожидалось 1 для успеха)")
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error(f"❌ Ошибка выбора режима: устройство вернуло код ошибки {r[0]}")
                raise SkyCookerError(f"Ошибка выбора режима: код {r[0]}")
            _LOGGER.debug(f"✅ Режим успешно выбран: mode={mode}")
        except Exception as e:
            _LOGGER.error(f"❌ Исключение при выборе режима: {e}")
            raise SkyCookerError(f"Исключение при выборе режима: {e}")

    async def set_main_mode(self, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0, bit_flags=0):
        # В текущей реализации битовые флаги берутся из MODE_DATA
        # Для MODEL_3 битовые флаги не добавляются
        # В будущем, когда будет понятно, как использовать битовые флаги, этот код будет обновлен
        if self.model_code == MODEL_3:
            # bit_flags = 1 # Автоподогрев (1 - включен, 0 выключен)
            data = pack("BBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat))
        else:
            mode_data = MODE_DATA.get(self.model_code, [])
            if mode < len(mode_data) and bit_flags == 0:
                bit_flags = mode_data[mode][3]
            data = pack("BBBBBBBBB", int(mode), int(subprog), int(target_temp), int(hours), int(minutes), int(dhours), int(dminutes), int(heat), int(bit_flags))

        _LOGGER.debug(f"📤 Отправка команды SET_MAIN_MODE (0x05) с данными: {data.hex().upper()}")
        _LOGGER.debug(f"   Параметры: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")

        try:
            r = await self.command(COMMAND_SET_MAIN_MODE, list(data))
            _LOGGER.debug(f"📥 Получен ответ на SET_MAIN_MODE: {r.hex().upper() if r else 'None'}")
            if r and len(r) > 0:
                _LOGGER.debug(f"   Первый байт ответа: {r[0]} (ожидалось 1 для успеха)")
            # Accept both success code (0x01) and status updates as success
            if r and r[0] != 1 and len(r) != 1:
                _LOGGER.error(f"❌ Ошибка установки режима: устройство вернуло код ошибки {r[0]}")
                raise SkyCookerError(f"Ошибка установки режима: код {r[0]}")
            _LOGGER.debug(f"✅ Режим успешно установлен: mode={mode}")
        except Exception as e:
            _LOGGER.error(f"❌ Исключение при установке режима: {e}")
            raise SkyCookerError(f"Исключение при установке режима: {e}")

    async def get_status(self):
        r = await self.command(COMMAND_GET_STATUS)
        _LOGGER.debug(f"Raw status data: {r.hex().upper()}, length: {len(r)}")
        if len(r) < 16:
            _LOGGER.error(f"❌ Ошибка: получено {len(r)} байт вместо ожидаемых 16")
            raise SkyCookerError(f"Некорректный размер данных статуса: {len(r)} байт")
        try:
            # Parse the 16-byte status response according to the new format
            # Format: mode(1), subprog(1), target_temp(1), hours(1), minutes(1),
            #         dhours(1), dminutes(1), auto_warm(1), status(1), ...
            mode = r[0]
            subprog = r[1]
            target_temp = r[2]
            hours = r[3]
            minutes = r[4]
            dhours = r[5]
            dminutes = r[6]
            auto_warm = r[7]
            is_on = r[8] != 0
            sound_enabled = r[9] != 0
            
            # Calculate boil_time from remaining time
            boil_time = dhours * 60 + dminutes
            
            status = SkyCooker.Status(
                mode=mode,
                subprog=subprog,
                target_temp=target_temp,
                hours=hours,
                minutes=minutes,
                dhours=dhours,
                dminutes=dminutes,
                auto_warm=auto_warm,
                is_on=is_on,
                sound_enabled=sound_enabled,
                parental_control=False,
                error_code=0,
                boil_time=boil_time
            )
        except Exception as e:
            _LOGGER.error(f"❌ Ошибка распаковки статуса: {e}")
            raise SkyCookerError(f"Ошибка распаковки статуса: {e}")
        
        _LOGGER.debug(f"Status: mode={status.mode}, subprog={status.subprog}, is_on={status.is_on}, "+
                     f"target_temp={status.target_temp}, hours={status.hours}, minutes={status.minutes}, "+
                     f"dhours={status.dhours}, dminutes={status.dminutes}, "+
                     f"auto_warm={status.auto_warm}, sound_enabled={status.sound_enabled}, boil_time={status.boil_time}")
        return status

    async def sync_time(self):
        try:
            t = time.localtime()
            offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
            now = int(time.time())
            data = pack("<ii", now, offset)
            _LOGGER.debug(f"🕒 Синхронизация времени: time={now}, offset={offset}")
            r = await self.command(COMMAND_SYNC_TIME, data)
            if r[0] != 0:
                _LOGGER.warning(f"⚠️  Не удалось синхронизировать время. Код ответа: {r[0]}")
                return
            _LOGGER.debug(f"✅ Время синхронизировано: {now} ({datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        except Exception as e:
            _LOGGER.warning(f"⚠️  Ошибка синхронизации времени: {e}")

    async def get_time(self):
        r = await self.command(COMMAND_GET_TIME)
        t, offset = unpack("<ii", r)
        _LOGGER.debug(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        return t, offset


class SkyCookerError(Exception):
    pass