import asyncio
import os
import sqlite3

from PIL import Image

from bridge.tomorin import on_event, SessionExtension, h
from bot_run import botrun
from tools import get_command, get_unity_user_id, get_unity_user_data, connect_api, kn_config, get_file_path
from config import command_list


@on_event.message_created
def kanon_created(session: SessionExtension):
    command_data = command_list()
    commandlist = []
    for command in command_data["精准"]:
        commandlist.append(command)
    session.function.register(commandlist)
    session.function.description = "Tomorin_plugin_Kanonbot"  # 功能描述
    session.action(kanon)


async def kanon(session: SessionExtension):
    # 读取默认配置
    basepath = "./Kanobot/"
    commandlist = command_list()
    # 添加插件参数
    platform = "Tomorin"
    commandname = ""
    # 读取消息内容
    msg = session.message.command.text
    commands = get_command(msg)
    command = commands[0]
    unity_channel_id = f"channel_{platform}_{session.message.channel}"
    unity_guild_id = f"channel_{platform}_{session.message.guild}"
    bot_id = session.self_id

    run = False
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
        cursor.execute(f'select * from gameinglist where channelid = "{unity_channel_id}"')
        data = cursor.fetchone()
        cursor.close()
        conn.close()
        if data is not None:
            # 有聊天数据
            gameing = data[3]
            if gameing == 1:
                # 有正在进行的聊天
                commandname = data[1]
                run = True

    user_id = session.user.id
    unity_user_id = get_unity_user_id("tomorin", user_id)
    unity_user_data = get_unity_user_data(unity_user_id)
    if "user_id" not in list(unity_user_data):
        unity_user_data["user_id"] = unity_user_id
    unity_user_data["avatar"] = session.user.avatar
    unity_user_data["username"] = session.user.name
    unity_user_data["nick_name"] = session.user.nick
    if "avatar" not in list(unity_user_data):
        unity_user_data["avatar"] = None
        save = True
    if "face_image" not in list(unity_user_data) and unity_user_data["avatar"] is not None:
        image_path = f"{basepath}file/user_face/"
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        image_path += f"{unity_user_id}.png"
        image = await connect_api("image", unity_user_data["avatar"])
        image.save(image_path)
        unity_user_data["face_image"] = image_path
        save = True

    msg_info = {
        "msg": msg,
        "commands": commands,
        "commandname": commandname,
        "bot_id": bot_id,
        "channel_id": unity_channel_id,
        "guild_id": unity_channel_id,
        "at_datas": [],
        "user": unity_user_data,
        "imgmsgs": [],
        "platform": platform,
        "event_name": "message_event",
        "friend_list": [],
        "channel_member_datas": {}
    }

    # 全局默认变量
    # return_data = {"code": 0,
    #         "message": "None",
    #         "returnpath": "None",
    #         "returnpath2": "None",
    #         "returnpath3": "None"
    #         }

    return_data = await botrun(msg_info)

    # 貌似不需要另外异步
    # # 添加异步运行函数
    # async def run_plugins():
    #     global return_data
    #     return_data = await botrun(msg_info)
    #     return
    #
    # # 运行插件
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(run_plugins())

    # 总结与发送
    print(return_data)
    code = int(return_data["code"])
    if code == 1:
        msg = return_data["message"]
        session.send(msg)
    elif code == 2:
        image = Image.open(return_data["returnpath"], "r")
        session.send(h.image(image))
    elif code == 3:
        msg = return_data["message"]
        session.send(msg)
        image = Image.open(return_data["returnpath"], "r")
        session.send(h.image(image))
    elif code == 4:
        msg = return_data["message"]
        session.send(msg)
        image = Image.open(return_data["returnpath"], "r")
        session.send(h.image(image))
        image = Image.open(return_data["returnpath2"], "r")
        session.send(h.image(image))
    elif code == 5:
        msg = return_data["message"]
        session.send(msg)
        image = Image.open(return_data["returnpath"], "r")
        session.send(h.image(image))
        image = Image.open(return_data["returnpath2"], "r")
        session.send(h.image(image))
        image = Image.open(return_data["returnpath3"], "r")
        session.send(h.image(image))
