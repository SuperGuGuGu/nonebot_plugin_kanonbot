import asyncio
import base64
import json
import random
from nonebot import logger
import sqlite3
from .tools import _kanonbot_plugin_config, kn_cache

_config = _kanonbot_plugin_config()
basepath = _config["basepath"]
command_starts = _config["command_starts"]
kn_config_data = None


async def auto_run_kanonbot_1hour():
    logger.debug(f"auto_run_1hour")

    await asyncio.sleep(random.randint(5, 10))
    # 保存群员列表
    logger.debug("开始保存群员列表")
    path = f"{basepath}cache/channel_member_list.json"
    file = open(path, "r", encoding="UTF-8")
    channel_member_list: dict = json.loads(file.read())
    file.close()

    if "channel_member_list" not in kn_cache.keys():
        kn_cache["channel_member_list"] = channel_member_list
    else:
        for channel_id in kn_cache["channel_member_list"]:
            if channel_id not in channel_member_list.keys():
                channel_member_list[channel_id] = kn_cache["channel_member_list"][channel_id]
            else:
                channel_member_list[channel_id].update(kn_cache["channel_member_list"][channel_id])
        kn_cache["channel_member_list"] = channel_member_list

        file = open(path, "w", encoding="UTF-8")
        file.write(json.dumps(channel_member_list, ensure_ascii=False, indent=2))
        file.close()

    logger.success("保存群员列表成功")

    # 保存群数据列表
    logger.debug("开始保存群数据列表")
    path = f"{basepath}cache/channel_data.json"
    file = open(path, "r", encoding="UTF-8")
    channel_data: dict = json.loads(file.read())
    file.close()

    if "channel_data" not in kn_cache.keys():
        kn_cache["channel_data"] = channel_data
    else:
        for channel_id in kn_cache["channel_data"].keys():
            if channel_id not in channel_data.keys():
                channel_data[channel_id] = kn_cache["channel_data"][channel_id]
            else:
                if kn_cache["channel_data"][channel_id]["name"] is not None:
                    channel_data[channel_id]["name"] = kn_cache["channel_data"][channel_id]["name"]
        kn_cache["channel_data"] = channel_data

        file = open(path, "w", encoding="UTF-8")
        file.write(json.dumps(channel_data, ensure_ascii=False, indent=2))
        file.close()

        logger.debug("更新群id替换列表")
        channel_replace_data = {}
        for channel_id in kn_cache["channel_data"].keys():
            for channel_name in kn_cache["channel_data"][channel_id]["id_list"]:
                channel_replace_data[channel_name] = channel_id

    logger.success("保存群数据列表成功")


async def auto_run_kanonbot_1day():
    logger.debug(f"auto_run_1day")

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
