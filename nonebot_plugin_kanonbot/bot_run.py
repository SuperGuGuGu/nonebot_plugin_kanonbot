# coding=utf-8
import re

from .config import kn_config, _config_list
from .tools import lockst, locked, command_cd, get_command
from .plugins import (
    plugins_zhanbu,
    plugins_config,
    plugins_emoji_xibao, plugins_emoji_yizhi, plugins_game_cck, plugins_game_blowplane
)
import time
import nonebot
from nonebot import logger
import os
import sqlite3

config = nonebot.get_driver().config
# 配置1
try:
    adminqq = list(config.superusers)
except Exception as e:
    adminqq = []
# 配置2：
try:
    basepath = config.kanonbot_basepath
    if "\\" in basepath:
        basepath = basepath.replace("\\", "/")
    if basepath.startswith("./"):
        basepath = os.path.abspath('.') + basepath.removeprefix(".")
        if not basepath.endswith("/"):
            basepath += "/"
    else:
        if not basepath.endswith("/"):
            basepath += "/"
except Exception as e:
    basepath = os.path.abspath('.') + "/KanonBot/"
if not os.path.exists(basepath):
    os.makedirs(basepath)


async def botrun(msg_info):
    logger.info("KanonBot-0.2.5")
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
    else:
        command2 = None
    at_datas: list = msg_info["at_datas"]
    user_permission: str = msg_info["user"]["permission"]
    user_id: str = msg_info["user"]["id"]
    user_avatar: str = msg_info["user"]["avatar"]
    user_nick_name: str = msg_info["user"]["nick_name"]
    if user_nick_name is not None:
        user_username: str = user_nick_name
    else:
        user_username: str = msg_info["user"]["username"]
    commandname: str = msg_info["commandname"]
    guild_id: str = msg_info["guild_id"]
    channel_id: str = msg_info["channel_id"]
    imgmsgs = msg_info["imgmsgs"]
    botid: str = msg_info["bot_id"]
    friend_list: list = msg_info["friend_list"]
    group_member_list: list = msg_info["group_member_list"]
    event_name: str = msg_info["event_name"]

    image_face = []
    image_face2 = []
    username = None
    qq2name = None

    # ## 变量初始化 ##
    date: str = time.strftime("%Y-%m-%d", time.localtime())
    date_year: str = time.strftime("%Y", time.localtime())
    date_month: str = time.strftime("%m", time.localtime())
    date_day: str = time.strftime("%d", time.localtime())
    time_h: str = time.strftime("%H", time.localtime())
    time_m: str = time.strftime("%M", time.localtime())
    time_s: str = time.strftime("%S", time.localtime())
    time_now: str = str(time.time())
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
        conn = sqlite3.connect(f"{basepath}db/comfig.db")
        cursor = conn.cursor()
        state = False
        try:
            if not os.path.exists(f"{basepath}db/comfig.db"):
                # 数据库文件 如果文件不存在，会自动在当前目录中创建
                cursor.execute(f"create table {guild_id}(command VARCHAR(10) primary key, state BOOLEAN(20))")
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
            datas = cursor.fetchall()
            tables = []
            for data in datas:
                if data[1] != "sqlite_sequence":
                    tables.append(data[1])
            if guild_id not in tables:
                cursor.execute(f"create table {guild_id}(command VARCHAR(10) primary key, state BOOLEAN(20))")
            cursor.execute(f'SELECT * FROM {guild_id} WHERE command = "{channel_id}-{commandname}"')
            data = cursor.fetchone()
            if data is not None:
                state = data[1]
            else:
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                # 数据库列表转为序列
                tables = []
                for data in datas:
                    if data[1] != "sqlite_sequence":
                        tables.append(data[1])
                if "list" not in tables:
                    cursor.execute("create table list(command VARCHAR(10) primary key, state BOOLEAN(20), "
                                   "message VARCHAR(20), 'group' VARCHAR(20), name VARCHAR(20))")
                cursor.execute(f'SELECT * FROM list WHERE command="{channel_id}-{commandname}"')
                data = cursor.fetchone()
                if data is not None:
                    state = data[1]
                    cursor.execute(
                        f'replace into {guild_id} ("command","state") values("{channel_id}-{commandname}",{state})')
                    conn.commit()
                else:
                    config_list = _config_list()
                    if commandname in list(config_list):
                        state = config_list[commandname]["state"]
                    else:
                        state = False
        finally:
            pass
        cursor.close()
        conn.close()
        return state

    # ## 心跳服务相关 ##
    # 判断心跳服务是否开启。
    if kn_config("botswift-state"):
        # 读取忽略该功能的群聊
        ignore_list = kn_config("botswift-ignore_list")
        if guild_id.startswith("channel-"):
            if guild_id[8:] in kn_config("botswift-ignore_list"):
                run = True
        elif guild_id.startswith("group-"):
            if guild_id[6:] in kn_config("botswift-ignore_list"):
                run = True

    # 处理消息
    if commandname.startswith("config"):
        if user_permission == 7 or user_id in adminqq or commandname == "config查询":
            logger.info(f"run-{commandname}")
            if command2 is not None:
                config_name = get_command(command2)[0]
            else:
                config_name = None
            message, returnpath = plugins_config(commandname, config_name, channel_id)
            if message is not None:
                code = 1
            else:
                code = 2
        else:
            logger.info(f"run-{commandname}, 用户权限不足")
            # code = 1
            # message = "权限不足"

    elif commandname.startswith("群聊功能-"):
        commandname = commandname.removeprefix("群聊功能-")
        if "zhanbu" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != "7" and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    at = True
                    logger.info(f"run-{commandname}")
                    message, returnpath = await plugins_zhanbu(user_id, cachepath)
                    if returnpath is not None:
                        code = 3
                    else:
                        code = 1
            else:
                at = True
                logger.info(f"run-{commandname}")
                message, returnpath = await plugins_zhanbu(user_id, cachepath)
                if returnpath is not None:
                    code = 3
                else:
                    code = 1

    elif commandname.startswith("表情功能-"):
        commandname = commandname.removeprefix("表情功能-")
        if "喜报" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != "7" and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    returnpath = await plugins_emoji_xibao(command, command2, imgmsgs)
                    code = 2
            else:
                logger.info(f"run-{commandname}")
                returnpath = await plugins_emoji_xibao(command, command2, imgmsgs)
                code = 2
        if "一直" == commandname and getconfig(commandname):
            if getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id,
                    groupcode=channel_id,
                    timeshort=time_now,
                    coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != "7" and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    if imgmsgs:
                        returnpath = await plugins_emoji_yizhi(imgmsgs[0])
                    else:
                        returnpath = await plugins_emoji_yizhi(user_avatar)
                    code = 2
            else:
                at = True
                logger.info(f"run-{commandname}")
                if imgmsgs:
                    returnpath = await plugins_emoji_yizhi(imgmsgs[0])
                else:
                    returnpath = await plugins_emoji_yizhi(user_avatar)
                code = 2
    elif commandname.startswith("小游戏"):
        commandname = commandname.removeprefix("小游戏-")
        if "猜猜看" == commandname and getconfig(commandname):
            # 转换命令名
            if command2 is not None:
                command = command2
            if command == "cck":
                command = "猜猜看"
            elif command == "bzd":
                command = "不知道"

            # 判断指令冷却
            if command == "猜猜看" and getconfig("commandcd"):
                cooling = command_cd(
                    user_id=user_id, groupcode=channel_id, timeshort=time_now, coolingdb=f"{dbpath}cooling.db")
                if cooling != "off" and user_permission != "7" and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath = await plugins_game_cck(command=command, channel_id=channel_id)
            else:
                logger.info(f"run-{commandname}")
                code, message, returnpath = await plugins_game_cck(command=command, channel_id=channel_id)
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
                if cooling != "off" and user_permission != "7" and user_id not in adminqq:
                    code = 1
                    message = f"指令冷却中（{cooling}s)"
                    logger.info("指令冷却中")
                else:
                    logger.info(f"run-{commandname}")
                    code, message, returnpath = await plugins_game_blowplane(command=command, channel_id=channel_id)
            else:
                logger.info(f"run-{commandname}")
                code, message, returnpath = await plugins_game_blowplane( command=command, channel_id=channel_id)

    elif "###" == commandname:
        pass

    # 这两位置是放心跳服务相关代码，待后续完善
    # 本bot存入mainbot数据库
    # 保活

    # log记录
    # 目前还不需要这个功能吧，先放着先

    # 返回消息处理
    locked(lockdb)
    return {"code": code,
            "message": message,
            "returnpath": returnpath,
            "returnpath2": returnpath2,
            "returnpath3": returnpath3
            }
