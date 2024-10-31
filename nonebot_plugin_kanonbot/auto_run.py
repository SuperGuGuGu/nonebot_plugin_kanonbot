import base64
import traceback
from nonebot import require, logger
import sqlite3
from .tools import _kanonbot_plugin_config, kn_cache

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler

_config = _kanonbot_plugin_config()
basepath = _config["basepath"]
command_starts = _config["command_starts"]
kn_config_data = None


@scheduler.scheduled_job("cron", hour="*/1", id="job_0")
async def suto_run_kanonbot_1hour_():
    try:
        await suto_run_kanonbot_1hour()
    except Exception as e:
        logger.error("定时任务运行异常：1hour")
        logger.error(e)
        logger.error(traceback.format_exc())


@scheduler.scheduled_job("cron", day="*/1", id="job_1")
async def suto_run_kanonbot_1day_():
    try:
        await suto_run_kanonbot_1day()
    except Exception as e:
        logger.error("定时任务运行异常：1day")
        logger.error(e)
        logger.error(traceback.format_exc())


async def suto_run_kanonbot_1hour():
    logger.debug(f"suto_run_1hour")


async def suto_run_kanonbot_1day():
    logger.debug(f"suto_run_1day")

    logger.debug("刷新违禁词")
    conn = sqlite3.connect(f"{basepath}db/content_compliance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM content_compliance WHERE state IS NOT 'Pass' AND audit IS 1")
    datas = cursor.fetchall()
    cursor.execute("SELECT * FROM blacklist WHERE state IS NOT 'Pass' AND audit IS 1")
    datas2 = cursor.fetchall()
    cursor.close()
    conn.close()

    kn_cache["content_compliance_list"] = {"part": [], "full": []}
    for data in datas:
        if data[2] == "Pass" or data[4] != 1:
            continue
        text = str(base64.b64decode(data[1]), "utf-8")
        if data[5] == 5:
            kn_cache["content_compliance_list"]["full"].append(text)
        else:
            kn_cache["content_compliance_list"]["part"].append(text)
    for data in datas2:
        if data[2] == "Pass" or data[4] != 1:
            continue
        text = data[1]
        if data[5] == 5:
            kn_cache["content_compliance_list"]["full"].append(text)
        else:
            kn_cache["content_compliance_list"]["part"].append(text)

    logger.success("刷新违禁词成功")

