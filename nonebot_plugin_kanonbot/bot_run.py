# coding=utf-8
from .config import _config_list
from .tools import kn_config, lockst, locked, command_cd, get_command, start_with_list, _config
from .plugins import (
    plugin_zhanbu, plugin_config, plugin_emoji_xibao, plugin_emoji_yizhi, plugin_game_cck, plugin_game_blowplane,
    plugin_checkin, plugin_emoji_keai, plugin_emoji_jiehun, plugin_emoji_momo,
    plugin_emoji_emoji, plugin_jellyfish_box
)
import time
from nonebot import logger
import os
import sqlite3

basepath = _config["basepath"]
command_starts = _config["command_starts"]
adminqq = _config["superusers"]


async def botrun(msg_info):
    logger.info("KanonBot-0.3.9")
    # ## 初始化 ##
    lockdb = f"{basepath}db/"
    if not os.path.exists(lockdb):
        os.makedirs(lockdb)
    lockdb += "lock.db"
    await lockst(lockdb)
    msg: str = msg_info["msg"]
    commands: list = msg_info["commands"]
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
    at_datas: list = msg_info["at_datas"]
    if "permission" in list(msg_info["user"]):
        user_permission:int = int(msg_info["user"]["permission"])
    else:
        user_permission: int = 5
    user_id: str = msg_info["user"]["user_id"]
    if "face_image" in list(msg_info["user"]):
        user_avatar = msg_info["user"]["face_image"]
    else:
        user_avatar = None
    if msg_info["user"]["nick_name"] is not None:
        user_name: str = msg_info["user"]["nick_name"]
    else:
        user_name: str = msg_info["user"]["username"]
    commandname: str = msg_info["commandname"]
    guild_id: str = msg_info["guild_id"]
    channel_id: str = msg_info["channel_id"]
    imgmsgs = msg_info["imgmsgs"]
    botid: str = msg_info["bot_id"]
    friend_list: list = msg_info["friend_list"]
    group_member_datas = msg_info["channel_member_datas"]
    event_name: str = msg_info["event_name"]
    platform: str = msg_info["platform"]
    keyboard = None  # 按钮
    markdown = None  # markdown

    # 黑白名单
    # 频道黑白名单
    if channel_id in kn_config("plugin-channel_black_list"):
        return {"code": 0, "message": "channel in black list"}  # 结束运行
    elif channel_id in kn_config("plugin-channel_white_list"):
        pass
    else:
        pass

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
    date: str = time.strftime("%Y-%m-%d", time.localtime())
    date_year: str = time.strftime("%Y", time.localtime())
    date_month: str = time.strftime("%m", time.localtime())
    date_day: str = time.strftime("%d", time.localtime())
    time_h: str = time.strftime("%H", time.localtime())
    time_m: str = time.strftime("%M", time.localtime())
    time_s: str = time.strftime("%S", time.localtime())
    time_now: int = int(time.time())
    config_list = _config_list()

    cachepath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/"
    if not os.path.exists(cachepath):
        os.makedirs(cachepath)

    def del_files2(dir_path):
        """
        删除文件夹下所有文件和路径，保留要删的父文件夹
        """
        for root, dirs, files in os.walk(dir_path, topdown=False):
            # 第一步：删除文件
            for name in files:
                os.remove(os.path.join(root, name))  # 删除文件
            # 第二步：删除空文件夹
            for name in dirs:
                os.rmdir(os.path.join(root, name))  # 删除一个空目录

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
    cut = 'off'
    run = True

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
                                    config_gruop_list.append(config_list[config_id]["group"] )
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

    # ## 处理消息 ##
    if commandname.startswith("config"):
        if user_permission == 7 or user_id in adminqq or commandname == "config查询":
            pass
        run = True
        if run:
            logger.info(f"run-{commandname}")
            message, returnpath = plugin_config(command, command2, guild_id, channel_id)
            if message is not None:
                code = 1
            else:
                code = 2
        else:
            logger.info(f"run-{commandname}, 用户权限不足")
            code = 1
            message = "权限不足"

    elif commandname.startswith("群聊功能-") and botswitch is True:
        commandname = commandname.removeprefix("群聊功能-")
        if "塔罗牌" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    at = True
                    logger.info(f"run-{commandname}")
                    message, returnpath = await plugin_zhanbu(user_id, cachepath)
                    if returnpath is not None:
                        code = 3
                    else:
                        code = 1
            else:
                at = True
                logger.info(f"run-{commandname}")
                message, returnpath = await plugin_zhanbu(user_id, cachepath)
                if returnpath is not None:
                    code = 3
                else:
                    code = 1
        elif "签到" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    state, message = await plugin_checkin(user_id=user_id, group_id=guild_id, date=date)
                    code = 1
            else:
                logger.info(f"run-{commandname}")
                state, message = await plugin_checkin(user_id=user_id, group_id=guild_id, date=date)
                code = 1
        elif "水母箱" == commandname and getconfig(commandname):
            if command2 is not None and command == "水母箱":
                command = command2
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db"
                )
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath = await plugin_jellyfish_box(
                        user_id=user_id,
                        user_name=user_name,
                        channel_id=channel_id,
                        msg=command,
                        time_now=time_now
                    )
            else:
                logger.info(f"run-{commandname}")
                code, message, returnpath = await plugin_jellyfish_box(
                    user_id=user_id,
                    user_name=user_name,
                    channel_id=channel_id,
                    msg=command,
                    time_now=time_now
                )

    elif commandname.startswith("表情功能-") and botswitch is True:
        commandname = commandname.removeprefix("表情功能-")
        if "emoji" == commandname and getconfig(commandname):
            if command == "合成":
                command = command2
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    message, returnpath = await plugin_emoji_emoji(command)
                    if message is not None:
                        code = 1
                    else:
                        code = 2
            else:
                logger.info(f"run-{commandname}")
                message, returnpath = await plugin_emoji_emoji(command)
                if message is not None:
                    code = 1
                else:
                    code = 2
        elif "喜报" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    returnpath = await plugin_emoji_xibao(command, command2, imgmsgs)
                    code = 2
            else:
                logger.info(f"run-{commandname}")
                returnpath = await plugin_emoji_xibao(command, command2, imgmsgs)
                code = 2
        elif "一直" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if imgmsgs:
                        returnpath = await plugin_emoji_yizhi(imgmsgs[0])
                    else:
                        returnpath = await plugin_emoji_yizhi(user_avatar)
                    code = 2
            else:
                logger.info(f"run-{commandname}")
                if imgmsgs:
                    returnpath = await plugin_emoji_yizhi(imgmsgs[0])
                else:
                    returnpath = await plugin_emoji_yizhi(user_avatar)
                code = 2
        elif "可爱" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if command2 is not None:
                        user_name = command2
                    if imgmsgs:
                        returnpath = await plugin_emoji_keai(imgmsgs[0], user_name)
                        code = 2
                    elif at_datas:
                        at_data = at_datas[0]
                        if "face_image" in at_data:
                            returnpath = await plugin_emoji_keai(at_data["face_image"], user_name)
                            code = 2
                        elif "avatar" in at_data:
                            returnpath = await plugin_emoji_keai(at_data["avatar"], user_name)
                            code = 2
                    else:
                        pass
                        # returnpath = await plugin_emoji_keai(user_avatar, user_name)

            else:
                logger.info(f"run-{commandname}")
                if command2 is not None:
                    user_name = command2
                if imgmsgs:
                    returnpath = await plugin_emoji_keai(imgmsgs[0], user_name)
                    code = 2
                elif at_datas:
                    at_data = at_datas[0]
                    if "face_image" in at_data:
                        returnpath = await plugin_emoji_keai(at_data["face_image"], user_name)
                        code = 2
                    elif "avatar" in at_data:
                        returnpath = await plugin_emoji_keai(at_data["avatar"], user_name)
                        code = 2
                else:
                    pass
                    # returnpath = await plugin_emoji_keai(user_avatar, user_name)
        elif "结婚" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if command2 is not None:
                        if " " in command2:
                            command2 = command2.split(" ", 1)
                            name1 = command2[0]
                            name2 = command2[1]
                        else:
                            name1 = user_name
                            name2 = command2
                    else:
                        name1 = user_name
                        name2 = " "

                    if imgmsgs:
                        returnpath = await plugin_emoji_jiehun(imgmsgs[0], name1, name2)
                        code = 2
                    elif at_datas:
                        at_data = at_datas[0]
                        if "face_image" in at_data:
                            returnpath = await plugin_emoji_jiehun(at_data["face_image"], name1, name2)
                            code = 2
                        elif "avatar" in at_data:
                            returnpath = await plugin_emoji_jiehun(at_data["avatar"], name1, name2)
                            code = 2
                    else:
                        pass
                        # returnpath = await plugin_emoji_jiehun(user_avatar, name1, name2)

            else:
                logger.info(f"run-{commandname}")
                if command2 is not None:
                    if " " in command2:
                        command2 = command2.split(" ", 1)
                        name1 = command2[0]
                        name2 = command2[1]
                    else:
                        name1 = user_name
                        name2 = command2
                else:
                    name1 = user_name
                    name2 = " "

                if imgmsgs:
                    returnpath = await plugin_emoji_jiehun(imgmsgs[0], name1, name2)
                    code = 2
                elif at_datas:
                    at_data = at_datas[0]
                    if "face_image" in at_data:
                        returnpath = await plugin_emoji_jiehun(at_data["face_image"], name1, name2)
                        code = 2
                    elif "avatar" in at_data:
                        returnpath = await plugin_emoji_jiehun(at_data["avatar"], name1, name2)
                        code = 2
                else:
                    pass
                    # returnpath = await plugin_emoji_jiehun(user_avatar, name1, name2)
        elif "摸摸" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if imgmsgs:
                        returnpath = await plugin_emoji_momo(imgmsgs[0])
                        code = 2
                    elif at_datas:
                        at_data = at_datas[0]
                        if "face_image" in at_data:
                            returnpath = await plugin_emoji_momo(at_data["face_image"])
                            code = 2
                        elif "avatar" in at_data:
                            returnpath = await plugin_emoji_momo(at_data["avatar"])
                            code = 2
                    else:
                        pass
                        # returnpath = await plugin_emoji_momo(user_avatar)
            else:
                logger.info(f"run-{commandname}")
                if imgmsgs:
                    returnpath = await plugin_emoji_momo(imgmsgs[0])
                    code = 2
                elif at_datas:
                    at_data = at_datas[0]
                    if "face_image" in at_data:
                        returnpath = await plugin_emoji_momo(at_data["face_image"])
                        code = 2
                    elif "avatar" in at_data:
                        returnpath = await plugin_emoji_momo(at_data["avatar"])
                        code = 2
                else:
                    pass
                    # returnpath = await plugin_emoji_momo(user_avatar)

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

            # 判断指令冷却
            if command == "猜猜看" and getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id, groupcode=channel_id, timeshort=time_now, coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath, markdown, keyboard = await plugin_game_cck(
                        command=command, channel_id=channel_id, platform=platform)
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
            if command == "炸飞机" and getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id, groupcode=channel_id, timeshort=time_now, coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != 7 and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath = await plugin_game_blowplane(command=command, channel_id=channel_id)
            else:
                logger.info(f"run-{commandname}")
                code, message, returnpath = await plugin_game_blowplane( command=command, channel_id=channel_id)

    elif "###" == commandname:
        pass

    # log记录
    # 目前还不需要这个功能吧，先放着先

    # 返回消息处理
    locked(lockdb)
    return {"code": code,
            "message": message,
            "returnpath": returnpath,
            "returnpath2": returnpath2,
            "returnpath3": returnpath3,
            "at": False,
            "keyboard": keyboard,
            "markdown": markdown,
            }
