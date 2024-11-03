# coding=utf-8
import json
import random
import time
import traceback
from nonebot import logger, require
import os
import sqlite3
from .config import _zhanbu_datas, _config_list, greet_list_
from .tools import (kn_config, connect_api, save_image, image_resize2, draw_text, get_file_path, new_background,
                    circle_corner, get_command, get_unity_user_data, _config, imgpath_to_url,
                    get_unity_user_id, get_image_path, load_image, get_file_path_v2, images_to_gif,
                    kn_cache, read_db, draw_line_chart, draw_pie_chart, save_unity_user_data, content_compliance)
from PIL import Image, ImageDraw, ImageFont

basepath = _config["basepath"]
adminqq = _config["superusers"]
test_id = "KnTest"

run = True  # 代码折叠助手


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
        tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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

            if kn_config("kanon_api", "state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                os.makedirs(returnpath, exist_ok=True)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api', 'url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
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


async def plugin_checkin(user_id: str, date: str = None, modified: int = None):
    """
    签到功能，state=0,message="签到成功" state=1,message="签到失败"
    :param user_id: 用户id
    :param date: 今日日期
    :param modified: 手动修改的薯条数量
    :return: {"state": state, "message": message}
    """
    state = 0
    point = 0
    returnpath = None
    message = ""

    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    if not os.path.exists(f"{basepath}db/"):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        os.makedirs(f"{basepath}db/")
        cursor.execute(f"CREATE TABLE checkin(user_id VARCHAR (10) PRIMARY KEY, date VARCHAR(10), point BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
    if "checkin" not in tables:
        cursor.execute(f"create table checkin(user_id VARCHAR(10) primary key, date VARCHAR(10), point INT(20))")
    try:
        cursor.execute(f'select * from checkin where user_id = "{user_id}"')
        data = cursor.fetchone()
        add_point = random.randint(2, 3)
        if modified is None:
            if data is None:
                # 未有数据，签到并返回成功
                point = add_point
                cursor.execute(f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
                conn.commit()
                state = 0
            else:
                last_data = data[1]
                point = data[2]
                if date == last_data and user_id != test_id:
                    # 已经签到过，不再签到
                    state = 1
                else:
                    # 今日未签到，正常签到
                    point = int(point) + add_point
                    cursor.execute(
                        f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
                    conn.commit()
                    state = 0
        else:
            if data is None:
                if modified > 0:
                    cursor.execute(
                        f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{modified})')
                    conn.commit()
                    state = 0
                    message = f"成功-{modified}"
                else:
                    state = -1
                    message = "薯条数量不够-0"
            else:
                point = data[2]
                if modified + point >= 0:
                    cursor.execute(f'replace into checkin ("user_id","date","point") '
                                   f'values("{user_id}","{data[1]}",{modified + point})')
                    conn.commit()
                    state = 0
                    message = f"成功-{modified + point}"
                else:
                    state = -1
                    message = f"薯条数量不够-{point}"

    except Exception:
        raise Exception
    finally:
        cursor.close()
        conn.close()

    if modified is None:
        # 创建返回的消息
        if state == 0:
            message = f"获得{add_point}根薯条\n现在有{point}根薯条"
            image_data = {
                "1": {
                    "coordinates": (123, 390),
                    "background": "background_1.png"
                },
                "2": {
                    "coordinates": (56, 828),
                    "background": "background_2.png"
                },
                "3": {
                    "coordinates": (0, 0),
                    "background": "background_3.png"
                }
            }
            image_id = random.choice(list(image_data))
            image_path = await get_image_path(f"chicken-{image_data[image_id]['background']}")
            image = Image.open(image_path)
            draw = ImageDraw.Draw(image)
            if image_id == "3":
                font_path = await get_file_path("Muyao-Softbrush-2.ttf")
                font = ImageFont.truetype(font=font_path, size=80)
                draw.text(
                    text=str(add_point),
                    xy=(480, 474),
                    fill="#FFFFFF",
                    font=font)
                draw.text(
                    text=str(point),
                    xy=(409, 863),
                    fill="#FFFFFF",
                    font=font)
            else:
                font_path = await get_file_path("SourceHanSansK-Medium.ttf")
                font = ImageFont.truetype(font=font_path, size=80)
                draw.text(
                    text=message,
                    xy=image_data[image_id]['coordinates'],
                    fill="#FFFFFF",
                    font=font)
            returnpath = save_image(image)
        else:
            message = f"今天签到过啦，{point}根薯条还不够吃嘛…QAQ…"

    return state, message, returnpath


async def plugin_config(
        command: str, command2: str | None, channel_id: str,
        platform: str = None, user_id: str = None):
    # 默认变量 & 插件数据
    message = None
    returnpath = None
    config_list = _config_list()
    time_h: int = time.localtime().tm_hour

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
            return f"无法找到命令，请检查命令名是否正确", None
    elif command == "关闭":
        command_state = False
        if command2 is None:
            return "请添加要关闭的功能名字，例：“关闭 签到”", None
        if command_id is None:
            return f"无法找到命令，请检查命令名是否正确", None
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
    datas: list = cursor.fetchall()
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
    if "command_state" not in tables:
        cursor.execute(
            f"create table command_state(id_ INTEGER primary key AUTOINCREMENT, "
            f"command VARCHAR(10), state BOOLEAN(10), channel_id VARCHAR(10))")

    # 判断要运行的命令
    if command in ["开启", "关闭"]:
        if config_list[command_id]["swift_by_admin"] is True and user_id not in adminqq:
            message = "指令功能无法设置"
        else:
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
        if platform == "qq_Official":
            config_list = _config_list(qq=True)
        state = {}
        for command_id in list(config_list):
            cursor.execute(
                f'SELECT * FROM command_state WHERE "command" = "{command_id}" AND "channel_id" = "{channel_id}"')
            data = cursor.fetchone()
            if data is None:
                command_state = config_list[command_id]["state"]
            else:
                command_state = True if data[2] == 1 else False

            config_group = config_list[command_id]["group"]
            if config_group not in list(state):
                state[config_group] = {"开启": [], "关闭": []}

            if command_state is True:
                state[config_group]["开启"].append(command_id)
            else:
                state[config_group]["关闭"].append(command_id)

        image_path = await get_file_path_v2("》plugin》help》v1》p1.png")
        image = await load_image(image_path)
        x = 53
        y = 558
        for config_group in list(state):
            paste_image = await draw_text(
                texts=f"- {config_group} -",
                size=70,
                fontfile=await get_file_path("YSHaoShenTi-2.ttf"),
                textlen=20,
                text_color="#516a8a",
                calculate=False
            )
            image.paste(paste_image, (x, y), mask=paste_image)
            y += 79
            num = -1
            for config_state in state[config_group].keys():
                for command_id in state[config_group][config_state]:
                    if num == -1:
                        num = 0
                    elif num == 0:
                        num = 1
                        x += 570
                    else:
                        num = 0
                        x -= 570
                        y += 70

                    paste_image = await draw_text(
                        texts=config_list[command_id]['message'],
                        size=50,
                        textlen=20,
                        text_color="#000000" if config_state == "开启" else "#a9b0c0",
                        calculate=False
                    )
                    image.paste(paste_image, (x, y), mask=paste_image)
                if num == 1:
                    num = 0
                    x -= 570
                    y += 60

            y += 50
            y += 7

        returnpath = save_image(image)

    cursor.close()
    conn.close()

    if command == "运行状态":
        # 查询开启的功能
        image_path = await get_file_path("plugin-config-state.png")
        image = await load_image(image_path, (3000, 2250))
        state_url = kn_config("plugin", "state_url")
        if state_url is None:
            logger.debug("未配置查询api地址，将不回复运行状态")
        else:
            data = await connect_api("json", state_url, timeout=50)

            # 粘贴24小时数据
            card_image = Image.new("RGBA", (1400, 550), (0, 0, 0, 0))
            card_draw = ImageDraw.Draw(card_image)
            log_data = data["data"]
            paste_datas = log_data["daily_use"]
            paste_datas = paste_datas[::-1]
            color_list = [(0, 0, 0, 255)]
            color = (12, 136, 218)
            num = len(paste_datas) - 1
            for i in range(num):
                add_color = (color[0], color[1], color[2],
                             int(255 / (i + 1)))
                color_list.append(add_color)
            color_list = color_list[::-1]

            num = -1
            for paste_data in paste_datas:
                num += 1
                paste_data_list = [[int(k), int(v)] for k, v in paste_data.items()]
                color = color_list[num]
                paste_image = await draw_line_chart(
                    datas=paste_data_list,
                    size=(1270, 310),
                    enlarge_num=4,
                    color=color,
                    mirror_x=True
                )
                card_image.paste(paste_image, (50, 123), paste_image)

            card_draw.line(
                xy=((120 + 1270 - int(1270 / 24 * time_h), 210), (120 + 1270 - int(1270 / 24 * time_h), 210 + 310)),
                fill=(50, 50, 50, 100),
                width=7)

            time_h_2 = time_h - 12 if time_h > 12 else time_h + 12
            card_draw.line(
                xy=((120 + 1270 - int(1270 / 24 * time_h_2), 210), (120 + 1270 - int(1270 / 24 * time_h_2), 210 + 310)),
                fill=(200, 200, 200, 50),
                width=7)
            image.paste(card_image, (55, 77), card_image)

            # 粘贴7天每天消息数
            card_image = Image.new("RGBA", (830, 550), (0, 0, 0, 0))
            data_list = log_data["log_nums"]
            paste_data_list = []
            list_x = []
            list_y = []
            for x in range(len(data_list)):
                list_x.append(x)
                list_y.append(data_list[x])
                paste_data_list.append([x, data_list[x]])

            color = "#128bd3"
            paste_image = await draw_line_chart(
                datas=paste_data_list,
                size=(690, 300),
                enlarge_num=4,
                color=color,
                mirror_x=True
            )
            image.paste(paste_image, (120, 800), paste_image)

            paste_image = await draw_text(
                str(max(list_y)),
                size=40,
                text_color="#A0A0A0",
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
            )
            image.paste(paste_image, (740, 735), paste_image)

            paste_image = await draw_text(
                str(min(list_y)),
                size=40,
                text_color="#A0A0A0",
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
            )
            image.paste(paste_image, (740, 1150), paste_image)

            # 粘贴7天每天用户数
            data_list = log_data["user_nums"]
            paste_data_list = []
            list_x = []
            list_y = []
            for x in range(len(data_list)):
                list_x.append(x)
                list_y.append(data_list[x])
                paste_data_list.append([x, data_list[x]])

            color = "#128bd3"
            paste_image = await draw_line_chart(
                datas=paste_data_list,
                size=(690, 300),
                enlarge_num=4,
                color=color,
                mirror_x=True
            )
            image.paste(paste_image, (1010, 800), paste_image)

            paste_image = await draw_text(
                str(max(list_y)),
                size=40,
                text_color="#A0A0A0",
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
            )
            image.paste(paste_image, (1620, 735), paste_image)

            paste_image = await draw_text(
                str(min(list_y)),
                size=40,
                text_color="#A0A0A0",
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
            )
            image.paste(paste_image, (1620, 1150), paste_image)

            # 粘贴用户发言数
            draw_datas = log_data["user_list"]

            num = -1
            paste_x = 610
            paste_y = 1300
            for data in draw_datas:
                num += 1
                if num >= 10:
                    break
                paste_text = f"{data}: {draw_datas[data]}"
                paste_image = await draw_text(
                    paste_text.removeprefix("user_"),
                    size=57, text_color=(0, 0, 0), fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
                )
                image.paste(paste_image, (paste_x, paste_y), paste_image)
                paste_y += 85

            # 粘贴功能调用数
            draw_datas: dict = log_data["command_name_list"]
            num_list = draw_datas.values()
            all_num = sum(num_list)
            num_list_2 = []
            for num in num_list:
                if num == 0 or (all_num / num) == 0:
                    num_list_2.append(0)
                else:
                    num_list_2.append(1 / (all_num / num))
            num_list_2 = sorted(num_list_2)
            is_zero = True
            for i in num_list_2:
                if i != 0:
                    is_zero = False
            if is_zero is True:
                num_list_3 = []
                for i in range(len(num_list_2)):
                    num_list_3.append(1 / len(num_list_2))
                num_list_2 = num_list_3
            paste_image = await draw_pie_chart(datas=num_list_2, size=(380, 380))
            image.paste(paste_image, (1880, 740), paste_image)

            num = -1
            paste_x = 2370
            paste_y = 700
            for data in draw_datas:
                num += 1
                if num >= 5:
                    break
                paste_text = f"{data}: {draw_datas[data]}"
                paste_image = await draw_text(
                    paste_text, size=72, text_color=(0, 0, 0), fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
                )
                image.paste(paste_image, (paste_x, paste_y), paste_image)
                paste_y += 100

            # 粘贴指令运行趋势
            draw_datas = log_data["command_name_list_daily"]
            min_num = 99999
            max_num = -10
            for command_name in draw_datas.keys():
                for day in draw_datas[command_name].keys():
                    min_num = min(min_num, draw_datas[command_name][day])
                    max_num = max(max_num, draw_datas[command_name][day])

            max_command_name_data = {}
            for command_name in draw_datas.keys():
                num = 0
                for i in draw_datas[command_name].keys():
                    num += draw_datas[command_name][i]
                max_command_name_data[command_name] = num
            max_command_name_data = dict(sorted(max_command_name_data.items(), key=lambda item: item[1], reverse=True))
            command_name_list = list(max_command_name_data.keys())
            max_command_name_list = command_name_list[:12]

            colors = ["#26bad8", "#f49b9d", "#f1c85e", "#f59c40", "#f5d5be", "#7cbe81", "#d3abc5", "#b46698", "#5a94b9",
                      "#aec64e", "#b9a695", "#000000", "#f15f46", "#5a3f25", "#3f6137", "#a73c3a", "#6f7134", "#c33c85",
                      "#26bad8", "#f49b9d", "#f1c85e", "#f59c40", "#f5d5be", "#7cbe81", "#d3abc5", "#b46698", "#5a94b9",
                      "#aec64e", "#b9a695", "#000000", "#f15f46", "#5a3f25", "#3f6137", "#a73c3a", "#6f7134", "#c33c85",
                      ]
            draw_text_num = -1
            num = -1
            for command_name in command_name_list:
                num += 1
                paste_data_list = []
                for x in draw_datas[command_name].keys():
                    paste_data_list.append([int(x), draw_datas[command_name][x]])

                paste_image = await draw_line_chart(
                    datas=paste_data_list,
                    size=(550, 400),
                    enlarge_num=4,
                    color=colors[num],
                    mirror_x=True,
                    max_min_y=[max_num, min_num]
                )
                image.paste(paste_image, (2130, 1380), paste_image)

                if command_name in max_command_name_list:
                    draw_text_num += 1
                    paste_image = await draw_text(
                        "-",
                        size=40,
                        text_color=colors[num],
                        fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
                    )
                    image.paste(paste_image, (2700, 1270 + int(draw_text_num * 45) + 10), paste_image)
                    image.paste(paste_image, (2700 + 5, 1270 + int(draw_text_num * 45) + 15), paste_image)
                    image.paste(paste_image, (2700, 1270 + int(draw_text_num * 45) + 20), paste_image)
                    paste_image = await draw_text(
                        command_name,
                        size=40,
                        text_color="#000000",
                        fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
                    )
                    image.paste(paste_image, (2700 + 20, 1270 + int(draw_text_num * 45)), paste_image)

            # 粘贴服务器状态
            draw_datas = log_data["state_data"]
            text = ""
            for data in draw_datas.keys():
                text += f"{data}: "
                if draw_datas[data]["state"] is True:
                    text += f"✅:{draw_datas[data]['message']}\n"
                else:
                    text += f"❌:{draw_datas[data]['message']}\n"
            text = text.removesuffix("\n")

            paste_image = await draw_text(
                text, size=55, text_color=(0, 0, 0),
                fontfile=await get_file_path("SourceHanSansK-Medium.ttf")
            )
            image.paste(paste_image, (1270, 1410), paste_image)

            # 返回图片
            returnpath = save_image(image)
    elif command == "关闭md":
        user_data = get_unity_user_data(user_id)
        user_data["use_markdown"] = False
        save_unity_user_data(user_id, user_data)
        message = "md已关闭"
    elif command == "开启md":
        user_data = get_unity_user_data(user_id)
        user_data["use_markdown"] = True
        save_unity_user_data(user_id, user_data)
        message = "md已开启"

    return message, returnpath


async def plugin_emoji_emoji(command, user_id: str = None):
    message = None
    os.makedirs(f"{basepath}cache/emoji/", exist_ok=True)
    returnpath = f"{basepath}cache/emoji/{command}.png"

    if command is None or command == "None":
        message = "请添加要合成的emoji。例：“/合成 🥹😗”"
    elif not os.path.exists(returnpath):
        url = f"{kn_config('kanon_api-url')}/json/emoji?imageid={command}"
        return_json = await connect_api("json", url, timeout=30)
        if return_json["code"] == 0:
            url = f"{kn_config('kanon_api-url')}/api/emoji?imageid={command}"
            try:
                image = await connect_api("image", url)
                image.save(returnpath)
            except Exception as e:
                message = f"{command}不支持合成"
        else:
            message = f"{command}不支持合成"

    # 内容合规检测
    if "参数输入" in kn_config("content_compliance", "enabled_list"):
        content_compliance_data = await content_compliance("text", command, user_id=user_id)
        if content_compliance_data["conclusion"] != "Pass":
            # 仅阻止审核拒绝内容
            if (content_compliance_data.get("review") is not None and
                    content_compliance_data["review"] is True):
                message = "不支持合成"
    if message is not None:
        if user_id in kn_config("content_compliance", "input_ban_list"):
            message = "不支持合成"

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
            xibao_image = await load_image(file_path)
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
            user_image = await load_image(user_avatar)
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
            user_image = await load_image(user_avatar)
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
            user_image = await load_image(user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    image = Image.new("RGB", (640, 640), "#FFFFFF")
    path = await get_file_path("plugin-jiehun-jiehun.png")
    paste_image = await load_image(path)
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


async def plugin_emoji_momo(user_avatar, cachepath):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = await load_image(user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    filepath = await get_file_path("plugin-emoji-momo-0.png")
    pic = await load_image(filepath)

    timestamp = str(time.time())
    returnpath = f"{cachepath}摸摸/"
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
        pic = await load_image(filepath)
        filepath = await get_file_path(f"plugin-emoji-momo-{num}.png")
        paste_image = await load_image(filepath)

        pic1.paste(pic, (0, 0))
        pic1.paste(print_image_face, (print_imagepace_x, print_imagepace_y),
                   mask=print_image_face_clown)
        pic1.paste(paste_image, (0, 0), mask=paste_image)

        pic1.save(f"{gifcache}/{num}.png")
        num += 1

    returnpath = f"{returnpath}{timestamp}_{random.randint(1000, 9999)}.gif"
    await images_to_gif(
        gifs=gifcache,
        gif_path=returnpath,
        duration=70,
    )
    return returnpath


async def plugin_emoji_daibu(user_avatar: str, user_name: str):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = await load_image(user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (128, 128), overturn=False)

    image_path = await get_image_path("meme-daibu")
    image = await load_image(image_path)
    image.paste(user_image, (69, 89), mask=user_image)

    return save_image(image)


async def plugin_emoji_ji():
    num = random.randint(1, 32)
    image_path = await get_image_path(f"meme-ji_{num}")
    return image_path


async def plugin_emoji_ji2():
    num = random.randint(1, 10)
    image_path = await get_image_path(f"meme-ji2_{num}")
    return image_path


async def plugin_emoji_pa():
    num = random.randint(1, 16)
    image_path = await get_image_path(f"meme-pa_{num}")
    return image_path


async def plugin_emoji_reply_keai():
    num = random.randint(1, 108)
    image_path = await get_image_path(f"reply_keai-{num}")
    return image_path


async def plugin_function_greet(command: str, time_h: int = time.localtime().tm_hour, user_name: str = "你"):
    message_list = []
    greet_list = greet_list_()
    for group in greet_list:
        if command in group["ask"]:
            for t in group["answer"].keys():
                time_1, time_2 = t.split("-", 1)
                if int(time_1) <= time_h <= int(time_2):
                    message_list.extend(group["answer"][t])

    if not message_list:
        return None
    choose_msg: str = random.choice(message_list)
    if choose_msg is None:
        return None
    if user_name is not None:
        choose_msg = choose_msg.replace("{user_name}", user_name)
    return choose_msg.replace("{command}", command).replace("{time_h}", str(time_h))


async def plugin_emoji_wlp(user_avatar: str, user2_avatar: str, user2_name: str = None):
    # 获取头像1
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = await load_image(user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")

    # 获取头像2
    try:
        if user2_avatar in [None, "None", "none"]:
            user2_image = await draw_text("图片", 50, 10)
        elif user2_avatar.startswith("http"):
            user2_image = await connect_api("image", user2_avatar)
        else:
            user2_image = await load_image(user2_avatar)
    except Exception as e:
        user2_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")

    # 获取底图
    image_path = await get_image_path("meme-wlp")
    image = await load_image(image_path)
    draw = ImageDraw.Draw(image)
    # 粘贴头像1
    user_image = image_resize2(user_image, (200, 200), overturn=False)
    image.paste(user_image, (421, 670), mask=user_image)
    # 粘贴头像1贴图
    paste_image_path = await get_image_path("meme-zhi")
    paste_image = await load_image(paste_image_path)
    paste_image = image_resize2(paste_image, (200, 200), overturn=False)
    image.paste(paste_image, (421, 670), mask=paste_image)
    # 粘贴头像2
    user2_image = image_resize2(user2_image, (400, 400), overturn=False)
    image.paste(user2_image, (125, 105), mask=user2_image)

    return save_image(image)


# async def plugin_emoji_qinqin(user_avatar, user_name):
#     try:
#         if user_avatar in [None, "None", "none"]:
#             user_image = await draw_text("图片", 50, 10)
#         elif user_avatar.startswith("http"):
#             user_image = await connect_api("image", user_avatar)
#         else:
#             user_image = await load_image(user_avatar)
#     except Exception as e:
#         user_image = await draw_text("图片", 50, 10)
#         logger.error(f"获取图片出错:{e}")
#     user_image = image_resize2(user_image, (640, 640), overturn=False)
#
#
#     pass
#
#     return save_image(image)


async def plugin_game_cck(
        command: str,
        channel_id: str,
        platform: str,
        user_id: str,
        use_markdown: bool = False
):
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
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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
                    elif command == "结束":
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}已结束"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}时间超时，请重新开始"
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

    if code == 1 and message != " " and game_state != "exit":
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
        cck_card = await load_image(returnpath)
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

        if (
                platform == "qq_Official" and
                kn_config("plugin_cck", "send_markdown") and
                use_markdown is True):
            # 去除消息的图片内容
            if code == 3:
                code = 1
            elif code == 2:
                code = 0
            # 转换图片为md
            image_url = await imgpath_to_url(returnpath, host='http://txs.kanon.ink:8991')
            markdown = {
                "id": kn_config("plugin", "image_markdown"),
                "params": [
                    {"key": "text", "values": ["img"]},
                    {"key": "imagex", "values": [f"{image.size[0]}"]},
                    {"key": "imagey", "values": [f"{image.size[1]}"]},
                    {"key": "image", "values": [image_url]},
                ]
            }
        if (
                platform == "qq_Official" and
                kn_config("plugin_cck", "send_button") and
                use_markdown is True):
            if 1 <= int(member_id) <= 15 or 21 <= int(member_id) <= 25:
                button_id = "button_1_id"
            elif 16 <= int(member_id) <= 20 or 26 <= int(member_id) <= 25:
                button_id = "button_2_id"
            else:
                button_id = None

            if button_id is not None:
                keyboard = {"id": kn_config("plugin_cck", button_id)}
                if platform != "qq_Official" or kn_config("plugin_cck", "send_markdown") is False:
                    markdown = {"id": kn_config("plugin", "none_markdown")}
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

            # 转换wlp名称
            wlp_id = "wlp_id"
            if command in ["wlp", "我老婆", "w老婆", "我lp"]:
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                if not os.path.exists(f"{basepath}db/"):
                    # 数据库文件 如果文件不存在，会自动在当前目录中创建
                    os.makedirs(f"{basepath}db/")
                    cursor.execute(
                        f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
                if "wlp" not in tables:
                    cursor.execute(
                        f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
                try:
                    cursor.execute(f'select * from wlp where user_id = "{user_id}"')
                    data = cursor.fetchone()
                except Exception as e:
                    logger.error(e)
                    raise "获取lp数据错误"
                finally:
                    cursor.close()
                    conn.close()

                if data is not None:
                    wlp_id = data[1]
                    command = "你lp"

            # 判断用户发送词是否符合
            if command.lower() in member_alias or wlp_id == member_id:
                if "game_id" in list(gamedata):
                    game_id = gamedata["game_id"]
                    if game_id in list(kn_cache["plugin_game_cck"]["game_data"]):
                        kn_cache["plugin_game_cck"]["game_data"][game_id]["gameing"] = False
                # 添加回复句子与图
                message = f"恭喜猜中，她就是{command}（{image_name.removesuffix('.png')}）"
                # 添加薯条
                try:
                    point = random.randint(1, 2)
                    state, msg, _pass_ = await plugin_checkin(user_id=user_id, modified=point)
                    if state == 0:
                        message += f"\n增加了{point}根薯条，现有{msg.split('-')[1]}根薯条"

                except Exception as e:
                    logger.error("写入薯条数据错误")

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
                # 阻止黑名单用户的输入
                if user_id in kn_config("content_compliance", "input_ban_list"):
                    message = f"猜错了哦"

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

    if message == " " and code == 1:
        code = 0
        message = None
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
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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
                    elif command == "结束":
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}已结束"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}时间超时，请重新开始"
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
        paste_image = await load_image(filepath)
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
            paste_image = await load_image(filepath)
            image.paste(paste_image, (0, 0), mask=paste_image)

            # 获取飞机图片
            filepath = await get_file_path("plugin-zfj-plane1.png")
            paste_image_1 = await load_image(filepath)
            filepath = await get_file_path("plugin-zfj-plane2.png")
            paste_image_2 = await load_image(filepath)
            filepath = await get_file_path("plugin-zfj-plane3.png")
            paste_image_3 = await load_image(filepath)

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
            paste_image_0 = await load_image(filepath)
            filepath = await get_file_path("plugin-zfj-injured.png")
            paste_image_1 = await load_image(filepath)
            filepath = await get_file_path("plugin-zfj-crash.png")
            paste_image_2 = await load_image(filepath)

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
                    paste_image = await load_image(filepath)
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取飞机图片
                    filepath = await get_file_path("plugin-zfj-plane1.png")
                    plane_image_1 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = await load_image(filepath)

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
                    state_image_0 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = await load_image(filepath)

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
                    paste_image = await load_image(filepath)
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取状态图片
                    filepath = await get_file_path("plugin-zfj-miss.png")
                    state_image_0 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = await load_image(filepath)

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
                    plane_image_1 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = await load_image(filepath)
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = await load_image(filepath)

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
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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
                    elif command == "结束":
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}已结束"
                    else:
                        game_state = "exit"
                        code = 1
                        message = f"{gamename.split('-')[1]}时间超时，请重新开始"
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
        returnpath2 = save_image(image_1)  # 将有变化的图和文字一起发出
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
            image_1 = await load_image(image_1_path)

            for different in different_list:
                if different in seek_out:
                    continue
                location = region_to_coord(different_game_data["data"][card_id]["different_list"][different]["region"])
                x, y = location
                x = 111 - 100 + (x * 222)
                y = 100 - 100 + (y * 200)
                image_1.paste(paste_image, (x, y), paste_image)

            # 保存图片
            returnpath = save_image(image_1)
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

            if command in seek_out:
                code = 1
                message = "这里已经找到啦，找找别的地方吧"
            elif find is False:
                code = 1
                message = "不是这里哦"
            else:
                seek_out.append(command)
                # 绘制图片
                paste_image = await load_image(await get_image_path("different-different.png"))
                image_1 = await load_image(image_1_path)
                location = region_to_coord(different_game_data["data"][card_id]["different_list"][different]["region"])
                x, y = location
                x = 111 - 100 + (x * 222)
                y = 100 - 100 + (y * 200)
                image_1.paste(paste_image, (x, y), paste_image)

                if len(seek_out) == len(different_list):
                    code = 3
                    message = "恭喜找到所有不同"
                    returnpath = save_image(image_1)

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
                    returnpath = save_image(image_1)
                    gameinfo = {
                        "card_id": card_id,
                        "image_1": returnpath,
                        "image_2": image_1_path,
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
        tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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


async def plugin_function_pic(
        msg: str,
        user_id: str
):
    message = None
    images = None
    trace = []

    eagle_path = kn_config("pic", "eagle-path")
    eagle_url = kn_config("pic", "eagle-url")
    if eagle_path is None or eagle_url is None:
        logger.warning("未配置图库路径或url，将不返回消息")
        return message, images, trace

    # 替换同义词
    msg = msg.replace("老婆", "lp").replace("我lp", "wlp")
    msg = msg.replace("你wlp是", "wlp是你")
    msg = msg.replace("花音kanon", "花音").replace("花音Kanon", "花音")

    # 解析指令
    if msg.startswith("来点") and msg[2:3] != " ":
        msg = f"{msg[:3]} {msg[2:]}"
    elif msg.startswith("多来点") and msg[3:4] != " ":
        msg = f"{msg[:4]} {msg[3:]}"
    elif msg.startswith("wlp是") and msg[4:5] != " ":
        msg = f"{msg[:5]} {msg[4:]}"

    commands = get_command(msg)
    command = commands[0]
    command2 = None if len(commands) == 1 else commands[1]
    if command2 == "你":
        command2 = "花音"

    filepath = await get_file_path("plugin-pic-member_list.json")
    file = open(filepath, 'r', encoding='utf8')
    member_data: dict = json.load(file)
    file.close()

    def find_member_id(member_name: str) -> str | None:
        for member_id in member_data.keys():
            if member_name in member_data[member_id]["alias"]:
                return member_id
        return None

    # 执行指令
    if command == "来点":
        if command2 in ["wlp", "我老婆", "w老婆", "我lp"]:
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            if not os.path.exists(f"{basepath}db/"):
                # 数据库文件 如果文件不存在，会自动在当前目录中创建
                os.makedirs(f"{basepath}db/")
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
            datas = cursor.fetchall()
            tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
            if "wlp" not in tables:
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            try:
                cursor.execute(f'select * from wlp where user_id = "{user_id}"')
                data = cursor.fetchone()
            except Exception as e:
                logger.error(e)
                raise "获取lp数据错误"
            finally:
                cursor.close()
                conn.close()

            if data is None:
                member_id = None
            else:
                member_id = data[1]
        else:
            member_id = find_member_id(command2)

        if member_id is None and command2 in ["wlp", "我老婆", "w老婆", "我lp"]:
            message = "你还没有lp哦，\n请发送wlp是+lp名称来添加lp。\n例：wlp是爱美"
        elif member_id is None:
            message = "找不到相关成员"
        else:
            # 检查库名称
            url = f"{eagle_url}api/library/info"
            data = await connect_api("json", url)
            lib_name = data["data"]["library"]["name"]
            eagle_name = kn_config("pic", "eagle-name")
            if eagle_name is not None and lib_name != eagle_name:
                message = "管理员忘记切换库啦，没有lp看啦"
            else:
                # 获取成员图片列表
                url = f"{eagle_url}api/item/list?folders={member_data[member_id]['id']}"
                data = await connect_api("json", url)
                image_data = random.choice(data['data'])
                images = [f"{eagle_path}images/{image_data['id']}.info/{image_data['name']}.{image_data['ext']}"]

    elif command == "多来点":
        if command2 in ["wlp", "我老婆", "w老婆", "我lp"]:
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            if not os.path.exists(f"{basepath}db/"):
                # 数据库文件 如果文件不存在，会自动在当前目录中创建
                os.makedirs(f"{basepath}db/")
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
            datas = cursor.fetchall()
            tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
            if "wlp" not in tables:
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            try:
                cursor.execute(f'select * from wlp where user_id = "{user_id}"')
                data = cursor.fetchone()
            except Exception as e:
                logger.error(e)
                raise "获取lp数据错误"
            finally:
                cursor.close()
                conn.close()

            if data is None:
                member_id = None
            else:
                member_id = data[1]
        else:
            member_id = find_member_id(command2)

        # 获取成员图片
        if member_id is None and command2 in ["wlp", "我老婆", "w老婆", "我lp"]:
            message = "你还没有lp哦，\n请发送wlp是+lp名称来添加lp。\n例：wlp是爱美"
        elif member_id is None:
            message = "找不到相关成员"
        else:
            # 获取成员图片列表
            url = f"{eagle_url}api/item/list?folders={member_data[member_id]['id']}"
            data = await connect_api("json", url)
            num = random.randint(2, 3)
            images = []
            while num >= 1:
                num -= 1
                image_data = random.choice(data['data'])
                image_path = f"{eagle_path}images/{image_data['id']}.info/{image_data['name']}.{image_data['ext']}"
                images.append(image_path)
            point = random.randint(2, 3)
            state, message, _none_ = await plugin_checkin(user_id=user_id, modified=-point)
            if state == 0:
                message = f"吃了{point}根薯条，还剩{message.split('-')[1]}根薯条"
            else:
                message = f"没有薯条啦。。QaQ。"
                images = [images[0]]

    elif command == "wlp是":
        member_id = find_member_id(command2)
        if command2 == "谁":
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            if not os.path.exists(f"{basepath}db/"):
                # 数据库文件 如果文件不存在，会自动在当前目录中创建
                os.makedirs(f"{basepath}db/")
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
            datas = cursor.fetchall()
            tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
            if "wlp" not in tables:
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            try:
                cursor.execute(f"SELECT * FROM wlp WHERE user_id='{user_id}'")
                data = cursor.fetchone()
                if data is None:
                    message = f"你还没有lp哦"
                else:
                    message = f"你lp是{member_data[str(data[1])]['name']}"

            except Exception as e:
                logger.error(e)
                message = "读取lp数据错误"
            finally:
                cursor.close()
                conn.close()
        elif member_id is None:
            message = "找不到该lp哦"
        else:
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            if not os.path.exists(f"{basepath}db/"):
                # 数据库文件 如果文件不存在，会自动在当前目录中创建
                os.makedirs(f"{basepath}db/")
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
            datas = cursor.fetchall()
            tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
            if "wlp" not in tables:
                cursor.execute(
                    f"CREATE TABLE wlp(user_id VARCHAR(10) primary key, member_id VARCHAR(10), times INT(10))")
            try:
                cursor.execute(f"SELECT * FROM wlp WHERE user_id='{user_id}'")
                data = cursor.fetchone()
                if data is None:
                    cursor.execute(
                        f'replace into wlp ("user_id","member_id","times") values("{user_id}",{member_id},0)')
                    conn.commit()
                    message = f"你lp就是{command2}"
                elif member_id == data[1]:
                    message = f"你lp已经是{command2}啦"
                else:
                    cursor.execute(
                        f'replace into wlp ("user_id","member_id","times") values("{user_id}",{member_id},{data[2] + 1})')
                    conn.commit()
                    message = f"你的新lp就是{command2}， 已经换了{data[2] + 1}次lp"

            except Exception as e:
                logger.error(e)
                message = "写入lp数据错误"
            finally:
                cursor.close()
                conn.close()

    return message, images, trace
