# coding=utf-8
from nonebot import logger
from .tools import _kanonbot_plugin_config, kn_cache

_config = _kanonbot_plugin_config()
basepath = _config["basepath"]
command_starts = _config["command_starts"]
kn_config_data = None


async def auto_run_kanonbot_1hour():
    logger.debug(f"auto_run_1hour")
    return


async def auto_run_kanonbot_1day():
    logger.debug(f"auto_run_1day")
    return
