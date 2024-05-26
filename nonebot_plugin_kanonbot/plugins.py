# coding=utf-8
import json
import math
import random
import time
from nonebot import logger
import os
import sqlite3
from .config import _zhanbu_datas, _config_list, _jellyfish_box_datas, jellyfish_box_draw_config
from .tools import kn_config, connect_api, save_image, image_resize2, draw_text, get_file_path, new_background, \
    circle_corner, get_command, get_unity_user_data, json_to_str, _config, imgpath_to_url, del_files2, \
    statistics_list, get_unity_user_id, get_image_path, load_image, list_in_list
from PIL import Image, ImageDraw, ImageFont
import numpy
from datetime import datetime

basepath = _config["basepath"]
adminqq = _config["superusers"]
kn_cache = {}


async def plugin_zhanbu(user_id, cachepath):
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
        cursor.execute(f'select * from zhanbu where userid = "{user_id}"')
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
            cursor.execute(f'replace into zhanbu("userid","id") values("{user_id}", "{zhanbu_id}")')

            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    try:
                        image = await connect_api("image", url)
                        image.save(returnpath)
                    except Exception as e:
                        image = await draw_text("获取图片出错", 50, 10)
                        logger.error(f"获取图片出错:{e}")
                        returnpath = save_image(image)
                    message = f"抽到了一张塔罗牌：{zhanbu_name}\n{zhanbu_message}"
            else:
                # 使用本地数据
                # message = f"抽到了一张塔罗牌：{zhanbu_data['title']}\n{zhanbu_data['message']}"
                message = f"抽到了一张塔罗牌：{zhanbu_name}\n{zhanbu_message}"
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

            message = f"抽到这张塔罗牌哦：{zhanbu_name}\n{zhanbu_message}"
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    try:
                        image = await connect_api("image", url)
                        image.save(returnpath)
                    except Exception as e:
                        image = await draw_text("获取图片出错", 50, 10)
                        logger.error(f"获取图片出错:{e}")
                        returnpath = save_image(image)
    except Exception as e:
        logger.error("KanonBot插件出错-plugin-zhanbu")
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return message, returnpath


