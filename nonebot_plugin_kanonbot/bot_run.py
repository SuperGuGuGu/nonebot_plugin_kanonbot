# coding=utf-8
from .config import kn_config, _config_list
from .tools import lockst, locked, command_cd
import plugins
import time
import nonebot
from nonebot import logger
import os
import sqlite3

config = nonebot.get_driver().config
# 配置1
try:
    adminqq = config.superusers
    adminqq = list(adminqq)
except Exception as e:
    adminqq = []
# 配置2：
try:
    basepath = config.kanon_basepath
    if "\\" in basepath:
        basepath = basepath.replace("\\", "/")
    if basepath.startswith("./"):
        basepath = os.path.abspath('.') + basepath.removeprefix(".")
        if not basepath.endswith("/"):
            basepath += "/"
    else:
        basepath += "/"
except Exception as e:
    basepath = os.path.abspath('.') + "/KanonBot/"


def botrun(bot, allfriendlist, allgroupmemberlist, msg_info):
    # ## 初始化 ##
    lockdb = './lock.db'
    lockst(lockdb)
    global image, addimage
    msg = msg_info["msg"]
    commands = msg_info["commands"]
    command = str(commands[0])
    if len(commands) >= 2:
        command2 = commands[1]
    else:
        command2 = ''
    atmsg = atmsgs = msg_info["atmsgs"]
    info_premission = msg_info["info_premission"]
    commandname = msg_info["commandname"]
    groupcode = msg_info["groupcode"]
    qq = msg_info["qq"]
    imgmsgs = msg_info["imgmsgs"]
    botid = bot.self_id()

    if len(atmsg) >= 1:
        qq2 = atmsgs[0]
    else:
        if len(command2) >= 5:
            try:
                qq2 = int(command2)
                qq2 = str(qq2)
            except:
                qq2 = ''
        else:
            qq2 = ''
    image_face = []
    image_face2 = []
    username = ''
    qq2name = ''
    # 提取好友、群列表
    friendlist = []
    if allfriendlist:
        for friendinfo in allfriendlist:
            friendlist.append(str(friendinfo['user_id']))
    groupmemberlist = []
    if allgroupmemberlist:
        for memberinfo in allgroupmemberlist:
            groupmemberlist.append(str(memberinfo['user_id']))

    # ## 变量初始化 ##
    date = str(time.strftime("%Y-%m-%d", time.localtime()))
    date_year = str(time.strftime("%Y", time.localtime()))
    date_month = str(time.strftime("%m", time.localtime()))
    date_day = str(time.strftime("%d", time.localtime()))
    timenow = str(time.strftime("%H-%M-%S", time.localtime()))
    dateshort = date_year + date_month + date_day
    time_h = str(time.strftime("%H", time.localtime()))
    time_m = str(time.strftime("%M", time.localtime()))
    time_s = str(time.strftime("%S", time.localtime()))
    timeshort = time_h + time_m + time_s

    cachepath = basepath + "cache/" + date_year + '/' + date_month + '/' + date_day + '/'
    if not os.path.exists(cachepath):
        os.makedirs(cachepath)
    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)

    # 貌似还没用上，先放着
    # heartdb = basepath + "cache/heart.db"
    # gameinglistdb = basepath + "cache/gameing/gameing-list.db"
    # imagepath = basepath + "APIimage/"
    # logdb = basepath + "cache/" + "log/log.db"
    # errorimagepath = imagepath + "Message/error.png"
    # configpart = dbpath + "config/"
    # chickindbname = dbpath + "chickin/chickin.db"
    # lpdbname = dbpath + "wlp/wlp.db"
    # emojidbname = dbpath + "emoji/emoji.db"
    # configlistdb = configpart + "config.db"
    # fontdb = configpart + "font.db"
    # groupconfigdb = configpart + "groupconfig.db"

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
    coolingmessage = "指令冷却中"

    # 添加函数
    # 查询功能开关
    def getconfig(commandname: str) -> bool:
        """
        查询指令是否开启
        :param commandname: 查询的命令名
        :return: True or False
        """
        db_path = dbpath + "comfig.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if not os.path.exists(db_path):
            # 数据库文件 如果文件不存在，会自动在当前目录中创建
            cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")
        cursor.execute(f'SELECT * FROM {groupcode} WHERE command = "{commandname}"')
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
                cursor.execute(f"create table list(command VARCHAR(10) primary key, state BOOLEAN(20), "
                               f"message VARCHAR(20), group VARCHAR(20), name VARCHAR(20))")
            cursor.execute(f'SELECT * FROM list WHERE command="{commandname}"')
            data = cursor.fetchone()
            if data is not None:
                state = data[1]
                cursor.execute(f"replace into {groupcode} ('command','state') values('{commandname}',{state})")
                conn.commit()
            else:
                config_list = _config_list()
                if commandname in list(config_list):
                    state = config_list[commandname]["state"]
                else:
                    state = False
        cursor.close()
        conn.close()
        return state

    # 查询冷却
    def command_cooling() -> bool:
        # 查询冷却代码位置
        return False

    # ## 心跳服务相关 ##
    # 判断心跳服务是否开启。
    if kn_config("botswift-state"):
        # 如所在的群关闭心跳功能，则全部响应
        ignore_list = kn_config("botswift-ignore_list")
        if groupcode[3:] in kn_config("botswift-ignore_list"):
            run = True
    # 如果需要继续运行则True
    run = True

    if run is True:
        # 处理消息
        if "zhanbu" == commandname:
            if getconfig("zhanbu"):
                if getconfig("commandcd") and info_premission != "10" and qq not in adminqq:
                    coolingdb = dbpath + "cooling.db"
                    cooling = command_cd(qq, groupcode, timeshort, coolingdb)
                    if cooling != "off":
                        code = 1
                        coolingmessage = f"指令冷却中（{cooling}s)"
                        logger.info("指令冷却中")
                    else:
                        at = 'on'
                        message, returnpath = plugins.plugins_zhanbu(qq, cachepath)
                        if returnpath is not None:
                            code = 3
                        else:
                            code = 1
        elif "###" == commandname:
            pass

    # 这两位置是放心跳服务相关代码，待后续完善
    # 本bot存入mainbot数据库
    # 保活

    # log记录
    # 目前还不需要这个功能吧，先放着先

    # 返回消息处理
    code = str(code)
    if 'p' in groupcode:
        at = 'off'
    if at == 'on':
        at = qq
    locked(lockdb)
    return {"code": code,
            "message": message,
            "returnpath": returnpath,
            "at": at,
            "returnpath2": returnpath2,
            "returnpath3": returnpath3
            }
