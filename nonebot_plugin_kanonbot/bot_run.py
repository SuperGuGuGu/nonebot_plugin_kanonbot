# coding=utf-8
from .config import kn_config, _config_list
from .tools import lockst, locked
import time
import nonebot
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
    qq = msg_info["qq"]
    groupcode = msg_info["groupcode"]
    botid = bot.self_id()
    atmsg = atmsgs = msg_info["atmsgs"]
    imgmsgs = msg_info["imgmsgs"]
    info_premission = msg_info["info_premission"]

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

    # 添加函数
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

    # ## 心跳服务相关 ##
    # 判断心跳服务是否开启。
    if kn_config("botswift-state"):
        # 如所在的群关闭心跳功能，则全部响应
        ignore_list = kn_config("botswift-ignore_list")
        if groupcode[3:] in kn_config("botswift-ignore_list"):
            send = True
    # 如果需要发送则True
    send = True

    # ## 指令冷却 ##
    # 读取该群是否开启指令冷却
    if getconfig("commandcd"):
        # 群主无冷却
        if info_premission == "10":
            send = True
        # bot管理员无冷却
        elif qq in adminqq:
            send = True
        else:
            # 判断冷却代码位置（待更新）
            send = True










    locked(lockdb)
    return