async def plugin_checkin(user_id: str, date: str):
    """
    签到功能，state=0,message="签到成功" state=1,message="签到失败"
    :param user_id: 用户id
    :param date: 今日日期
    :return: {"state": state, "message": message}
    """
    state = 0
    message = ""
    date: str = time.strftime("%Y-%m-%d", time.localtime())

    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    if not os.path.exists(f"{basepath}db/"):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        os.makedirs(f"{basepath}db/")
        cursor.execute(f"CREATE TABLE checkin(user_id VARCHAR (10) PRIMARY KEY, point BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "checkin" not in tables:
        cursor.execute(f"create table checkin(user_id VARCHAR(10) primary key, date VARCHAR(10), point INT(20))")
    try:
        cursor.execute(f'select * from checkin where user_id = "{user_id}"')
        data = cursor.fetchone()
        add_point = random.randint(2, 3)
        if data is None:
            # 未有数据，签到并返回成功
            point = add_point
            cursor.execute(f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
            conn.commit()
            state = 0
        else:
            last_data = data[1]
            point = data[2]
            if date == last_data:
                # 已经签到过，不再签到
                state = 1
            else:
                # 今日未签到，正常签到
                point = int(point) + add_point
                cursor.execute(f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
                conn.commit()
                state = 0
    except Exception:
        raise Exception
    finally:
        cursor.close()
        conn.close()

    # 创建返回的消息
    if state == 0:
        message = f"签到成功，获得{add_point}根薯条，现在有{point}根薯条"
    else:
        message = f"今天签到过啦，{point}根薯条还不够吃嘛…QAQ…"

    return state, message


async def plugin_jellyfish_box(user_id: str, user_name: str, channel_id: str, msg: str, time_now: int):
    """
    群聊功能-水母箱
    :return:
    """
    """
    命令列表：
    水母箱：总命令，输入可查看水母箱和相关指令列表
    查看水母箱：获取水母箱的图片
    帮助: 指令说明
    抓水母: 抓水母，并放入箱中
    投喂: 往杠中添加饲料（未实装）
    换水: 恢复水质状态（未实装）
    丢弃: 丢弃指定水母
    装饰: 开启装饰模式指令（未实装）
    结束: 关闭水母箱对话进程（未实装）
    """
    # 指令解析
    commands = get_command(msg)
    command = commands[0]
    if len(commands) > 1:
        command2 = commands[1]
    else:
        command2 = None

    # 添加必要参数
    code = 0
    message = None
    returunpath = None
    trace = []  # 用于日志记录插件运行内容
    jellyfish_group_list = ["perfect", "great", "good", "normal", "special", "ocean"]
    jellyfish_box_datas = await _jellyfish_box_datas()  # 插件数据
    event_datas = jellyfish_box_datas["event_datas"]  # 所有事件
    jellyfish_datas = jellyfish_box_datas["jellyfish_datas"]  # 所有水母
    food_datas = jellyfish_box_datas["food_datas"]  # 所有事件
    ornament_datas = jellyfish_box_datas["ornament_datas"]  # 所有装饰物
    medal_datas = jellyfish_box_datas["medal_datas"]  # 所有勋章
    user_data = get_unity_user_data(user_id)

    date_y: str = time.strftime("%Y", time.localtime(time_now))
    date_m: str = time.strftime("%m", time.localtime(time_now))
    date_d: str = time.strftime("%d", time.localtime(time_now))
    time_h: int = int(time.strftime("%H", time.localtime(time_now)))

    global kn_cache

    # 添加数据参数
    news = []
    new_jellyfish = []
    command_prompt_list = []
    jellyfish_menu = []
    """
    示例：
    :param news: 新增的水母列表
    :param new_jellyfish: 新闻列表，显示最近的动态
    :param command_prompt_list: 指令列表，建议可以输入的指令

    nwes = [
        {
        "icon": file_path,  # 图片路径
        "title": "标题",
        "message": "事件介绍"
        },
        {
        "icon": None,  # 没有图片
        "title": "这是没有图标的消息事件",
        "message": "这条消息没有图标，这是为什么呢？"
        }
    ]

    new_jellyfish = [
        {
        "id": id,  # 水母的id
        "number": 10,  # 水母数量
        "name": "水母名称",
        "message": "水母介绍"
        },
        {
        "id": id,  # 水母的id
        "number": 10,  # 水母数量
        "name": "水母名称",
        "message": "这条消息没有图标，这是为什么呢？"
        }
    ]
    
    command_prompt_list = [
        {
        "title": "/水母箱 抓水母",
        "message": "发送指令来获取新水母"
        }
    ]
    """
    # 读取用户水母箱的状态
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "jellyfish_box" not in tables:
            cursor.execute(
                'create table "jellyfish_box"'
                '(user_id VARCHAR(10) primary key, data VARCHAR(10))')
        cursor.execute(f'SELECT * FROM "jellyfish_box" WHERE user_id = "{user_id}"')
        data = cursor.fetchone()
    except:
        logger.error("水母箱读取用户数据出错")
        data = "error"
    cursor.close()
    conn.close()

    if data is None:
        box_data = {
            "info": {
                "oner": user_id,
                "oner_name": user_name
            },
            "sign_in_time": int(time_now / 3600 - 2) * 3600,  # 上次抓水母时间小时计算
            "refresh_time": int(time_now / 3600) * 3600,  # 更新时间小时计算
            "jellyfish": {"j1": {"number": 3}},
            "ornament": {},
            "salinity": 30,  # 千分盐度
            "temperature": 25,  # 温度
            "draw_style": "normal"  # 绘制风格
        }
    else:
        box_data = json.loads(data[1])

    # 绘制样式
    draw_dark_model = False if 5 <= time_h <= 20 else True
    draw_model_list = {
        "04-01": "mixieer",
        "--ppp--": "--",
        "03-23": "birthday_rimi",
        "05-19": "birthday_saya",
        "07-14": "birthday_kasumi",
        "10-27": "birthday_arisa",
        "12-04": "birthday_tae",
        "--ag--": "--",
        "01-07": "birthday_tsugumi",
        "04-10": "birthday_ran",
        "04-15": "birthday_tomoe",
        "09-03": "birthday_moca",
        "10-23": "birthday_himari",
        "--r--": "--",
        "03-20": "birthday_hikawa",
        "07-03": "birthday_ako",
        "08-25": "birthday_lisa",
        "10-17": "birthday_rinko",
        "10-26": "birthday_yukina",
        "--pp--": "--",
        "04-06": "birthday_chisato",
        "06-27": "birthday_eve",
        "11-03": "birthday_maya",
        "12-27": "birthday_aya",
        "--hhw--": "--",
        "02-28": "birthday_kaoru",
        "05-11": "birthday_kanon",
        "07-30": "birthday_misaki",
        "08-08": "birthday_kokoro",
        "10-01": "birthday_hagumi",
        "--m--": "--",
        "02-19": "birthday_mashiro",
        "06-16": "birthday_nanami",
        "09-15": "birthday_tsukushi",
        "11-19": "birthday_rui",
        "12-16": "birthday_toko",
        "--ras--": "--",
        "01-13": "birthday_rei",
        "03-25": "birthday_pareo",
        "05-12": "birthday_masuki",
        "07-17": "birthday_rokka",
        "12-07": "birthday_chuchu",
        "--mygo--": "--",
        "02-22": "birthday_rana",
        "05-27": "birthday_soyo",
        "08-09": "birthday_taki",
        "09-08": "birthday_anon",
        "11-22": "birthday_tomori",
        "--ave--": "--",
        "01-14": "birthday_若叶睦",
        "02-14": "birthday_丰川祥子",
        "04-07": "birthday_八幡海铃",
        "06-26": "birthday_uika",
        "06-01": "birthday_祐天寺若麦",
    }
    if f"{date_m}-{date_d}" in list(draw_model_list):
        draw_model = draw_model_list[f"{date_m}-{date_d}"]
    else:
        draw_model = "normal"

    if "draw_model" in list(box_data) and draw_model == "normal":
        draw_model = box_data["draw_model"]

    draw_config = jellyfish_box_draw_config(draw_model, draw_dark_model)

    # 更新水母箱状态，并写入
    refresh: bool = False  # 判断是否更新
    refresh_period: int = 0  # 要更新的周期
    if (time_now - box_data["refresh_time"]) > 3600:
        # 超过1小时，进行更新
        refresh_period = int((time_now - box_data["refresh_time"]) / 3600)  # 要更新的周期数量，int
        if refresh_period > 0:
            refresh = True
            box_data["refresh_time"] += refresh_period * 3600
        if refresh_period > 168:
            # 超过7天未抓，减少刷新次数
            refresh_period = 24
        elif refresh_period > 96:
            # 超过4天未抓，减少刷新次数
            refresh_period = 96

    trace.append(f"将刷新{refresh_period}次")

    if refresh:
        # 更新数据
        logger.debug("正在刷新水母箱")
        if len(box_data["jellyfish"]) == 0:
            # 无水母，仅更新时间
            box_data["refresh_time"] = int(time_now / 3600) * 3600
        elif command not in ["水母箱", "抓水母"]:
            pass  # 运行命令中，跳过更新
        else:
            # 更新时间并更新事件
            box_data["refresh_time"] = int(time_now / 3600) * 3600

            # 统计现有水母数量
            jellyfish_number = 0
            for jellyfish_id in box_data["jellyfish"]:
                jellyfish_number += box_data["jellyfish"][jellyfish_id]["number"]

            # 更新繁殖
            num = refresh_period
            if num > 72:
                num = 72  # 最高单次更新3天的数量
            new = {}
            while num > 0:
                num -= 1
                for jellyfish_id in box_data["jellyfish"]:
                    reproductive_rate = jellyfish_datas[jellyfish_id]["reproductive_rate"]
                    if reproductive_rate == 0:
                        continue

                    # 计算繁殖概率
                    add_jellyfish = 0
                    rate = reproductive_rate / 30 / 24 * box_data["jellyfish"][jellyfish_id]["number"]

                    if jellyfish_number < 10:
                        rate = rate / jellyfish_number
                    elif jellyfish_number < 20:
                        rate = rate / jellyfish_number
                    elif jellyfish_number < 40:
                        rate = rate / jellyfish_number
                    elif jellyfish_number < 80:
                        rate = rate / jellyfish_number
                    elif jellyfish_number < 160:
                        rate = rate / jellyfish_number
                    else:
                        rate = rate / jellyfish_number

                    if rate > 1:
                        add_jellyfish += int(rate)
                        rate -= int(rate)

                    # 判断是否繁殖
                    p = numpy.array([rate, (1 - rate)]).ravel()
                    choose = numpy.random.choice(["True", "False"], p=p)
                    if choose == "True":
                        add_jellyfish += 1

                    # 添加进水母箱
                    if add_jellyfish != 0:
                        if jellyfish_id in new:
                            new[jellyfish_id] += add_jellyfish
                        else:
                            new[jellyfish_id] = add_jellyfish
                        box_data["jellyfish"][jellyfish_id]["number"] += add_jellyfish

            for jellyfish_id in list(new):
                pass
            # 按周期更新数据
            while refresh_period > 0:
                refresh_period -= 1
                if len(news) > 9:
                    # 单次最多更新10条消息
                    break
                # 开始随机事件

                # 提取事件id与事件概率，用来选取事件
                event_list = []
                for event_id in event_datas:
                    choose = random.randint(0, 100000) / 100000
                    if choose < event_datas[event_id]["probability"]:
                        event_list.append(event_id)

                if event_list:
                    event_id = random.choice(event_list)
                else:
                    continue

                if event_id not in ["e1", "e2", "e3", "e4", "e5", "e7", "e8", "e9"]:
                    continue
                # 准备事件
                event_name: str = event_datas[event_id]["name"]
                event_message: str = event_datas[event_id]["message"]
                # event_icon = await get_file_path(f"plugin-jellyfish_box-{event_id}")
                event_icon: str | None = None

                trace.append(f"添加事件{event_id}")

                if event_id in ["e2"]:
                    # 无变化中立事件
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        num = box_data["jellyfish"][jellyfish_id]["number"]
                        while num > 0:
                            num -= 1
                            jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 1:
                        continue  # 没有水母，跳过事件
                    if len(news) < 7:
                        # 超过7条就不发中立事件的内容
                        news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e1":
                    # 判断事件是否成立
                    # 计算未受保护的水母的数量
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        if (jellyfish_datas[jellyfish_id]["protected"] is False or
                                box_data["jellyfish"][jellyfish_id]["number"] > 40):
                            num = box_data["jellyfish"][jellyfish_id]["number"]
                            while num > 0:
                                num -= 1
                                jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 11:
                        continue  # 少于11条，跳过事件
                    # 进行数据修改
                    subtract_quantity = int(len(jellyfish_list) / 10)  # 要减去的数量
                    # 挑选减去的列表
                    choose_list = []
                    while subtract_quantity > 0:
                        subtract_quantity -= 1
                        choose_jellyfish = random.choice(jellyfish_list)
                        jellyfish_list.remove(choose_jellyfish)
                        choose_list.append(jellyfish_list)
                    # 修改现有数据
                    for jellyfish_id in choose_list:
                        box_data["jellyfish"][jellyfish_id]["number"] -= 1
                        if box_data["jellyfish"][jellyfish_id]["number"] == 0:
                            box_data["jellyfish"].pop(jellyfish_id)
                    # 总结事件
                    event_message += ": "
                    # 统计各水母数量
                    choose_jellyfish = {}
                    for jellyfish_id in choose_list:
                        if jellyfish_id in list(choose_jellyfish):
                            choose_jellyfish[jellyfish_id] += 1
                        else:
                            choose_jellyfish[jellyfish_id] = 1
                    # 添加到消息中
                    for jellyfish_id in list(choose_jellyfish):
                        event_message += f"{jellyfish_datas[jellyfish_id]['name']}"
                        event_message += f"{choose_jellyfish[jellyfish_id]}只、"
                        trace.append(f"{event_id}-{jellyfish_id}减去{choose_jellyfish[jellyfish_id]}")

                    event_message.removesuffix("、")
                    event_message = event_message.replace("{num}", str(len(choose_list)))

                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e3":
                    # 判断事件是否成立
                    # 计算未受保护的水母的数量
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        if int(jellyfish_datas[jellyfish_id]["reproductive_rate"]) > 0:
                            num = box_data["jellyfish"][jellyfish_id]["number"]
                            while num > 0:
                                num -= 1
                                jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 1:
                        continue  # 少于1条，跳过事件
                    # 计算事件发生的内容
                    new_jellyfish_list = []
                    for jellyfish_id in jellyfish_list:
                        reproductive_rate = int(jellyfish_datas[jellyfish_id]["reproductive_rate"])
                        if random.randint(0, 30) < reproductive_rate:
                            new_jellyfish_list.append(jellyfish_id)
                    if len(new_jellyfish_list) > 1:
                        # 总结事件
                        event_message = f"新增了{len(new_jellyfish_list)}只水母，分别是:"
                        # 统计各种水母的数量，转成json
                        new_jellyfish_datas = {}
                        for jellyfish_id in new_jellyfish_list:
                            if jellyfish_id not in list(new_jellyfish_datas):
                                new_jellyfish_datas[jellyfish_id] = 1
                            else:
                                new_jellyfish_datas[jellyfish_id] += 1
                        # 进行数据修改
                        for jellyfish_id in new_jellyfish_datas:
                            number = new_jellyfish_datas[jellyfish_id]
                            box_data["jellyfish"][jellyfish_id]["number"] += number

                        # 读取水母名称并添加到列表
                        for jellyfish_id in new_jellyfish_datas:
                            jellyfish_name = jellyfish_datas[jellyfish_id]["name"]
                            num = new_jellyfish_datas[jellyfish_id]
                            event_message += f"{jellyfish_name}{num}只、"
                            trace.append(f"{event_id}-{jellyfish_id}增加{num}")

                        news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e4":
                    # 判断事件是否成立
                    # 计算水母的数量
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        num = box_data["jellyfish"][jellyfish_id]["number"]
                        while num > 0:
                            num -= 1
                            jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 1:
                        continue  # 少于1条，跳过事件
                    # 计算事件发生的内容
                    new_jellyfish_list = []
                    num = 5  # 增加的水母数量
                    event_message = event_message.replace("{num}", str(num))
                    while num > 0:
                        num -= 1
                        new_jellyfish_list.append(random.choice(jellyfish_list))

                    # 统计各种水母的数量，转成json
                    new_jellyfish_datas = {}
                    for jellyfish_id in new_jellyfish_list:
                        if jellyfish_id not in list(new_jellyfish_datas):
                            new_jellyfish_datas[jellyfish_id] = 1
                        else:
                            new_jellyfish_datas[jellyfish_id] += 1

                    # 进行数据修改
                    for jellyfish_id in new_jellyfish_datas:
                        number = new_jellyfish_datas[jellyfish_id]
                        box_data["jellyfish"][jellyfish_id]["number"] += number

                    # 读取水母名称并添加到列表
                    event_message += ":"
                    for jellyfish_id in new_jellyfish_datas:
                        jellyfish_name = jellyfish_datas[jellyfish_id]["name"]
                        jellyfish_number = new_jellyfish_datas[jellyfish_id]
                        event_message += f"{jellyfish_name}{jellyfish_number}只、"
                        trace.append(f"{event_id}-{jellyfish_id}增加{jellyfish_number}")

                    # 总结事件
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e5":
                    # 判断事件是否成立
                    # 计算未受保护的水母的数量
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        if jellyfish_datas[jellyfish_id]["protected"] is False:
                            num = box_data["jellyfish"][jellyfish_id]["number"]
                            while num > 0:
                                num -= 1
                                jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 11:
                        continue  # 少于11条，跳过事件
                    if "j24" in list(box_data["jellyfish"]) and box_data["jellyfish"]["j24"]["number"] > 4:
                        continue  # 超过4条，跳过
                    # 计算事件发生的内容
                    choose_jellyfish = random.choice(jellyfish_list)

                    # 进行数据修改
                    if box_data["jellyfish"][choose_jellyfish]["number"] == 1:
                        box_data["jellyfish"].pop(choose_jellyfish)
                    else:
                        box_data["jellyfish"][choose_jellyfish]["number"] -= 1

                    if "j24" in list(box_data["jellyfish"]):
                        box_data["jellyfish"]["j24"]["number"] += 1
                    else:
                        box_data["jellyfish"]["j24"] = {"number": 1}

                    # 总结事件
                    event_message = event_message.replace("{name}", jellyfish_datas[choose_jellyfish]["name"])
                    trace.append(f"{event_id}-{choose_jellyfish}转为j24")
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "":
                    # 判断事件是否成立
                    # 计算事件发生的内容
                    # 进行数据修改
                    # 总结事件
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e7":
                    # 计算未受保护的水母的数量
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        if (jellyfish_datas[jellyfish_id]["protected"] is False or
                                box_data["jellyfish"][jellyfish_id]["number"] > 30):
                            num = box_data["jellyfish"][jellyfish_id]["number"]
                            while num > 0:
                                num -= 1
                                jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 11:
                        continue  # 少于11条，跳过事件
                    # 进行数据修改
                    subtract_quantity = 3  # 要减去的数量

                    # 挑选减去的列表
                    choose_list = []
                    while subtract_quantity > 0:
                        subtract_quantity -= 1
                        choose_jellyfish = random.choice(jellyfish_list)
                        jellyfish_list.remove(choose_jellyfish)
                        choose_list.append(choose_jellyfish)
                    # 修改现有数据
                    for jellyfish_id in choose_list:
                        box_data["jellyfish"][jellyfish_id]["number"] -= 1
                        if box_data["jellyfish"][jellyfish_id]["number"] == 0:
                            box_data["jellyfish"].pop(jellyfish_id)
                    # 总结事件
                    # 转换数据
                    choose_jellyfish = {}
                    for jellyfish_id in choose_list:
                        if jellyfish_id in list(choose_jellyfish):
                            choose_jellyfish[jellyfish_id] += 1
                        else:
                            choose_jellyfish[jellyfish_id] = 1
                    event_message = event_message.replace("{num}", "3")
                    event_message += ": "
                    for jellyfish_id in list(choose_jellyfish):
                        num = choose_jellyfish[jellyfish_id]
                        event_message += f"{jellyfish_datas[jellyfish_id]['name']}{num}只、"
                        trace.append(f"{event_id}-{jellyfish_id}减少{num}")
                    event_message.removesuffix("、")
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e8":
                    # 判断事件是否成立
                    jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"]:
                        if (jellyfish_datas[jellyfish_id]["protected"] is False or
                                box_data["jellyfish"][jellyfish_id]["number"] > 30):
                            num = box_data["jellyfish"][jellyfish_id]["number"]
                            while num > 0:
                                num -= 1
                                jellyfish_list.append(jellyfish_id)
                    if len(jellyfish_list) < 11:
                        continue  # 少于11条，跳过事件
                    # 计算事件发生的内容
                    jellyfishs = []
                    for _ in range(3):
                        choose_jellyfish = random.choice(jellyfish_list)
                        jellyfish_list.remove(choose_jellyfish)
                        jellyfishs.append(choose_jellyfish)
                    choose_jellyfish = statistics_list(jellyfishs)
                    # 进行数据修改
                    for jellyfish_id in list(choose_jellyfish):
                        if box_data["jellyfish"][jellyfish_id]["number"] == choose_jellyfish[jellyfish_id]:
                            box_data["jellyfish"].pop(jellyfish_id)
                        else:
                            box_data["jellyfish"][jellyfish_id]["number"] -= choose_jellyfish[jellyfish_id]
                    # 总结事件
                    event_message += ":"
                    for jellyfish_id in list(choose_jellyfish):
                        name = jellyfish_datas[jellyfish_id]["name"]
                        event_message += f"{name}{choose_jellyfish[jellyfish_id]}只、"
                        trace.append(f"{event_id}-{jellyfish_id}减{choose_jellyfish[jellyfish_id]}")
                    event_message.removesuffix("、")
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e9":
                    # 判断事件是否成立
                    if jellyfish_number < 4:
                        continue  # 少于4只，跳过

                    # 计算事件发生的内容
                    jellyfish_list = []
                    for jellyfish_id in list(jellyfish_datas):
                        if jellyfish_datas[jellyfish_id]["group"] in ["normal", "good"]:
                            jellyfish_list.append(jellyfish_id)
                    choose_list = []
                    for _ in range(3):
                        choose_list.append(random.choice(jellyfish_list))
                    choose_jellyfish = statistics_list(choose_list)

                    # 进行数据修改
                    for jellyfish_id in list(choose_jellyfish):
                        if jellyfish_id in list(box_data["jellyfish"]):
                            box_data["jellyfish"][jellyfish_id]["number"] += choose_jellyfish[jellyfish_id]
                        else:
                            box_data["jellyfish"][jellyfish_id] = {"number": choose_jellyfish[jellyfish_id]}
                    # 总结事件
                    event_message += ":"
                    for jellyfish_id in list(choose_jellyfish):
                        name = jellyfish_datas[jellyfish_id]["name"]
                        event_message += f"{name}{choose_jellyfish[jellyfish_id]}只、"
                        trace.append(f"{event_id}-{jellyfish_id}增{num}")
                    event_message.removesuffix("、")
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "":
                    # 判断事件是否成立
                    # 计算事件发生的内容
                    # 进行数据修改
                    # 总结事件
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                else:
                    news.append(
                        {"icon": event_icon, "title": "程序出错事件", "message": "什么都没发生，只是代码出现了问题"})

        # 写入水母箱数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json_to_str(box_data)}')")
            conn.commit()
        except:
            logger.error("水母箱保存用户数据出错")
        cursor.close()
        conn.close()

    # 绘制
    async def draw_jellyfish(size=(910, 558)):
        """
        绘制水母的图片
        :param size: 要绘制的大小
        :return: image
        """
        global kn_cache
        x = size[0] * 2  # 2倍抗锯齿长
        y = size[1] * 2  # 2倍抗锯齿宽
        # 计算水母的大小
        number = 0
        for jellyfish_id in box_data["jellyfish"]:
            number += box_data["jellyfish"][jellyfish_id]["number"]
        num_list = [400, 353, 306, 260, 236, 213, 190, 166, 143, 120, 96, 73, 50]
        size_list = [100, 104, 109, 117, 124, 134, 144, 154, 165, 180, 197, 218, 244]

        j_size = 100
        num = len(num_list)
        while num > 0:
            num -= 1
            if number < num_list[num]:
                j_size = size_list[num]
                break

        j_image = Image.new("RGBA", (x, y), (0, 0, 0, 0))

        num = 0
        for jellyfish_id in box_data["jellyfish"]:
            # 加载要绘制水母的数量
            num += box_data["jellyfish"][jellyfish_id]["number"]

        for jellyfish_id in box_data["jellyfish"]:
            # 加载要绘制水母的数量
            number = box_data["jellyfish"][jellyfish_id]["number"]

            # 检查绘制样式是否指定水母
            if draw_config["jellyfish"]["replace_jellyfish"] is not None:
                jellyfish_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])

            # 读取水母图片
            file_path = await get_file_path(f"plugin-jellyfish_box-{jellyfish_id}.png")
            jellyfish_image = Image.open(file_path, "r")
            jellyfish_image = jellyfish_image.resize((j_size, j_size))

            # 绘制旋转
            if jellyfish_datas[jellyfish_id]["draw"]["rotate"] != 0:
                jellyfish_image = jellyfish_image.rotate(jellyfish_datas[jellyfish_id]["draw"]["rotate"])

            w, h = jellyfish_image.size
            living_locations = jellyfish_datas[jellyfish_id]["living_location"]
            foreground_num = 0
            while number > 0:
                number -= 1
                # 判断水母所在区域
                if living_locations:
                    living_location = random.choice(living_locations)
                else:
                    living_location = "中"
                if living_location == "中":
                    paste_x = random.randint(0, (x - w))
                    paste_y = random.randint(0, (y - h))
                    direction = random.randint(-180, 180)
                elif living_location == "左":
                    paste_x = random.randint(-50, 0)
                    paste_y = random.randint(0, (y - h))
                    direction = random.randint(10, 170)
                elif living_location == "右":
                    paste_x = random.randint((x - w), (x - w + 50))
                    paste_y = random.randint(0, (y - h))
                    direction = random.randint(-170, 10)
                elif living_location == "上":
                    paste_x = random.randint(0, (x - w))
                    paste_y = random.randint(0, int(h * 1.5))
                    direction = random.randint(-80, 80)
                elif living_location == "下":
                    paste_x = random.randint(0, (x - w))
                    paste_y = random.randint((y - h - int(h * 1.5)), (y - h))
                    direction = random.randint(-80, 80)
                else:
                    paste_x = random.randint(0, (x - w))
                    paste_y = random.randint(0, (y - h))
                    direction = random.randint(-180, 180)

                # 绘制
                foreground_num += 1
                paste_image = jellyfish_image.copy()

                if draw_config["jellyfish"]["jellyfish_foreground"] is not None:
                    choose_foreground = random.choice(draw_config['jellyfish']['jellyfish_foreground'])
                    file_path = await get_file_path(f"plugin-jellyfish_box-{choose_foreground}.png")
                    foreground_image = Image.open(file_path, "r")
                    foreground_image = foreground_image.resize((j_size, j_size))
                    paste_image.paste(foreground_image, (0, 0), mask=foreground_image)

                paste_image = paste_image.rotate(direction)
                j_image.paste(paste_image, (paste_x, paste_y), paste_image)
        j_image = j_image.resize(size)
        return j_image

    async def draw_jellyfish_box(draw_box=True, draw_title=None, ) -> str:
        if draw_model in ["freehand", "freehand_dark"]:
            return await draw_jellyfish_box_freehand(draw_box, draw_title)
        elif draw_model == "text":
            return await draw_jellyfish_box_text(draw_box, draw_title)
        else:
            return await draw_jellyfish_box_normal(draw_box, draw_title)

    async def draw_jellyfish_box_text(draw_box=True, draw_title=None) -> str:
        """
        绘制状态图
        :return: 字符串
        """
        """
        内容：
        :param bd: 水母箱数据 user_box_data
        :param news: 新增的水母列表
        :param new_jellyfish: 新闻列表，显示最近的动态
        :param command_prompt_list: 指令列表，建议可以输入的指令
        """
        msg = ""

        # 添加水母箱
        if draw_box is True:
            msg += ("\n[                 🪼                     🪼]\n"
                    "[     🪼             🪼                    ]\n"
                    "[            🪼                 🪼         ]\n")

        # 添加新水母
        if len(new_jellyfish) > 0:
            msg += draw_config["text"]["新水母_标题"] + "\n"

            # 添加水母
            for data in new_jellyfish:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None:
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_number = data["number"]
                j_message = data["message"]

                msg += f"{j_name}x{j_number}，{j_group}"

        # 添加水母图鉴
        if len(jellyfish_menu) > 0:
            msg += "\n"

            # 添加水母
            num = 0
            group = ""
            for data in jellyfish_menu:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None and (
                        draw_title is None or draw_title in ["水母统计表"]):
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_message = data["message"]

                if group != j_group:
                    num = 0
                    if msg.endswith("\n"):
                        msg += f"{j_group}:\n"
                    else:
                        msg += f"\n{j_group}:\n"
                    group = j_group

                if num == 0:
                    num = 1
                    msg += f"🪼{j_name}{j_message}"
                else:
                    num = 0
                    msg += f"🪼{j_name}{j_message} \n"
            if not msg.endswith("\n"):
                msg += "\n"

        # 添加事件
        if len(news) > 0:
            msg += draw_config["text"]["事件_标题"] + "\n"
            # 添加事件
            for data in news:
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]
                msg += f"{title}: {message}\n"

        # 添加指令介绍
        if len(command_prompt_list) > 0:
            msg += draw_config["text"]["指令_标题"] + "\n"

            for data in command_prompt_list:
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]
                msg += f"{title}: {message}\n"

        return msg

    async def draw_jellyfish_box_normal(draw_box=True, draw_title=None) -> str:
        """
        绘制状态图
        :return: 图片路径 save_image(image)
        """
        """
        内容：
        :param bd: 水母箱数据 user_box_data
        :param news: 新增的水母列表
        :param new_jellyfish: 新闻列表，显示最近的动态
        :param command_prompt_list: 指令列表，建议可以输入的指令
        """
        font_shsk_H_path = await get_file_path("SourceHanSansK-Heavy.ttf")
        font_shsk_M_path = await get_file_path("SourceHanSansK-Medium.ttf")
        font_shsk_B_path = await get_file_path("SourceHanSansK-Bold.ttf")

        # 计算长度
        x = 1000
        y = 0
        # 添加基础高度（图片头）
        y += 258
        # 添加水母箱高度
        if draw_box is True:
            y += 563
        # 添加新水母高度
        if len(new_jellyfish) > 0:
            y += 36  # 空行
            y += 33  # 标题
            for data in new_jellyfish:
                y += 261
            y += 14  # 结尾
        # 添加水母图鉴
        if len(jellyfish_menu) > 0:
            y += 36  # 空行
            y += 33  # 标题
            for data in jellyfish_menu:
                y += 261
            y += 14  # 结尾
        # 添加事件高度
        if len(news) > 0:
            y += 20  # 空行
            y += 60  # 标题
            for data in news:
                y += 20  # 空行
                y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                y += h + 15  # 事件介绍
            y += 60  # 结尾
        # 添加指令提示高度
        if len(command_prompt_list) > 0:
            y += 20  # 空行
            y += 60  # 事件标题
            for data in command_prompt_list:
                y += 20  # 空行
                y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                y += h + 15  # 事件介绍
            y += 60  # 结尾
        # 添加图片尾
        y += 43

        # 创建底图
        image = Image.new("RGB", (x, y), draw_config["color"]["bg"])
        draw = ImageDraw.Draw(image)

        # 绘制内容
        # 添加背景大字
        draw_x = 0
        draw_y = 0
        font = ImageFont.truetype(font=font_shsk_H_path, size=300)
        draw.text(
            xy=(draw_x + 136, draw_y + 28),
            text=draw_config["text"]["背景大字"],
            fill=draw_config["color"]["背景大字"],
            font=font)

        # 添加时间
        text = f"{datetime.fromtimestamp(time_now)}"[0:10]
        font = ImageFont.truetype(font=font_shsk_M_path, size=40)
        draw.text(xy=(draw_x + 64, draw_y + 68), text=text, fill=draw_config["color"]["date"], font=font)

        # 添加标题
        if draw_title is None:
            text = user_name
        else:
            text = draw_title
        font = ImageFont.truetype(font=font_shsk_M_path, size=70)
        draw.text(xy=(draw_x + 54, draw_y + 112), text=text, fill=draw_config["color"]["name"], font=font)

        # 绘制头像
        if "face_image" in list(user_data) and draw_title is None:
            user_avatar = user_data["face_image"]
            try:
                if user_avatar in [None, "None", "none"]:
                    user_image = await draw_text("图片", 50, 10)
                elif user_avatar.startswith("http"):
                    user_image = await connect_api("image", user_avatar)
                else:
                    user_image = Image.open(user_avatar, "r")
            except Exception as e:
                user_image = await draw_text("头像", 50, 10)
                logger.error(f"获取图片出错:{e}")
            user_image = user_image.resize((158, 158))
            user_image = circle_corner(user_image, 79)
            paste_image = Image.new("RGB", (160, 160), (255, 255, 255))
            paste_image = circle_corner(paste_image, 80)
            image.paste(paste_image, (draw_x + 744, draw_y + 62), paste_image)
            image.paste(user_image, (draw_x + 745, draw_y + 63), user_image)

        draw_x += 43
        draw_y += 258
        # 添加水母箱
        if draw_box is True:
            x = 914  # 卡片宽度
            y = 563  # 卡片长度

            paste_image = Image.new("RGB", (x, y), draw_config["color"]["box_outline"])
            paste_image = circle_corner(paste_image, 30)  # 圆角
            image.paste(paste_image, (draw_x, draw_y), paste_image)
            paste_image = Image.new("RGB", (x - 6, y - 6), draw_config["color"]["box_bg"])
            paste_image = circle_corner(paste_image, 28)  # 圆角
            image.paste(paste_image, (draw_x + 3, draw_y + 3), paste_image)

            if draw_config['jellyfish']['box_background'] is not None:
                path = await get_file_path(f"plugin-jellyfish_box-{draw_config['jellyfish']['box_background']}.png")
                paste_image = Image.open(path, "r")
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            paste_image = await draw_jellyfish((x - 6, y - 6))  # 水母们
            image.paste(paste_image, (draw_x + 3, draw_y + 3), paste_image)

            if draw_config['jellyfish']['box_foreground'] is not None:
                path = await get_file_path(f"plugin-jellyfish_box-{draw_config['jellyfish']['box_foreground']}.png")
                paste_image = Image.open(path, "r")
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            draw_x += 754
            draw_y += 0
            # 添加水母箱状态

            draw_x -= 754
            draw_y += 563

        # 添加新水母
        if len(new_jellyfish) > 0:
            draw_y += 36  # 空行
            card_x = 914  # 卡片宽度
            card_y = 69  # 卡片长度 标题
            for data in new_jellyfish:
                card_y += 261  # 卡片长度 水母
            card_y += 14  # 卡片长度 结尾

            # 开始绘制卡片
            paste_card_image = Image.new("RGB", (card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            font = ImageFont.truetype(font=font_shsk_B_path, size=50)
            draw.text(
                xy=(32, 20),
                text=draw_config["text"]["新水母_标题"],
                fill=draw_config["color"]["title"],
                font=font)
            # 添加水母
            card_num = -1
            for data in new_jellyfish:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None:
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_number = data["number"]
                j_message = data["message"]
                card_num += 1
                # 添加水母图标
                paste_image = Image.new("RGB", (248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)
                paste_image = Image.new("RGB", (234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.paste(paste_image, (11 + 7, 69 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                color = (
                    int(draw_config["color"]["icon_bg"][1:3], 16),
                    int(draw_config["color"]["icon_bg"][3:5], 16),
                    int(draw_config["color"]["icon_bg"][5:7], 16),
                    102,
                )
                mask_image = Image.new("RGBA", (575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278 + 150, 152 + (card_num * 261)), text=f"分组：",
                    fill=draw_config["color"]["event_message"], font=font)
                if j_group in list(draw_config["color"]["group_color"]):
                    color = draw_config["color"]["group_color"][j_group]
                else:
                    color = draw_config["color"]["event_message"]
                draw.text(
                    xy=(278 + 150 + 120, 152 + (card_num * 261)), text=j_group,
                    fill=color, font=font)

                # 添加水母数量
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278, 152 + (card_num * 261)), text=f"x{j_number}",
                    fill=draw_config["color"]["event_message"], font=font)

                # 添加消息
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(xy=(278, 200 + (card_num * 261)), text=j_message,
                          fill=draw_config["color"]["event_message"], font=font)

            paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_image)

            draw_x += 0
            draw_y += card_y  # 卡片高度

        # 添加水母图鉴
        if len(jellyfish_menu) > 0:
            draw_y += 0  # 空行
            card_x = 914  # 卡片宽度
            card_y = 33  # 卡片长度 标题
            for data in jellyfish_menu:
                card_y += 261  # 卡片长度 水母
            card_y += 14  # 卡片长度 结尾

            # 开始绘制卡片
            paste_card_image = Image.new("RGB", (card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)
            # 添加标题
            # font = ImageFont.truetype(font=font_shsk_B_path, size=50)
            # draw.text(xy=(32, 20), text="新增水母", fill=draw_config["color"]["title"], font=font)
            # 添加水母
            card_num = -1
            for data in jellyfish_menu:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None and (
                        draw_title is None or draw_title in ["水母统计表"]):
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_message = data["message"]
                card_num += 1
                # 添加水母图标
                paste_image = Image.new("RGB", (248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)
                paste_image = Image.new("RGB", (234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.paste(paste_image, (11 + 7, 0 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                color = (
                    int(draw_config["color"]["icon_bg"][1:3], 16),
                    int(draw_config["color"]["icon_bg"][3:5], 16),
                    int(draw_config["color"]["icon_bg"][5:7], 16),
                    102,
                )
                mask_image = Image.new("RGBA", (575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -69 - 27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, -69 + 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278, -69 + 152 + (card_num * 261)),
                    text=f"分组：",
                    fill=draw_config["color"]["event_message"],
                    font=font)
                if j_group in list(draw_config["color"]["group_color"]):
                    color = draw_config["color"]["group_color"][j_group]
                else:
                    color = draw_config["color"]["event_message"]
                draw.text(
                    xy=(278 + 120, -69 + 152 + (card_num * 261)), text=j_group,
                    fill=color, font=font)

                # 添加消息
                paste_text = await draw_text(
                    texts=f"简介：{j_message}",
                    size=40,
                    textlen=12,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_text, (278, -69 + 200 + (card_num * 261)), paste_text)

            paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_image)

            draw_x += 0
            draw_y += card_y  # 卡片高度

        # 添加事件
        if len(news) > 0:
            draw_y += 20  # 空行
            card_x = 914  # 卡片宽度
            card_y = 60  # 卡片长度 标题
            for data in news:
                card_y += 20  # 空行
                card_y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                card_y += h + 15  # 事件介绍
            card_y += 30  # 结尾

            # 开始绘制卡片
            draw_event_y = 0
            paste_card_image = Image.new("RGB", (card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)
            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=font_shsk_B_path, size=45)
            draw.text(
                xy=(32, draw_event_y),
                text=draw_config["text"]["事件_标题"],
                fill=draw_config["color"]["title"],
                font=font)

            # 添加事件
            draw_event_y += 55
            event_num = -1
            for data in news:
                event_num += 1
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]

                # 添加标题
                font = ImageFont.truetype(font=font_shsk_M_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                # 添加消息
                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_image, (23, draw_event_y), paste_image)
                draw_event_y += paste_image.size[1] + 15

            paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (43, draw_y), paste_card_image)
            draw_event_y += 20  # 卡片结尾高度

            draw_x += 0
            draw_y += draw_event_y  # 卡片高度

        # 添加指令介绍
        if len(command_prompt_list) > 0:
            draw_y += 20  # 空行
            card_x = 914  # 卡片宽度
            card_y = 60  # 卡片长度 标题
            for data in command_prompt_list:
                card_y += 20  # 空行
                card_y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                card_y += h + 15  # 事件介绍
            card_y += 30  # 结尾

            # 开始绘制卡片
            draw_event_y = 0
            paste_card_image = Image.new("RGB", (card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=font_shsk_B_path, size=45)
            draw.text(
                xy=(32, draw_event_y),
                text=draw_config["text"]["指令_标题"],
                fill=draw_config["color"]["title"],
                font=font)

            # 添加事件
            draw_event_y += 55
            event_num = -1
            for data in command_prompt_list:
                event_num += 1
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]

                # 添加标题
                font = ImageFont.truetype(font=font_shsk_M_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_image, (23, draw_event_y), paste_image)
                draw_event_y += paste_image.size[1] + 15

            paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (43, draw_y), paste_card_image)
            draw_event_y += 20  # 卡片结尾高度

            draw_x += 0
            draw_y += draw_event_y  # 卡片高度

        return save_image(image)

    async def draw_jellyfish_box_freehand(draw_box=True, draw_title=None) -> str:
        """
        绘制状态图
        :return: 图片路径 save_image(image)
        """
        """
        内容：
        :param bd: 水母箱数据 user_box_data
        :param news: 新增的水母列表
        :param new_jellyfish: 新闻列表，显示最近的动态
        :param command_prompt_list: 指令列表，建议可以输入的指令
        """
        font_shsk_H_path = await get_file_path("SourceHanSansK-Heavy.ttf")
        font_shsk_M_path = await get_file_path("SourceHanSansK-Medium.ttf")
        font_shsk_B_path = await get_file_path("SourceHanSansK-Bold.ttf")
        muyao_softbrush = await get_file_path("Muyao-Softbrush-2.ttf")

        # 计算长度
        x = 1000
        y = 0
        # 添加基础高度（图片头）
        y += 258
        # 添加水母箱高度
        if draw_box is True:
            y += 563
        # 添加新水母高度
        if len(new_jellyfish) > 0:
            y += 36  # 空行
            y += 60  # 标题
            for data in new_jellyfish:
                y += 261
            y += 14  # 结尾
        # 添加水母图鉴
        if len(jellyfish_menu) > 0:
            y += 36  # 空行
            y += 60  # 标题
            for data in jellyfish_menu:
                y += 261
            y += 14  # 结尾
        # 添加事件高度
        if len(news) > 0:
            y += 36  # 空行
            y += 60  # 标题
            for data in news:
                y += 20  # 空行
                y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                y += h + 15  # 事件介绍
            y += 14  # 结尾
        # 添加指令提示高度
        if len(command_prompt_list) > 0:
            y += 36  # 空行
            y += 60  # 事件标题
            for data in command_prompt_list:
                y += 20  # 空行
                y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                y += h + 15  # 事件介绍
            y += 14  # 结尾
        # 添加图片尾
        y += 43

        # 创建底图
        image = Image.new("RGB", (x, y), draw_config["color"]["bg"])
        draw = ImageDraw.Draw(image)
        # 添加底色
        file_path = await get_image_path(f"jellyfish_box-freehand_background.png")
        paste_image = Image.open(file_path, "r")
        image.paste(paste_image, (0, 0), paste_image)
        if y > 2000:
            image.paste(paste_image, (0, 2000), paste_image)

        # 绘制内容
        # 添加背景大字
        draw_x = 0
        draw_y = 0
        font = ImageFont.truetype(font=muyao_softbrush, size=300)
        draw.text(
            xy=(draw_x + 136, draw_y + 28),
            text=draw_config["text"]["背景大字"],
            fill=draw_config["color"]["背景大字"],
            font=font)

        # 添加时间
        text = f"{datetime.fromtimestamp(time_now)}"[0:10]
        font = ImageFont.truetype(font=muyao_softbrush, size=40)
        draw.text(xy=(draw_x + 64, draw_y + 68), text=text, fill=draw_config["color"]["date"], font=font)

        # 添加标题
        if draw_title is None:
            text = user_name
        else:
            text = draw_title
        font = ImageFont.truetype(font=muyao_softbrush, size=70)
        draw.text(xy=(draw_x + 54, draw_y + 112), text=text, fill=draw_config["color"]["name"], font=font)

        # 绘制头像
        if "face_image" in list(user_data) and draw_title is None:
            user_avatar = user_data["face_image"]
            try:
                if user_avatar in [None, "None", "none"]:
                    user_image = await draw_text("图片", 50, 10)
                elif user_avatar.startswith("http"):
                    user_image = await connect_api("image", user_avatar)
                else:
                    user_image = Image.open(user_avatar, "r")
            except Exception as e:
                user_image = await draw_text("头像", 50, 10)
                logger.error(f"获取图片出错:{e}")
            user_image = user_image.resize((158, 158))
            user_image = circle_corner(user_image, 79)
            paste_image = Image.new("RGB", (160, 160), (255, 255, 255))
            paste_image = circle_corner(paste_image, 80)
            image.paste(paste_image, (draw_x + 744, draw_y + 62), paste_image)
            image.paste(user_image, (draw_x + 745, draw_y + 63), user_image)

        draw_x += 43
        draw_y += 258
        # 添加水母箱
        if draw_box is True:
            x = 914  # 卡片宽度
            y = 563  # 卡片长度

            file_path = await get_image_path(f"jellyfish_box-freehand_box_background.png")
            paste_alpha = Image.open(file_path, "r")
            paste_alpha = paste_alpha.resize((x, y))
            paste_image = Image.new("RGBA", (x, y), draw_config["color"]["box_bg"])
            image.paste(paste_image, (draw_x, draw_y), paste_alpha)

            if draw_config['jellyfish']['box_background'] is not None:
                path = await get_file_path(f"plugin-jellyfish_box-{draw_config['jellyfish']['box_background']}.png")
                paste_image = Image.open(path, "r")
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            paste_image = await draw_jellyfish((x - 6 - 40, y - 6 - 40))  # 水母们
            image.paste(paste_image, (draw_x + 3 + 20, draw_y + 3 + 20), paste_image)

            if draw_config['jellyfish']['box_foreground'] is not None:
                path = await get_file_path(f"plugin-jellyfish_box-{draw_config['jellyfish']['box_foreground']}.png")
                paste_image = Image.open(path, "r")
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            draw_x += 754
            draw_y += 0
            # 添加水母箱状态

            draw_x -= 754
            draw_y += 563

        # 添加新水母
        if len(new_jellyfish) > 0:
            draw_y += 36  # 空行
            card_x = 914  # 卡片宽度
            card_y = 69  # 卡片长度 标题
            for data in new_jellyfish:
                card_y += 261  # 卡片长度 水母
            card_y += 14  # 卡片长度 结尾

            # 开始绘制卡片
            file_path = await get_image_path(f"jellyfish_box-freehand_card_background.png")
            paste_card_alpha = Image.open(file_path, "r")
            paste_card_alpha = paste_card_alpha.resize((card_x, card_y))
            paste_card_image = Image.new("RGBA", (card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = Image.new("RGBA", (card_x, card_y), (0, 0, 0, 0))

            # paste_card_image = Image.new("RGBA", (card_x, card_y), color)
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            font = ImageFont.truetype(font=muyao_softbrush, size=50)
            draw.text(
                xy=(32, 20),
                text=draw_config["text"]["新水母_标题"],
                fill=draw_config["color"]["title"],
                font=font)
            # 添加水母
            card_num = -1
            for data in new_jellyfish:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None:
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_number = data["number"]
                j_message = data["message"]
                card_num += 1
                # 添加水母图标
                # paste_image = Image.new("RGB", (248, 248), draw_config["color"]["icon_outline"])
                # paste_image = circle_corner(paste_image, 24)
                # paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)
                # paste_image = Image.new("RGB", (234, 234), draw_config["color"]["icon_bg"])
                # paste_image = circle_corner(paste_image, 18)
                # paste_card_image.paste(paste_image, (11 + 7, 69 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                color = (
                    int(draw_config["color"]["icon_bg"][1:3], 16),
                    int(draw_config["color"]["icon_bg"][3:5], 16),
                    int(draw_config["color"]["icon_bg"][5:7], 16),
                    102,
                )
                mask_image = Image.new("RGBA", (575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278 + 150, 152 + (card_num * 261)), text=f"分组：",
                    fill=draw_config["color"]["event_message"], font=font)
                if j_group in list(draw_config["color"]["group_color"]):
                    color = draw_config["color"]["group_color"][j_group]
                else:
                    color = draw_config["color"]["event_message"]
                draw.text(
                    xy=(278 + 150 + 120, 152 + (card_num * 261)), text=j_group,
                    fill=color, font=font)

                # 添加水母数量
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278, 152 + (card_num * 261)), text=f"x{j_number}",
                    fill=draw_config["color"]["event_message"], font=font)

                # 添加消息
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(xy=(278, 200 + (card_num * 261)), text=j_message,
                          fill=draw_config["color"]["event_message"], font=font)

            # paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_image)

            draw_x += 0
            draw_y += card_y  # 卡片高度

        # 添加水母图鉴
        if len(jellyfish_menu) > 0:
            draw_y += 0  # 空行
            card_x = 914  # 卡片宽度
            card_y = 33  # 卡片长度 标题
            for data in jellyfish_menu:
                card_y += 261  # 卡片长度 水母
            card_y += 14  # 卡片长度 结尾

            # 开始绘制卡片
            file_path = await get_image_path(f"jellyfish_box-freehand_card_background.png")
            paste_card_alpha = Image.open(file_path, "r")
            paste_card_alpha = paste_card_alpha.resize((card_x, card_y))
            paste_card_image = Image.new("RGBA", (card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = Image.new("RGBA", (card_x, card_y), (0, 0, 0, 0))
            draw = ImageDraw.Draw(paste_card_image)
            # 添加标题
            # font = ImageFont.truetype(font=font_shsk_B_path, size=50)
            # draw.text(xy=(32, 20), text="新增水母", fill=draw_config["color"]["title"], font=font)
            # 添加水母
            card_num = -1
            for data in jellyfish_menu:
                j_id = data["id"]
                if draw_config["jellyfish"]["replace_jellyfish"] is not None and (
                        draw_title is None or draw_title in ["水母统计表"]):
                    j_id = random.choice(draw_config["jellyfish"]["replace_jellyfish"])
                j_name = data["name"]
                j_group = data["group"]
                j_message = data["message"]
                card_num += 1
                # 添加水母图标
                # paste_image = Image.new("RGB", (248, 248), draw_config["color"]["icon_outline"])
                # paste_image = circle_corner(paste_image, 24)
                # paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)
                # paste_image = Image.new("RGB", (234, 234), draw_config["color"]["icon_bg"])
                # paste_image = circle_corner(paste_image, 18)
                # paste_card_image.paste(paste_image, (11 + 7, 0 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                paste_image = Image.open(file_path, "r")
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                color = (
                    int(draw_config["color"]["icon_bg"][1:3], 16),
                    int(draw_config["color"]["icon_bg"][3:5], 16),
                    int(draw_config["color"]["icon_bg"][5:7], 16),
                    102,
                )
                mask_image = Image.new("RGBA", (575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -69 - 27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, -69 + 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                font = ImageFont.truetype(font=font_shsk_M_path, size=40)
                draw.text(
                    xy=(278, -69 + 152 + (card_num * 261)),
                    text=f"分组：",
                    fill=draw_config["color"]["event_message"],
                    font=font)
                if j_group in list(draw_config["color"]["group_color"]):
                    color = draw_config["color"]["group_color"][j_group]
                else:
                    color = draw_config["color"]["event_message"]
                draw.text(
                    xy=(278 + 120, -69 + 152 + (card_num * 261)), text=j_group,
                    fill=color, font=font)

                # 添加消息
                paste_text = await draw_text(
                    texts=f"简介：{j_message}",
                    size=40,
                    textlen=12,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_text, (278, -69 + 200 + (card_num * 261)), paste_text)

            # paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_image)

            draw_x += 0
            draw_y += card_y  # 卡片高度

        # 添加事件
        if len(news) > 0:
            draw_y += 20  # 空行
            card_x = 914  # 卡片宽度
            card_y = 60  # 卡片长度 标题
            for data in news:
                card_y += 20  # 空行
                card_y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                card_y += h + 15  # 事件介绍
            card_y += 30  # 结尾

            # 开始绘制卡片
            draw_event_y = 0

            file_path = await get_image_path(f"jellyfish_box-freehand_card_background.png")
            paste_card_alpha = Image.open(file_path, "r")
            paste_card_alpha = paste_card_alpha.resize((card_x, card_y))
            paste_card_image = Image.new("RGBA", (card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = Image.new("RGBA", (card_x, card_y), (0, 0, 0, 0))
            draw = ImageDraw.Draw(paste_card_image)
            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=muyao_softbrush, size=45)
            draw.text(
                xy=(32, draw_event_y),
                text=draw_config["text"]["事件_标题"],
                fill=draw_config["color"]["title"],
                font=font)

            # 添加事件
            draw_event_y += 55
            event_num = -1
            for data in news:
                event_num += 1
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]

                # 添加标题
                font = ImageFont.truetype(font=font_shsk_B_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                # 添加消息
                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_image, (23, draw_event_y), paste_image)
                draw_event_y += paste_image.size[1] + 15

            # paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (43, draw_y), paste_card_image)
            draw_event_y += 20  # 卡片结尾高度

            draw_x += 0
            draw_y += draw_event_y  # 卡片高度

        # 添加指令介绍
        if len(command_prompt_list) > 0:
            draw_y += 20  # 空行
            card_x = 914  # 卡片宽度
            card_y = 60  # 卡片长度 标题
            for data in command_prompt_list:
                card_y += 20  # 空行
                card_y += 22  # 事件标题
                paste_image = await draw_text(
                    data["message"],
                    size=35,
                    textlen=21,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"],
                    calculate=True
                )
                w, h = paste_image.size
                card_y += h + 15  # 事件介绍
            card_y += 30  # 结尾

            # 开始绘制卡片
            draw_event_y = 0

            file_path = await get_image_path(f"jellyfish_box-freehand_card_background.png")
            paste_card_alpha = Image.open(file_path, "r")
            paste_card_alpha = paste_card_alpha.resize((card_x, card_y))
            paste_card_image = Image.new("RGBA", (card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = Image.new("RGBA", (card_x, card_y), (0, 0, 0, 0))
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                path = await get_file_path(f"plugin-jellyfish_box-{choose_card_background}.png")
                card_background = Image.open(path, "r")
                paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=muyao_softbrush, size=45)
            draw.text(
                xy=(32, draw_event_y),
                text=draw_config["text"]["指令_标题"],
                fill=draw_config["color"]["title"],
                font=font)

            # 添加事件
            draw_event_y += 55
            event_num = -1
            for data in command_prompt_list:
                event_num += 1
                # icon = data["icon"]  # 暂时用不上
                title = data["title"]
                message = data["message"]

                # 添加标题
                font = ImageFont.truetype(font=font_shsk_B_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_shsk_M_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_image, (23, draw_event_y), paste_image)
                draw_event_y += paste_image.size[1] + 15

            # paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (43, draw_y), paste_card_image)
            draw_event_y += 20  # 卡片结尾高度

            draw_x += 0
            draw_y += draw_event_y  # 卡片高度

        return save_image(image)

    # 判断指令
    if command == "查看水母箱":
        if kn_config("plugin_jellyfish_box", "draw_gif") is True:
            draw_data = {
                "jellyfish": box_data["jellyfish"],
                "size": (1000, 750),  # 图片大小
                "frame_rate": 8,  # 每秒图片数量，帧率
                "duration": 5.0,  # 时长（秒）
                "background_color": (22, 84, 123, 255),  # 背景颜色
            }
            returunpath = await draw_jellyfish_live(draw_data=draw_data)
        elif os.path.exists(f"{basepath}cache/jellyfish_box/{user_id}.gif"):
            returunpath = f"{basepath}cache/jellyfish_box/{user_id}.gif"
        else:
            image = Image.new("RGB", (2000, 1500), "#16547b")
            paste_image = await draw_jellyfish((1900, 1400))
            image.paste(paste_image, (50, 50), paste_image)
            returunpath = save_image(image)
        code = 2
    elif command == "水母箱":
        if draw_model == "text":
            code = 1
            message = await draw_jellyfish_box()
        else:
            command_prompt_list.append({"title": "/水母箱 帮助", "message": "查看水母箱指令介绍"})
            command_prompt_list.append({"title": "/水母箱 抓水母", "message": "抓几只水母进水母箱（每2小时抓一次）"})
            returunpath = await draw_jellyfish_box()
            code = 2
    elif command == "抓水母":
        # 抓水母 每2小时7200秒抓一次
        time_difference = time_now - box_data["sign_in_time"]
        if time_difference < 7200:
            time_difference = 7200 - time_difference
            t_text = ""
            if time_difference > 3600:
                t_hour = int(time_difference / 3600)
                time_difference -= t_hour * 3600
                t_text += f"{t_hour}小时"
            if time_difference > 60:
                t_minute = int(time_difference / 60)
                time_difference -= t_minute * 60
                t_text += f"{t_minute}分钟"
            t_text += f"{time_difference}秒"

            code = 1
            message = f"别抓啦，过{t_text}再来吧"
        else:
            box_data["sign_in_time"] = time_now
            # 随机数量
            jellyfish_num = 0
            if len(box_data["jellyfish"]) == 0:
                grab_quantity = random.randint(4, 6)
            else:
                for jellyfish_id in box_data["jellyfish"]:
                    jellyfish_num += box_data["jellyfish"][jellyfish_id]["number"]
                if jellyfish_num < 10:
                    grab_quantity = random.randint(3, 4)
                elif jellyfish_num < 20:
                    grab_quantity = random.randint(2, 3)
                elif jellyfish_num < 50:
                    grab_quantity = random.randint(1, 2)
                else:
                    grab_quantity = 1
            if jellyfish_num > 250:
                code = 1
                message = "别抓啦，水母箱已经满啦"
            else:
                # 随机水母类型
                group = ["perfect", "great", "good", "normal", "special", "ocean"]
                if date_m == "05" and date_d == "11":
                    group_probability = [0.00, 0.05, 0.30, 0.55, 0.10, 0.00]
                else:
                    group_probability = [0.00, 0.02, 0.15, 0.83, 0.00, 0.00]
                p = numpy.array(group_probability).ravel()
                choose_group = numpy.random.choice(group, p=p)
                choose_list = []
                for jellyfish_id in jellyfish_datas:
                    if jellyfish_datas[jellyfish_id]["group"] == choose_group:
                        choose_list.append(jellyfish_id)
                choose_jellyfish = random.choice(choose_list)
                # 添加到水母箱数据库中
                if choose_jellyfish not in list(box_data["jellyfish"]):
                    # 新水母，添加数据
                    box_data["jellyfish"][choose_jellyfish] = {"number": grab_quantity}
                else:
                    box_data["jellyfish"][choose_jellyfish]["number"] += grab_quantity

                new_jellyfish.append(
                    {"id": choose_jellyfish,
                     "number": grab_quantity,
                     "name": jellyfish_datas[choose_jellyfish]["name"],
                     "group": jellyfish_datas[choose_jellyfish]["group"],
                     "message": f"抓到了{grab_quantity}只"}
                )

                trace.append(f"抓到水母：{choose_jellyfish}， 数量：{grab_quantity}")

                # 节日抓水母事件
                if date_m == "05" and date_d == "11":
                    number = random.randint(1, 3)
                    choose_jellyfish = "j31"
                    if "j31" not in list(box_data["jellyfish"]):
                        new_jellyfish.append(
                            {"id": choose_jellyfish,
                             "number": number,
                             "name": jellyfish_datas[choose_jellyfish]["name"],
                             "group": jellyfish_datas[choose_jellyfish]["group"],
                             "message": f"抓到了{number}只"}
                        )
                        box_data["jellyfish"]["j31"] = {"number": number}
                    elif box_data["jellyfish"]["j31"]["number"] < 7:
                        if random.randint(0, 5) == 5:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            box_data["jellyfish"]["j31"]["number"] += number
                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json_to_str(box_data)}')")
                    conn.commit()
                except:
                    logger.error("水母箱保存用户数据出错")
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()

                # 绘制
                if draw_model == "text":
                    code = 1
                    message = await draw_jellyfish_box(draw_box=False)
                else:
                    command_prompt_list.append({"title": "/水母箱 帮助", "message": "查看水母箱指令介绍"})
                    returunpath = await draw_jellyfish_box()
                    code = 2
    elif command == "水母统计表":
        # 读取水母箱内容并分组

        # 获取分组
        group_list = jellyfish_group_list.copy()
        for jellyfish_id in list(box_data["jellyfish"]):
            if jellyfish_datas[jellyfish_id]["group"] not in group_list:
                group_list.append(jellyfish_datas[jellyfish_id]["group"])

        # 转换格式
        j_list = {}
        for group in group_list:
            if group not in list(j_list):
                j_list[f"cache_{group}"] = []
            for jellyfish_id in list(box_data["jellyfish"]):
                if group == jellyfish_datas[jellyfish_id]["group"]:
                    j_list[f"cache_{group}"].append(jellyfish_id)

        # 排列大小
        for group in group_list:
            num = 99
            while num > 0 and len(j_list[f"cache_{group}"]) > 0:
                num -= 1
                j_max_number = 0
                j_max_id = ""
                for jellyfish_id in j_list[f"cache_{group}"]:
                    if box_data["jellyfish"][jellyfish_id]["number"] > j_max_number:
                        j_max_number = box_data["jellyfish"][jellyfish_id]["number"]
                        j_max_id = jellyfish_id

                j_list[f"cache_{group}"].remove(j_max_id)
                if group not in list(j_list):
                    j_list[group] = []
                j_list[group].append(j_max_id)
        for group in list(j_list):
            if group.startswith("cache"):
                j_list.pop(group)

        # 渲染成图片
        cache_groups = []
        cache_group = []
        for group in list(j_list):
            for jellyfish_id in j_list[group]:
                if len(cache_group) > 9:
                    cache_groups.append(cache_group)
                    cache_group = []

                cache_group.append(
                    {"id": jellyfish_id,
                     "name": jellyfish_datas[jellyfish_id]["name"],
                     "group": jellyfish_datas[jellyfish_id]["group"],
                     "message": f"x{box_data['jellyfish'][jellyfish_id]['number']}"}
                )

        if cache_group:
            cache_groups.append(cache_group)

        if draw_model == "text":
            for cache_data in cache_groups[0]:
                jellyfish_menu.append(cache_data)
            code = 1
            message = await draw_jellyfish_box(draw_box=False, draw_title="水母统计表")
        else:
            if len(cache_groups) == 1:
                for cache_data in cache_groups[0]:
                    jellyfish_menu.append(cache_data)
                returunpath = await draw_jellyfish_box(draw_box=False, draw_title="水母统计表")
            else:
                num_x = 0
                image = Image.new("RGB", ((1000 * len(cache_groups)), 2994), draw_config["color"]["bg"])
                for cache_group in cache_groups:
                    jellyfish_menu = []
                    for cache_data in cache_group:
                        jellyfish_menu.append(cache_data)
                    cache_path = await draw_jellyfish_box(draw_box=False, draw_title="水母统计表")
                    paste_image = Image.open(cache_path, "r")
                    image.paste(paste_image, ((1000 * num_x), 0))
                    num_x += 1
                returunpath = save_image(image)
            code = 2
    elif command in ["丢弃", "抛弃", "放生"]:
        if command2 is None:
            code = 1
            message = "请添加水母名称以及数量\n例：“/水母箱 丢弃 普通水母 10”"
        else:
            numbers = ["1", "2", "3", "4", "5", "7", "8", "9", "0"]
            command = command2

            # 指令解析
            # 获取水母名称列表
            jellyfish_list = {}
            for jellyfish_id in list(jellyfish_datas):
                jellyfish_list[jellyfish_datas[jellyfish_id]["name"]] = jellyfish_id
            # 指令间加空格
            command = command.lower()
            for group in jellyfish_group_list:
                command = command.replace(group, f" {group} ")
            if "x" in command:
                num = -1
                for c in command:
                    num += 1
                    if c == "x":
                        for n in numbers:
                            if num < len(command) and command[num + 1:num + 2].startswith(n):
                                command = command[:num] + " " + command[num + 1:]
            if "-" in command:
                command = command.replace("-", " ")
            if "只" in command:
                command = command.replace("只", "")
            if "全部" in command:
                command = command.replace("all", "全部")
            if "所有" in command:
                command = command.replace("all", "所有")
            if "all" in command:
                command = command.replace("all", "all")
            num = -1
            for c in command:
                num += 1
                if c == "a":
                    if command[num:].startswith("all") and command[num - 1] != " ":
                        command = command[:num] + " " + command[num:]
                        num += 1
                    if command[num:].startswith("all") and (command[num:] == "all" or command[num + 3] != " "):
                        command = command[:num + 3] + " " + command[num + 3:]
                        num += 1

            if list_in_list(command, numbers):
                num = -1
                for c in command:
                    num += 1
                    if c in numbers:
                        if command[num - 1:num] != " " and command[num - 1:num] not in numbers and num > 0:
                            command = command[:num] + " " + command[num:]
                            num += 1
                    else:
                        if command[num - 1:num] != " " and command[num - 1:num] in numbers and num > 0:
                            command = command[:num] + " " + command[num:]
                            num += 1
            for jellyfish_id in list(jellyfish_datas):
                name = jellyfish_datas[jellyfish_id]['name']
                command = command.replace(name, f" {name} ")
            commands = command.split()

            # 转数字
            num = -1
            commands2 = []
            for command in commands:
                num += 1
                if command == "0":
                    num -= 1
                    commands2.remove(commands2[num])
                elif list_in_list(command, numbers):
                    commands2.append(int(command))
                elif command == "all":
                    commands2.append(0)
                else:
                    commands2.append(command)

            # 如果只有结尾为全部，则所有都丢弃
            num = 0
            for command in commands2:
                if type(command) is int:
                    num += 1
            if num == 1 and commands2[-1] == 0:
                commands3 = []
                for command in commands2:
                    if type(command) is str:
                        commands3.append(command)
                        commands3.append(0)
            else:
                commands3 = commands2
            drop_list = {}
            num = -1
            for command in commands3:
                num += 1
                if type(command) is not str:
                    continue
                if command in list(jellyfish_list):
                    if num < len(commands3) - 1 and type(commands3[num + 1]) is int:
                        drop_list[jellyfish_list[command]] = commands3[num + 1]
                    else:
                        drop_list[jellyfish_list[command]] = 1
                elif command in jellyfish_group_list:
                    if len(commands3) > num and type(commands3[num + 1]) is int:
                        if commands3[num + 1] != 0:
                            drop_list[command] = "无法指定数量"
                        else:
                            drop_list[command] = 0
                    else:
                        logger.warning(len(commands3))
                        logger.warning(num)
                        drop_list[command] = "无法指定数量-"
                else:
                    drop_list[command] = "不在水母箱"

            logger.debug(drop_list)

            # 检查丢弃数量
            for jellyfish_id in list(drop_list):
                if jellyfish_id in jellyfish_group_list:
                    continue
                else:
                    if jellyfish_id not in list(box_data["jellyfish"]):
                        drop_list[jellyfish_id] = "不在水母箱"
                    elif drop_list[jellyfish_id] > box_data["jellyfish"][jellyfish_id]["number"]:
                        drop_list[jellyfish_id] = "没有这么多哦"
                    elif drop_list[jellyfish_id] == box_data["jellyfish"][jellyfish_id]["number"]:
                        drop_list[jellyfish_id] = 0

            if len(drop_list) == 0:
                message = "丢弃失败，请检查输入信息。例：“丢弃 普通水母 5”"
            else:
                remove_group = []
                message = "成功丢弃"
                for jellyfish_id in list(drop_list):
                    if type(drop_list[jellyfish_id]) is int:
                        if drop_list[jellyfish_id] == 0:
                            if jellyfish_id in jellyfish_group_list:
                                remove_group.append(jellyfish_id)
                            else:
                                message += f"全部{jellyfish_datas[jellyfish_id]['name']}"
                                message += f"{box_data['jellyfish'][jellyfish_id]['number']}只、"
                                box_data["jellyfish"].pop(jellyfish_id)
                        else:
                            box_data["jellyfish"][jellyfish_id]["number"] -= drop_list[jellyfish_id]
                            message += f"{jellyfish_datas[jellyfish_id]['name']}{drop_list[jellyfish_id]}只、"
                message = message.removesuffix("、")
                for jellyfish_id in list(box_data["jellyfish"]):
                    if jellyfish_datas[jellyfish_id]["group"] in remove_group:
                        box_data["jellyfish"].pop(jellyfish_id)
                        message += f"全部{jellyfish_datas[jellyfish_id]['name']}、"

                if message == "成功丢弃":
                    message = ""
                message += "\n出错："
                for jellyfish_id in list(drop_list):
                    if type(drop_list[jellyfish_id]) is not int:
                        if jellyfish_id in list(jellyfish_datas):
                            name = jellyfish_datas[jellyfish_id]["name"]
                        else:
                            name = jellyfish_id
                        message += f"”{name}“:{drop_list[jellyfish_id]}\n"
                if message.endswith("\n出错："):
                    message = message.removesuffix("\n出错：")
                code = 1

                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') "
                        f"values('{user_id}','{json_to_str(box_data)}')")
                    conn.commit()
                except:
                    logger.error("水母箱保存用户数据出错")
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()

    elif command in ["水母图鉴", "图鉴"]:
        # 读取水母箱内容并分组

        # 获取分组
        group_list = jellyfish_group_list.copy()
        for jellyfish_id in jellyfish_datas:
            if jellyfish_datas[jellyfish_id]["group"] not in group_list:
                group_list.append(jellyfish_datas[jellyfish_id]["group"])

        # 转换格式
        j_list = {}
        for group in group_list:
            if group not in list(j_list):
                j_list[group] = []
            for jellyfish_id in jellyfish_datas:
                if group == jellyfish_datas[jellyfish_id]["group"]:
                    j_list[group].append(jellyfish_id)

        # 渲染成图片
        cache_groups = []
        cache_group = []
        for group in list(j_list):
            for jellyfish_id in j_list[group]:
                if len(cache_group) > 11:
                    cache_groups.append(cache_group)
                    cache_group = []

                cache_group.append(
                    {"id": jellyfish_id,
                     "name": jellyfish_datas[jellyfish_id]["name"],
                     "group": jellyfish_datas[jellyfish_id]["group"],
                     "message": jellyfish_datas[jellyfish_id]["message"]}
                )

        if cache_group:
            cache_groups.append(cache_group)

        if draw_model == "text":
            code = 1
            message = "水母图鉴\n"
            num = 0
            for cache_group in cache_groups:
                for cache_data in cache_group:
                    message += f"🪼{cache_data['name']}"
                    if num == 0:
                        num = 1
                    else:
                        num = 0
                        message += "\n"
        else:
            if len(cache_groups) == 1:
                # for cache_group in cache_groups:
                for cache_data in cache_groups[0]:
                    jellyfish_menu.append(cache_data)
                returunpath = await draw_jellyfish_box(draw_box=False, draw_title="水母图鉴")
            else:
                num_x = 0
                image = Image.new("RGB", ((1000 * len(cache_groups)), 3516), draw_config["color"]["bg"])
                for cache_group in cache_groups:
                    jellyfish_menu = []
                    for cache_data in cache_group:
                        jellyfish_menu.append(cache_data)
                    cache_path = await draw_jellyfish_box(draw_box=False, draw_title="水母图鉴")
                    paste_image = Image.open(cache_path, "r")
                    image.paste(paste_image, ((1000 * num_x), 0))
                    num_x += 1
                returunpath = save_image(image)
            code = 2
    elif command == "水母箱样式":
        draw_model_list = {
            "normal": {"name": "默认"},
            "freehand": {"name": "手绘"},
            "text": {"name": "文字"},
        }
        if command2 is None:
            code = 1
            message = "可更换样式："
            num = 0
            for name in list(draw_model_list):
                if num == 0:
                    num = 1
                    message += f"\n| {draw_model_list[name]['name']}"
                elif num == 1:
                    num = 2
                    message += f" | {draw_model_list[name]['name']}"
                elif num == 2:
                    num = 0
                    message += f" | {draw_model_list[name]['name']} |"
            message += "\n例：”水母箱样式 手绘“"
        else:
            # 查找配置名称
            model_name = None
            for name in list(draw_model_list):
                if command2 == draw_model_list[name]["name"]:
                    model_name = name
                    break

            if model_name is None:
                code = 1
                message = "找不到该样式，请检查名称"
            else:
                box_data["draw_model"] = model_name

                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json_to_str(box_data)}')")
                    conn.commit()
                except:
                    logger.error("水母箱保存用户数据出错")
                cursor.close()
                conn.close()

                code = 1
                message = "替换样式成功"
    elif command == "投喂":
        # 投喂

        # 保存

        # 绘制
        returunpath = await draw_jellyfish_box()
        code = 2
    elif command == "换水":
        pass
    elif command == "水母榜":
        pass
    elif command == "装饰":
        pass
    elif command == "帮助":
        command_prompt_list.append({"title": "/水母箱", "message": "查看水母箱相关"})
        command_prompt_list.append({"title": "/水母箱 查看水母箱", "message": "发送水母箱的图片"})
        command_prompt_list.append({"title": "/水母箱 抓水母", "message": "抓几只水母进水母箱（每2小时抓一次）"})
        command_prompt_list.append({"title": "/水母箱 丢弃 普通水母 5", "message": "将5只普通水母丢弃"})
        command_prompt_list.append({"title": "/水母箱 水母图鉴", "message": "查看水母图鉴"})
        command_prompt_list.append({"title": "/水母箱 水母统计表", "message": "查看目前水母箱有多少水母"})
        command_prompt_list.append({"title": "/水母箱 水母箱样式 手绘", "message": "更换显示样式"})
        returunpath = await draw_jellyfish_box(draw_box=False)
        code = 2
    else:
        code = 1
        message = "错误命令"

    return code, message, returunpath, trace


async def draw_jellyfish_live(
        draw_data,
        user_id: str = None,
        path: str = None,
        del_cache: bool = True,
        to_gif: bool = True
):
    """
    绘制动态的水母图片
    :param draw_data: 水母箱的内容
    :param user_id: 用户ID，用于自动修改gif文件名为"{user_id}.gif"
    :param path: 保存的路径，一般不需要填，除非需要指定保存的位置
    :param del_cache: 是否删除gif生成缓存
    :param to_gif: 说否生成gif图，如否则返回 list(多张图片路径)
    :return: 图片路径
    """
    """
    draw_data = {
        "jellyfish": {  # 水母数据
            "j1": {"number": 3},
            "j2": {"number": 5}
        },
        "size": (200, 100),  # 图片大小
        "frame_rate": 10,  # 每秒图片数量，帧率
        "duration": 1.0,  # 时长（秒）
        "background_color": (22, 84, 123, 0),  # 背景颜色
    }
    """

    def azimuthangle(p1, p2):
        """ 已知两点坐标计算角度 -
        :param p1: 原点横坐标(1, 2)
        :param p2: 目标纵坐标(3, 4)
        """
        x = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        x = x * 180 / math.pi  # 转换为角度
        if x < 0:
            x = 360 + x
        return x

    jellyfish_box_datas = await _jellyfish_box_datas()  # 插件数据
    jellyfish_datas = jellyfish_box_datas["jellyfish_datas"]  # 所有水母
    if "draw_model" not in list(draw_data):
        draw_data["draw_model"] = "normal"
    draw_model = draw_data["draw_model"]
    draw_config = jellyfish_box_draw_config(draw_model)

    if "draw_model" in list(draw_data) and draw_data["draw_model"] == "freehand":
        # 创建底图
        image_base = Image.new("RGB", draw_data["size"], draw_config["color"]["bg"])
        draw = ImageDraw.Draw(image_base)
        # 添加底色
        file_path = await get_image_path(f"jellyfish_box-freehand_background.png")
        paste_image = Image.open(file_path, "r")
        paste_image = paste_image.resize(draw_data["size"])
        image_base.paste(paste_image, (0, 0))

        file_path = await get_image_path(f"jellyfish_box-freehand_box_background.png")
        paste_alpha = Image.open(file_path, "r")
        paste_alpha = paste_alpha.resize(draw_data["size"])
        paste_image = Image.new("RGBA", draw_data["size"], draw_config["color"]["box_bg"])
        image_base.paste(paste_image, (0, 0), paste_alpha)
    else:
        image_base = Image.new("RGBA", draw_data["size"], draw_data["background_color"])

    x, y = draw_data["size"]
    # 计算水母的大小
    num = 0
    for jellyfish_id in draw_data["jellyfish"]:
        num += draw_data["jellyfish"][jellyfish_id]["number"]
    if num < 100:
        j_size = int((x + y) / 12)
    elif num < 200:
        j_size = int((x + y) / 12 / 1.5)
    else:
        j_size = int((x + y) / 12 / 2.5)
    # j_size = int(j_size / 2)  # 绘制视频使用，将水母尺寸缩小到25%（长宽各50%）

    # 转换水母数据格式
    jellyfish_data = {}
    num = 0
    for jellyfish_id in draw_data["jellyfish"]:
        jellyfish_num = draw_data["jellyfish"][jellyfish_id]["number"]
        while jellyfish_num > 0:
            jellyfish_num -= 1
            num += 1

            living_locations = jellyfish_datas[jellyfish_id]["living_location"]
            if living_locations:
                living_location = random.choice(living_locations)
            else:
                living_location = "中"
            if living_location == "中":
                paste_x = random.randint(int(x * 0.2), int(x * 0.8))
                paste_y = random.randint(int(y * 0.2), int(y * 0.8))
            elif living_location == "左":
                paste_x = random.randint(0, int(x * 0.2))
                paste_y = random.randint(0, y)
            elif living_location == "右":
                paste_x = random.randint(int(x * 0.8), x)
                paste_y = random.randint(0, y)
            elif living_location == "上":
                paste_x = random.randint(0, x)
                paste_y = random.randint(0, int(y * 0.2))
            elif living_location == "下":
                paste_x = random.randint(0, x)
                paste_y = random.randint(int(y * 0.8), y)
            else:
                paste_x = random.randint(0, x)
                paste_y = random.randint(0, y)

            paste_x -= int(j_size / 2)
            paste_y -= int(j_size / 2)

            jellyfish_data[str(num)] = {
                "jellyfish_id": jellyfish_id,  # s水母id
                "jumping": 0.0,  # 是否在跳跃。False或者0-1的小数
                "x": paste_x,  # 位置x
                "y": paste_y,  # 位置y
                "x_speed": random.randint(j_size * -35, j_size * 35) / 100 / draw_data["frame_rate"],
                "y_speed": random.randint(j_size * -35, j_size * 35) / 100 / draw_data["frame_rate"],
            }

            if living_location != "中":
                jellyfish_data[str(num)]["x_speed"] = random.randint(j_size * -15, j_size * 15) / 100 / draw_data[
                    "frame_rate"]
                jellyfish_data[str(num)]["y_speed"] = random.randint(j_size * -15, j_size * 15) / 100 / draw_data[
                    "frame_rate"]

    # 绘制图片
    date: str = time.strftime("%Y-%m-%d", time.localtime())
    date_year: str = time.strftime("%Y", time.localtime())
    date_month: str = time.strftime("%m", time.localtime())
    date_day: str = time.strftime("%d", time.localtime())
    time_h: str = time.strftime("%H", time.localtime())
    time_m: str = time.strftime("%M", time.localtime())
    time_s: str = time.strftime("%S", time.localtime())
    time_now: int = int(time.time())
    cachepath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/"
    gifcache = f"{cachepath}jellyfish_box/live_cache_{time_now}/"
    if not os.path.exists(gifcache):
        os.makedirs(gifcache)

    returnpath_list = []
    image_num = int(draw_data["frame_rate"] * draw_data["duration"])
    for frame_num in range(image_num):
        logger.debug(f"正在绘制{frame_num}/{image_num}")

        image_box = image_base.copy()
        load_image = "none"
        jellyfish_image = None
        for j_id in list(jellyfish_data):
            j_data = jellyfish_data[j_id]

            # 读取水母图片
            if load_image != j_data['jellyfish_id']:
                file_path = await get_file_path(f"plugin-jellyfish_box-{j_data['jellyfish_id']}.png")
                jellyfish_image = Image.open(file_path, "r")
                jellyfish_image = jellyfish_image.resize((j_size, j_size))
                load_image = j_data['jellyfish_id']
            paste_image = jellyfish_image.copy()

            # 绘制折叠加速效果
            if j_data["jumping"] != 0:
                paste_image = paste_image.resize((
                    int(j_size * (1 + (j_data["jumping"] / 2))),
                    int(j_size * (1.01 - (j_data["jumping"] / 4)))
                ))
                if j_data["jumping"] > 0.05:
                    jellyfish_data[j_id]["jumping"] -= (j_data["jumping"] / 0.3 / draw_data["frame_rate"])
                else:
                    jellyfish_data[j_id]["jumping"] = 0

            # 绘制转向效果
            angle = - 90 - azimuthangle((0, 0), (j_data["x_speed"], j_data["y_speed"]))
            angle += jellyfish_datas[jellyfish_data[j_id]["jellyfish_id"]]["draw"]["rotate"]
            paste_image = paste_image.rotate(angle)
            image_box.paste(paste_image, (j_data["x"], j_data["y"]), mask=paste_image)

            # 更新水母状态
            jellyfish_data[j_id]["x_speed"] -= jellyfish_data[j_id]["x_speed"] * 1 / 3 / draw_data["frame_rate"]
            jellyfish_data[j_id]["y_speed"] -= jellyfish_data[j_id]["y_speed"] * 1 / 3 / draw_data["frame_rate"]
            jellyfish_data[j_id]["x"] = int(jellyfish_data[j_id]["x"] + (jellyfish_data[j_id]["x_speed"]))
            jellyfish_data[j_id]["y"] = int(jellyfish_data[j_id]["y"] + (jellyfish_data[j_id]["y_speed"]))

            # 如果碰到墙壁，则反向游动
            if j_size / 2 - j_size > jellyfish_data[j_id]["x"]:
                jellyfish_data[j_id]["x_speed"] = abs(jellyfish_data[j_id]["x_speed"])
            elif jellyfish_data[j_id]["x"] > x - j_size / 2:
                jellyfish_data[j_id]["x_speed"] = -abs(jellyfish_data[j_id]["x_speed"])
            if j_size / 2 - j_size > jellyfish_data[j_id]["y"]:
                jellyfish_data[j_id]["y_speed"] = abs(jellyfish_data[j_id]["y_speed"])
            elif jellyfish_data[j_id]["y"] > y - j_size / 2:
                jellyfish_data[j_id]["y_speed"] = -abs(jellyfish_data[j_id]["y_speed"])

            # 如果游得很慢，那就加速一次
            if (abs(jellyfish_data[j_id]["x_speed"]) + abs(jellyfish_data[j_id]["x_speed"])) < (j_size * 0.005):
                if jellyfish_datas[jellyfish_data[j_id]["jellyfish_id"]]["draw"]["bounce"] is True:
                    jellyfish_data[j_id]["jumping"] = 1.0
                else:
                    jellyfish_data[j_id]["jumping"] = 0.0
                living_locations = jellyfish_datas[j_data["jellyfish_id"]]["living_location"]
                if living_locations:
                    living_location = random.choice(living_locations)
                else:
                    living_location = "中"

                vr = velocity_ratio = 12 if living_location == "中" else 7
                vr2 = j_size * vr / 20 / draw_data["frame_rate"] / 3

                jellyfish_data[j_id]["x_speed"] = random.randint(j_size * -vr, j_size * vr) / 20 / draw_data[
                    "frame_rate"]
                jellyfish_data[j_id]["y_speed"] = random.randint(j_size * -vr, j_size * vr) / 20 / draw_data[
                    "frame_rate"]

                # 限制最小加速速度，防止发生来回抽搐
                if -vr2 < (jellyfish_data[j_id]["x_speed"] + jellyfish_data[j_id]["y_speed"]) < vr2:
                    jellyfish_data[j_id]["x_speed"] += jellyfish_data[j_id]["x_speed"]
                    jellyfish_data[j_id]["y_speed"] += jellyfish_data[j_id]["y_speed"]

        image_box = image_box.resize(draw_data["size"])
        save_path = f"{gifcache}{frame_num + 1}.png"
        image_box.save(save_path)
        returnpath_list.append(save_path)

    if to_gif is True:
        # 拼接成gif
        logger.info(f"正在拼接gif")
        if path is None:
            if user_id is None:
                returnpath = f"{cachepath}{time_now}_{random.randint(1000, 9999)}.gif"
            else:
                returnpath = f"{cachepath}{user_id}.gif"
        else:
            if user_id is None:
                returnpath = f"{path}{time_now}_{random.randint(1000, 9999)}.gif"
            else:
                returnpath = f"{path}{user_id}.gif"
        frames = []
        png_files = os.listdir(gifcache)
        for frame_id in range(1, len(png_files) + 1):
            frame = Image.open(os.path.join(gifcache, '%d.png' % frame_id))
            frames.append(frame)
        frames[0].save(returnpath, save_all=True, append_images=frames[1:], duration=1000 / draw_data["frame_rate"],
                       loop=0, disposal=2)
        if del_cache is True:
            del_files2(gifcache)

        return returnpath
    else:
        return returnpath_list


def plugin_config(command: str, command2: str | None, channel_id: str):
    # 默认变量 & 插件数据
    message = None
    returnpath = None
    config_list = _config_list()

    # 解析参数中的实际命令名称（命令id）
    command_id = None
    if command2 is not None:
        for name in list(config_list):
            if command2 == config_list[name]["name"]:
                command_id = name
                break

    # 判断格式是否正确
    if command == "开启":
        command_state = True
        if command2 is None:
            return "请添加要关闭的功能名字，例：“开启 签到”", None
        if command_id is None:
            return f"无法找到命令“{command2}”，请检查命令名是否正确", None
    elif command == "关闭":
        command_state = False
        if command2 is None:
            return "请添加要关闭的功能名字，例：“关闭 签到”", None
        if command_id is None:
            return f"无法找到命令“{command2}”，请检查命令名是否正确", None
    else:
        command_state = "查询"

    # 初始化数据库
    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db_path = dbpath + "config.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if not os.path.exists(db_path):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        cursor.execute(
            f"create table command_state(id_ INTEGER primary key AUTOINCREMENT, "
            f"command VARCHAR(10), state BOOLEAN(10), channel_id VARCHAR(10))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "command_state" not in tables:
        cursor.execute(
            f"create table command_state(id_ INTEGER primary key AUTOINCREMENT, "
            f"command VARCHAR(10), state BOOLEAN(10), channel_id VARCHAR(10))")

    # 判断要运行的命令
    if command in ["开启", "关闭"]:
        # 开启或关闭功能
        cursor.execute(
            f'SELECT * FROM command_state WHERE "command" = "{command_id}" AND "channel_id" = "{channel_id}"')
        data = cursor.fetchone()
        if data is not None:
            state = True if data[2] == 1 else False
            if state == command_state:
                pass
            else:
                cursor.execute(
                    f'replace into command_state ("id_","command","state","channel_id") '
                    f'values("{data[0]}","{command_id}",{command_state},"{channel_id}")')
                conn.commit()
        else:
            cursor.execute(
                f'replace into command_state ("command","state","channel_id") '
                f'values("{command_id}",{command_state},"{channel_id}")')
            conn.commit()
        message = f"{command2}已{command}"
    elif command == "菜单":
        # 查询开启的功能
        state = {
            "开启": [],
            "关闭": []
        }
        for command_id in list(config_list):
            cursor.execute(
                f'SELECT * FROM command_state WHERE "command" = "{command_id}" AND "channel_id" = "{channel_id}"')
            data = cursor.fetchone()
            if data is None:
                command_state = config_list[command_id]["state"]
            else:
                command_state = True if data[2] == 1 else False
            if command_state is True:
                state["开启"].append(command_id)
            else:
                state["关闭"].append(command_id)
        message = "功能列表：\n已开启的功能：\n"
        for command_id in state["开启"]:
            command_name = config_list[command_id]["name"]
            message += f"{command_name}\n"
        message += "\n已关闭的功能：\n"
        for command_id in state["关闭"]:
            command_name = config_list[command_id]["name"]
            message += f"{command_name}\n"
        message = message.removesuffix("\n")

    cursor.close()
    conn.close()
    return message, returnpath


async def plugin_emoji_emoji(command):
    message = None

    returnpath = f"{basepath}cache/emoji/"
    if not os.path.exists(returnpath):
        os.makedirs(returnpath)
    returnpath += f"{command}.png"

    if not os.path.exists(returnpath):
        url = f"{kn_config('kanon_api-url')}/json/emoji?imageid={command}"
        return_json = await connect_api("json", url)
        if return_json["code"] == 0:
            url = f"{kn_config('kanon_api-url')}/api/emoji?imageid={command}"
            image = await connect_api("image", url)
            image.save(returnpath)
        else:
            message = f"{command}不支持合成"
    return message, returnpath


async def plugin_emoji_xibao(command, command2, imgmsgs):
    if imgmsgs:
        url = imgmsgs[0]
        try:
            image = await connect_api("image", url)
        except Exception as e:
            image = await draw_text("获取图片出错", 50, 10)
            logger.error(f"获取图片出错:{e}")
    else:
        image = None

    if command2 is None:
        command2 = " "

    if command == "喜报":
        text_color1 = "#FFFF00"
        text_color2 = "#FF0000"
        text_color3 = "#EC5307"
    else:
        text_color1 = "#FFFFFF"
        text_color2 = "#000000"
        text_color3 = "#ECECEC"

    if kn_config("kanon_api-state"):
        file_path = f"{basepath}cache/plugin_image/"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        if command == "喜报":
            file_path += "喜报.png"
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-xibao"
        else:
            file_path += "悲报.png"
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-beibao"
        if os.path.exists(file_path):
            xibao_image = Image.open(file_path, "r")
        else:
            try:
                xibao_image = await connect_api("image", url)
                xibao_image.save(file_path)
            except Exception as e:
                xibao_image = await draw_text("获取图片出错", 50, 10)
                logger.error(f"368-获取图片出错:{e}")
                return save_image(xibao_image)
    else:
        xibao_image = Image.new("RGB", (600, 450), (0, 0, 0))

    if command2 != " " and imgmsgs:
        image = image_resize2(image, (200, 200), overturn=False)
        w, h = image.size
        x = int((600 - w) / 2 + 130)
        y = int((450 - h) / 2 + 30)
        xibao_image.paste(image, (x, y), mask=image)

        textlen = len(command2)
        fortlen = 40
        x = 190
        if textlen <= 6:
            x = int(x - ((textlen / 2) * fortlen))
        else:
            x = x - (3 * fortlen)
        y = 200 - int(textlen * 0.05 * fortlen)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            textlen=6,
            text_color=text_color1,
            draw_qqemoji=False,
            calculate=False
        )
        box = (x + 2, y + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x - 2, y + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x + 2, y - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x - 2, y - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            text_color=text_color2,
            textlen=6,
            draw_qqemoji=True,
            calculate=False
        )
        box = (x, y)
        xibao_image.paste(paste_image, box, mask=paste_image)

    elif command2 != " ":
        textlen = len(command2)
        if textlen <= 6:
            fortlen = 200 - (textlen * 25)
        else:
            fortlen = 40

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            textlen=12,
            text_color=text_color1,
            draw_qqemoji=False,
            calculate=False
        )
        w, h = paste_image.size
        x, y = xibao_image.size
        box = (int((x - w) / 2) + 2, int((y - h) / 2) + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) - 2, int((y - h) / 2) + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) + 2, int((y - h) / 2) - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) - 2, int((y - h) / 2) - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            text_color=text_color2,
            textlen=12,
            draw_qqemoji=True,
            calculate=False
        )
        w, h = paste_image.size
        x, y = xibao_image.size
        box = (int((x - w) / 2), int((y - h) / 2))
        xibao_image.paste(paste_image, box, mask=paste_image)

    elif imgmsgs:
        image = image_resize2(image, (500, 300), overturn=False)
        w, h = image.size
        xibao_image_w, xibao_image_h = xibao_image.size
        x = int((xibao_image_w - w) / 2)
        y = int((xibao_image_h - h) / 2 + 30)
        xibao_image.paste(image, (x, y), mask=image)
        image = Image.new(mode='RGB', size=(w, h), color=text_color3)
        mask_image = Image.new("RGBA", (w, h), (0, 0, 0, 15))
        xibao_image.paste(image, (x, y), mask=mask_image)

    return save_image(xibao_image)


async def plugin_emoji_yizhi(user_avatar: str):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = Image.open(user_avatar, "r")
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    imageyizhi = Image.new(mode='RGB', size=(768, 950), color="#FFFFFF")
    draw = ImageDraw.Draw(imageyizhi)

    imageyizhi.paste(user_image, (64, 64), mask=user_image)
    image_face = image_resize2(user_image, (100, 100), overturn=False)
    imageyizhi.paste(image_face, (427, 800), mask=image_face)

    file_path = await get_file_path("SourceHanSansK-Bold.ttf")
    font = ImageFont.truetype(font=file_path, size=85)
    draw.text(xy=(60, 805), text='要我一直        吗？', fill=(0, 0, 0), font=font)

    return save_image(imageyizhi)


async def plugin_emoji_keai(user_avatar: str, user_name: str):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = Image.open(user_avatar, "r")
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    image = Image.new(mode='RGB', size=(768, 950), color="#FFFFFF")
    draw = ImageDraw.Draw(image)
    w, h = user_image.size
    image.paste(user_image, (int((768 - w) / 2), int((854 - h) / 2)))

    text = f'请问你们看到{user_name}了吗？'
    image_paste = await draw_text(text, 50, 30)
    image_paste = image_resize2(image_paste, (730, 82), overturn=False)
    image.paste(image_paste, (19, 10), mask=image_paste)

    font_file = await get_file_path("SourceHanSansK-Bold.ttf")
    font = ImageFont.truetype(font=font_file, size=60)
    draw.text(xy=(20, 810), text='非常可爱！简直就是小天使', fill=(0, 0, 0), font=font)

    font = ImageFont.truetype(font=font_file, size=32)
    draw.text(xy=(30, 900), text='ta没失踪也没怎么样，我只是觉得你们都该看一下', fill=(0, 0, 0),
              font=font)

    return save_image(image)


async def plugin_emoji_jiehun(user_avatar, name1, name2):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = Image.open(user_avatar, "r")
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    image = Image.new("RGB", (640, 640), "#FFFFFF")
    path = await get_file_path("plugin-jiehun-jiehun.png")
    paste_image = Image.open(path, mode="r")
    image.paste(user_image, (0, 0), mask=user_image)
    image.paste(paste_image, (0, 0), mask=paste_image)

    # 添加名字1
    if len(name1) >= 10:
        name1 = name1[0:9] + "..."

    imagetext = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    paste_image = await draw_text(name1, 17, 13)
    imagetext.paste(paste_image, (0, 90), mask=paste_image)
    imagetext = imagetext.rotate(-18.5)
    image.paste(imagetext, (40, 443), mask=imagetext)

    # 添加名字1
    if len(name2) >= 10:
        name2 = name2[0:9] + "..."

    imagetext = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    paste_image = await draw_text(name2, 17, 13)
    imagetext.paste(paste_image, (0, 90), mask=paste_image)
    imagetext = imagetext.rotate(-18.5)
    image.paste(imagetext, (210, 500), mask=imagetext)

    return save_image(image)


async def plugin_emoji_momo(user_avatar):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = Image.open(user_avatar, "r")
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    filepath = await get_file_path("plugin-emoji-momo-0.png")
    pic = Image.open(filepath, mode="r")

    date_year = time.strftime("%Y", time.localtime())
    date_month = time.strftime("%m", time.localtime())
    date_day = time.strftime("%d", time.localtime())
    timestamp = str(time.time())
    returnpath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/摸摸/"
    gifcache = f"{returnpath}{timestamp}_{random.randint(1000, 9999)}gifcache/"
    if not os.path.exists(gifcache):
        os.makedirs(gifcache)

    image_x = [75, 74, 76, 78, 77]
    image_y = [83, 84, 82, 80, 81]
    imagepace_x = [33, 33, 33, 33, 33]
    imagepace_y = [37, 35, 33, 36, 40]

    image_face_clown = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    image_face_clown = circle_corner(image_face_clown, 30)

    imagenum = len(image_x)
    num = 1
    while num <= imagenum:
        print_imagepace_x = imagepace_x[num - 1]
        print_imagepace_y = imagepace_y[num - 1]
        print_image_x = image_x[num - 1]
        print_image_y = image_y[num - 1]
        print_image_face = user_image.resize((print_image_x, print_image_y))
        print_image_face_clown = image_face_clown.resize((print_image_x, print_image_y))

        pic1 = pic
        filepath = await get_file_path("plugin-emoji-momo-0.png")
        pic = Image.open(filepath, mode="r")
        filepath = await get_file_path(f"plugin-emoji-momo-{num}.png")
        paste_image = Image.open(filepath, mode="r")

        pic1.paste(pic, (0, 0))
        pic1.paste(print_image_face, (print_imagepace_x, print_imagepace_y),
                   mask=print_image_face_clown)
        pic1.paste(paste_image, (0, 0), mask=paste_image)

        pic1.save(f"{gifcache}/{num}.png")
        num += 1

    returnpath = f"{returnpath}{timestamp}_{random.randint(1000, 9999)}.gif"
    frames = []
    png_files = os.listdir(gifcache)
    for frame_id in range(1, len(png_files) + 1):
        frame = Image.open(os.path.join(gifcache, '%d.png' % frame_id))
        frames.append(frame)
    frames[0].save(returnpath, save_all=True, append_images=frames[1:], duration=70, loop=0,
                   disposal=2)

    return returnpath


# async def plugin_emoji_qinqin(user_avatar, user_name):
#     try:
#         if user_avatar in [None, "None", "none"]:
#             user_image = await draw_text("图片", 50, 10)
#         elif user_avatar.startswith("http"):
#             user_image = await connect_api("image", user_avatar)
#         else:
#             user_image = Image.open(user_avatar, "r")
#     except Exception as e:
#         user_image = await draw_text("图片", 50, 10)
#         logger.error(f"获取图片出错:{e}")
#     user_image = image_resize2(user_image, (640, 640), overturn=False)
#
#
#     pass
#
#     return save_image(image)


async def plugin_game_cck(command: str, channel_id: str, platform: str):
    """
    cck插件内容
    返回：
    当code = 0时，不做任何回复；
    当code = 1时，回复message消息；
    当code = 2时，回复returnpath目录中的图片
    当code = 3时，回复message消息和returnpath目录中的图片
    :param command: 命令
    :param channel_id: 频道号
    :return: code, message, returnpath
    """
    global kn_cache
    time_now = int(time.time())
    code = 0
    message = " "
    returnpath = None
    markdown = keyboard = None
    if not kn_config("kanon_api-state"):
        logger.error("未开启api，已经退出cck")
        return 0, message, returnpath

    # 获取游戏基本数据（卡牌列表）
    filepath = await get_file_path("plugin-cck-member_list.json")
    data = open(filepath, 'r', encoding='utf8')
    cck_game_data = json.load(data)

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
    logger.debug(f"该群正在进行的游戏{data}")

    game_state = None
    if data is not None:
        # 有game数据
        gameing = data[3]
        if gameing == 1:
            # 有正在进行的game
            gamename: str = data[1]
            if gamename == "小游戏-猜猜看":
                # 正在进行的是猜猜看
                if int(time_now) <= (int(data[2]) + 600):
                    # 正在运行的cck最后一次运行时间相隔现在5分钟内
                    if command == "猜猜看":
                        message = "已经在cck了"
                        code = 1
                    else:
                        game_state = "gameing"
                else:
                    # 正在运行的cck最后一次运行时间相隔现在5分钟后
                    if command == "猜猜看":
                        game_state = "new"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename}时间超时，请重新开始"
            else:
                # 正在进行其他游戏
                code = 1
                if "-" in gamename:
                    gamename = gamename.split("-")[1]
                message = f"正在进行{gamename}，请先结束{gamename}。\n结束指令“/{gamename} 结束”"
        else:
            # 没有正在进行的game
            if command == '猜猜看':
                game_state = "new"
            else:
                code = 1
                message = "没有在猜猜看哦"
    else:
        # data is None
        if command == "猜猜看":
            game_state = "new"
        elif command in ["不知道", "是"]:
            code = 1
            message = "没有在进行猜猜看哦"
        else:
            code = 1
            message = "没有在猜猜看哦。"

    if "plugin_game_cck" not in list(kn_cache):
        kn_cache["plugin_game_cck"] = {"game_data": {}}
    if "game_data" not in list(kn_cache["plugin_game_cck"]):
        kn_cache["plugin_game_cck"]["game_data"] = {}
    if command in list(kn_cache["plugin_game_cck"]["game_data"]):
        member_id: str = kn_cache["plugin_game_cck"]["game_data"][command]["member_id"]
        member_name: str = kn_cache["plugin_game_cck"]["game_data"][command]["member_name"]
        image_name: str = kn_cache["plugin_game_cck"]["game_data"][command]["image_name"]
        if kn_cache["plugin_game_cck"]["game_data"][command]["gameing"] is False:
            message = f"是{member_name}哦（{image_name.removesuffix('.png')}）"
            code = 1
        else:
            message = "游戏未完成，不能查询结果哦"
            code = 1

    if code == 1 and message != " ":
        pass
    elif game_state == "new":
        logger.debug('新建游戏')
        member_ids = list(cck_game_data["member_data"])
        member_id = random.choice(member_ids)  # 选择一个角色

        image_name = random.choice(cck_game_data["member_data"][member_id]["images"])  # 选择一张卡牌
        member_name = cck_game_data["member_data"][member_id]["member_name"]
        member_alias = cck_game_data["member_data"][member_id]["alias"]

        # 收集本次游戏数据
        gameinfo = {
            "member_id": member_id,  # 角色id
            "member_name": member_name,  # 角色名称
            "image_name": image_name,  # 卡牌的文件名
            "member_alias": member_alias,  # 角色别称
        }

        # 获取卡牌png文件
        if cck_game_data["info"]["version"] == "1":
            returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/"
        else:
            returnpath = f"{basepath}cache/plugin/bangdream-card/"

        if not os.path.exists(returnpath):
            os.makedirs(returnpath)
        returnpath += image_name
        if not os.path.exists(returnpath):
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-"

            if cck_game_data["info"]["version"] == "1":
                url += f"cck-{member_id}-{image_name}"
            else:
                url += f"bangdream_card-{image_name}"

            try:
                image = await connect_api("image", url)
                image.save(returnpath)
            except Exception as e:
                logger.error(f"获取图片出错:{e}")
                return 1, "图片下载出错"

        # 保存缓存
        num = 50
        game_id = "0"
        while num > 0:
            num -= 1
            if num < 5:
                game_id = str(random.randint(10000000, 99999999))
            elif num < 10:
                game_id = str(random.randint(1000000, 9999999))
            else:
                game_id = str(random.randint(10000, 99999))
            if game_id in list(kn_cache["plugin_game_cck"]["game_data"]) and num > 1:
                continue
            kn_cache["plugin_game_cck"]["game_data"][game_id] = {
                "member_id": member_id,
                "member_name": member_name,
                "image_name": image_name,
                "gameing": True,
            }
            break
        gameinfo["game_id"] = game_id

        # 保存数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","小游戏-猜猜看","{time_now}",True,"{gameinfo}")')
        cursor.close()
        conn.commit()
        conn.close()

        # 切分卡牌为3张，并保存为1张
        cck_card = Image.open(returnpath, mode="r")
        x = 1334
        y = 1002

        # 切分1
        cck_imane1 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane1)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane1.paste(cck_card, (trimx, trimy))

        # 切分2
        cck_imane2 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane2)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane2.paste(cck_card, (trimx, trimy))

        # 切分3
        cck_imane3 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane3)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane3.paste(cck_card, (trimx, trimy))

        # 合并1
        cck_imane = Image.new("RGB", (150, 150), "#FFFFFF")
        cck_imane1 = cck_imane1.resize((150, 50))
        cck_imane.paste(cck_imane1, (0, 0))

        # 合并2
        cck_imane2 = cck_imane2.resize((150, 50))
        cck_imane.paste(cck_imane2, (0, 50))

        # 合并3
        cck_imane3 = cck_imane3.resize((150, 50))
        cck_imane.paste(cck_imane3, (0, 100))

        # 添加回复的句子
        num = random.randint(1, 5)
        if num == 1:
            message = '那个女人是谁呢？好美'
        elif num == 2:
            message = '猜猜wlp是谁～'
        elif num == 3:
            message = '猜猜她是谁～'
        elif num == 4:
            message = '猜猜她是谁～'
        elif num == 5:
            message = '猜猜她是谁～'
        message += ("\n游戏限制5分钟内"
                    "\n@bot并发送/猜猜看+名字"
                    "\n例：“@kanon/猜猜看 花音”"
                    "\n发送“/猜猜看 不知道”结束游戏"
                    f"\ncck_id: {game_id}")

        if kn_config("plugin_cck", "draw_type") == 1:
            image = Image.new("RGB", (150, 150), "#FFFFFF")
            image.paste(cck_imane, (0, 0))
            returnpath = save_image(image)
            code = 3
        elif kn_config("plugin_cck", "draw_type") == 2:
            image = Image.new("RGB", (440, 150), "#FFFFFF")
            image.paste(cck_imane, (0, 0))

            paste_image = await draw_text(
                message,
                size=16,
                textlen=30,
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf"),
                text_color="#000000"
            )
            image.paste(paste_image, (163, 10), paste_image)
            returnpath = save_image(image)

            code = 2  # 添加回复的类型
        else:
            image = Image.new("RGB", (150, 150), "#FFFFFF")
            image.paste(cck_imane, (0, 0))
            returnpath = save_image(image)
            code = 3

        # # 以下plugin_cck的设置内容需要md按钮模板，故不推荐设置，默认就好，这里仅作展示，未来也许会删除
        # [plugin]
        # # md模板，可配合cck功能使用
        # none_markdown = "123456"  # 空白模板
        # [plugin_cck]
        # # 发送按钮开关 需要开发者自行申请按钮模板
        # send_button = false
        # button_1_id = "123456"  # 分组1按钮id  成员id为11-30发送 (按钮json在developer/plugin_cck_config文件夹内）
        # button_2_id = "123456"  # 分组2按钮id  成员id为31-45、106-110发送 (按钮json在developer/plugin_cck_config文件夹内）
        # markdown_id = "123456"  # 空白模板id，用于配合按钮一起发送
        # # 发送markdown开关 需要开发者自行申请按钮模板
        # send_markdown = false  # 将图片以md形式发送，开启后可配合按钮一起发送

        if platform == "qq_Official" and kn_config("plugin_cck", "send_markdown"):
            # 去除消息的图片内容
            if code == 3:
                code = 1
            elif code == 2:
                code = 0
            # 转换图片为md
            markdown = {
                "id": kn_config("plugin", "markdown_id"),
                "params": [
                    {"key": "text", "values": ["img"]},
                    {"key": "imagex", "values": [f"{image.size[0]}"]},
                    {"key": "imagey", "values": [f"{image.size[1]}"]},
                    {"key": "image", "values": [f"{await imgpath_to_url(returnpath)}"]},
                ]
            }

        if platform == "qq_Official" and kn_config("plugin_cck", "send_button"):
            if 11 <= int(member_id) <= 30:
                button_id = "button_1_id"
            elif 31 <= int(member_id) <= 45 or 106 <= int(member_id) <= 110:
                button_id = "button_2_id"
            else:
                button_id = None

            if button_id is not None:
                keyboard = {"id": kn_config("plugin_cck", button_id)}
                markdown = {"id": kn_config("plugin_cck", "markdown_id")}

    elif game_state == "gameing":
        # 正在游戏中，判断不是”不知道“，否则为判断角色名是否符合
        if command == "不知道":
            # 读取游戏数据
            gamedata = json.loads(data[4].replace("'", '"'))
            member_id: str = gamedata["member_id"]
            member_name: str = gamedata["member_name"]
            image_name: str = gamedata["image_name"]
            if "game_id" in list(gamedata):
                game_id = gamedata["game_id"]
                if game_id in list(kn_cache["plugin_game_cck"]["game_data"]):
                    kn_cache["plugin_game_cck"]["game_data"][game_id]["gameing"] = False

            # 返回卡牌图片和句子
            if cck_game_data["info"]["version"] == "1":
                returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/{image_name}"
            else:
                returnpath = f"{basepath}cache/plugin/bangdream-card/{image_name}"

            message = f"是{member_name}哦（{image_name.removesuffix('.png')}）"
            code = 3

            # 将”结束游戏状态“写入到数据库
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            cursor.execute(
                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                f'"{channel_id}","none","0",False,"none")')
            cursor.close()
            conn.commit()
            conn.close()
        else:
            # 读取游戏内容
            gamedata = json.loads(data[4].replace("'", '"'))
            member_id: str = gamedata["member_id"]
            member_name: str = gamedata["member_name"]
            image_name: str = gamedata["image_name"]
            member_alias = gamedata["member_alias"]

            # 判断用户发送词是否符合
            if command.lower() in member_alias:
                if "game_id" in list(gamedata):
                    game_id = gamedata["game_id"]
                    if game_id in list(kn_cache["plugin_game_cck"]["game_data"]):
                        kn_cache["plugin_game_cck"]["game_data"][game_id]["gameing"] = False
                # 添加回复句子与图
                message = f"恭喜猜中，她就是{command}（{image_name.removesuffix('.png')}）"
                if cck_game_data["info"]["version"] == "1":
                    returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/{image_name}"
                else:
                    returnpath = f"{basepath}cache/plugin/bangdream-card/{image_name}"
                code = 3

                # 将”结束游戏状态“写入到数据库
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                cursor.execute(
                    f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                    f'"{channel_id}","none","0",False,"none")')
                cursor.close()
                conn.commit()
                conn.close()
            else:
                message = f"猜错了哦，她不是{command}"
                code = 0
    elif game_state == "exit":
        # 手动退出game状态
        # 读取游戏数据
        try:
            gamedata = json.loads(data[4].replace("'", '"'))
            if "game_id" in list(gamedata):
                game_id = gamedata["game_id"]
                if game_id in list(kn_cache["plugin_game_cck"]["game_data"]):
                    kn_cache["plugin_game_cck"]["game_data"][game_id]["gameing"] = False
        except Exception as e:
            logger.error("保存游戏状态出错")

        # 将”结束游戏状态“写入到数据库
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","none","0",False,"none")')
        cursor.close()
        conn.commit()
        conn.close()

    return code, message, returnpath, markdown, keyboard


