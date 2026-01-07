#!/usr/local/bin/python3
# coding: utf-8

import calendar
import logging
import time
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime
from struct import pack, unpack

from .const import *

_LOGGER = logging.getLogger(__name__)


class SkyCooker(ABC):
    Status = namedtuple("Status", ["mode", "target_temp", "sound_enabled", "current_temp",
        "color_interval", "parental_control", "is_on", "error_code", "boil_time"])

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

    async def set_main_mode(self, mode, target_temp=0, boil_time=0):
        data = pack("BxBxxxxxxxxxxBxx", int(mode), int(target_temp), int(0x80 + boil_time))
        r = await self.command(COMMAND_SET_MAIN_MODE, data)
        if r[0] != 1: raise SkyCookerError("can't set mode")
        _LOGGER.debug(f"Mode set: mode={mode}, target_temp={target_temp}, boil_time={boil_time}")

    async def get_status(self):
        r = await self.command(COMMAND_GET_STATUS)
        status = SkyCooker.Status(*unpack("<BxBx?BB??BxxxBxx", r))
        status = status._replace(
            boil_time = status.boil_time - 0x80,
            error_code=None if status.error_code == 0 else status.error_code
        )
        _LOGGER.debug(f"Status: mode={status.mode}, is_on={status.is_on}, "+
                     f"target_temp={status.target_temp}, current_temp={status.current_temp}, sound_enabled={status.sound_enabled}, "+
                     f"color_interval={status.color_interval}, boil_time={status.boil_time}")
        return status

    async def sync_time(self):
        t = time.localtime()
        offset = calendar.timegm(t) - calendar.timegm(time.gmtime(time.mktime(t)))
        now = int(time.time())
        data = pack("<ii", now, offset)
        r = await self.command(COMMAND_SYNC_TIME, data)
        if r[0] != 0: raise SkyCookerError("can't sync time")
        _LOGGER.debug(f"Written time={now} ({datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")

    async def get_time(self):
        r = await self.command(COMMAND_GET_TIME)
        t, offset = unpack("<ii", r)
        _LOGGER.debug(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        return t, offset


class SkyCookerError(Exception):
    pass