# coding=utf-8
import json
import traceback

from .config import _config_list
from .tools import kn_config, command_cd, _config, del_files2, get_command, content_compliance
from .plugins import (
    plugin_zhanbu, plugin_config, plugin_emoji_xibao, plugin_emoji_yizhi, plugin_game_cck, plugin_game_blowplane,
    plugin_checkin, plugin_emoji_keai, plugin_emoji_jiehun, plugin_emoji_momo,
    plugin_emoji_emoji, plugin_jellyfish_box, plugin_function_jrlp, plugin_game_different, plugin_function_pic,
    plugin_emoji_daibu, plugin_emoji_ji, plugin_emoji_ji2, plugin_emoji_pa, plugin_emoji_wlp
)
import time
from nonebot import logger
import os
import sqlite3

basepath = _config["basepath"]
command_starts = _config["command_starts"]
adminqq = _config["superusers"]


async def botrun(msg_info: dict):
    logger.info("KanonBot-0.4.0")
    try:
        log_msg_info = msg_info.copy().pop("channel_member_datas")
        log_msg_info["channel_member_len"] = len(list(msg_info["channel_member_datas"]))
        logger.debug(log_msg_info)
    except Exception as e:
        logger.debug(msg_info)
    return_json = {"code": -1}
    user_id = ""
    trace_data = {"plugin": [], "content_compliance": []}
    date: str = time.strftime("%Y-%m-%d", time.localtime())
    local_time = time.localtime()
    date_year: int = local_time.tm_year
    date_month: int = local_time.tm_mon
    date_day: int = local_time.tm_mday
    time_h: int = local_time.tm_hour
    time_m: int = local_time.tm_min
    time_s: int = local_time.tm_sec
    time_now: int = int(time.time())
    try:
        # ## 初始化 ##

        # 读取消息
        msg: str = msg_info["msg"] if "msg" in msg_info else ""
        commands: list = msg_info["commands"] if "commands" in msg_info else [""]
        at_datas: list = msg_info["at_datas"] if "at_datas" in msg_info else []
        commandname: str = msg_info["commandname"] if "commandname" in msg_info else ""
        guild_id: str = msg_info["guild_id"] if "guild_id" in msg_info else "None_guild_id"
        channel_id: str = msg_info["channel_id"] if "channel_id" in msg_info else "None_channel_id"
        imgmsgs: list = msg_info["imgmsgs"] if "imgmsgs" in msg_info else []
        botid: str = msg_info["bot_id"] if "bot_id" in msg_info else "None_bot_id"
        friend_datas: dict = msg_info["friend_datas"] if "friend_datas" in msg_info else {}
        channel_member_datas: dict = msg_info["channel_member_datas"] if "channel_member_datas" in msg_info else {}
        event_name: str = msg_info["event_name"] if "event_name" in msg_info else "None_event_name"
        platform: str = msg_info["platform"] if "platform" in msg_info else "None_platform"
        reply_data: dict | None = msg_info["reply_data"] if "reply_data" in msg_info else None
        chat_type: str = msg_info["chat_type"] if "chat_type" in msg_info else "None_chat_type"

        if "user" not in msg_info:
            msg_info["user"] = {}

        user_id: str = msg_info["user"]["user_id"] if "user_id" in msg_info["user"] else ""
        user_permission: int = msg_info["user"]["permission"] if "permission" in msg_info["user"] else 5
        user_avatar: str = msg_info["user"]["avatar"] if "avatar" in msg_info["user"] else None

        if "username" in msg_info["user"]:  # 兼容性转换
            msg_info["user"]["name"] = msg_info["user"]["username"]

        user_name: str = msg_info["user"]["name"] if "name" in msg_info["user"] else ""

        if msg_info["user"]["nick_name"] is not None:
            user_name: str = msg_info["user"]["nick_name"]

        if "face_image" in list(msg_info["user"]):
            user_face_image = msg_info["user"]["face_image"]
        elif user_avatar is not None:
            user_face_image = msg_info["user"]["avatar"]
        else:
            user_face_image = None

        command: str = commands[0]
        if len(commands) >= 2:
            command2 = commands[1]
            # 去除前后空格
            while len(command2) > 0 and command2.startswith(" "):
                command2 = command2.removeprefix(" ")
            while len(command2) > 0 and command2.endswith(" "):
                command2 = command2.removesuffix(" ")
        else:
            command2 = None

        if chat_type != "None_chat_type" and event_name != "None_event_name":
            if event_name.lower() in ["GROUP_AT_MESSAGE_CREATE", "AT_MESSAGE_CREATE"]:
                chat_type = "channel"
            elif event_name.lower() in ["C2C_MESSAGE_CREATE"]:
                chat_type = "private"
            else:
                chat_type = "None_chat_type"

        # 读取回复的消息内容
        if reply_data is not None:
            conn = sqlite3.connect(f"{basepath}db/send_msg_log_{date_year}-{date_month}.db")
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                tables = []
                for data in datas:
                    if data[1] != "sqlite_sequence":
                        tables.append(data[1])
                if "send_msg_log" not in tables:
                    cursor.execute(
                        f"create table send_msg_log(id INTEGER primary key AUTOINCREMENT, "
                        f"msg_id VARCHAR(10), msg_data VARCHAR(10))")
                cursor.execute(
                    f'SELECT * FROM send_msg_log WHERE "msg_id" = "{reply_data["message_id"]}"')
                data = cursor.fetchone()
                if data is not None:
                    reply_data["plugin_data"] = json.loads(data[2])
                else:
                    reply_data["plugin_data"] = None
            except Exception as e:
                logger.error("读取send_msg_log.db失败")
            cursor.close()
            conn.close()

        reply_trace = None
        keyboard = None  # 按钮
        markdown = None  # markdown

        # 黑白名单
        if (kn_config("plugin", "black_white_list_platform") is not None and
                platform in kn_config("plugin", "black_white_list_platform")):
            # 频道黑白名单
            if channel_id in kn_config("plugin-channel_black_list"):
                return {"code": 0, "message": "channel in black list"}  # 结束运行
            elif channel_id in kn_config("plugin-channel_white_list"):
                pass
            else:
                pass  # 结束运行

            # 用户黑白名单
            if user_id in kn_config("plugin-user_black_list"):
                return {"code": 0, "message": "user in black list"}  # 结束运行
            elif user_id in kn_config("plugin-user_white_list"):
                pass
            else:
                pass

        # 跳过at其他bot的消息
        for at_data in at_datas:
            if str(at_data["id"]) in kn_config("plugin-bot_list"):
                return {"code": 0}  # 结束运行

        # ## 变量初始化 ##
        config_list = _config_list()

        cachepath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/"
        if not os.path.exists(cachepath):
            os.makedirs(cachepath)

        # 清除缓存
        if os.path.exists(f"{basepath}/cache/{int(date_year) - 1}"):
            filenames = os.listdir(f"{basepath}/cache/{int(date_year) - 1}")
            if filenames:
                del_files2(f"{basepath}/cache/{int(date_year) - 1}")
        elif os.path.exists(f"{basepath}/cache/{date_year}/{int(date_month) - 1}"):
            filenames = os.listdir(f"{basepath}/cache/{date_year}/{int(date_month) - 1}")
            if filenames:
                del_files2(f"{basepath}/cache/{date_year}/{int(date_month) - 1}")
        elif os.path.exists(f"{basepath}/cache/{date_year}/{date_month}/{int(date_day) - 1}"):
            filenames = os.listdir(f"{basepath}/cache/{date_year}/{date_month}/{int(date_day) - 1}")
            if filenames:
                del_files2(f"{basepath}/cache/{date_year}/{date_month}/{int(date_day) - 1}")

        dbpath = basepath + "db/"
        if not os.path.exists(dbpath):
            os.makedirs(dbpath)

        # ## 初始化回复内容 ##
        returnpath = None
        returnpath2 = None
        returnpath3 = None
        message = None
        reply = False
        at = False
        code = 0
        cut = False

        # 添加函数
        # 查询功能开关
        def getconfig(commandname: str) -> bool:
            """
            查询指令是否开启
            :param commandname: 查询的命令名
            :return: True or False
            """
            conn = sqlite3.connect(f"{basepath}db/config.db")
            cursor = conn.cursor()
            state = False
            try:
                if not os.path.exists(f"{basepath}db/config.db"):
                    # 数据库文件 如果文件不存在，会自动在当前目录中创建
                    cursor.execute(
                        f"create table command_state(command VARCHAR(10) primary key, "
                        f"state BOOLEAN(10), VARCHAR(10))")
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                tables = []
                for data in datas:
                    if data[1] != "sqlite_sequence":
                        tables.append(data[1])
                if "command_state" not in tables:
                    cursor.execute(
                        f"create table command_state(command VARCHAR(10) primary key, "
                        f"state BOOLEAN(10), channel_id VARCHAR(10))")
                cursor.execute(
                    f'SELECT * FROM command_state WHERE "command" = "{commandname}" AND "channel_id" = "{channel_id}"')
                data = cursor.fetchone()
                if data is not None:
                    state = data[1]
                else:
                    if commandname in list(config_list):
                        state = config_list[commandname]["state"]
                    else:
                        state = False
            except Exception as e:
                state = False
            cursor.close()
            conn.close()

            if state == 1:
                state = True
            elif state == 0:
                state = False
            logger.info(f"commandname:{commandname}, state:{state}")
            return state

        # ## 心跳服务相关1/2 ##
        # 查询bot是否需要运行
        if kn_config("botswift-state") and channel_id not in kn_config("botswift-ignore_list"):
            botswitch = False
            # 读取忽略该功能的群聊
            if channel_id in kn_config("botswift-ignore_list") or channel_id.startswith("private"):
                botswitch = True
            else:
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
                if "channel" not in tables:
                    cursor.execute(f'create table "channel"(id INTEGER primary key AUTOINCREMENT, '
                                   f'channel VARCHAR(10), botid VARCHAR(10), priority VARCHAR(10))')

                # 读取群bot设置
                cursor.execute(f'select * from "channel" WHERE channel = "{channel_id}"')
                datas = cursor.fetchall()
                if not datas:
                    # 没有数据，将本bot记为第一个bot
                    cursor.execute(
                        f'replace into "channel" ("channel","botid","priority") '
                        f'values("{channel_id}","{botid}",1)')
                    botswitch = True
                else:
                    # 提取优先级列表
                    priority_list = []
                    for data in datas:
                        priority_list.append(int(data[3]))
                    # 排序bot列表
                    channel_bots_list = []
                    num = len(datas)
                    cache_priority_list = priority_list.copy()
                    while num >= 1:
                        num -= 1
                        min_bot = min(cache_priority_list)
                        for data in datas:
                            priority = int(data[3])
                            if min_bot == priority:
                                data_botid = data[2]
                                channel_bots_list.append(data_botid)
                                cache_priority_list.remove(min_bot)
                                break
                    # 检测本bot是否在群内bot列表内
                    if botid not in channel_bots_list:
                        channel_bots_list.append(botid)
                        cursor.execute(
                            f'replace into channel ("channel","botid","priority") '
                            f'values("{channel_id}",{botid},{int(max(priority_list)) + 1})')
                    # 顺序检查bot列表
                    for channel_botid in channel_bots_list:
                        if channel_botid == botid:
                            botswitch = True
                            cursor.execute(f'select * from "heart" WHERE botid = "{channel_botid}"')
                            data = cursor.fetchone()
                            if data is None:
                                cursor.execute(
                                    f'replace into heart ("botid","times","hearttime") values("{channel_botid}",0,0)')
                            break
                        else:
                            cursor.execute(f'select * from "heart" WHERE botid = "{channel_botid}"')
                            data = cursor.fetchone()
                            if data is None:
                                continue
                            else:
                                times = int(data[1])  # 未检测到bot发消息的次数
                                hearttime = int(data[2])
                                cache = commandname
                                config_gruop_list = []
                                for config_id in config_list:
                                    if config_list[config_id]["group"] not in config_gruop_list:
                                        config_gruop_list.append(config_list[config_id]["group"])
                                for config_group in config_gruop_list:
                                    commandname = commandname.removeprefix(f"{config_group}-")
                                if getconfig(cache) and commandname not in ["小游戏-猜猜看"]:
                                    # cck功能会有大量不回复消息，进行排除
                                    cursor.execute(
                                        f'replace into heart ("botid","times","hearttime") '
                                        f'values("{channel_botid}",{times + 1},{hearttime})')
                                if (time_now - hearttime) >= 900 and times >= 20:
                                    # 15分钟内连续20次没有相应，
                                    continue
                                else:
                                    break

                conn.commit()
                cursor.close()
                conn.close()
        else:
            botswitch = True

        # 指令冷却
        def _command_cd():
            if getconfig("commandcd") and user_permission < 7 and user_id not in adminqq:
                cd = command_cd(cd_id=user_id, time_now=time_now, cd_type="user")
                if cd is False:
                    cd = command_cd(cd_id=channel_id, time_now=time_now, cd_type="channel")
                return cd
            else:
                return False

        # ## 处理消息 ##
        if commandname.startswith("config"):
            if user_permission >= 7 or user_id in adminqq or commandname == "config查询":
                pass
            run = True
            if run:
                logger.info(f"run-{commandname}")
                # 指令解析
                if command2 is not None and command == "菜单":
                    commands = get_command(command2)
                    if len(commands) > 1:
                        command = commands[0]
                        command2 = commands[1]
                    else:
                        command = commands[0]
                        command2 = None

                if command in ["帮助", "菜单", "使用说明", "help", "查询", "查询功能", "列表", "功能列表"]:
                    command = "菜单"

                if command in ["菜单", "开启", "关闭"]:
                    message, returnpath = await plugin_config(
                        command=command,
                        command2=command2,
                        channel_id=channel_id,
                        user_id=user_id
                    )
                    if message is not None:
                        code = 1
                    elif returnpath is not None:
                        code = 2
            else:
                logger.info(f"run-{commandname}, 用户权限不足")
                code = 1
                message = "权限不足"

        elif commandname.startswith("群聊功能-") and botswitch is True:
            commandname = commandname.removeprefix("群聊功能-")
            if "塔罗牌" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    at = True
                    logger.info(f"run-{commandname}")
                    message, returnpath = await plugin_zhanbu(user_id, cachepath)
                    if returnpath is not None:
                        code = 3
                    else:
                        code = 1
            elif "签到" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    state, message = await plugin_checkin(user_id=user_id, date=date)
                    code = 1
            elif "水母箱" == commandname and getconfig(commandname):
                if command2 is not None:
                    if command == "水母箱":
                        command = command2
                    else:
                        command += " " + command2

                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    (code,
                     message,
                     returnpath,
                     markdown,
                     keyboard,
                     trace,
                     reply_trace
                     ) = await plugin_jellyfish_box(
                        user_id=user_id,
                        user_name=user_name,
                        channel_id=channel_id,
                        msg=command,
                        time_now=time_now,
                        platform=platform,
                        reply_data=reply_data["plugin_data"] if reply_data is not None else None,
                        channel_member_datas=channel_member_datas
                    )
                    trace_data["plugin"].extend(trace)
            elif "今日老婆" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    data = await plugin_function_jrlp(
                        user_id=user_id,
                        channel_id=channel_id,
                        channel_member_datas=channel_member_datas,
                        time_now=time_now,
                        cachepath=cachepath,
                        platform=platform,
                    )
                    code = data["code"]
                    message = data["message"]
                    returnpath = data["returnpath"]
                    trace_data["plugin"].extend(data["trace"])
            elif "图库" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    message, images, trace = await plugin_function_pic(
                        msg=msg,
                        user_id=user_id,
                    )

                    if message is None and images is None:
                        code = 0
                    elif images is None:
                        code = 1
                    elif message is None:
                        code = 2
                        returnpath = images[0]
                    elif len(images) == 1:
                        code = 3
                        returnpath = images[0]
                    elif len(images) == 2:
                        code = 4
                        returnpath = images[0]
                        returnpath2 = images[1]
                    elif len(images) == 3:
                        code = 5
                        returnpath = images[0]
                        returnpath2 = images[1]
                        returnpath3 = images[2]

                    trace = []
                    trace_data["plugin"].extend(trace)

        elif commandname.startswith("表情功能-") and botswitch is True:
            commandname = commandname.removeprefix("表情功能-")
            if "emoji" == commandname and getconfig(commandname):
                if command == "合成":
                    command = command2
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    message, returnpath = await plugin_emoji_emoji(command)
                    if message is not None:
                        code = 1
                    else:
                        code = 2
            elif "喜报" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    if kn_config("content_compliance", "state") is True:
                        content_compliance_data = await content_compliance("text", command2, user_id=user_id)
                        if content_compliance_data["conclusion"] in ["不合规"]:
                            command2 = "message"
                            trace_data["content_compliance"].append(content_compliance_data)

                    returnpath = await plugin_emoji_xibao(command, command2, imgmsgs)
                    code = 2
            elif "一直" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if imgmsgs:
                        returnpath = await plugin_emoji_yizhi(imgmsgs[0])
                    else:
                        returnpath = await plugin_emoji_yizhi(user_avatar)
                    code = 2
            elif "可爱" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    name1 = user_name

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = "ta"

                    if imgmsgs:
                        image = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image = at_data["avatar"]
                        else:
                            image = None
                    else:
                        image = None

                    if image is not None:
                        returnpath = await plugin_emoji_keai(image, name2)
                        code = 2
            elif "结婚" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    name1 = user_name

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = " "

                    if imgmsgs:
                        image = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image = at_data["avatar"]
                        else:
                            image = None
                    else:
                        image = None

                    if image is not None:
                        returnpath = await plugin_emoji_jiehun(image, name1, name2)
                        code = 2
            elif "摸摸" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    name1 = user_name

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = " "

                    if imgmsgs:
                        image = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image = at_data["avatar"]
                        else:
                            image = None
                    else:
                        image = None

                    if image is not None:
                        returnpath = await plugin_emoji_momo(image, cachepath)
                        code = 2
            elif "逮捕" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    name1 = user_name

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = "ta"

                    if imgmsgs:
                        image = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image = at_data["avatar"]
                        else:
                            image = None
                    else:
                        image = None

                    if image is not None:
                        returnpath = await plugin_emoji_daibu(image, name2)
                        code = 2
            elif "寄" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    returnpath = await plugin_emoji_ji()
                    code = 2
            elif "急" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    returnpath = await plugin_emoji_ji2()
                    code = 2
            elif "爬" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    returnpath = await plugin_emoji_pa()
                    code = 2
            elif "我老婆" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    image = user_face_image

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = "ta"

                    if imgmsgs:
                        image2 = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image2 = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image2 = at_data["avatar"]
                        else:
                            image2 = None
                    else:
                        image2 = None

                    if image is not None and image2 is not None:
                        returnpath = await plugin_emoji_wlp(image, image2, name2)
                        code = 2
            elif "结婚证--" == commandname and getconfig(commandname):
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")

                    image = user_face_image

                    at_data = at_datas[0] if at_datas else None
                    if command2 is not None and not at_datas:
                        name2 = command2
                    elif at_datas and "username" in list(at_data):
                        if "nick_name" in list(at_data) and at_data["nick_name"] is not None:
                            name2 = at_data["nick_name"]
                        else:
                            name2 = at_data["username"]
                    else:
                        name2 = "ta"

                    if imgmsgs:
                        image2 = imgmsgs[0]
                    elif at_datas:
                        if "face_image" in list(at_data):
                            image2 = at_data["face_image"]
                        elif "avatar" in list(at_data):
                            image2 = at_data["avatar"]
                        else:
                            image2 = None
                    else:
                        image2 = None

                    if image is not None and image2 is not None:
                        returnpath = await plugin_emoji_wlp(image, image2, name2)
                        code = 2

        elif commandname.startswith("小游戏") and botswitch is True:
            commandname = commandname.removeprefix("小游戏-")
            if "猜猜看" == commandname and getconfig(commandname):
                # 转换命令名
                if command2 is not None:
                    command = command2
                if command == "cck":
                    command = "猜猜看"
                elif command == "bzd":
                    command = "不知道"
                elif command == "结束":
                    command = "不知道"

                commandcd = _command_cd()
                if commandcd is not False and command == "猜猜看":
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath, markdown, keyboard = await plugin_game_cck(
                        command=command, channel_id=channel_id, platform=platform)
            elif "炸飞机" == commandname and getconfig(commandname):
                # 转换命令名
                if command.startswith("炸") and not command.startswith("炸飞机"):
                    command = command.removeprefix("炸")
                if command2 is not None:
                    command = command2
                if command == "zfj":
                    command = "炸飞机"

                # 判断指令冷却
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath = await plugin_game_blowplane(command=command, channel_id=channel_id)
            elif "找不同" == commandname and getconfig(commandname):
                # 转换命令名
                if command2 is not None:
                    command = command2
                if command == "zbt":
                    command = "找不同"

                # 判断指令冷却
                commandcd = _command_cd()
                if commandcd is not False:
                    code = 1
                    message = f"指令冷却中（{commandcd}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    data = await plugin_game_different(command=command, channel_id=channel_id)
                    code = data["code"]
                    message = data["message"]
                    returnpath = data["returnpath"]
                    returnpath2 = data["returnpath2"]
                    trace_data["plugin"].extend(data["trace"])

        elif "###" == commandname:
            pass

        # 返回消息处理
        return_json = {
            "code": code,
            "message": message,
            "returnpath": returnpath,
            "returnpath2": returnpath2,
            "returnpath3": returnpath3,
            "at": False,
            "keyboard": keyboard,
            "markdown": markdown,
            "trace": trace_data,
            "reply_trace": reply_trace,
            }

    except Exception as e:
        logger.error("bot_run.py运行异常")
        return_json["code"] = -1
        return_json["error_message"] = str(e).replace("'", '"')
        return_json["error_traceback"] = str(traceback.format_exc()).replace("'", '"')

        logger.error(e)
        logger.error(traceback.format_exc())

    # 合规检测
    # if return_json["code"] in [1, 3, 4, 5]:
    #     if kn_config("content_compliance", "state") is True:
    #         content_compliance_data = await content_compliance("text", return_json["message"], user_id=user_id)
    #         if content_compliance_data["conclusion"] in ["不合规"]:
    #             return_json["message"] = "message"
    #             trace_data["content_compliance"].append(content_compliance_data)

    # 日志记录
    if kn_config("plugin", "log") is True:
        conn = sqlite3.connect(f"{basepath}db/log_{date_year}-{date_month}.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "log" not in tables:
            cursor.execute(
                f'create table "log"(id INTEGER primary key AUTOINCREMENT, '
                f'time VARCHAR(10), input VARCHAR(10), output VARCHAR(10), trace_data VARCHAR(10))')
        try:
            msg_info["friend_datas"] = {}
            msg_info["channel_member_datas"] = {}
            log_input = json.dumps(msg_info)
            log_output = json.dumps(return_json)
            log_trace = json.dumps(trace_data)

            sql_text = f'replace into "log" ("time","input","output","trace_data") '
            sql_text += f"values('{time_now}',"
            sql_text += f"'{log_input}'," if log_input.startswith("{") else f'"{log_input}",'
            sql_text += f"'{log_output}'," if log_output.startswith("{") else f'"{log_output}",'
            sql_text += f"'{log_trace}')"

            cursor.execute(sql_text)
            conn.commit()
        except Exception as e:
            logger.error("写入日志失败（1/3）")
            logger.error(e)
            try:
                cursor.execute(
                    f'replace into "log" ("time","input") '
                    f"values('{time_now}','{json.dumps({'code': -2})}')")
                conn.commit()
            except Exception as e:
                logger.error("写入日志失败（2/3）")
                logger.error(e)
                path = f"{basepath}cache/log/"
                if not os.path.exists(path):
                    os.makedirs(path)
                path += f"{time_now}.log"
                file = open(path, "w")
                file.write(json.dumps({
                    "time": time_now,
                    "input": msg_info,
                    "output": return_json,
                    "trace": trace_data
                }))
                file.close()
        cursor.close()
        conn.close()

    return return_json