async def plugin_game_blowplane(command: str, channel_id: str):
    """
    炸飞机插件内容
    返回：
    当code = 0时，不做任何回复；
    当code = 1时，回复message消息；
    当code = 2时，回复returnpath目录中的图片
    当code = 3时，回复message消息和returnpath目录中的图片
    :param command: 命令
    :param channel_id: 频道号
    :return: code, message, returnpath
    """
    code = 0
    message = ""
    returnpath = ""
    time_now = str(int(time.time()))

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
    logger.debug(f"该群正在进行的游戏{data}")

    game_state = None
    if data is not None:
        # 有game数据
        gameing = data[3]
        if gameing == 1:
            # 有正在进行的game
            gamename = data[1]
            if gamename == "小游戏-炸飞机":
                # 正在进行的是炸飞机
                if int(time_now) <= (int(data[2]) + 300):
                    # 正在运行的炸飞机最后一次运行时间相隔现在5分钟内
                    if command == "炸飞机":
                        message = "已经在炸飞机了"
                        code = 1
                    else:
                        game_state = "gameing"
                else:
                    # 正在运行的炸飞机最后一次运行时间相隔现在5分钟后
                    if command == "炸飞机":
                        game_state = "new"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename}时间超时，请重新开始"
            else:
                # 正在进行其他游戏
                if "-" in gamename:
                    gamename = gamename.split("-")[1]
                code = 1
                message = f"正在进行{gamename}，请先结束{gamename}。\n结束指令“/{gamename} 结束”"
        else:
            # 没有正在进行的game
            if command == "炸飞机":
                game_state = "new"
            else:
                code = 1
                message = "没有在炸飞机哦"
    else:
        # data is None
        if command == "炸飞机":
            game_state = "new"
        elif command.startswith("炸") or command == "结束":
            code = 1
            message = "没有在进行炸飞机哦"
        else:
            code = 1
            message = "没有在炸飞机哦。"

    if game_state == "new":
        # 生成游戏数据
        #  生成飞机位置
        plantnum = 3
        num = plantnum
        plants_info = []
        while num >= 1:
            num -= 1
            plant_info = []
            plant_dection = random.randint(0, 3)
            if plant_dection == 0:  # 向下
                plantx1 = 3
                plantx2 = 8
                planty1 = 1
                planty2 = 7
            elif plant_dection == 1:  # 向左
                plantx1 = 1
                plantx2 = 7
                planty1 = 3
                planty2 = 8
            elif plant_dection == 2:  # 向上
                plantx1 = 3
                plantx2 = 8
                planty1 = 4
                planty2 = 10
            else:  # 向右
                plantx1 = 4
                plantx2 = 10
                planty1 = 3
                planty2 = 8
            plantx = random.randint(plantx1, plantx2)
            planty = random.randint(planty1, planty2)
            plant_info.append(plantx)
            plant_info.append(planty)
            plant_info.append(plant_dection)

            # 计算出飞机各个坐标
            plantxys = []
            if plant_dection == 0:  # 向上
                plantxys.append((plantx, planty))
                plantxys.append((plantx - 2, planty + 1))
                plantxys.append((plantx - 1, planty + 1))
                plantxys.append((plantx, planty + 1))
                plantxys.append((plantx + 1, planty + 1))
                plantxys.append((plantx + 2, planty + 1))
                plantxys.append((plantx, planty + 2))
                plantxys.append((plantx - 1, planty + 3))
                plantxys.append((plantx, planty + 3))
                plantxys.append((plantx + 1, planty + 3))
            elif plant_dection == 1:  # 向左
                plantxys.append((plantx, planty))
                plantxys.append((plantx + 1, planty - 2))
                plantxys.append((plantx + 1, planty - 1))
                plantxys.append((plantx + 1, planty))
                plantxys.append((plantx + 1, planty + 1))
                plantxys.append((plantx + 1, planty + 2))
                plantxys.append((plantx + 2, planty))
                plantxys.append((plantx + 3, planty - 1))
                plantxys.append((plantx + 3, planty))
                plantxys.append((plantx + 3, planty + 1))
            elif plant_dection == 2:  # 向下
                plantxys.append((plantx, planty))
                plantxys.append((plantx + 2, planty - 1))
                plantxys.append((plantx + 1, planty - 1))
                plantxys.append((plantx, planty - 1))
                plantxys.append((plantx - 1, planty - 1))
                plantxys.append((plantx - 2, planty - 1))
                plantxys.append((plantx, planty - 2))
                plantxys.append((plantx + 1, planty - 3))
                plantxys.append((plantx, planty - 3))
                plantxys.append((plantx - 1, planty - 3))
            else:  # 向右
                plantxys.append((plantx, planty))
                plantxys.append((plantx - 1, planty - 2))
                plantxys.append((plantx - 1, planty - 1))
                plantxys.append((plantx - 1, planty))
                plantxys.append((plantx - 1, planty + 1))
                plantxys.append((plantx - 1, planty + 2))
                plantxys.append((plantx - 2, planty))
                plantxys.append((plantx - 3, planty - 1))
                plantxys.append((plantx - 3, planty))
                plantxys.append((plantx - 3, planty + 1))

            # 检查是否合理
            plane_save = True
            for cache_plant_info in plants_info:
                cache_plant_dection = cache_plant_info[2]
                cache_plantx = cache_plant_info[0]
                cache_planty = cache_plant_info[1]

                cache_plantxys = []
                if cache_plant_dection == 0:  # 向上
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                elif cache_plant_dection == 1:  # 向左
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                elif cache_plant_dection == 2:  # 向下
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                else:  # 向右
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                for cache_plantxy in cache_plantxys:
                    for plantxy in plantxys:
                        if plantxy == cache_plantxy:
                            plane_save = False
            if plane_save is True:
                plants_info.append(plant_info)
            else:
                num += 1

        # 创建底图
        image = new_background(900, 900)
        filepath = await get_file_path("plugin-zfj-farme.png")
        paste_image = Image.open(filepath, mode="r")
        image.paste(paste_image, (0, 0), mask=paste_image)

        returnpath = save_image(image)

        boms_list = []

        # 收集本次游戏数据
        gameinfo = {
            "plants_info": plants_info,  # 飞机数据
            "boms_list": boms_list,  # 炸弹数据
        }

        # 保存数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","小游戏-炸飞机","{time_now}",True,"{gameinfo}")')
        cursor.close()
        conn.commit()
        conn.close()

        message = '游戏已生成，发送/炸飞机+坐标进行游戏。' \
                  '\n例：“@kanon/炸飞机 a1”' \
                  '\n请在5分钟内完成游戏。' \
                  '\n你拥有13颗炸弹' \
                  '\n发送“/炸飞机 结束”可以提前结束游戏'
        code = 3
    elif game_state == "gameing":
        # 读取游戏数据
        gamedata = json.loads(data[4].replace("'", '"'))
        plants_info = gamedata["plants_info"]
        boms_list = gamedata["boms_list"]

        if command == "结束":
            # 创建底图
            image = new_background(900, 900)
            filepath = await get_file_path("plugin-zfj-farme.png")
            paste_image = Image.open(filepath, mode="r")
            image.paste(paste_image, (0, 0), mask=paste_image)

            # 获取飞机图片
            filepath = await get_file_path("plugin-zfj-plane1.png")
            paste_image_1 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-plane2.png")
            paste_image_2 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-plane3.png")
            paste_image_3 = Image.open(filepath, mode="r")

            # 绘制飞机的位置
            num = 0
            for plant_info in plants_info:
                if num == 0:
                    paste_image_0 = paste_image_1
                elif num == 1:
                    paste_image_0 = paste_image_2
                else:
                    paste_image_0 = paste_image_3
                num += 1

                cache_plantx = int(plant_info[0])
                cache_planty = int(plant_info[1])
                cache_plant_dection = int(plant_info[2])
                cache_plantxy = (cache_plantx, cache_planty)

                cache_plantxys = []
                if cache_plant_dection == 0:  # 向上
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                elif cache_plant_dection == 1:  # 向左
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                elif cache_plant_dection == 2:  # 向下
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                else:  # 向右
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                for cache_plantxy in cache_plantxys:
                    plantx = cache_plantxy[0]
                    planty = cache_plantxy[1]
                    printx = -16 + plantx * 78
                    printy = -16 + planty * 78
                    image.paste(paste_image_0, (printx, printy), mask=paste_image_0)

            # 获取状态图片
            filepath = await get_file_path("plugin-zfj-miss.png")
            paste_image_0 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-injured.png")
            paste_image_1 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-crash.png")
            paste_image_2 = Image.open(filepath, mode="r")

            # 绘制现在状态图
            for bom in boms_list:
                printx = -16 + (int(bom[0]) * 78)
                printy = -16 + (int(bom[1]) * 78)
                bom_state = int(bom[2])
                if bom_state == 0:
                    image.paste(paste_image_0, (printx, printy), mask=paste_image_0)
                elif bom_state == 1:
                    image.paste(paste_image_1, (printx, printy), mask=paste_image_1)
                elif bom_state == 2:
                    image.paste(paste_image_2, (printx, printy), mask=paste_image_2)

            # 保存图片
            returnpath = save_image(image)
            message = "游戏已结束"
            code = 3

            # 将”结束游戏状态“写入到数据库
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            cursor.execute(
                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                f'"{channel_id}","none","0",False,"none")')
            cursor.close()
            conn.commit()
            conn.close()
        else:
            if command.startswith("炸"):
                command = command.removeprefix('炸')
            # 转换坐标为数字
            bomx = 0
            if "a" in command:
                bomx = 1
            elif "b" in command:
                bomx = 2
            elif "c" in command:
                bomx = 3
            elif "d" in command:
                bomx = 4
            elif "e" in command:
                bomx = 5
            elif "f" in command:
                bomx = 6
            elif "g" in command:
                bomx = 7
            elif "h" in command:
                bomx = 8
            elif "i" in command:
                bomx = 9
            elif "j" in command:
                bomx = 10

            bomy = 0
            if "10" in command:
                bomy = 10
            elif "1" in command:
                bomy = 1
            elif "2" in command:
                bomy = 2
            elif "3" in command:
                bomy = 3
            elif "4" in command:
                bomy = 4
            elif "5" in command:
                bomy = 5
            elif "6" in command:
                bomy = 6
            elif "7" in command:
                bomy = 7
            elif "8" in command:
                bomy = 8
            elif "9" in command:
                bomy = 9

            if bomx == 0 or bomy == 0:
                code = 1
                message = "错误，请检查拼写。只能使用小写字母和数字来表示位置"
            else:
                if len(boms_list) >= 14:
                    # 炸弹用完，结束游戏
                    # 创建底图
                    image = new_background(900, 900)
                    filepath = await get_file_path("plugin-zfj-farme.png")
                    paste_image = Image.open(filepath, mode="r")
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取飞机图片
                    filepath = await get_file_path("plugin-zfj-plane1.png")
                    plane_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = Image.open(filepath, mode="r")

                    # 绘制飞机的位置
                    num = 0
                    for plant_info in plants_info:
                        if num == 0:
                            paste_image = plane_image_1
                        elif num == 1:
                            paste_image = plane_image_2
                        else:
                            paste_image = plane_image_3
                        num += 1

                        cache_plantx = int(plant_info[0])
                        cache_planty = int(plant_info[1])
                        cache_plant_dection = int(plant_info[2])
                        cache_plantxy = (cache_plantx, cache_planty)

                        cache_plantxys = []
                        if cache_plant_dection == 0:  # 向上
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                            cache_plantxys.append((cache_plantx, cache_planty + 2))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                            cache_plantxys.append((cache_plantx, cache_planty + 3))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                        elif cache_plant_dection == 1:  # 向左
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                            cache_plantxys.append((cache_plantx + 2, cache_planty))
                            cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 3, cache_planty))
                            cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                        elif cache_plant_dection == 2:  # 向下
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                            cache_plantxys.append((cache_plantx, cache_planty - 2))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                            cache_plantxys.append((cache_plantx, cache_planty - 3))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                        else:  # 向右
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                            cache_plantxys.append((cache_plantx - 2, cache_planty))
                            cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 3, cache_planty))
                            cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                        for cache_plantxy in cache_plantxys:
                            plantx = cache_plantxy[0]
                            planty = cache_plantxy[1]
                            printx = -16 + plantx * 78
                            printy = -16 + planty * 78
                            image.paste(paste_image, (printx, printy), mask=paste_image)

                    # 获取状态图片
                    filepath = await get_file_path("plugin-zfj-miss.png")
                    state_image_0 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = Image.open(filepath, mode="r")

                    # 绘制现在状态图
                    for bom in boms_list:
                        printx = -16 + (int(bom[0]) * 78)
                        printy = -16 + (int(bom[1]) * 78)
                        bom_state = int(bom[2])
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 保存图片
                    returnpath = save_image(image)
                    message = "炸弹已用光，游戏结束"
                    code = 3

                    # 将”结束游戏状态“写入到数据库
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                        f'"{channel_id}","none","0",False,"none")')
                    cursor.close()
                    conn.commit()
                    conn.close()
                else:
                    # 创建底图
                    image = new_background(900, 900)
                    filepath = await get_file_path("plugin-zfj-farme.png")
                    paste_image = Image.open(filepath, mode="r")
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取状态图片
                    filepath = await get_file_path("plugin-zfj-miss.png")
                    state_image_0 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = Image.open(filepath, mode="r")

                    # 绘制现在状态图
                    for bom in boms_list:
                        printx = -16 + (int(bom[0]) * 78)
                        printy = -16 + (int(bom[1]) * 78)
                        bom_state = int(bom[2])
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 获取飞机图片
                    filepath = await get_file_path("plugin-zfj-plane1.png")
                    plane_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = Image.open(filepath, mode="r")

                    bomstate = -1
                    for bom in boms_list:
                        printx = int(bom[0])
                        printy = int(bom[1])
                        if printx == bomx and printy == bomy:
                            bomstate = 3
                    if bomstate != 3:
                        bomxy = (bomx, bomy)
                        for plant_info in plants_info:
                            cache_plantx = int(plant_info[0])
                            cache_planty = int(plant_info[1])
                            cache_plant_dection = int(plant_info[2])
                            cache_plantxy = (cache_plantx, cache_planty)
                            if bomxy == cache_plantxy:
                                bomstate = 2
                            else:
                                cache_plantxys = []
                                if cache_plant_dection == 0:  # 向上
                                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                                elif cache_plant_dection == 1:  # 向左
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                                elif cache_plant_dection == 2:  # 向下
                                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                                else:  # 向右
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                                for cache_plantxy in cache_plantxys:
                                    if bomxy == cache_plantxy:
                                        bomstate = 1
                        if bomstate == -1:
                            bomstate = 0
                    if bomstate != 3:
                        printx = -16 + (bomx * 78)
                        printy = -16 + (bomy * 78)
                        bom_state = int(bomstate)
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 保存数据
                    if bomstate == 0 or bomstate == 1 or bomstate == 2:
                        boom_data = [bomx, bomy, bomstate]
                        boms_list.append(boom_data)

                        # 收集本次游戏数据
                        gameinfo = {
                            "plants_info": plants_info,  # 飞机数据
                            "boms_list": boms_list,  # 炸弹数据
                        }

                        # 保存数据
                        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                        cursor = conn.cursor()
                        cursor.execute(
                            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                            f'"{channel_id}","小游戏-炸飞机","{time_now}",True,"{gameinfo}")')
                        cursor.close()
                        conn.commit()
                        conn.close()

                    if bomstate == 3:
                        code = 1
                        message = "出错!炸弹必须设置在未炸过的地方"
                    elif bomstate == 0:
                        code = 3
                        message = "引爆成功，该地方为空"
                    elif bomstate == 1:
                        code = 3
                        message = "成功炸伤飞机"
                    elif bomstate == 2:
                        code = 3
                        message = "成功炸沉飞机"

                    if bomstate == 2:
                        num = 0
                        for bom in boms_list:
                            bomstate = bom[2]
                            if bomstate == 2:
                                num += 1
                        if num >= 3:
                            # 绘制飞机的位置
                            num = 0
                            for plant_info in plants_info:
                                if num == 0:
                                    paste_image = plane_image_1
                                elif num == 1:
                                    paste_image = plane_image_2
                                else:
                                    paste_image = plane_image_3
                                num += 1

                                cache_plantx = int(plant_info[0])
                                cache_planty = int(plant_info[1])
                                cache_plant_dection = int(plant_info[2])
                                cache_plantxy = (cache_plantx, cache_planty)

                                cache_plantxys = []
                                if cache_plant_dection == 0:  # 向上
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                                elif cache_plant_dection == 1:  # 向左
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                                elif cache_plant_dection == 2:  # 向下
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                                else:  # 向右
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                                for cache_plantxy in cache_plantxys:
                                    plantx = cache_plantxy[0]
                                    planty = cache_plantxy[1]
                                    printx = -16 + plantx * 78
                                    printy = -16 + planty * 78
                                    image.paste(paste_image, (printx, printy), mask=paste_image)

                            # 将”结束游戏状态“写入到数据库
                            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                                f'"{channel_id}","none","0",False,"none")')
                            cursor.close()
                            conn.commit()
                            conn.close()

                            message = '恭喜炸沉所有飞机，游戏结束。'

                    returnpath = save_image(image)

    elif game_state == "exit":
        # 手动退出game状态
        # 将”结束游戏状态“写入到数据库
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","none","0",False,"none")')
        cursor.close()
        conn.commit()
        conn.close()
    return code, message, returnpath


