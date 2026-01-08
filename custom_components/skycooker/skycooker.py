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
    Status = namedtuple("Status", ["mode", "target_temp", "sound_enabled", "current_temp",
        "parental_control", "is_on", "error_code", "boil_time"])

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
        return major, minor

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

        r = await self.command(COMMAND_SELECT_MODE, list(data))
        if r[0] != 1: raise SkyCookerError("can't select mode")
        _LOGGER.debug(f"Mode selected: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")

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

        r = await self.command(COMMAND_SET_MAIN_MODE, list(data))
        if r[0] != 1: raise SkyCookerError("can't set mode")
        _LOGGER.debug(f"Mode set: mode={mode}, subprog={subprog}, target_temp={target_temp}, hours={hours}, minutes={minutes}, dhours={dhours}, dminutes={dminutes}, heat={heat}, bit_flags={bit_flags}")

    async def get_status(self):
        r = await self.command(COMMAND_GET_STATUS)
        _LOGGER.debug(f"Raw status data: {r.hex().upper()}, length: {len(r)}")
        if len(r) < 15:
            _LOGGER.error(f"❌ Ошибка: получено {len(r)} байт вместо ожидаемых 15")
            raise SkyCookerError(f"Некорректный размер данных статуса: {len(r)} байт")
        try:
            status = SkyCooker.Status(*unpack("<BxBx?BB??BxxBxx", r))
        except struct.error as e:
            _LOGGER.error(f"❌ Ошибка распаковки статуса: {e}")
            raise SkyCookerError(f"Ошибка распаковки статуса: {e}")
        # Calculate boil_time, ensuring it's not negative
        boil_time = status.boil_time - 0x80
        if boil_time < 0:
            boil_time = 0
        status = status._replace(
            boil_time = boil_time,
            error_code=None if status.error_code == 0 else status.error_code
        )
        _LOGGER.debug(f"Status: mode={status.mode}, is_on={status.is_on}, "+
                     f"target_temp={status.target_temp}, current_temp={status.current_temp}, sound_enabled={status.sound_enabled}, "+
                     f"boil_time={status.boil_time}")
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