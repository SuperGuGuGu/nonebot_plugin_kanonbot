import os
import sqlite3
import time

from YunHu_bot.YHChatClientSDK.Event import Event
from YunHu_bot.YHChatClientSDK.Message import MessageSegment
from YunHu_bot.YHChatClientSDK.YHChat_send import send_message
from YunHu_bot.YHChatClientSDK import YHChat_recv
from YunHu_bot.tools import logger

from .bot_run import botrun
from .config import command_list, _config_list
from .tools import get_command, kn_config, get_file_path, basepath, get_unity_user_id, get_unity_user_data, connect_api, \
    save_unity_user_data, imgpath_to_url


@YHChat_recv.on_command
@YHChat_recv.on_message
async def _(event: Event):
    botid = ""
    user_id = event.sender_info.id_
    platform = "Yunhu"

    # 获取群号
    if event.chat_type == "group":
        channel_id = guild_id = event.chat_id
        unity_channel_id = unity_guild_id = f"group_{platform}_{channel_id}"
    elif event.chat_type == "bot":
        guild_id = channel_id = user_id
        unity_guild_id = unity_channel_id = f"private_{platform}_{user_id}"
    else:
        guild_id = channel_id = user_id
        unity_guild_id = unity_channel_id = f"else_{platform}_{user_id}"

    msg = ""
    imgmsgs = []
    at_datas = {}
    markdown = None

    msg_data = event.message
    match msg_data["type"]:
        case "text":
            msg = msg_data["data"]["text"]
            if "@" in msg and " \u200B" in msg:
                num = -1
                for m in msg:
                    num += 1
                    if m == "@":
                        test_num = 0
                        while test_num < 50:
                            test_num += 1
                            if num + test_num > len(msg):
                                break
                            if msg[num:num + test_num + 1].endswith(" \u200B"):
                                msg = msg[:num] + " " + msg[num + test_num + 1:]
                                num -= test_num
                                break
            at_list = msg_data["data"]["at"] if "at" in list(msg_data["data"]) else []
            if at_list:
                for id_ in at_list:
                    at_unity_id = get_unity_user_id(platform, id_)
                    at_datas[at_unity_id] = get_unity_user_data(at_unity_id)
        case "markdown":
            markdown = msg_data["data"]["text"]
        case "image":
            imgmsgs.append(msg_data["data"]["url"])

    msg = msg.replace('"', "“").replace("'", "‘")
    msg = msg.replace("(", "（").replace(")", "）")
    msg = msg.replace("{", "（").replace("}", "）")
    msg = msg.replace("[", "【").replace("]", "】")
    commands = get_command(msg)
    command = commands[0]
    now = int(time.time())

    # ## 心跳服务相关 ##
    if kn_config("botswift", "state"):
        conn = sqlite3.connect(f"{basepath}db/botswift.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "heart" not in tables:
            cursor.execute(f'create table "heart"'
                           f'("botid" VARCHAR(10) primary key, times VARCHAR(10), hearttime VARCHAR(10))')
        # 读取bot名单
        cursor.execute(f'select * from heart')
        datas = cursor.fetchall()
        bots_list = []
        for data in datas:
            bots_list.append(data[0])
        # 如果发消息的用户为bot，则刷新心跳
        if user_id in bots_list:
            cursor.execute(f'SELECT * FROM heart WHERE "botid" = "{user_id}"')
            data = cursor.fetchone()
            cache_times = int(data[1])
            cache_hearttime = int(data[2])
            cursor.execute(f'replace into heart("botid", "times", "hearttime") '
                           f'values("{user_id}", "0", "{now}")')
            conn.commit()
        cursor.close()
        conn.close()

        if user_id in bots_list:
            # 不相应bot的消息
            return

    # 判断是否响应
    commandname = ""
    commandlist = command_list()
    config_list = _config_list()
    run = False
    time_now = int(time.time())

    # 识别命令
    if run is False:
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
        if run is False and kn_config("emoji", "state"):
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
            if not os.path.exists(f"{basepath}db/"):
                os.makedirs(f"{basepath}db/")
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

        # 排除部分相应词
        if run is True:
            if commandname == '小游戏-猜猜看':
                if len(command) >= 7:
                    run = False
            if commandname == '小游戏-炸飞机':
                if len(command) >= 7:
                    run = False

    # 开始处理消息
    run = True
    if run:
        # 获取用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)

        unity_user_data["user_id"] = unity_user_id
        unity_user_data["avatar"] = None
        unity_user_data["name"] = event.sender_info.nickname
        unity_user_data["nick_name"] = event.sender_info.nickname
        unity_user_data["is_bot"] = None
        if event.sender_info.type == "user":
            unity_user_data["is_bot"] = False
        elif event.sender_info.type == "bot":
            unity_user_data["is_bot"] = True
        unity_user_data["permission"] = 5

        # 同步unity数据
        if "face_image" not in list(unity_user_data) and unity_user_data["avatar"] is not None:
            image_path = f"{basepath}file/user_face/"
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            image_path += f"{unity_user_id}.png"
            image = await connect_api("image", unity_user_data["avatar"])
            image.save(image_path)
            unity_user_data["face_image"] = image_path
            save = True
        save_unity_user_data(unity_user_id, unity_user_data)

        # 组装信息，进行后续响应
        msg_info = {
            "msg": msg,
            "commands": get_command(msg),
            "commandname": commandname,
            "bot_id": botid,
            "channel_id": unity_channel_id,
            "guild_id": unity_guild_id,
            "at_datas": at_datas,
            "user": unity_user_data,
            "imgmsgs": imgmsgs,
            "event_name": event.event_type,
            "platform": platform,
            "friend_list": [],
            "friend_datas": {},
            "channel_member_datas": {},
        }

        logger.info(msg_info)
        data = await botrun(msg_info)
        logger.info(data)

        # 获取返回信息，进行回复
        code = int(data["code"])
        if code == 1:
            msg = MessageSegment.text(data["message"])
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
        elif code == 2:
            file_url = await imgpath_to_url(data["returnpath"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
        elif code == 3:
            msg = MessageSegment.text(data["message"])
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
        elif code == 4:
            msg = MessageSegment.text(data["message"])
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath2"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
        elif code == 5:
            msg = MessageSegment.text(data["message"])
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath2"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
            file_url = await imgpath_to_url(data["returnpath3"])
            msg = MessageSegment.image(fileUrl=file_url)
            await send_message(
                recv_type=event.chat_type,
                recv_id=event.chat_id,
                message=msg
            )