async def plugin_game_different(command: str, channel_id: str):
    """
    找不同插件内容
    返回：
    当code = 0时，不做任何回复；
    当code = 1时，回复message消息；
    当code = 2时，回复returnpath目录中的图片
    当code = 3时，回复message消息和returnpath目录中的图片
    :param command: 命令
    :param channel_id: 频道号
    :return: code, message, returnpath
    """
    code = 0
    message = ""
    returnpath = ""
    returnpath2 = ""
    time_now = str(int(time.time()))
    trace = []

    # 获取游戏基本数据（卡牌列表）
    filepath = await get_file_path("plugin-different_data.json")
    data = open(filepath, 'r', encoding='utf8')
    different_game_data = json.load(data)

    def region_to_coord(region: str):
        region = region.lower()
        x = None
        y = None
        alphabet = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t"]
        number = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18"]
        num = -1
        for a in alphabet:
            num += 1
            if region.startswith(a):
                region = region.removeprefix(a)
                x = num
                break
        for n in number:
            if region == n:
                y = int(n) - 1
                break
        if x is None or y is None:
            logger.error(f"无法转换位置“{region}”, x:{x}, y:{y}")
            raise f"无法转换位置“{region}”, x:{x}, y:{y}"
        return x, y

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
    logger.debug(f"该群正在进行的游戏{data}")

    game_state = None
    if data is not None:
        # 有game数据
        gameing = data[3]
        if gameing == 1:
            # 有正在进行的game
            gamename = data[1]
            if gamename == "小游戏-找不同":
                # 正在进行的是找不同
                if int(time_now) <= (int(data[2]) + 300):
                    # 正在运行的找不同最后一次运行时间相隔现在5分钟内
                    if command == "找不同":
                        message = "已经在找不同了"
                        code = 1
                    else:
                        game_state = "gameing"
                else:
                    # 正在运行的炸飞机最后一次运行时间相隔现在5分钟后
                    if command == "找不同":
                        game_state = "new"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename}时间超时，请重新开始"
            else:
                # 正在进行其他游戏
                if "-" in gamename:
                    gamename = gamename.split("-")[1]
                code = 1
                message = f"正在进行{gamename}，请先结束{gamename}。\n结束指令“/{gamename} 结束”"
        else:
            # 没有正在进行的game
            if command == "找不同":
                game_state = "new"
            else:
                code = 1
                message = "没有在找不同哦"
    else:
        # data is None
        if command == "找不同":
            game_state = "new"
        else:
            code = 1
            message = "没有在找不同哦。"

    trace.append(f"game_state: {game_state}")
    if game_state == "new":
        # 生成游戏数据
        card_id = random.choice(list(different_game_data['data']))
        card_data = different_game_data['data'][card_id]
        choose_list = []
        num = 15
        while num > 1:
            num -= 1
            if len(choose_list) == len(card_data['different_list']):
                break
            if len(choose_list) >= 4:
                break
            choose_id = random.choice(list(card_data['different_list']))
            if choose_id not in choose_list:
                choose_list.append(choose_id)

        trace.append(f"card_id={card_id}")
        trace.append(f"choose_list={choose_list}")
        # 绘制图片
        path = await get_image_path("different-shade.png")
        shade_image = await load_image(path)

        path = await get_image_path(f"bangdream_card-{card_id}.png")
        image_1 = await load_image(path)
        image_2 = image_1.copy()
        image_1.paste(shade_image, (0, 0), mask=shade_image)

        for choose_id in choose_list:
            path = await get_image_path(f"different-image-{card_id}-{choose_id}.png")
            paste_image = await load_image(path)
            paste_box = (
                card_data['different_list'][choose_id]['coord'][0],
                card_data['different_list'][choose_id]['coord'][1]
            )
            image_2.paste(paste_image, paste_box)

        image_2.paste(shade_image, (0, 0), mask=shade_image)
        returnpath2 = save_image(image_1)   # 将有变化的图和文字一起发出
        returnpath = save_image(image_2)

        gameinfo = {
            "card_id": card_id,
            "image_1": returnpath,
            "image_2": returnpath2,
            "different": choose_list,
            "seek_out": []
        }
        # 保存数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f"'{channel_id}','小游戏-找不同','{time_now}',True,'{json.dumps(gameinfo)}')")
        cursor.close()
        conn.commit()
        conn.close()

        message = '游戏已生成，发送/找不同+坐标进行游戏。' \
                  '\n例：“@kanon/找不同 a1”' \
                  '\n请在5分钟内完成游戏。' \
                  '\n发送“/找不同 结束”可以提前结束游戏'
        code = 4
    elif game_state == "gameing":
        # 读取游戏数据
        gamedata = json.loads(data[4])
        card_id = gamedata["card_id"]
        card_data = different_game_data['data'][card_id]
        image_1_path = (gamedata["image_1"])
        image_2_path = (gamedata["image_2"])
        different_list = gamedata["different"]
        seek_out = gamedata["seek_out"]

        if command == "结束":
            # 绘制不同的位置
            paste_image = await load_image(await get_image_path("different-different.png"))
            image_2 = await load_image(image_2_path)

            for different in different_list:
                if different in seek_out:
                    continue
                location = region_to_coord(different_game_data["data"][card_id]["different_list"][different]["region"])
                x, y = location
                x = 111 - 100 + (x * 222)
                y = 100 - 100 + (y * 200)
                image_2.paste(paste_image, (x, y), paste_image)

            # 保存图片
            returnpath = save_image(image_2)
            message = "游戏已结束"
            code = 3

            # 将”结束游戏状态“写入到数据库
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            cursor.execute(
                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                f'"{channel_id}","none","0",False,"none")')
            cursor.close()
            conn.commit()
            conn.close()
        else:
            if command.startswith("在"):
                command = command.removeprefix('在')
            # 判断是否找到
            find = False
            different = None
            for different in different_list:
                if different in seek_out:
                    continue
                if command == card_data["different_list"][different]["region"] and command not in seek_out:
                    find = True
                    break

            if  command in seek_out:
                code = 1
                message = "这里已经找到啦，找找别的地方吧"
            elif find is False:
                code = 1
                message = "不是这里哦"
            else:
                seek_out.append(command)
                # 绘制图片
                paste_image = await load_image(await get_image_path("different-different.png"))
                image_2 = await load_image(image_2_path)
                location = region_to_coord(different_game_data["data"][card_id]["different_list"][different]["region"])
                x, y = location
                x = 111 - 100 + (x * 222)
                y = 100 - 100 + (y * 200)
                image_2.paste(paste_image, (x, y), paste_image)

                if len(seek_out) == len(different_list):
                    code = 3
                    message = "恭喜找到所有不同"
                    returnpath = save_image(image_2)

                    # 将”结束游戏状态“写入到数据库
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                        f'"{channel_id}","none","0",False,"none")')
                    cursor.close()
                    conn.commit()
                    conn.close()
                else:
                    code = 3
                    message = f"找到了{len(seek_out)}/{len(different_list)}处不同"
                    returnpath = save_image(image_2)
                    gameinfo = {
                        "card_id": card_id,
                        "image_1": image_1_path,
                        "image_2": returnpath,
                        "different": different_list,
                        "seek_out": seek_out
                    }

                    # 保存数据
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                        f"'{channel_id}','小游戏-找不同','{time_now}',True,'{json.dumps(gameinfo)}')")
                    cursor.close()
                    conn.commit()
                    conn.close()

    elif game_state == "exit":
        # 手动退出game状态
        # 将”结束游戏状态“写入到数据库
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","none","0",False,"none")')
        cursor.close()
        conn.commit()
        conn.close()
    return {
        "code": code,
        "message": message,
        "returnpath": returnpath,
        "returnpath2": returnpath2,
        "trace": trace
    }


