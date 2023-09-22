# coding=utf-8
import random
from nonebot import logger
import nonebot
import os
import sqlite3
from .config import kn_config, _zhanbu_datas, _config_list
from .tools import get_file_path, connect_api

config = nonebot.get_driver().config
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


def plugins_zhanbu(qq, cachepath):
    message = ""
    returnpath = None

    zhanbudb = cachepath + 'zhanbu/'
    if not os.path.exists(zhanbudb):
        os.makedirs(zhanbudb)
    zhanbudb = f"{zhanbudb}zhanbu.db"

    conn = sqlite3.connect(zhanbudb)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        # 数据库列表转为序列
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "zhanbu" not in tables:
            cursor.execute('create table zhanbu (userid varchar(10) primary key, id varchar(20))')
        cursor.execute(f'select * from zhanbu where userid = "{qq}"')
        data = cursor.fetchone()
        if data is None:
            # 随机卡牌的好坏。1/3是坏，2/3是好
            # 但是貌似有些是混在一起的，有空再去琢磨一下概率（下次一定，咕咕咕
            zhanbu_type = random.randint(0, 2)
            if zhanbu_type == 0:
                zhanbu_type = "bad"
            else:
                zhanbu_type = "good"
            zhanbu_id = random.choice(list(_zhanbu_datas()[zhanbu_type]))
            zhanbu_data = _zhanbu_datas()[zhanbu_type][zhanbu_id]
            zhanbu_name = zhanbu_data["name"]
            zhanbu_message = zhanbu_data["message"]
            # 写入占卜结果
            cursor.execute(f'replace into zhanbu("userid","id") values("{qq}", "{zhanbu_id}")')

            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    image = connect_api("image", url)
                    image.save(returnpath)
                    message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            else:
                # 使用本地数据
                # message = f"今日占卜结果：{zhanbu_data['title']}\n{zhanbu_data['message']}"
                message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            pass
        else:
            zhanbu_name = ""
            zhanbu_message = ""
            zhanbu_id = str(data[1])
            zhanbu_datas = _zhanbu_datas()
            for ids in zhanbu_datas["good"]:
                if ids == zhanbu_id:
                    zhanbu_data = zhanbu_datas["good"]
                    zhanbu_name = zhanbu_data[ids]["name"]
                    zhanbu_message = zhanbu_data[ids]["message"]
                    break
            for ids in zhanbu_datas["bad"]:
                if ids == zhanbu_id:
                    zhanbu_data = zhanbu_datas["bad"]
                    zhanbu_name = zhanbu_data[ids]["name"]
                    zhanbu_message = zhanbu_data[ids]["message"]
                    break

            message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    image = connect_api("image", url)
                    image.save(returnpath)
    except:
        logger.error("KanonBot插件出错-plugin-zhanbu")
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return message, returnpath


def plugins_config(command_name: str, config_name: str, groupcode: str):
    message = ""
    returnpath = None
    command_name = command_name.removeprefix("config")
    if command_name == "开启":
        command_state = True
    elif command_name == "关闭":
        command_state = False
    else:
        command_state = "查询"
    config_list = _config_list()
    config_real_name = ""
    for name in config_list:
        config = config_list[name]
        if config_name == config["name"]:
            config_real_name = name
            break

    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db_path = dbpath + "comfig.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if not os.path.exists(db_path):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if groupcode not in tables:
        cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")

    if command_state is True or command_state is False:
        # 开启或关闭功能
        cursor.execute(f'SELECT * FROM {groupcode} WHERE command = "{config_real_name}"')
        data = cursor.fetchone()
        if data is not None:
            state = data[1]
            if state == command_state:
                message = f"{config_name}已{command_name}"
            else:
                cursor.execute(f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
                conn.commit()
            message = f"{config_name}已{command_name}"
        else:
            cursor.execute(f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
            conn.commit()
            message = f"{config_name}已{command_name}"
    else:
        # 查询开启的功能
        code = 1
        message = "查询功能"
        pass
    cursor.close()
    conn.close()
    return message, returnpath
