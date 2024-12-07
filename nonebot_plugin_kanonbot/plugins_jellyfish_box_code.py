# coding=utf-8
import json
import math
import random
import time
from nonebot import logger
import os
import sqlite3
from .config import _jellyfish_box_datas, jellyfish_box_draw_config, _jellyfish_box_weather_name_data
from .tools import (kn_config, connect_api, save_image, image_resize2, draw_text, get_file_path, \
                    circle_corner, get_command, get_unity_user_data, _config, imgpath_to_url, del_files2, \
                    statistics_list, get_image_path, load_image, list_in_list,
                    images_to_gif, read_db, content_compliance, kn_cache, new_image, get_weather_image_list)
from PIL import Image, ImageDraw, ImageFont
import numpy
from datetime import datetime
from zhdate import ZhDate

basepath = _config["basepath"]
adminqq = _config["superusers"]


async def plugin_jellyfish_box(
        user_id: str,
        user_name: str,
        channel_id: str,
        msg: str,
        time_now: int,
        platform: str = "None",
        reply_data: dict | None = None,
        channel_member_datas=None,
        at_datas=None,
        use_markdown: bool=False
):
    """
    群聊功能-水母箱
    :return:
    """
    if channel_member_datas is None:
        channel_member_datas = {}
    """
    命令列表：
    水母箱：总命令，输入可查看水母箱和相关指令列表
    查看水母箱：获取水母箱的图片
    帮助: 指令说明
    抓水母: 抓水母，并放入箱中
    投喂: 往杠中添加饲料
    换水: 恢复水质状态（未实装）
    丢弃: 丢弃指定水母
    装饰: 开启装饰模式指令（未实装）
    拜访水母箱: 拜访其他人的水母箱（未实装）
    结束: 关闭水母箱对话进程（未实装）
    """
    # 指令解析
    commands = get_command(msg)
    command: str = commands[0]
    if len(commands) > 1:
        command2 = commands[1]
    else:
        command2 = None

    # 添加必要参数
    code = 0
    message = None
    returnpath = None
    markdown = None
    keyboard = None
    reply_trace = {
        "plugin_name": "群聊功能-水母箱",
        "data": {}
    }
    trace = []  # 用于日志记录插件运行内容
    jellyfish_group_list = ["perfect", "great", "good", "normal", "special", "ocean"]
    jellyfish_box_datas = await _jellyfish_box_datas()  # 插件数据
    event_datas = jellyfish_box_datas["event_datas"]  # 所有事件
    jellyfish_datas = jellyfish_box_datas["jellyfish_datas"]  # 所有水母
    feed_datas = jellyfish_box_datas["food_datas"]  # 所有事件
    ornament_datas = jellyfish_box_datas["ornament_datas"]  # 所有装饰物
    medal_datas = jellyfish_box_datas["medal_datas"]  # 所有勋章
    user_data = get_unity_user_data(user_id)

    date_y: int = int(time.strftime("%Y", time.localtime(time_now)))
    date_m: int = int(time.strftime("%m", time.localtime(time_now)))
    date_d: int = int(time.strftime("%d", time.localtime(time_now)))
    time_h: int = int(time.strftime("%H", time.localtime(time_now)))
    # logger.debug(f"date:{date_y}-{date_m}-{date_d}")
    date_zh = ZhDate.from_datetime(datetime(date_y, date_m, date_d))
    lunar_date_y: int = date_zh.lunar_year
    lunar_date_m: int = date_zh.lunar_month
    lunar_date_d: int = date_zh.lunar_day
    # logger.debug(f"date:{lunar_date_y}-{lunar_date_m}-{lunar_date_d}")

    # 加载缓存
    global kn_cache
    if "jellyfish_box_image" not in list(kn_cache):
        kn_cache['jellyfish_box_image'] = {}

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
    # 读取用户水母箱
    data = read_db(
        db_path="{basepath}db/" + f"plugin_data.db",
        sql_text=f'SELECT * FROM "jellyfish_box" WHERE user_id = "{user_id}"',
        table_name="jellyfish_box",
        select_all=False
    )
    if data is None:
        box_data = {
            "info": {
                "owner": user_id,
                "owner_name": user_name
            },
            "sign_in_time": int(time_now / 3600 - 2) * 3600,  # 上次抓水母时间小时计算
            "refresh_time": int(time_now / 3600) * 3600,  # 更新时间小时计算
            "jellyfish": {"j1": {"number": 3}},
            "ornament": {},
            "salinity": 30,  # 千分盐度
            "temperature": 25,  # 温度
            "draw_style": "normal"  # 绘制风格
        }
    elif data == "error":
        raise "获取水母箱数据错误"
    else:
        box_data = json.loads(data[1])

    # 水母箱数据更新
    if "event_list" not in box_data.keys():
        box_data["event_list"] = []
    if "feed" not in box_data.keys():
        if "food" in box_data.keys():
            box_data["feed"] = box_data["food"]
            box_data.pop("food")
        else:
            box_data["feed"] = {}
    if "draw_event_box" not in box_data.keys():
        box_data["draw_event_box"] = True  # 绘制节日效果
    if "weather" not in box_data.keys():
        box_data["weather"] = None  # 实时天气

    # 绘制样式
    draw_dark_model = False if 5 <= time_h <= 19 else True
    if "draw_model" in list(box_data):
        draw_model = box_data["draw_model"]
    else:
        draw_model = "normal"

    draw_config = jellyfish_box_draw_config(
        draw_model, draw_dark_model, date_m=date_m, date_d=date_d, draw_event_box=box_data['draw_event_box'])

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

    if refresh:
        # 更新数据
        logger.debug("正在刷新水母箱")
        trace.append(f"将刷新{refresh_period}次")
        if len(box_data["jellyfish"]) == 0:
            # 无水母，仅更新时间
            box_data["refresh_time"] = int(time_now / 3600) * 3600
        elif command not in ["水母箱", "抓水母", "投喂"]:
            pass  # 运行命令中，跳过更新
        else:
            # 更新时间并更新事件
            box_data["refresh_time"] = int(time_now / 3600) * 3600

            # 统计现有水母数量
            jellyfish_number = 0
            for jellyfish_id in box_data["jellyfish"].keys():
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
                trace.append(f"水母繁殖，trace， ”{jellyfish_id}“增加{new[jellyfish_id]}只")

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

                if event_id not in ["e1", "e2", "e3", "e4", "e5", "e7", "e8", "e9", "e10", "e11", "e12"]:
                    continue
                # 准备事件
                event_name: str = event_datas[event_id]["name"]
                event_message: str = event_datas[event_id]["message"]
                # event_icon = await get_image_path(f"jellyfish_box-{event_id}")
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
                                box_data["jellyfish"][jellyfish_id]["number"] > 80):
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
                        choose_list.append(choose_jellyfish)
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
                        if jellyfish_datas[jellyfish_id]["group"] not in ["normal", "good"]:
                            num = 0
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
                elif event_id == "e10":
                    # 判断事件是否成立
                    # if len(jellyfish_list) < 1:
                    #     continue  # 少于1条，跳过事件
                    # 计算事件发生的内容
                    jellyfish_id = "j11"
                    number = 6  # 增加的水母数量
                    event_message = event_message.replace("{num}", str(number))

                    # 进行数据修改
                    if jellyfish_id in box_data["jellyfish"].keys():
                        box_data["jellyfish"][jellyfish_id]["number"] += number
                    else:
                        box_data["jellyfish"][jellyfish_id] = {"number": number}

                    # 总结事件
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e11":
                    # 计算事件发生的内容
                    jellyfish_id = "j52"
                    number = 1  # 增加的水母数量
                    event_message = event_message.replace("{num}", str(number))

                    # 进行数据修改
                    if jellyfish_id in box_data["jellyfish"].keys():
                        box_data["jellyfish"][jellyfish_id]["number"] += number
                    else:
                        box_data["jellyfish"][jellyfish_id] = {"number": number}

                    # 总结事件
                    news.append({"icon": event_icon, "title": event_name, "message": event_message})
                elif event_id == "e12":
                    # 计算事件发生的内容
                    jellyfish_id = "j49"
                    number = 3  # 增加的水母数量
                    event_message = event_message.replace("{num}", str(number))

                    # 进行数据修改
                    if jellyfish_id in box_data["jellyfish"].keys():
                        box_data["jellyfish"][jellyfish_id]["number"] += number
                    else:
                        box_data["jellyfish"][jellyfish_id] = {"number": number}

                    # 总结事件
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
                f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
            conn.commit()
        except:
            logger.error("水母箱保存用户数据出错")
        cursor.close()
        conn.close()

    # 绘制
    draw_foods_list = ["抓水母", "投喂"]

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
        num_list = [439, 389, 339, 290, 263, 237, 211, 184, 158, 132, 105, 79, 53]
        size_list = [100, 104, 109, 117, 124, 134, 144, 154, 165, 180, 197, 218, 244]

        j_size = 100
        num = len(num_list)
        while num > 0:
            num -= 1
            if number < num_list[num]:
                j_size = size_list[num]
                break

        j_image = new_image((x, y), (0, 0, 0, 0))

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
            file_path = await get_image_path(f"jellyfish_box-{jellyfish_id}.png")
            jellyfish_image = await load_image(file_path)
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
                    if choose_foreground is not None:
                        file_path = await get_image_path(f"jellyfish_box-{choose_foreground}.png")
                        foreground_image = await load_image(file_path)
                        foreground_image = foreground_image.resize((j_size, j_size))
                        paste_image.paste(foreground_image, (0, 0), mask=foreground_image)

                paste_image = paste_image.rotate(direction)
                j_image.alpha_composite(paste_image, (paste_x, paste_y))
        j_image = j_image.resize(size)
        return j_image

    async def draw_jellyfish_box(draw_box=True, draw_title=None, ) -> str:
        if draw_model in ["freehand", "freehand_dark"]:
            return_data = await draw_jellyfish_box_freehand(draw_box, draw_title)
        elif draw_model == "text":
            return_data = await draw_jellyfish_box_text(draw_box, draw_title)
        elif draw_model == "starlight":
            return_data = await draw_jellyfish_box_starlight(draw_box, draw_title)
        else:
            # draw_model == "normal":
            return_data = await draw_jellyfish_box_normal(draw_box, draw_title)
        if type(return_data) is Image.Image:
            return_data = save_image(return_data)
        return return_data

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

    async def draw_jellyfish_box_normal(draw_box=True, draw_title=None) -> Image.Image:
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
        bg_color = draw_config["color"]["bg"]
        image = new_image((x, y), draw_config["color"]["bg"])
        
        if draw_config["jellyfish"]["background"] is not None:
            paste_image = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['background']}.png")
            paste_image = await load_image(paste_image)
            image.alpha_composite(paste_image, (0, 0))
        draw = ImageDraw.Draw(image)

        # 绘制内容
        # 添加背景大字
        draw_x = 0
        draw_y = 0
        paste_image = await draw_text(
            texts=draw_config["text"]["背景大字"],
            text_color=draw_config["color"]["背景大字"],
            fontfile=font_shsk_H_path,
            size=300,
        )
        paste_image = image_resize2(paste_image, (745, 230), overturn=False)
        image.alpha_composite(paste_image, (draw_x + 200, draw_y + 74))

        # 添加时间
        text = f"{datetime.fromtimestamp(time_now)}"[0:10]
        font = ImageFont.truetype(font=font_shsk_M_path, size=40)
        draw.text(xy=(draw_x + 64, draw_y + 68), text=text, fill=draw_config["color"]["date"], font=font)

        # 添加标题
        if draw_title is None:
            text = user_name
        else:
            text = draw_title
        paste_image = await draw_text(
            texts=text,
            size=70,
            textlen=20,
            fontfile=font_shsk_M_path,
            text_color=draw_config["color"]["name"]
        )
        image.paste(paste_image, (draw_x + 54, draw_y + 122), paste_image)

        # 绘制头像
        if "face_image" in list(user_data) and draw_title is None:
            user_avatar = user_data["face_image"]
            try:
                if user_avatar in [None, "None", "none"]:
                    user_image = await draw_text("图片", 50, 10)
                else:
                    user_image = await load_image(user_avatar, (50, 10))
            except Exception as e:
                user_image = await draw_text("头像", 50, 10)
                logger.error(f"获取图片出错:{e}")
            user_image = user_image.resize((158, 158))
            user_image = circle_corner(user_image, 79)
            paste_image = new_image((160, 160), (255, 255, 255))
            paste_image = circle_corner(paste_image, 80)
            image.paste(paste_image, (draw_x + 744, draw_y + 62), paste_image)
            image.paste(user_image, (draw_x + 745, draw_y + 63), user_image)

        draw_x += 43
        draw_y += 258
        # 添加水母箱
        if draw_box is True:

            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 754  # 卡片宽度
                y = 563  # 卡片长度
            else:
                x = 914  # 卡片宽度
                y = 563  # 卡片长度

            paste_image = new_image((x, y), draw_config["color"]["box_outline"])
            paste_image = circle_corner(paste_image, 30)  # 圆角
            image.paste(paste_image, (draw_x, draw_y), paste_image)
            paste_image = new_image((x - 6, y - 6), draw_config["color"]["box_bg"])
            paste_image = circle_corner(paste_image, 28)  # 圆角
            image.paste(paste_image, (draw_x + 3, draw_y + 3), paste_image)

            if draw_config['jellyfish']['box_background'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_background']}.png")
                paste_image = await load_image(path)
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            paste_image = await draw_jellyfish((x - 6, y - 6))  # 水母们
            image.paste(paste_image, (draw_x + 3, draw_y + 3), paste_image)

            if draw_config['jellyfish']['box_foreground'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_foreground']}.png")
                paste_image = await load_image(path)
                if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                    image.paste(paste_image, (0 - 160, draw_y - 45), paste_image)
                else:
                    image.paste(paste_image, (0, draw_y - 45), paste_image)

            if box_data["weather"] is not None:
                weather_image_list = await get_weather_image_list(box_data["weather"], time_h, draw_dark_model)
                logger.debug(f"weather_image_list:{weather_image_list}")
                for weather_image in weather_image_list:
                    paste_image = await load_image(weather_image)
                    image.paste(paste_image, (0, draw_y - 60), paste_image)

            draw_x += 760
            draw_y += 0
            # 添加饲料数量
            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 140  # 卡片宽度
                y = 563  # 卡片长度

                paste_image = new_image((x, y), draw_config["color"]["card"])
                paste_image = circle_corner(paste_image, 30)  # 圆角
                image.paste(paste_image, (draw_x, draw_y), paste_image)

                # 饲料排序
                num_list = [box_data["feed"][f]["number"] for f in box_data["feed"].keys()]

                food_data_list = {}
                while len(num_list) > 0:
                    chose_num = max(num_list)
                    num_list.remove(chose_num)
                    choose_id = ""
                    for choose_id in box_data["feed"].keys():
                        if box_data["feed"][choose_id][
                            "number"] == chose_num and choose_id not in food_data_list.keys():
                            break
                    food_data_list[choose_id] = {"number": chose_num}

                draw_food_num = -1
                for food_id in food_data_list.keys():
                    draw_food_num += 1
                    # 加载饲料图
                    paste_image_path = await get_image_path(f"jellyfish_box-{food_id}.png")
                    paste_image = Image.open(paste_image_path)
                    paste_image = paste_image.resize((140, 140))

                    if draw_food_num <= 3:
                        # 添加饲料名
                        paste_font = await draw_text(
                            texts=feed_datas[food_id]["name"],
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (int((140 - paste_font.size[0]) / 2), 10), paste_font)

                        # 添加饲料尺寸
                        paste_font = await draw_text(
                            texts=f"({1 / feed_datas[food_id]['weight']})",
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (15, 97), paste_font)

                        # 添加饲料数量
                        paste_font = await draw_text(
                            texts=f"x{box_data['feed'][food_id]['number']}",
                            size=20,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_title"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (85, 95), paste_font)

                        image.paste(paste_image, (draw_x, draw_y + (draw_food_num * 140)), paste_image)
                    else:
                        paste_image = paste_image.resize((30, 30))
                        image.paste(paste_image, (
                            draw_x + 8 + (draw_food_num - 4) * 30,
                            draw_y + (4 * 140) - 20
                        ), paste_image)

            draw_x -= 760
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
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
                paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)
                paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.paste(paste_image, (11 + 7, 69 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
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
                paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.alpha_composite(paste_image, (11, 0 + 20 + (card_num * 261)))
                paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.alpha_composite(paste_image, (11 + 7, 0 + 20 + (card_num * 261) + 7))
                # file_path = await get_file_path(f"plugin-jellyfish_box-{j_id}.png")
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.alpha_composite(paste_image, (11, 0 + 20 + (card_num * 261)))

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -69 - 27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, -69 + 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
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
                paste_card_image.alpha_composite(paste_text, (278, -69 + 200 + (card_num * 261)))

            paste_card_image = circle_corner(paste_card_image, 30)
            image.alpha_composite(paste_card_image, (draw_x, draw_y))

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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)
            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
                    paste_card_image.alpha_composite(card_background, (0, card_y - card_background.size[1]))

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
            image.alpha_composite(paste_card_image, (43, draw_y))
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
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

        # 添加水印
        x, y = image.size
        paste_image = new_image((100, 100), (0, 0, 0, 0))
        paste_draw = ImageDraw.Draw(paste_image)
        font = ImageFont.truetype(font_shsk_M_path, size=10)
        paste_draw.text((0, 0), user_id, fill=(150, 150, 150, 20), font=font)
        image.alpha_composite(paste_image, (x - 70, y - 30))
        return image

    async def draw_jellyfish_box_freehand(draw_box=True, draw_title=None) -> Image.Image:
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
        async def load_freehand_card(size: tuple[int, int]):
            w, h = size
            if w / h > 2.4:
                image_name = "jellyfish_box-freehand_card_background_w2.png"
            elif w / h > 1:
                image_name = "jellyfish_box-freehand_card_background_w1.png"
            elif w / h > 0.41:
                image_name = "jellyfish_box-freehand_card_background_h1.png"
            else:
                image_name = "jellyfish_box-freehand_card_background_h2.png"

            file_path = await get_image_path(image_name)
            Image = await load_image(file_path)
            Image = Image.resize(size)
            return Image
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
        image = new_image((x, y), draw_config["color"]["bg"])
        if draw_config["jellyfish"]["background"] is not None:
            paste_image = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['background']}.png")
            paste_image = await load_image(paste_image)
            image.alpha_composite(paste_image, (0, 0))
        draw = ImageDraw.Draw(image)
        # 添加底色
        file_path = await get_image_path(f"jellyfish_box-freehand_background.png")
        paste_image = await load_image(file_path)
        image.alpha_composite(paste_image, (0, 0))
        if y > 2000:
            image.alpha_composite(paste_image, (0, 2000))

        # 绘制内容
        # 添加背景大字
        draw_x = 0
        draw_y = 0

        paste_image = await draw_text(
            texts=draw_config["text"]["背景大字"],
            text_color=draw_config["color"]["背景大字"],
            fontfile=muyao_softbrush,
            size=300,
        )
        paste_image = image_resize2(paste_image, (745, 230), overturn=False)
        image.alpha_composite(paste_image, (draw_x + 200, draw_y + 74))

        # 添加时间
        text = f"{datetime.fromtimestamp(time_now)}"[0:10]
        font = ImageFont.truetype(font=muyao_softbrush, size=40)
        draw.text(xy=(draw_x + 64, draw_y + 68), text=text, fill=draw_config["color"]["date"], font=font)

        # 添加标题
        if draw_title is None:
            text = user_name
        else:
            text = draw_title
        paste_image = await draw_text(
            texts=text,
            size=70,
            textlen=20,
            fontfile=muyao_softbrush,
            text_color=draw_config["color"]["name"]
        )
        image.alpha_composite(paste_image, (draw_x + 54, draw_y + 122))

        # 绘制头像
        if "face_image" in list(user_data) and draw_title is None:
            user_avatar = user_data["face_image"]
            try:
                if user_avatar in [None, "None", "none"]:
                    user_image = await draw_text("图片", 50, 10)
                elif user_avatar.startswith("http"):
                    user_image = await connect_api("image", user_avatar)
                else:
                    user_image = await load_image(user_avatar)
            except Exception as e:
                user_image = await draw_text("头像", 50, 10)
                logger.error(f"获取图片出错:{e}")
            user_image = user_image.resize((158, 158))
            user_image = circle_corner(user_image, 79)
            paste_image = new_image((160, 160), (255, 255, 255))
            paste_image = circle_corner(paste_image, 80)
            image.alpha_composite(paste_image, (draw_x + 744, draw_y + 62))
            image.alpha_composite(user_image, (draw_x + 745, draw_y + 63))

        draw_x += 43
        draw_y += 258
        # 添加水母箱
        if draw_box is True:
            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 754  # 卡片宽度
                y = 563  # 卡片长度
            else:
                x = 914  # 卡片宽度
                y = 563  # 卡片长度

            file_path = await get_image_path(f"jellyfish_box-freehand_box_background.png")
            paste_alpha = await load_image(file_path)
            paste_alpha = paste_alpha.resize((x, y))
            paste_image = new_image((x, y), draw_config["color"]["box_bg"])
            image.paste(paste_image, (draw_x, draw_y), paste_alpha)

            if draw_config['jellyfish']['box_background'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_background']}.png")
                paste_image = await load_image(path)
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            paste_image = await draw_jellyfish((x - 6 - 40, y - 6 - 40))  # 水母们
            image.paste(paste_image, (draw_x + 3 + 20, draw_y + 3 + 20), paste_image)

            if draw_config['jellyfish']['box_foreground'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_foreground']}.png")
                paste_image = await load_image(path)
                if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                    image.paste(paste_image, (0 - 160, draw_y - 45), paste_image)
                else:
                    image.paste(paste_image, (0, draw_y - 45), paste_image)

            if box_data["weather"] is not None:
                weather_image_list = await get_weather_image_list(box_data["weather"], time_h, draw_dark_model)
                logger.debug(f"weather_image_list:{weather_image_list}")
                for weather_image in weather_image_list:
                    paste_image = await load_image(weather_image)
                    image.paste(paste_image, (0, draw_y - 60), paste_image)

            draw_x += 760
            draw_y += 0
            # 添加饲料数量
            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 140  # 卡片宽度
                y = 563  # 卡片长度

                paste_alpha = await load_freehand_card((x, y))
                paste_image = new_image((x, y), draw_config["color"]["card"])
                image.paste(paste_image, (draw_x, draw_y), paste_alpha)

                # 饲料排序
                num_list = [box_data["feed"][f]["number"] for f in box_data["feed"].keys()]

                food_data_list = {}
                while len(num_list) > 0:
                    chose_num = max(num_list)
                    num_list.remove(chose_num)
                    choose_id = ""
                    for choose_id in box_data["feed"].keys():
                        if box_data["feed"][choose_id][
                            "number"] == chose_num and choose_id not in food_data_list.keys():
                            break
                    food_data_list[choose_id] = {"number": chose_num}

                draw_food_num = -1
                for food_id in food_data_list.keys():
                    draw_food_num += 1
                    paste_image_path = await get_image_path(f"jellyfish_box-{food_id}.png")
                    paste_image = Image.open(paste_image_path)
                    paste_image = paste_image.resize((140, 140))

                    if draw_food_num <= 3:
                        paste_font = await draw_text(
                            texts=feed_datas[food_id]["name"],
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (int((140 - paste_font.size[0]) / 2), 10), paste_font)

                        # 添加饲料尺寸
                        paste_font = await draw_text(
                            texts=f"({1 / feed_datas[food_id]['weight']})",
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (15, 97), paste_font)

                        paste_font = await draw_text(
                            texts=f"x{box_data['feed'][food_id]['number']}",
                            size=20,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_title"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (85, 95), paste_font)

                        image.paste(paste_image, (draw_x, draw_y + (draw_food_num * 140)), paste_image)
                    else:
                        paste_image = paste_image.resize((30, 30))
                        image.paste(paste_image, (
                            draw_x + 8 + (draw_food_num - 4) * 30,
                            draw_y + (4 * 140) - 20
                        ), paste_image)

            draw_x -= 760
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
            paste_card_alpha = await load_freehand_card((card_x, card_y))
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = new_image((card_x, card_y), (0, 0, 0, 0))

            # paste_card_image = new_image((card_x, card_y), color)
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
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
                # paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                # paste_image = circle_corner(paste_image, 24)
                # paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)
                # paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                # paste_image = circle_corner(paste_image, 18)
                # paste_card_image.paste(paste_image, (11 + 7, 69 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
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
            paste_card_alpha = await load_freehand_card((card_x, card_y))
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = new_image((card_x, card_y), (0, 0, 0, 0))
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
                # paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                # paste_image = circle_corner(paste_image, 24)
                # paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)
                # paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                # paste_image = circle_corner(paste_image, 18)
                # paste_card_image.paste(paste_image, (11 + 7, 0 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.alpha_composite(paste_image, (11, 0 + 20 + (card_num * 261)))

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -69 - 27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_shsk_M_path, size=50)
                draw.text(xy=(278, -69 + 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
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
            image.alpha_composite(paste_card_image, (draw_x, draw_y))

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

            paste_card_alpha = await load_freehand_card((card_x, card_y))
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = new_image((card_x, card_y), (0, 0, 0, 0))
            draw = ImageDraw.Draw(paste_card_image)
            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
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

            paste_card_alpha = await load_freehand_card((card_x, card_y))
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            image.paste(paste_card_image, (draw_x, draw_y), paste_card_alpha)

            paste_card_image = new_image((card_x, card_y), (0, 0, 0, 0))
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
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

        # 添加水印
        x, y = image.size
        paste_image = new_image((100, 100), (0, 0, 0, 0))
        paste_draw = ImageDraw.Draw(paste_image)
        font = ImageFont.truetype(font_shsk_M_path, size=10)
        paste_draw.text((0, 0), user_id, fill=(150, 150, 150, 20), font=font)
        image.paste(paste_image, (x - 70, y - 30), mask=paste_image)
        return image

    async def draw_jellyfish_box_starlight(draw_box=True, draw_title=None) -> Image.Image:
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
        font_path = await get_file_path("caerw01.ttf")
        font_shsk_M_path = await get_file_path("SourceHanSansK-Medium.ttf")

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
        image = new_image((x, y), draw_config["color"]["bg"])
        draw = ImageDraw.Draw(image)
        # 添加底色
        if draw_config["jellyfish"]["background"] is not None:
            paste_image = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['background']}.png")
            paste_image = await load_image(paste_image)
            image.alpha_composite(paste_image, (0, 0))
        # 绘制内容
        # 添加背景大字
        draw_x = 0
        draw_y = 0

        paste_image = await draw_text(
            texts=draw_config["text"]["背景大字"],
            text_color=draw_config["color"]["背景大字"],
            fontfile=font_path,
            size=300,
        )
        paste_image = image_resize2(paste_image, (745, 230), overturn=False)
        image.paste(paste_image, (draw_x + 200, draw_y + 74), paste_image)

        # 添加时间
        text = f"{datetime.fromtimestamp(time_now)}"[0:10]
        font = ImageFont.truetype(font=font_path, size=40)
        draw.text(xy=(draw_x + 64, draw_y + 68), text=text, fill=draw_config["color"]["date"], font=font)

        # 添加标题
        if draw_title is None:
            text = user_name
        else:
            text = draw_title
        paste_image = await draw_text(
            texts=text,
            size=70,
            textlen=20,
            fontfile=font_path,
            text_color=draw_config["color"]["name"]
        )
        image.paste(paste_image, (draw_x + 54, draw_y + 122), paste_image)

        # 绘制头像
        if "face_image" in list(user_data) and draw_title is None:
            user_avatar = user_data["face_image"]
            try:
                if user_avatar in [None, "None", "none"]:
                    user_image = await draw_text("图片", 50, 10)
                elif user_avatar.startswith("http"):
                    user_image = await connect_api("image", user_avatar)
                else:
                    user_image = await load_image(user_avatar)
            except Exception as e:
                user_image = await draw_text("头像", 50, 10)
                logger.error(f"获取图片出错:{e}")
            user_image = user_image.resize((158, 158))
            user_image = circle_corner(user_image, 79)
            paste_image = new_image((160, 160), (255, 255, 255))
            paste_image = circle_corner(paste_image, 80)
            image.paste(paste_image, (draw_x + 744, draw_y + 62), paste_image)
            image.paste(user_image, (draw_x + 745, draw_y + 63), user_image)

        draw_x += 43
        draw_y += 258
        # 添加水母箱
        if draw_box is True:

            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 754  # 卡片宽度
                y = 563  # 卡片长度
            else:
                x = 914  # 卡片宽度
                y = 563  # 卡片长度

            if draw_config['jellyfish']['box_background'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_background']}.png")
                paste_image = await load_image(path)
                image.paste(paste_image, (0, draw_y - 45), paste_image)

            paste_image = await draw_jellyfish((x - 6, y - 6))  # 水母们
            image.paste(paste_image, (draw_x + 3, draw_y + 3), paste_image)

            if draw_config['jellyfish']['box_foreground'] is not None:
                path = await get_image_path(f"jellyfish_box-{draw_config['jellyfish']['box_foreground']}.png")
                paste_image = await load_image(path)
                if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                    image.paste(paste_image, (0 - 160, draw_y - 45), paste_image)
                else:
                    image.paste(paste_image, (0, draw_y - 45), paste_image)

            if box_data["weather"] is not None:
                weather_image_list = await get_weather_image_list(box_data["weather"], time_h, draw_dark_model)
                logger.debug(f"weather_image_list:{weather_image_list}")
                for weather_image in weather_image_list:
                    try:
                        paste_image = await load_image(weather_image)
                        image.paste(paste_image, (0, draw_y - 60), paste_image)
                    except Exception as e:
                        logger.error(e)
                        logger.error(weather_image)
                        logger.error("粘贴天气图片失败")

            draw_x += 760
            draw_y += 0
            # 添加饲料数量
            if len(box_data["feed"].keys()) > 0 and command in draw_foods_list:
                x = 140  # 卡片宽度
                y = 563  # 卡片长度

                paste_image = new_image((x, y), draw_config["color"]["card"])
                paste_image = circle_corner(paste_image, 30)  # 圆角
                image.paste(paste_image, (draw_x, draw_y), paste_image)

                # 饲料排序
                num_list = [box_data["feed"][f]["number"] for f in box_data["feed"].keys()]

                food_data_list = {}
                while len(num_list) > 0:
                    chose_num = max(num_list)
                    num_list.remove(chose_num)
                    choose_id = ""
                    for choose_id in box_data["feed"].keys():
                        if box_data["feed"][choose_id][
                            "number"] == chose_num and choose_id not in food_data_list.keys():
                            break
                    food_data_list[choose_id] = {"number": chose_num}

                draw_food_num = -1
                for food_id in food_data_list.keys():
                    draw_food_num += 1
                    paste_image_path = await get_image_path(f"jellyfish_box-{food_id}.png")
                    paste_image = Image.open(paste_image_path)
                    paste_image = paste_image.resize((140, 140))

                    if draw_food_num <= 3:
                        paste_font = await draw_text(
                            texts=feed_datas[food_id]["name"],
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (int((140 - paste_font.size[0]) / 2), 10), paste_font)

                        # 添加饲料尺寸
                        paste_font = await draw_text(
                            texts=f"({1 / feed_datas[food_id]['weight']})",
                            size=16,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_message"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (15, 97), paste_font)

                        paste_font = await draw_text(
                            texts=f"x{box_data['feed'][food_id]['number']}",
                            size=20,
                            textlen=99,
                            fontfile=font_shsk_M_path,
                            text_color=draw_config["color"]["event_title"],
                            calculate=False
                        )
                        paste_image.paste(paste_font, (85, 95), paste_font)

                        image.paste(paste_image, (draw_x, draw_y + (draw_food_num * 140)), paste_image)
                    else:
                        paste_image = paste_image.resize((30, 30))
                        image.paste(paste_image, (
                            draw_x + 8 + (draw_food_num - 4) * 30,
                            draw_y + (4 * 140) - 20
                        ), paste_image)

            draw_x -= 760
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
                    paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            font = ImageFont.truetype(font=font_path, size=50)
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
                paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)
                paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.paste(paste_image, (11 + 7, 69 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 69 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_path, size=50)
                draw.text(xy=(278, 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
                    font = ImageFont.truetype(font=font_path, size=40)
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
                font = ImageFont.truetype(font=font_path, size=40)
                draw.text(
                    xy=(278, 152 + (card_num * 261)), text=f"x{j_number}",
                    fill=draw_config["color"]["event_message"], font=font)

                # 添加消息
                font = ImageFont.truetype(font=font_path, size=40)
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
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
                paste_image = new_image((248, 248), draw_config["color"]["icon_outline"])
                paste_image = circle_corner(paste_image, 24)
                paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)
                paste_image = new_image((234, 234), draw_config["color"]["icon_bg"])
                paste_image = circle_corner(paste_image, 18)
                paste_card_image.paste(paste_image, (11 + 7, 0 + 20 + (card_num * 261) + 7), paste_image)
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((248, 248))
                paste_card_image.paste(paste_image, (11, 0 + 20 + (card_num * 261)), paste_image)

                # 添加水母背景
                file_path = await get_image_path(f"jellyfish_box-{j_id}.png")
                paste_image = await load_image(file_path)
                paste_image = paste_image.resize((575, 575))
                paste_image = paste_image.rotate(30)
                if type(draw_config["color"]["card"]) is str:
                    color = (
                        int(draw_config["color"]["card"][1:3], 16),
                        int(draw_config["color"]["card"][3:5], 16),
                        int(draw_config["color"]["card"][5:7], 16),
                        102,
                    )
                else:
                    color = draw_config["color"]["card"]
                    color = (color[0], color[1], color[2], 102)
                mask_image = new_image((575, 575), color)
                mask_image.paste(paste_image, (0, 0), mask_image)
                paste_card_image.paste(mask_image, (542, -69 - 27 + (card_num * 261)), paste_image)

                # 添加水母名字
                font = ImageFont.truetype(font=font_path, size=50)
                draw.text(xy=(278, -69 + 95 + (card_num * 261)), text=j_name,
                          fill=draw_config["color"]["event_title"], font=font)

                # 添加水母分组
                if j_group is not None:
                    font = ImageFont.truetype(font=font_path, size=40)
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
                    fontfile=font_path,
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)
            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
                    paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=font_path, size=45)
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
                font = ImageFont.truetype(font=font_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                # 添加消息
                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_path,
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
            paste_card_image = new_image((card_x, card_y), draw_config["color"]["card"])
            draw = ImageDraw.Draw(paste_card_image)

            if draw_config["jellyfish"]["card_background"] is not None:
                choose_card_background = random.choice(draw_config['jellyfish']['card_background'])
                if choose_card_background is not None:
                    path = await get_image_path(f"jellyfish_box-{choose_card_background}.png")
                    card_background = await load_image(path)
                    paste_card_image.paste(card_background, (0, card_y - card_background.size[1]), card_background)

            # 添加标题
            draw_event_y += 20
            font = ImageFont.truetype(font=font_path, size=45)
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
                font = ImageFont.truetype(font=font_path, size=42)
                draw.text(xy=(23, draw_event_y), text=title, fill=draw_config["color"]["event_title"],
                          font=font)
                draw_event_y += 52  # 标题高度

                paste_image = await draw_text(
                    message,
                    size=35,
                    textlen=21,
                    fontfile=font_path,
                    text_color=draw_config["color"]["event_message"]
                )
                paste_card_image.paste(paste_image, (23, draw_event_y), paste_image)
                draw_event_y += paste_image.size[1] + 15

            paste_card_image = circle_corner(paste_card_image, 30)
            image.paste(paste_card_image, (43, draw_y), paste_card_image)
            draw_event_y += 20  # 卡片结尾高度

            draw_x += 0
            draw_y += draw_event_y  # 卡片高度

        # 添加水印
        x, y = image.size
        paste_image = new_image((150, 150), (0, 0, 0, 0))
        paste_draw = ImageDraw.Draw(paste_image)
        font = ImageFont.truetype(font_shsk_M_path, size=30)
        paste_draw.text((0, 0), user_id, fill=(150, 150, 150, 10), font=font)
        image.paste(paste_image, (x - 150, y - 40), mask=paste_image)
        return image

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
            returnpath = await draw_jellyfish_live(draw_data=draw_data)
        elif os.path.exists(f"{basepath}cache/jellyfish_box/{user_id}.gif"):
            returnpath = f"{basepath}cache/jellyfish_box/{user_id}.gif"
        else:
            image = new_image((2000, 1500), "#16547b")
            paste_image = await draw_jellyfish((1900, 1400))
            image.paste(paste_image, (50, 50), paste_image)
            returnpath = save_image(image)
        code = 2
    elif command == "水母箱":
        if draw_model == "text":
            code = 1
            message = await draw_jellyfish_box()
        else:
            command_prompt_list.append({"title": "/水母箱 帮助", "message": "查看水母箱指令介绍"})
            command_prompt_list.append({"title": "/水母箱 抓水母", "message": "抓几只水母进水母箱（每2小时抓一次）"})
            returnpath = await draw_jellyfish_box()
            code = 2
    elif command == "抓水母":
        # 抓水母 每2小时7200秒抓一次
        time_difference = time_now - box_data["sign_in_time"]
        if 1 <= time_h <= 4:
            time_difference -= 3600
        if time_difference < 7200:
            time_difference = 7200 - time_difference
            t_text = ""
            t_hour, t_second = divmod(time_difference, 3600)
            if t_hour > 0:
                t_text += f"{t_hour}小时"
            t_minute, t_second = divmod(t_second, 60)
            if t_minute > 0 or t_hour > 0:
                t_text += f"{t_minute}分钟"
            t_text += f"{t_second}秒"

            code = 1
            if 1 <= time_h <= 4:
                message = f"很晚了，别抓啦，过{t_text}再来吧"
            else:
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
            if jellyfish_num > 300:
                code = 1
                message = "别抓啦，水母箱已经满啦"
            else:
                # ## 随机水母类型 ##
                # jellyfish_group_list
                group = ["perfect", "great", "good", "normal", "special", "ocean"]
                if date_m == 5 and date_d == 11:
                    group_probability = [0.00, 0.05, 0.50, 0.35, 0.10, 0.00]
                else:
                    group_probability = [0.00, 0.03, 0.42, 0.55, 0.00, 0.00]
                p = numpy.array(group_probability).ravel()
                choose_group = numpy.random.choice(group, p=p)
                choose_list = []
                for jellyfish_id in jellyfish_datas:
                    if jellyfish_datas[jellyfish_id]["group"] == choose_group:
                        if jellyfish_datas[jellyfish_id]["exhibition_time"] < time_now:
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
                reply_trace["data"]["抓水母"] = {
                    "jellyfish_id": choose_jellyfish,
                    "number": grab_quantity,
                    "user": user_id
                }
                trace.append(f"抓到水母：{choose_jellyfish}， 数量：{grab_quantity}")

                # ## 抓饲料 ##
                food_id = random.choice(["f1", "f2"])
                food_num = random.randint(1, 4)
                if food_id not in box_data["feed"].keys():
                    box_data["feed"][food_id] = {"number": food_num}
                else:
                    box_data["feed"][food_id]["number"] += food_num

                news.append({
                    "icon": None,
                    "title": f"获得{feed_datas[food_id]['name']}x{food_num}",
                    "message": "可发送指令“/水母箱 投喂”进行投喂"
                })

                trace.append(f"抓到饲料：{food_id}， 数量：{food_num}")

                # ## 节日抓水母事件 ##

                # 元旦 - 未定义
                if date_m == 1 and date_d == 1:  # 元旦
                    pass
                # 情人节
                elif date_m == 2 and date_d == 14:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j52"
                    event_title = "情人节"
                    event_name = f"{event_title}_{date_y}"
                    event_message = (
                        f"才..才不是节日礼物..只是碰巧多了{number}只"
                        f"{jellyfish_datas[choose_jellyfish]['name']}，放你这了")

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 植树节 - 未定义
                if date_m == 3 and date_d == 12:
                    pass
                # 世界无肉日
                elif date_m == 3 and date_d == 20:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j41"
                    event_title = "世界无肉日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}颗{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界睡眠日 - 未定义
                if date_m == 3 and date_d == 21:
                    pass
                # 愚人节 - 未定义
                if date_m == 4 and date_d == 1:
                    pass
                # 泼水节
                elif date_m == 4 and date_d == 13:
                    # 事件内容
                    number = 1
                    choose_jellyfish = "j34"
                    event_title = "泼水节"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}把{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界艺术日
                elif date_m == 4 and date_d == 15:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j27"
                    event_title = "世界艺术日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界地球日 - 未定义
                if date_m == 4 and date_d == 22:
                    pass
                # 世界企鹅日 - 未定义
                if date_m == 4 and date_d == 25:
                    pass
                # 劳动节 - 未定义
                if date_m == 5 and date_d == 1:
                    pass
                # 花音生日
                elif date_m == 5 and date_d == 11:  # 花音生日
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
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
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
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            box_data["jellyfish"]["j31"]["number"] += number
                # 玫瑰情人节 - 未定义
                if date_m == 5 and date_d == 14:
                    pass
                # 世界龟鳖日
                elif date_m == 5 and date_d == 23:
                    # 事件内容
                    number = 4
                    choose_jellyfish = "j9"
                    event_title = "世界龟鳖日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 儿童节
                elif date_m == 6 and date_d == 1:
                    # 事件内容
                    number = 3
                    choose_jellyfish = "j48"
                    event_title = "儿童节"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界UFO日 - 未定义
                elif date_m == 7 and date_d == 2:
                    pass
                # 世界表情符号日
                elif date_m == 7 and date_d == 17:
                    # 事件内容
                    number = 3
                    choose_jellyfish = "j25"
                    event_title = "世界表情符号日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界棉花日
                elif date_m == 10 and date_d == 7:
                    # 事件内容
                    number = 3
                    choose_jellyfish = "j43"
                    event_title = "世界棉花日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界棉花日
                elif date_m == 10 and date_d == 17:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j3"
                    event_title = "世界扶贫日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"请V我点水母。获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 程序员节 - 未定义
                elif date_m == 10 and date_d == 24:
                    pass
                # 万圣节前夜
                elif date_m == 10 and date_d == 31:
                    # 事件内容
                    number = 2
                    choose_jellyfish = "j53"
                    event_title = "万圣节之夜"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"不给水母就捣蛋！获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        number = random.randint(0, 2)
                        choose_jellyfish = random.choice(["j53", "j54"])
                        if number != 0:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 万圣节
                elif date_m == 11 and date_d == 1:
                    # 事件内容
                    number = 3
                    choose_jellyfish = "j54"
                    event_title = "万圣节"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"不给水母就捣蛋！获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        number = random.randint(0, 2)
                        choose_jellyfish = random.choice(["j53", "j54"])
                        if number != 0:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 节后补偿
                elif date_m == 11 and date_d in [2, 3]:
                    # 事件内容
                    number = 1
                    choose_jellyfish = "j53"
                    event_title = "万圣节之夜"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"
                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": "幽灵出没",
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        # 事件内容
                        number = 1
                        choose_jellyfish = "j54"
                        event_title = "万圣节"
                        event_name = f"{event_title}_{date_y}"
                        event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"
                        # 事件执行
                        if event_name not in box_data["event_list"]:
                            box_data["event_list"].append(event_name)
                            news.append({
                                "icon": None,
                                "title": "南瓜出没",
                                "message": event_message
                            })
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界水母日
                if date_m == 11 and date_d == 3:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j24"
                    event_title = "世界水母日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 世界渔业日
                elif date_m == 11 and date_d == 21:
                    # 事件内容
                    number = 2
                    choose_jellyfish = "j8"
                    event_title = "世界渔业日"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # tae生日
                elif date_m == 12 and date_d == 4:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j16"
                    event_title = "今天要来点兔子吗？"
                    event_name = f"tae生日_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 平安夜
                elif date_m == 12 and date_d == 24:
                    # 事件内容
                    number = 2
                    choose_jellyfish = "j2"
                    event_title = "平安夜"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"平安夜快乐！获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        number = random.randint(0, 2)
                        choose_jellyfish = random.choice(["j2", "j59"])
                        if number != 0:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 圣诞节
                elif date_m == 12 and date_d == 25:
                    # 事件内容
                    number = 3
                    choose_jellyfish = "j59"
                    event_title = "圣诞节"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"圣诞节快乐！获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        number = random.randint(0, 2)
                        choose_jellyfish = random.choice(["j2", "j59"])
                        if number != 0:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 节后补偿
                elif date_m == 12 and date_d in [26, 27]:
                    # 事件内容
                    number = 1
                    choose_jellyfish = "j2"
                    event_title = "平安夜"
                    event_name = f"{event_title}_{date_y}"
                    event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"
                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": "幽灵出没",
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    else:
                        # 事件内容
                        number = 1
                        choose_jellyfish = "j59"
                        event_title = "圣诞节"
                        event_name = f"{event_title}_{date_y}"
                        event_message = f"获得{number}只{jellyfish_datas[choose_jellyfish]['name']}"
                        # 事件执行
                        if event_name not in box_data["event_list"]:
                            box_data["event_list"].append(event_name)
                            news.append({
                                "icon": None,
                                "title": "南瓜出没",
                                "message": event_message
                            })
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            if choose_jellyfish in box_data["jellyfish"]:
                                box_data["jellyfish"][choose_jellyfish]["number"] += number
                            else:
                                box_data["jellyfish"][choose_jellyfish] = {"number": number}

                # 除夕 & 春节 - 未定义
                if lunar_date_m == 12 and lunar_date_d == 29:
                    pass
                # 端午节 - 未定义
                elif lunar_date_m == 5 and lunar_date_d == 5:
                    pass
                # 七夕
                elif lunar_date_m == 7 and lunar_date_d == 7:
                    # 事件内容
                    number = 5
                    choose_jellyfish = "j52"
                    event_title = "七夕"
                    event_name = f"{event_title}_{date_y}"
                    event_message = (
                        f"才..才不是送给你的..只是帮我保管一下这{number}只"
                        f"{jellyfish_datas[choose_jellyfish]['name']}，放你这了")

                    # 事件执行
                    if event_name not in box_data["event_list"]:
                        box_data["event_list"].append(event_name)
                        news.append({
                            "icon": None,
                            "title": event_title,
                            "message": event_message
                        })
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        if choose_jellyfish in box_data["jellyfish"]:
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                        else:
                            box_data["jellyfish"][choose_jellyfish] = {"number": number}
                # 中秋节
                elif lunar_date_m == 8 and lunar_date_d == 15:
                    number = random.randint(2, 3)
                    choose_jellyfish = "j16"
                    if choose_jellyfish not in list(box_data["jellyfish"]):
                        new_jellyfish.append(
                            {"id": choose_jellyfish,
                             "number": number,
                             "name": jellyfish_datas[choose_jellyfish]["name"],
                             "group": jellyfish_datas[choose_jellyfish]["group"],
                             "message": f"抓到了{number}只"}
                        )
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        box_data["jellyfish"][choose_jellyfish] = {"number": number}
                    elif box_data["jellyfish"][choose_jellyfish]["number"] < 7:
                        number = random.randint(1, 2)
                        new_jellyfish.append(
                            {"id": choose_jellyfish,
                             "number": number,
                             "name": jellyfish_datas[choose_jellyfish]["name"],
                             "group": jellyfish_datas[choose_jellyfish]["group"],
                             "message": f"抓到了{number}只"}
                        )
                        trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                        box_data["jellyfish"][choose_jellyfish]["number"] += number
                    else:
                        if random.randint(0, 5) == 0:
                            new_jellyfish.append(
                                {"id": choose_jellyfish,
                                 "number": number,
                                 "name": jellyfish_datas[choose_jellyfish]["name"],
                                 "group": jellyfish_datas[choose_jellyfish]["group"],
                                 "message": f"抓到了{number}只"}
                            )
                            trace.append(f"节日抓到水母：{choose_jellyfish}， 数量：{number}")
                            box_data["jellyfish"][choose_jellyfish]["number"] += number
                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
                    conn.commit()
                except Exception as e:
                    logger.error("水母箱保存用户数据出错")
                    logger.error(e)
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()

                # 绘制
                if draw_model == "text":
                    code = 1
                    message = await draw_jellyfish_box(draw_box=False)
                else:
                    returnpath = await draw_jellyfish_box()
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

        j_list[f"cache_feed"] = []
        for feed_id in box_data["feed"]:
            j_list[f"cache_feed"].append(feed_id)

        # 排列大小
        group_list.append("feed")
        for group in group_list:
            num = 99
            while num > 0 and len(j_list[f"cache_{group}"]) > 0:
                num -= 1
                j_max_number = 0
                j_max_id = ""
                for jellyfish_id in j_list[f"cache_{group}"]:
                    if jellyfish_id.startswith("j"):
                        if box_data["jellyfish"][jellyfish_id]["number"] > j_max_number:
                            j_max_number = box_data["jellyfish"][jellyfish_id]["number"]
                            j_max_id = jellyfish_id
                    elif jellyfish_id.startswith("f"):
                        if box_data["feed"][jellyfish_id]["number"] > j_max_number:
                            j_max_number = box_data["feed"][jellyfish_id]["number"]
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
                if jellyfish_id.startswith("j"):
                    cache_group.append(
                        {"id": jellyfish_id,
                         "name": jellyfish_datas[jellyfish_id]["name"],
                         "group": jellyfish_datas[jellyfish_id]["group"],
                         "message": f"x{box_data['jellyfish'][jellyfish_id]['number']}"}
                    )
                elif jellyfish_id.startswith("f"):
                    cache_group.append(
                        {"id": jellyfish_id,
                         "name": feed_datas[jellyfish_id]["name"],
                         "group": "feed",
                         "message": f"x{box_data['feed'][jellyfish_id]['number']}"}
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
                returnpath = await draw_jellyfish_box(draw_box=False, draw_title="水母统计表")
            else:
                num_x = 0
                image = new_image(((1000 * len(cache_groups)), 2994), draw_config["color"]["bg"])
                for cache_group in cache_groups:
                    jellyfish_menu = []
                    for cache_data in cache_group:
                        jellyfish_menu.append(cache_data)
                    cache_path = await draw_jellyfish_box(draw_box=False, draw_title="水母统计表")
                    paste_image = await load_image(cache_path)
                    image.paste(paste_image, ((1000 * num_x), 0))
                    num_x += 1
                returnpath = save_image(image)
            code = 2
    elif command in ["丢弃", "抛弃", "放生"]:
        command_message = command
        if command2 is None:
            if reply_data is None:
                code = 1
                message = "请添加水母名称以及数量\n例：“/水母箱 丢弃 普通水母 10”"
            elif "抓水母" not in reply_data["data"]:
                code = 1
                message = "请添加水母名称和数量\n例：“/水母箱 丢弃 普通水母 10”"
            else:
                jellyfish_id = reply_data["data"]["抓水母"]["jellyfish_id"]
                number = reply_data["data"]["抓水母"]["number"]
                user = reply_data["data"]["抓水母"]["user"]

                if user != user_id:
                    code = 1
                    message = "只能回复自己的水母箱哦"
                elif jellyfish_id not in list(box_data["jellyfish"]):
                    code = 1
                    message = f"水母箱没有{jellyfish_datas[jellyfish_id]['name']}哦"
                elif box_data["jellyfish"][jellyfish_id]["number"] < number:
                    code = 1
                    message = f"水母箱没有这么多{jellyfish_datas[jellyfish_id]['name']}哦"
                elif box_data["jellyfish"][jellyfish_id]["number"] > number:
                    box_data["jellyfish"][jellyfish_id]["number"] -= number
                    code = 1
                    message = f"成功丢弃{jellyfish_datas[jellyfish_id]['name']}{number}只"

                    # 写入水母箱数据
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            f"replace into 'jellyfish_box' ('user_id','data') "
                            f"values('{user_id}','{json.dumps(box_data)}')")
                        conn.commit()
                    except:
                        logger.error("水母箱保存用户数据出错")
                        news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                    cursor.close()
                    conn.close()

                elif box_data["jellyfish"][jellyfish_id]["number"] == number:
                    box_data["jellyfish"].pop(jellyfish_id)
                    code = 1
                    message = f"成功丢弃全部{jellyfish_datas[jellyfish_id]['name']}"

                    # 写入水母箱数据
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            f"replace into 'jellyfish_box' ('user_id','data') "
                            f"values('{user_id}','{json.dumps(box_data)}')")
                        conn.commit()
                    except:
                        logger.error("水母箱保存用户数据出错")
                        news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                    cursor.close()
                    conn.close()
        else:
            numbers = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
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
            drop_list: dict = {}
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
                    if len(commands3) - 1 > num and type(commands3[num + 1]) is int:
                        if commands3[num + 1] != 0:
                            drop_list[command] = "无法指定数量"
                        else:
                            drop_list[command] = 0
                    else:
                        drop_list[command] = "无法指定数量-"
                else:
                    # 内容合规检测
                    if "参数输入" in kn_config("content_compliance", "enabled_list"):
                        content_compliance_data = await content_compliance("text", command, user_id=user_id)
                        if content_compliance_data["conclusion"] != "Pass":
                            # 仅阻止审核拒绝内容
                            if (content_compliance_data.get("review") is not None and
                                    content_compliance_data["review"] is True):
                                command = "水母"
                            # 阻止黑名单用户的输入
                            elif user_id in kn_config("content_compliance", "input_ban_list"):
                                command = "水母"

                    drop_list[command] = "不在水母箱"

            logger.debug(drop_list)

            # 检查丢弃数量
            for jellyfish_id in drop_list.keys():
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
                message = "丢弃丢失败，请检查输入信息。例：“丢弃 普通水母 5”"
                code = 1
            else:
                remove_group = []
                drop_num = 0
                message = f"成功{command_message}"
                for jellyfish_id in list(drop_list):
                    if type(drop_list[jellyfish_id]) is int:
                        if drop_list[jellyfish_id] == 0:
                            if jellyfish_id in jellyfish_group_list:
                                remove_group.append(jellyfish_id)
                            else:
                                drop_num += box_data['jellyfish'][jellyfish_id]['number']
                                message += f"全部{jellyfish_datas[jellyfish_id]['name']}"
                                message += f"{box_data['jellyfish'][jellyfish_id]['number']}只、"
                                box_data["jellyfish"].pop(jellyfish_id)
                        else:
                            drop_num += drop_list[jellyfish_id]
                            box_data["jellyfish"][jellyfish_id]["number"] -= drop_list[jellyfish_id]
                            message += f"{jellyfish_datas[jellyfish_id]['name']}{drop_list[jellyfish_id]}只、"
                message = message.removesuffix("、")
                for jellyfish_id in box_data["jellyfish"].copy().keys():
                    if jellyfish_datas[jellyfish_id]["group"] in remove_group:
                        drop_num += box_data["jellyfish"][jellyfish_id]["number"]
                        message += (f"全部{jellyfish_datas[jellyfish_id]['name']}"
                                    f"x{box_data['jellyfish'][jellyfish_id]['number']}、")
                        box_data["jellyfish"].pop(jellyfish_id)

                if message == f"成功{command_message}":
                    for group in remove_group:
                        message += f"{group}、"
                message = message.removesuffix("、")
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

                # 添加水母碎片
                if drop_num > 0:
                    if "f5" in box_data["feed"].keys():
                        box_data["feed"]["f5"]["number"] += drop_num
                    else:
                        box_data["feed"]["f5"] = {"number": drop_num}
                    message += f"\n获得水母拼图x{drop_num}"

                code = 1

                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') "
                        f"values('{user_id}','{json.dumps(box_data)}')")
                    conn.commit()
                except:
                    logger.error("水母箱保存用户数据出错")
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()
    elif command in ["水母图鉴", "图鉴"]:
        # 读取水母箱内容并分组
        # 读取是否有缓存
        draw_new = True
        if f"menu_{draw_model}" in list(kn_cache['jellyfish_box_image']):
            if time_now - kn_cache['jellyfish_box_image'][f"menu_{draw_model}"]["time"] < 10800:
                today_s = time_now - (int(time_now / 3600) * 3600)
                if time_h > 3 or today_s > time_now - kn_cache['jellyfish_box_image'][f"menu_{draw_model}"]["time"]:
                    draw_new = False

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
                    if jellyfish_datas[jellyfish_id]["exhibition_time"] < time_now:
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

        # 添加饲料列表
        for food_id in feed_datas.keys():
            if len(cache_group) > 11:
                cache_groups.append(cache_group)
                cache_group = []
            food_weight = float(1 / feed_datas[food_id]["weight"])
            food_weight = '{:.2f}'.format(food_weight)
            cache_group.append(
                {"id": food_id,
                 "name": feed_datas[food_id]["name"],
                 "group": "feed",
                 "message": f"({food_weight}){feed_datas[food_id]['message']}"}
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
            if draw_new is True:
                if len(cache_groups) == 1:
                    # for cache_group in cache_groups:
                    for cache_data in cache_groups[0]:
                        jellyfish_menu.append(cache_data)
                    returnpath = await draw_jellyfish_box(draw_box=False, draw_title="水母图鉴")
                else:
                    num_x = 0
                    image = new_image(((1000 * len(cache_groups)), 3516), draw_config["color"]["bg"])
                    for cache_group in cache_groups:
                        jellyfish_menu = []
                        for cache_data in cache_group:
                            jellyfish_menu.append(cache_data)
                        cache_path = await draw_jellyfish_box(draw_box=False, draw_title="水母图鉴")
                        paste_image = await load_image(cache_path)
                        image.paste(paste_image, ((1000 * num_x), 0))
                        num_x += 1
                    returnpath = save_image(image)
                code = 2

                kn_cache['jellyfish_box_image'][f"menu_{draw_model}"] = {
                    "time": time_now,
                    "image_path": returnpath
                }
            else:
                returnpath = kn_cache['jellyfish_box_image'][f"menu_{draw_model}"]["image_path"]
                code = 2
    elif command in ["水母箱样式", "样式"]:
        draw_model_list = {
            "normal": {"name": "默认"},
            "freehand": {"name": "手绘"},
            "text": {"name": "文字"},
            "starlight": {"name": "星光"},
            # "box": {"name": "盒子"},  # 3d渲染，类似高清mc
            # "birthday": {"name": "生日"},  # 生日专用
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
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
                    conn.commit()
                except:
                    logger.error("水母箱保存用户数据出错")
                cursor.close()
                conn.close()

                code = 1
                message = "替换样式成功"
    elif command == "投喂":
        if command2 is not None:
            code = 1
            message = "暂不支持指定投喂内容"
        else:
            # 判断是否能投喂
            feed = False
            for f in box_data["feed"].keys():
                if box_data["feed"][f]["number"] >= feed_datas[f]["weight"]:
                    feed = True
            # 投喂
            if feed is True:
                add_jellyfish_num = 0
                feed_message = "投喂了"
                food_list = list(box_data["feed"].keys()).copy()
                for f in food_list:
                    food_weight = feed_datas[f]["weight"]
                    if box_data["feed"][f]["number"] >= food_weight:
                        food_num = int(box_data["feed"][f]["number"] / food_weight)
                        add_jellyfish_num += food_num
                        box_data["feed"][f]["number"] -= int(food_num * food_weight)
                        if box_data["feed"][f]["number"] <= 0:
                            box_data["feed"].pop(f)
                        feed_message += f"{feed_datas[f]['name']}x{int(food_num * food_weight)}、"
                feed_message = feed_message.removesuffix("、")
                news.append({"icon": None, "title": "投喂", "message": feed_message})
                trace.append(feed_message)

                feed_data = {}
                for i in range(add_jellyfish_num):
                    choose_jellyfish_list = []
                    for jellyfish_id in box_data["jellyfish"].keys():
                        if jellyfish_datas[jellyfish_id]["group"] not in ["normal"]:
                            choose_jellyfish_list.append(jellyfish_id)

                    choose_jellyfish = random.choice(choose_jellyfish_list)
                    if choose_jellyfish in feed_data.keys():
                        feed_data[choose_jellyfish] += 1
                    else:
                        feed_data[choose_jellyfish] = 1

                for choose_jellyfish in feed_data.keys():
                    new_jellyfish.append({
                        "id": choose_jellyfish,
                        "number": feed_data[choose_jellyfish],
                        "name": jellyfish_datas[choose_jellyfish]["name"],
                        "group": None,
                        "message": f"新增了{feed_data[choose_jellyfish]}只"})

                    if choose_jellyfish in box_data["jellyfish"].keys():
                        box_data["jellyfish"][choose_jellyfish]["number"] += feed_data[choose_jellyfish]
                    else:
                        box_data["jellyfish"][choose_jellyfish] = {"number": feed_data[choose_jellyfish]}

            # 保存
            if feed is True:
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
                    conn.commit()
                except Exception as e:
                    logger.error("水母箱保存用户数据出错")
                    logger.error(e)
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()
            # 绘制
            if feed is False:
                code = 1
                message = "饲料不够啦，还不能投喂哦\n目前"
                if len(box_data["feed"].keys()) == 0:
                    message += "没有饲料"
                else:
                    message += "有："
                    for f in box_data["feed"].keys():
                        food_weight = float(1 / feed_datas[f]["weight"])
                        food_weight = '{:.1f}'.format(food_weight)
                        message += f"{feed_datas[f]['name']}({food_weight})x{box_data['feed'][f]['number']}、"
                    message = message.removesuffix("、")
            else:
                returnpath = await draw_jellyfish_box()
                code = 2
    elif command.startswith("开启") or command.startswith("关闭"):
        if len(command) > 2:
            if command2 is None:
                command2 = command[2:]
            else:
                command2 = f"{command[2:]} {command2}"
            command = command[:2]
            logger.debug(f"{command}, {command2}")

        if command2 is None:
            code = 1
            message = "请填写要修改的名称，例：\n“/水母箱 开启 节日效果”"

        if command == "开启":
            command_state = True
        elif command == "关闭":
            command_state = False
        else:
            raise "设置水母箱效果出错"

        result_list = ["生日效果", "节日效果"]
        if command2 in ["所有效果", "全部效果"]:
            box_data["draw_event_box"] = command_state
            code = 1
            message = f"已{command}所有效果"
        elif command2 in ["节日效果", "生日效果"]:
            if type(box_data["draw_event_box"]) is list:
                if command2 not in box_data["draw_event_box"]:
                    if command_state is True:
                        box_data["draw_event_box"].append(command2)
                    else:
                        message = f"{command2}已经{command}，无需重复{command}"
                else:
                    if command_state is False:
                        box_data["draw_event_box"].remove(command2)
                        if not box_data["draw_event_box"]:
                            box_data["draw_event_box"] = False
                    else:
                        message = f"{command2}已经{command}，无需重复{command}"

            elif box_data["draw_event_box"] is True:
                if command_state is True:
                    message = f"{command2}已经{command}，无需重复{command}"
                else:
                    result_list.remove(command2)
                    box_data["draw_event_box"] = result_list
            elif box_data["draw_event_box"] is False:
                if command_state is True:
                    box_data["draw_event_box"] = [command2]
                else:
                    message = f"{command2}已经{command}，无需重复{command}"

            code = 1
            if message is None:
                message = f"已{command}{command2}"

        # 保存
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
            conn.commit()
        except Exception as e:
            logger.error("水母箱保存用户数据出错")
            logger.error(e)
            news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
        cursor.close()
        conn.close()
    elif command == "设置天气":
        if command2 is None:
            code = 1
            message = "请添加地区名或地区代码。例：\n“/水母箱 设置天气 北京市”\n“/水母箱 设置天气 010”\n“/水母箱 设置天气 无”"
        else:
            weather_name_list = await _jellyfish_box_weather_name_data()
            if command2 == "无":
                city_id = "无"
            elif command2 in weather_name_list.keys():
                city_id = weather_name_list[command2]
            elif command2 in weather_name_list.items():
                city_id = command2
            elif f"{command2}省" in weather_name_list.keys():
                city_id = weather_name_list[f"{command2}省"]
            elif f"{command2}市" in weather_name_list.keys():
                city_id = weather_name_list[f"{command2}市"]
            elif f"{command2}区" in weather_name_list.keys():
                city_id = weather_name_list[f"{command2}区"]
            elif f"{command2}县" in weather_name_list.keys():
                city_id = weather_name_list[f"{command2}县"]
            elif f"{command2}自治县" in weather_name_list.keys():
                city_id = weather_name_list[f"{command2}自治县"]
            else:
                city_id = None

            if city_id is None:
                code = 1
                message = "无法找到该地区，请检查地区名字"
            else:
                box_data["weather"] = None if city_id == "无" else city_id
                code = 1
                message = "设置成功"

                # 写入水母箱数据
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"replace into 'jellyfish_box' ('user_id','data') values('{user_id}','{json.dumps(box_data)}')")
                    conn.commit()
                except Exception as e:
                    logger.error("水母箱保存用户数据出错")
                    logger.error(e)
                    news.append({"icon": None, "title": "数据库出错", "message": "本次数据不进行保存"})
                cursor.close()
                conn.close()

    elif command == "换水":
        pass
    elif command == "拜访":
        pass
    elif command == "水母榜":
        pass
    elif command == "装饰":
        pass
    elif command == "拜访水母箱":
        pass
    elif command == "兑换水母":
        pass
    elif command == "帮助":
        command_prompt_list.append({"title": "/水母箱", "message": "查看水母箱相关"})
        command_prompt_list.append({"title": "/水母箱 查看水母箱",
                                    "message": "发送水母箱的图片（非实时更新，箱内水母可能不是最新状态）"})
        command_prompt_list.append({"title": "/水母箱 抓水母", "message": "抓几只水母进水母箱（每2小时抓一次）"})
        command_prompt_list.append({"title": "/水母箱 丢弃 普通水母 5", "message": "将5只普通水母丢弃"})
        command_prompt_list.append({"title": "/水母箱 投喂",
                                    "message": "往水母箱投喂一些饲料（饲料通过抓水母获得）"})
        command_prompt_list.append({"title": "/水母箱 水母图鉴", "message": "查看水母图鉴"})
        command_prompt_list.append({"title": "/水母箱 水母统计表", "message": "查看目前水母箱有多少水母"})
        command_prompt_list.append({"title": "/水母箱 水母箱样式 手绘", "message": "更换显示样式"})
        command_prompt_list.append({"title": "/水母箱 开启 生日效果",
                                    "message": "开启成员生日效果。\n“/水母箱 [开启|关闭] [节日效果|生日效果|全部效果]”"})
        command_prompt_list.append({"title": "/水母箱 设置天气 北京", "message": "添加天气状态"})
        returnpath = await draw_jellyfish_box(draw_box=False)
        code = 2
    else:
        code = 1
        message = "错误命令"

    return code, message, returnpath, markdown, keyboard, trace, reply_trace


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
    draw_config = jellyfish_box_draw_config(draw_model, draw_event_box=False)

    if "draw_model" in list(draw_data) and draw_data["draw_model"] == "freehand":
        # 创建底图
        image_base = new_image(draw_data["size"], draw_config["color"]["bg"])
        draw = ImageDraw.Draw(image_base)
        # 添加底色
        file_path = await get_image_path(f"jellyfish_box-freehand_background.png")
        paste_image = await load_image(file_path)
        paste_image = paste_image.resize(draw_data["size"])
        image_base.paste(paste_image, (0, 0))

        file_path = await get_image_path(f"jellyfish_box-freehand_box_background.png")
        paste_alpha = await load_image(file_path)
        paste_alpha = paste_alpha.resize(draw_data["size"])
        paste_image = new_image(draw_data["size"], draw_config["color"]["box_bg"])
        image_base.paste(paste_image, (0, 0), paste_alpha)
    else:
        image_base = new_image(draw_data["size"], draw_data["background_color"])

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
        load_image_id = "none"
        jellyfish_image = None
        for j_id in list(jellyfish_data):
            j_data = jellyfish_data[j_id]

            # 读取水母图片
            if load_image_id != j_data['jellyfish_id']:
                file_path = await get_image_path(f"jellyfish_box-{j_data['jellyfish_id']}.png")
                jellyfish_image = await load_image(file_path)
                jellyfish_image = jellyfish_image.resize((j_size, j_size))
                load_image_id = j_data['jellyfish_id']
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

        await images_to_gif(
            gifs=gifcache,
            gif_path=returnpath,
            duration=1000 / draw_data["frame_rate"],
        )
        if del_cache is True:
            del_files2(gifcache)

        return returnpath
    else:
        return returnpath_list