async def plugin_function_jrlp(
        user_id: str,
        channel_id: str,
        channel_member_datas: dict,
        time_now: int,
        cachepath: str,
        platform: str
):
    date: str = time.strftime("%Y-%m-%d", time.localtime(time_now))
    return_data = {
        "code": 0,
        "message": None,
        "returnpath": None,
        "trace": [],
    }

    conn = sqlite3.connect(f"{cachepath}jrlp.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        # 数据库列表转为序列
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "jrlp" not in tables:
            cursor.execute('create table jrlp (userid varchar(10) primary key, data varchar(10), time varchar(10))')
        cursor.execute(f'select * from jrlp where userid = "{channel_id}_{user_id}" AND time = "{date}"')
        data = cursor.fetchone()
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    if len(list(channel_member_datas)) == 0:
        return_data["code"] = 0
        return_data["message"] = "获取群列表出错"
        return return_data

    # 判断状态
    lp_state = "None"
    if data is None:
        lp_state = "new"
    else:
        lp_state = "load"

    # 执行
    if lp_state == "new":
        lp_id = random.choice(list(channel_member_datas))
        lp_unity_id = get_unity_user_id(platform, lp_id)
        lp_unity_data = get_unity_user_data(lp_unity_id)

        if len(list(lp_unity_data)) == 0:
            lp_data = channel_member_datas[lp_id]
        else:
            lp_data = lp_unity_data

        # 获取lp名称
        if "nick_name" in list(lp_data) and lp_data["nick_name"] is not None:
            lp_name = lp_data["nick_name"]
        elif "name" in list(lp_data) and lp_data["name"] is not None:
            lp_name = lp_data["name"]
        else:
            lp_name = "name"

        # 获取lp图像
        if "face_image" in list(lp_data) and lp_data["face_image"] is not None:
            lp_image = lp_data["face_image"]
        elif "avatar" in list(lp_data) and lp_data["avatar"] is not None:
            image = await connect_api("image", lp_data["avatar"])
            lp_image = save_image(image)
        else:
            lp_image = None

        # 存储lp数据
        data = {
            "lp_name": lp_name,
            "lp_image": lp_image
        }

        # 写入水母箱数据
        conn = sqlite3.connect(f"{cachepath}jrlp.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"replace into 'jrlp' ('userid','data','time') "
                f"values('{channel_id}_{user_id}','{json.dumps(data)}','{date}')")
            conn.commit()
        except:
            logger.error("jrlp保存用户数据出错")
        cursor.close()
        conn.close()

        # 总结消息
        return_data["code"] = 3 if lp_image is not None else 1
        return_data["message"] = f"今日老婆是：{lp_name}"
        return_data["returnpath"] = lp_image

    elif lp_state == "load":
        lp_data = json.loads(data[1])
        lp_name = lp_data["lp_name"]
        lp_image = lp_data["lp_image"]

        return_data["code"] = 3 if lp_image is not None else 1
        return_data["message"] = f"今日老婆是：{lp_name}"
        return_data["returnpath"] = lp_image

    return return_data
