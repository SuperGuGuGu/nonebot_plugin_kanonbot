# coding=utf-8
import random
import time

from nonebot import logger
import nonebot
import os
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from .config import kn_config, _zhanbu_datas, _config_list
from .tools import get_file_path, connect_api, new_background2

config = nonebot.get_driver().config
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


def plugins_zhanbu(qq, cachepath):
    message = None
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


async def plugins_config(command_name: str, config_name: str, groupcode: str):
    # 默认变量与判断属于那个操作
    message = None
    returnpath = None
    command_name = command_name.removeprefix("config")
    if command_name == "开启":
        command_state = True
    elif command_name == "关闭":
        command_state = False
    else:
        command_state = "查询"

    # 匹配匹配对应的名称（commandname）
    config_list = _config_list()
    config_real_name = ""
    for name in config_list:
        config = config_list[name]
        if config_name == config["name"]:
            config_real_name = name
            break

    # 如果找不到名称则返回查询出错
    if command_state != "查询":
        if config_real_name == "":
            message = "设置失败，请检查名称是否正确"
            return message, returnpath

    # 连接数据库并进行下一步操作
    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db_path = dbpath + "config.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 读取对应表格，如不存在则创建
    # if not os.path.exists(db_path):
    #     cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if groupcode not in tables:
        cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")

    if command_state != "查询":
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
        configs = {}
        for config_name in config_list:
            config = config_list[config_name]
            cursor.execute(f'SELECT * FROM {groupcode} WHERE command = "{config_name}"')
            data = cursor.fetchone()
            if data is not None:
                config_state = data[1]  # 有群数据，读取群数据
                # 将神奇的数据库读取出来的1改为True
                # 存进去的是True，读出来的是1
                if config_state == 1:
                    config_state = True
                else:
                    config_state = False
            else:
                config_state = config["state"]  # 无群设置数据，读取默认数据

            group = config["group"]
            config_name = config["name"]
            if group not in list(configs):
                configs[group] = {"True": [], "False": []}
            configs[group][str(config_state)].append(config_name)
        # 跟读读取的json数据绘制开关列表
        image = await new_background2(
            1500, 1110, draw_name="KanonBot", draw_title="功能列表"
        )
        draw = ImageDraw.Draw(image)
        if kn_config("kanon_api-state"):
            # 如果开启了api，则从服务器下载字体数据
            fontfile = await get_file_path("SourceHanSansK-Normal.ttf")
        else:
            fontfile = None
        font = ImageFont.truetype(font=fontfile, size=20)
        draw.text(xy=(520, 90), text=groupcode, fill=(100, 100, 100), font=font)
        x = 303
        y = 196
        printx = x
        printy = y
        for config in configs:
            groupname = config
            print(groupname)
            fortlen = 45
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载字体数据
                fontfile = await get_file_path("SourceHanSansK-Medium.ttf")
            else:
                fontfile = None
            font = ImageFont.truetype(font=fontfile, size=20)
            draw.text(xy=(printx, printy), text=groupname, fill=(24, 148, 227), font=font)
            printy += fortlen + 8
            configlist = configs[groupname]["True"]
            fortlen = 40
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载字体数据
                fontfile = await get_file_path("SourceHanSansK-Normal.ttf")
            else:
                fontfile = None
            font = ImageFont.truetype(font=fontfile, size=20)
            xnum = 0
            for configname in configlist:
                xnum += 1
                if xnum >= 5:
                    xnum = 1
                    printy += fortlen + 5
                    printx = x
                draw.text(xy=(printx, printy), text=configname, fill=(0, 0, 0), font=font)
                printx += 300

            configlist = configs[groupname]["False"]
            xnum = 0
            for configname in configlist:
                xnum += 1
                if xnum >= 5:
                    xnum = 1
                    printy += fortlen + 5
                    printx = x
                draw.text(xy=(printx, printy), text=configname, fill=(150, 150, 150), font=font)
                printx += 300

            printy += fortlen + 5
            printx = x

        if kn_config("kanon_api-state"):
            # 如果开启了api，则从服务器下载字体数据
            fontfile = await get_file_path("SourceHanSansK-Normal.ttf")
        else:
            fontfile = None
        font = ImageFont.truetype(font=fontfile, size=40)
        text = "发送“开启/关闭 功能名”来 开启/关闭 相关功能。例：“开启 emoji”"
        draw.text(xy=(290, 940), text=text, fill="#001e36", font=font)

        # 保存内容
        date_year = str(time.strftime("%Y", time.localtime()))
        date_month = str(time.strftime("%m", time.localtime()))
        date_day = str(time.strftime("%d", time.localtime()))
        timenow = str(time.strftime("%H-%M-%S", time.localtime()))
        returnpath = f"{basepath}cache/{date_year}/{date_month}/{date_day}config/"
        if not os.path.exists(returnpath):
            os.makedirs(returnpath)
        returnpath = f"{returnpath}{timenow}.png"
        image.save(returnpath)

    # except Exception as e:
    #     message = "设置出错惹 >_<"
    cursor.close()
    conn.close()
    return message, returnpath
