#!/usr/local/bin/python3
# coding: utf-8

import calendar
import logging
import time
from abc import abstractmethod
from collections import namedtuple
from datetime import datetime, timedelta
from struct import pack, unpack

_LOGGER = logging.getLogger(__name__)


class SkyCooker():
    MODEL_0 = "MODEL_0"
    MODEL_1 = "MODEL_1"
    MODEL_2 = "MODEL_2"
    MODEL_3 = "MODEL_3"
    MODEL_4 = "MODEL_4"
    MODEL_5 = "MODEL_5"
    MODEL_6 = "MODEL_6"
    MODEL_7 = "MODEL_7"

    MODEL_TYPE = {
        "RMC-M40S": MODEL_3,
        "RMC-M42S": MODEL_3,
        "RMC-M92S": MODEL_6,
        "RMC-M92S-A": MODEL_6,
        "RMC-M92S-C": MODEL_6,
        "RMC-M92S-E": MODEL_6,
        "RMC-M222S": MODEL_7,
        "RMC-M222S-A": MODEL_7,
        "RMC-M223S": MODEL_7,
        "RMC-M223S-E": MODEL_7,
        "RMC-M224S": MODEL_7,
        "RFS-KMC001": MODEL_7,
        "RMC-M225S": MODEL_7,
        "RMC-M225S-E": MODEL_7,
        "RMC-M226S": MODEL_7,
        "RMC-M226S-E": MODEL_7,
        "JK-MC501": MODEL_7,
        "NK-MC10": MODEL_7,
        "RMC-M227S": MODEL_7,
        "RFS-KMC004": MODEL_7,
        "RMC-M800S": MODEL_0,
        "RMC-M903S": MODEL_5,
        "RFS-KMC005": MODEL_5,
        "RMC-961S": MODEL_4,
        "RMC-CBD100S": MODEL_1,
        "RMC-CBF390S": MODEL_2,
    }

    COMMAND_GET_VERSION = 0x01
    COMMAND_TURN_ON = 0x03
    COMMAND_TURN_OFF = 0x04
    COMMAND_SET_MAIN_MODE = 0x05
    COMMAND_GET_STATUS = 0x06
    COMMAND_SYNC_TIME = 0x6E
    COMMAND_GET_TIME = 0x6F
    COMMAND_AUTH = 0xFF

    Status = namedtuple("Status", ["mode", "target_temp", "sound_enabled", "current_temp",
        "color_interval", "parental_control", "is_on", "error_code", "boil_time"])

    def __init__(self, model):
        _LOGGER.info(f"Multicooker model: {model}")
        self.model = model
        self.model_code = self.get_model_code(model)
        if not self.model_code:
            raise SkyCookerError("Unknown multicooker model")

    @staticmethod
    def get_model_code(model):
        if model in SkyCooker.MODEL_TYPE:
            return SkyCooker.MODEL_TYPE[model]
        if model.endswith("-E"):
            return SkyCooker.MODEL_TYPE.get(model[:-2], None)
        return None

    @abstractmethod
    async def command(self, command, params=[]):
        pass

    async def auth(self, key):
        r = await self.command(SkyCooker.COMMAND_AUTH, key)
        ok = r[0] != 0
        _LOGGER.debug(f"Auth: ok={ok}")
        return ok

    async def get_version(self):
        r = await self.command(SkyCooker.COMMAND_GET_VERSION)
        major, minor = unpack("BB", r)
        ver = f"{major}.{minor}"
        _LOGGER.debug(f"Version: {ver}")
        return (major, minor)

    async def turn_on(self):
        r = await self.command(SkyCooker.COMMAND_TURN_ON)
        if r[0] != 1: raise SkyCookerError("can't turn on")
        _LOGGER.debug(f"Turned on")

    async def turn_off(self):
        r = await self.command(SkyCooker.COMMAND_TURN_OFF)
        if r[0] != 1: raise SkyCookerError("can't turn off")
        _LOGGER.debug(f"Turned off")

    async def set_main_mode(self, mode, target_temp=0, boil_time=0):
        data = pack("BxBxxxxxxxxxxBxx", int(mode), int(target_temp), int(0x80 + boil_time))
        r = await self.command(SkyCooker.COMMAND_SET_MAIN_MODE, data)
        if r[0] != 1: raise SkyCookerError("can't set mode")
        _LOGGER.debug(f"Mode set: mode={mode}, target_temp={target_temp}, boil_time={boil_time}")

    async def get_status(self):
        r = await self.command(SkyCooker.COMMAND_GET_STATUS)
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
        r = await self.command(SkyCooker.COMMAND_SYNC_TIME, data)
        if r[0] != 0: raise SkyCookerError("can't sync time")
        _LOGGER.debug(f"Writed time={now} ({datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")

    async def get_time(self):
        r = await self.command(SkyCooker.COMMAND_GET_TIME)
        t, offset = unpack("<ii", r)
        _LOGGER.debug(f"time={t} ({datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')}), offset={offset} (GMT{offset/60/60:+.2f})")
        return t, offset


class SkyCookerError(Exception):
    pass