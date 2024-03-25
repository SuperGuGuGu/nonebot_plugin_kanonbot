# coding=utf-8
import asyncio
import sqlite3
import sys
from nonebot import logger

sys.path.append("..")
from nonebot_plugin_kanonbot.plugins import plugin_config
from nonebot_plugin_kanonbot.bot_run import botrun
from nonebot_plugin_kanonbot.tools import get_command, kn_config, get_file_path
from nonebot_plugin_kanonbot.config import command_list

# #########################
# 无需运行bot就能测试插件的小工具
# 方便进行插件调试
# 如果填写的配置的路径开头为"./"，会在此文件所在文件夹生成一份新配置文件夹
# #########################



async def run_plugin():
    plugin_return_data = plugin_config(
        command="菜单",
        command2="命令",
        channel_id="test_channel",
        guild_id="帮助",
    )
    logger.info(plugin_return_data)
    return plugin_return_data


async def run_kanonbot():
    msg = "水母箱"

    commands = get_command(msg)
    command = commands[0]
    commandlist = command_list()
    commandname = "None"
    basepath = "./Kanonbot/"
    channel_id = "test_channel_id"
    run = False
    # 识别对话
    if run is False:
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "gameinglist" not in tables:
            cursor.execute(
                'CREATE TABLE gameinglist (channelid VARCHAR (10) PRIMARY KEY, gamename VARCHAR (10), '
                'lasttime VARCHAR (10), gameing BOOLEAN (10), gamedata VARCHAR (10))')
        cursor.execute(f'select * from gameinglist where channelid = "{channel_id}"')
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        logger.debug(f"该群正在进行的聊天{data}")
        if data is not None:
            # 有聊天数据
            gameing = data[3]
            if gameing == 1:
                # 有正在进行的聊天
                commandname = data[1]
                run = True

    # 识别精准
    if run is False:
        cache_commandlist = commandlist["精准"]
        if command in list(cache_commandlist):
            commandname = cache_commandlist[command]
            run = True

    # 识别开头
    if run is False:
        cache_commandlist = commandlist["开头"]
        for cache_command in list(cache_commandlist):
            if command.startswith(cache_command):
                commandname = cache_commandlist[cache_command]
                msg = f"{cache_command} {command.removeprefix(cache_command)}"
                run = True
                break

    # 识别结尾
    if run is False:
        cache_commandlist = commandlist["结尾"]
        for cache_command in list(cache_commandlist):
            if command.endswith(cache_command):
                commandname = cache_commandlist[cache_command]
                run = True
                break

    # 识别模糊
    if run is False:
        cache_commandlist = commandlist["模糊"]
        for cache_command in list(cache_commandlist):
            if cache_command in command:
                commandname = cache_commandlist[command]
                run = True
                break

    # 识别精准2
    if run is False:
        cache_commandlist = commandlist["精准2"]
        if command in list(cache_commandlist):
            commandname = cache_commandlist[command]
            run = True

    # 识别emoji
    if run is False and kn_config("emoji-state"):
        conn = sqlite3.connect(await get_file_path("emoji_1.db"))
        cursor = conn.cursor()
        cursor.execute(f'select * from emoji where emoji = "{command}"')
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if data is not None:
            commandname = "表情功能-emoji"
            run = True

    msg_info = {
        "msg": msg,
        "commands": commands,
        "commandname": commandname,
        "bot_id": "test_botid",
        "channel_id": channel_id,
        "guild_id": "test_guild_id",
        "at_datas": [],
        "user": {
            "user_id": "KnTest",
            "username": "nick_name",
            "nick_name": "nick_name",
            "permission": 5,
            "face_image": None
        },
        "imgmsgs": [],
        "event_name": "message_event",
        "platform": "test_platform",
        "friend_list": [],
        "channel_member_datas": {},
    }
    plugin_return_data = await botrun(msg_info)
    logger.info(plugin_return_data)
    return plugin_return_data


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run_plugin())
