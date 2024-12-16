# coding=utf-8
import json
import random
import time
import traceback
import numpy
from nonebot import logger
import sqlite3
from .config import _adventure_datas
from .plugins import plugin_checkin
from .tools import (kn_config, save_image, draw_text, get_file_path, circle_corner,
                    get_command, _config, get_image_path, load_image, read_db,
                    kn_cache, text_to_b64, b64_to_text)
from PIL import Image
from datetime import datetime
from zhdate import ZhDate

basepath = _config["basepath"]
adminqq = _config["superusers"]
num_list = "1234567890"
map_data_type = dict[str, dict[str, str | list[dict] | bool]]


async def plugin_adventure(
        user_id: str,
        user_name: str,
        channel_id: str,
        msg: str,
        time_now: int,
        platform: str = "None",
        reply_data: dict | None = None,
        channel_member_datas=None,
        at_datas=None
):
    """
    群聊功能-水母探险
    :return:
    """
    if channel_member_datas is None:
        channel_member_datas = {}
    """
    命令列表：
    出发: 向前移动
    装备: 装备获取的道具
    道具图鉴: 查看装备列表
    装饰: 装饰
    使用: 使用道具
    帮助: 指令说明
    """
    # 指令解析
    commands = get_command(msg)
    command: str = commands[0]
    if len(commands) > 1:
        command2 = commands[1]
    else:
        command2 = None
    command_list = ["水母探险", "出发", "装备", "卸下", "道具图鉴", "装饰", "使用", "帮助"]
    for c in command_list:
        if command.startswith(c) and command != c:
            command = c
            if command2 is None:
                command2 = command.removeprefix(c)
            else:
                command2 = f"{command.removeprefix(c)} {command2}"

    # 添加必要参数
    return_data = {
        "code": 0,
        "message": None,
        "returnpath": None,
        "markdown": None,
        "keyboard": None,
    }
    save_member_coordinates = False
    save_member_data = False
    adventure_game_datas = await _adventure_datas()  # 插件数据
    event_datas: dict[str, dict] = adventure_game_datas["event_datas"]  # 所有事件
    npc_datas: dict[str, dict] = adventure_game_datas["npc_datas"]  # 所有npc数据
    prop_datas: dict[str, dict] = adventure_game_datas["prop_datas"]  # 所有道具
    decorate_datas: dict[str, dict] = adventure_game_datas["decorate_datas"]  # 所有装饰物

    time_data = time.strftime("%Y %m %d %H", time.localtime(time_now)).split()
    date_y, date_m, date_d, time_h = map(int, time_data)
    time_now = int(time.time())
    time_now_h = int(time_now / 3600) * 3600
    date_zh = ZhDate.from_datetime(datetime(date_y, date_m, date_d))
    lunar_date_y: int = date_zh.lunar_year
    lunar_date_m: int = date_zh.lunar_month
    lunar_date_d: int = date_zh.lunar_day

    # 添加动态数据
    news = []
    command_prompt_list = []

    # 读取用户数据
    data = read_db(
        db_path="{basepath}db/plugin_data.db",
        sql_text=f'SELECT * FROM "adventure" WHERE user_id = "{user_id}"',
        table_name="adventure",
        select_all=False
    )
    if data is None:
        user_data: dict = {
            "info": {
                "owner": user_id,
                "owner_name": user_name
            },
            "energy": 10,  # 目前的体力
            "refresh_time": int(time_now / 3600) * 3600,  # 更新时间小时计算
            "profile": {
                "main": {"type": "avatar", "id": user_id},
                "decorate": {
                    "decorate": [],
                    "frame": [],
                }},  # 角色形象相关
            "event_history": [],  # 事件历史，防止同一位置事件重复触发
            "sleep_time": 0,  # 睡眠时间，暂停移动
            "map_event_history": [],  # 事件历史，防止同一位置事件重复触发
            "backpack": {
                "prop": {"p1": {"number": 4}, "p8": {"number": 2}},  # 拥有的道具
                "decorate": {},  # 拥有的装饰
            }
        }
        save_member_data = True
    elif data == "error":
        raise "获取冒险数据错误"
    else:
        user_data = json.loads(b64_to_text(data[1]))

    # 读取用户坐标
    data = read_db(
        db_path=f"{basepath}db/plugin_adventure_map-2411.db",
        sql_text=f'SELECT * FROM "user_map" WHERE user_id = "{user_id}"',
        table_name="user_map",
        select_all=False
    )
    if data is None:
        # 进入新地图，刷新状态
        user_data["map_event_history"] = []
        user_data["sleep_time"] = 0
        user_data["energy"] = 10
        if "p1" not in user_data["backpack"]["prop"].keys():
            user_data["backpack"]["prop"]["p1"] = {"number": 4}
        elif user_data["backpack"]["prop"]["p1"]["number"] < 4:
            user_data["backpack"]["prop"]["p1"] = {"number": 4}
        if "p8" not in user_data["backpack"]["prop"].keys():
            user_data["backpack"]["prop"]["p1"] = {"number": 2}
        elif user_data["backpack"]["prop"]["p1"]["number"] < 2:
            user_data["backpack"]["prop"]["p1"] = {"number": 2}

        # 随机生成一个用户坐标， 并写入
        user_coordinates = (random.randint(0, 2999), random.randint(0, 2999))
        save_member_coordinates = True
    else:
        user_coordinates = (data[1], data[2])

    # 数据更新
    user_data["info"] = {
        "owner": user_id,
        "owner_name": user_name}
    time_interval = int(time_now / 3600) - int(user_data["refresh_time"] / 3600)
    if time_interval > 0:
        user_data["energy"] += time_interval
        if user_data["energy"] > 10:
            user_data["energy"] = 10
        user_data["refresh_time"] = int(time_now / 3600) * 3600

    news.append({"title": "水母探险beta", "message": "游戏正在测试中，游戏数据将随时修改"})

    # 绘制
    async def draw():
        map_data = await load_map_data(user_coordinates, self_id=user_id, event_history=user_data["event_history"])
        return await draw_main(
            map_data=map_data,
            user_name=user_name,
            news=news,
            command_prompt_list=command_prompt_list,
            user_coordinates=user_coordinates,
            user_energy=user_data["energy"],
            user_profile=user_data["profile"],
            time_now=time_now,
            event_history=user_data["event_history"]
        )

    # 判断指令
    if command == "水母探险":
        return_data["code"] = 2
        command_prompt_list.append({"title": "/水母探险 出发", "message": "向前移动"})
        command_prompt_list.append({"title": "/水母探险 出发 前2", "message": "向东边移动2格"})
        command_prompt_list.append({"title": "test_/水母探险 帮助", "message": "查看水母探险指令列表"})
        return_data["returnpath"] = await draw()
    elif command in ["出发", "前进"]:
        if command2 is None:
            command2 = "前1"
        # 解析前进的方向以及格数
        direction = get_direction(command2)
        # 判断体力是否能移动到指定位置
        if user_data["sleep_time"] > time_now:
            message = "还不能移动哦，要过"
            t_s = user_data["sleep_time"] - time_now
            if t_s > 60:
                t_m, t_s = divmod(t_s, 60)
            else:
                t_m = 0
            if t_m > 60:
                t_h, t_m = divmod(t_m, 60)
            else:
                t_h = 0
            if t_h > 0:
                message += f"{t_h}时"
            if t_m > 0:
                message += f"{t_m}分"
            message += f"{t_s}秒才能移动哦"

            return_data["code"] = 1
            return_data["message"] = message
        elif type(direction) is str:
            return_data["code"] = 1
            return_data["message"] = direction
        elif user_data["energy"] < direction[1]:
            return_data["code"] = 1
            return_data["message"] = "体力不够哦，等体力恢复再出发吧"
        elif direction[1] > 6:
            return_data["code"] = 1
            return_data["message"] = "太远啦，一次只能移动6格哦"
        else:
            user_data["energy"] -= direction[1]
            save_member_data = True
            save_member_coordinates = True

            # 移动
            if direction[0] == "前":
                user_coordinates = (user_coordinates[0], user_coordinates[1] + direction[1])
            elif direction[0] == "后":
                user_coordinates = (user_coordinates[0], user_coordinates[1] - direction[1])
            elif direction[0] == "左":
                user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1])
            elif direction[0] == "右":
                user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1])
            elif direction[0] == "左前":
                user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1] + direction[1])
            elif direction[0] == "左后":
                user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1] - direction[1])
            elif direction[0] == "右前":
                user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1] + direction[1])
            elif direction[0] == "右后":
                user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1] - direction[1])

            # 判断超出边界
            if not 0 <= user_coordinates[0] <= 3000 or not 0 <= user_coordinates[1] <= 3000:
                # 超出了边界，撤回修改
                user_data["energy"] += direction[1]
                if direction[0] == "前":
                    user_coordinates = (user_coordinates[0], user_coordinates[1] - direction[1])
                elif direction[0] == "后":
                    user_coordinates = (user_coordinates[0], user_coordinates[1] + direction[1])
                elif direction[0] == "左":
                    user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1])
                elif direction[0] == "右":
                    user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1])
                elif direction[0] == "左前":
                    user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1] - direction[1])
                elif direction[0] == "左后":
                    user_coordinates = (user_coordinates[0] + direction[1], user_coordinates[1] + direction[1])
                elif direction[0] == "右前":
                    user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1] - direction[1])
                elif direction[0] == "右后":
                    user_coordinates = (user_coordinates[0] - direction[1], user_coordinates[1] + direction[1])

                return_data["code"] = 1
                return_data["message"] = "不能前进啦，前面走不通啦"
            else:
                # 判断事件
                data = await load_event(
                    user_data=user_data,
                    coordinates_real=user_coordinates,
                    time_h=time_h,
                    time_now=time_now,
                    user_id=user_id)
                user_data = data["user_data"]
                for n in data["news"]:
                    news.append(n)

                # 返回内容
                return_data["code"] = 2
                return_data["returnpath"] = await draw()
    elif command in ["使用", "道具列表"]:
        if command2 is None:
            draw_data = {"title": "道具列表", "datas": []}
            if len(user_data["backpack"]["prop"]) == 0:
                return_data["code"] = 1
                return_data["message"] = "背包中还没物品啦"
            else:
                item_list = []
                for decorate_id in user_data["backpack"]["prop"]:
                    item_list.append({
                        "image": await get_image_path(f"adventure-prop_{decorate_id}.png"),
                        "title": prop_datas[decorate_id]["name"],
                        "message": user_data["backpack"]["prop"][decorate_id]["number"]
                    })
                    draw_data["datas"].append({
                        "title": prop_datas[decorate_id]["name"],
                        "message": prop_datas[decorate_id]["message"]
                    })
                # draw_data["datas"] = item_list
                return_data["returnpath"] = await draw_menu(draw_data, item_list=item_list)
                return_data["code"] = 2
        else:
            command, command2 = get_command(command2, return_none=True)

            while True:
                prop_id = None
                for p_id in prop_datas:
                    if command == prop_datas[p_id]["name"]:
                        prop_id = p_id
                if prop_id is None:
                    return_data["code"] = 1
                    return_data["message"] = "没有找到这个道具哦，请检查道具名称。\n例：“/水母探险 使用 地图”"
                elif prop_id not in user_data["backpack"]["prop"].keys():
                    return_data["code"] = 1
                    return_data["message"] = "背包没有这个道具啦"
                else:
                    if prop_id not in ["p1", "p3", "p7", "p8", "p12"]:
                        break
                    if prop_id == "p1":
                        if command2 is None:
                            return_data["code"] = 1
                            return_data["message"] = "请添加要传送的坐标。\n例：“/水母探险 使用 传送卡 11,22”"
                            break
                        "".split()
                        replace_list = [", ", "， ", ". ", "  ", " ,", " ，", " .", ",", "，", ".", " "]
                        for r in replace_list:
                            command2 = command2.replace(r, ",")

                        if "," in command2:
                            coordinate = command2.split(",")
                        elif "，" in command2:
                            coordinate = command2.split("，")
                        elif "." in command2:
                            coordinate = command2.split(".")
                        elif "。" in command2:
                            coordinate = command2.split("。")
                        elif " " in command2:
                            coordinate = command2.split(" ")
                        else:
                            coordinate = []
                        if len(coordinate) == 1:
                            return_data["code"] = 1
                            return_data["message"] = '坐标设置失败，请使用","分割坐标\n例：“/水母探险 使用 传送卡 11,22”'
                            break
                        try:
                            new_coordinates = [int(coordinate[0]), int(coordinate[1])]
                        except:
                            return_data["code"] = 1
                            return_data["message"] = "传送失败，请检查坐标内容"
                            break

                        # 保存坐标
                        user_coordinates = new_coordinates
                        save_member_coordinates = True
                        return_data["code"] = 1
                        return_data["message"] = "传送成功"
                    elif prop_id in ["p3", "p12"]:
                        return_data["code"] = 1
                        return_data["message"] = "道具不能使用啦"
                        break
                    elif prop_id == "p7":
                        map_data = await load_map_data(
                            coordinates_real=user_coordinates,
                            self_id=user_id,
                            time_now=time_now,
                            event_history=user_data["event_history"],
                            coordinates_relative=[-4, -3, -2, -1, 0, 1, 2, 3, 4]
                        )
                        map_image = await draw_map_2d(map_data, view_occlusion=False)
                        map_info_image = await draw_map_inside(map_data)
                        map_image.alpha_composite(map_info_image, (0, 0))

                        return_data["code"] = 2
                        return_data["returnpath"] = save_image(map_image)

                    elif prop_id == "p8":
                        map_data = await load_map_data(
                            coordinates_real=user_coordinates,
                            self_id=user_id,
                            time_now=time_now,
                            event_history=user_data["event_history"],
                            coordinates_relative=[
                                -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                        )
                        map_image = await draw_map_2d(map_data, view_occlusion=False)
                        map_info_image = await draw_map_inside(map_data)
                        map_image.alpha_composite(map_info_image, (0, 0))

                        return_data["code"] = 2
                        return_data["returnpath"] = save_image(map_image)

                    if prop_datas[prop_id]["type"] == "单次":
                        if user_data["backpack"]["prop"][prop_id]["number"] == 1:
                            user_data["backpack"]["prop"].pop(prop_id)
                        else:
                            user_data["backpack"]["prop"][prop_id]["number"] -= 1

                break
    elif command in ["装备", "卸下"]:
        if command2 is None:
            draw_data = {"title": "装饰物列表", "datas": []}
            for decorate_id in user_data["backpack"]["decorate"]:
                draw_data["datas"].append({
                    "image": None,
                    "title": decorate_datas[decorate_id]["name"],
                    "message": decorate_datas[decorate_id]["message"]
                })
            return_data["returnpath"] = await draw_menu(draw_data)
            return_data["code"] = 2
        else:
            decorate_id = None
            for decorate in decorate_datas:
                if decorate_datas[decorate]["name"] == command2:
                    decorate_id = decorate
                    break
            if decorate_id is None:
                return_data["code"] = 1
                return_data["message"] = "找不到这件物品哦，请检查物品名称"
            elif decorate_id not in user_data["backpack"]["decorate"].keys() and command == "装备":
                return_data["code"] = 1
                return_data["message"] = "背包中没有这件物品啦"
            else:
                if command == "装备":
                    if decorate_datas[decorate_id]["type"] in ["decorate", "frame"]:
                        user_data["profile"]["decorate"][decorate_datas[decorate_id]["type"]].append({
                            "id": decorate_id,
                        })
                        return_data["code"] = 1
                        return_data["message"] = "装备成功"
                    else:
                        raise "意外类型decorate_datas[decorate_id]['type']"
                else:
                    success = False
                    new_list = []
                    for decorate in user_data["profile"]["decorate"]["decorate"]:
                        if decorate["id"] == decorate_id:
                            success = True
                            continue
                        new_list.append(decorate)
                    user_data["profile"]["decorate"]["decorate"] = new_list
                    if success is False:
                        new_list = []
                        for decorate in user_data["profile"]["decorate"]["frame"]:
                            if decorate["id"] == decorate_id:
                                success = True
                                continue
                            new_list.append(decorate)
                        user_data["profile"]["decorate"]["frame"] = new_list

                    if success is True:
                        return_data["code"] = 1
                        return_data["message"] = "卸下成功"
                    else:
                        return_data["code"] = 1
                        return_data["message"] = "物品没有装备起来哦"
    elif command == "道具图鉴":
        draw_data = {"title": "道具图鉴", "datas": []}
        for prop_id in prop_datas.keys():
            draw_data["datas"].append({
                "image": None,
                "title": prop_datas[prop_id]["name"],
                "message": prop_datas[prop_id]["message"]
            })
        return_data["returnpath"] = await draw_menu(draw_data)
        return_data["code"] = 2
    elif command == "装饰":
        pass
    elif command == "生成地图":
        path = save_image(await create_map())
        logger.info(f"地图图片：{path}")
    elif command == "帮助":
        draw_data = {"title": "指令列表", "datas": []}
        draw_data["datas"].append({"title": "/水母探险 出发", "message": "向前移动"})
        draw_data["datas"].append({"title": "/水母探险 出发 东2", "message": "向东边移动2格"})
        draw_data["datas"].append({"title": "/水母探险 装备", "message": "展示拥有的装饰品"})
        draw_data["datas"].append({"title": "/水母探险 装备 物品名称", "message": "将装饰品装备起来"})
        draw_data["datas"].append({"title": "/水母探险 卸下 物品名称", "message": "卸下装饰品"})
        draw_data["datas"].append({"title": "/水母探险 道具图鉴", "message": "查看道具图鉴"})
        # draw_data["datas"].append({"title": "/水母探险 装饰", "message": "1111111"})
        draw_data["datas"].append({"title": "/水母探险 道具列表", "message": "展示拥有的道具"})
        draw_data["datas"].append({"title": "/水母探险 使用 道具名称", "message": "使用道具"})
        return_data["returnpath"] = await draw_menu(draw_data)
        return_data["code"] = 2

    if save_member_coordinates is True:
        # 写入用户坐标
        read_db(
            db_path=f"{basepath}db/plugin_adventure_map-2411.db",
            sql_text=f'replace into user_map(user_id,coordinates_x,coordinates_y,user_name) '
                     f'values("{user_id}","{user_coordinates[0]}","{user_coordinates[1]}",'
                     f'"{text_to_b64(user_name)}")',
            table_name="user_map",
            select_all=False
        )
    if save_member_data is True:
        # 写入用户数据
        save_data = text_to_b64(json.dumps(user_data))
        read_db(
            db_path="{basepath}db/plugin_data.db",
            sql_text=f"replace into adventure('user_id','data') values('{user_id}','{save_data}')",
            table_name="adventure",
            select_all=False
        )
    return return_data


def get_direction(text: str):
    direction: list[None | str | int] = [None, None]

    text = text.lower()
    replace_list = {
        "前": "北上w",
        "后": "南下s",
        "左": "西la",
        "右": "东rd",
    }
    if "-" in text and text.split("-", 1)[1][0:1] in num_list:
        text = text.replace("前", "s")
    for d1 in replace_list.keys():
        for d2 in replace_list[d1]:
            text = text.replace(d2, d1)
    direction_list = []
    for d1 in replace_list.keys():
        if d1 in text:
            direction_list.append(d1)
    if not direction_list:
        direction[0] = "前"
    else:
        if "前" in direction_list and "后" in direction_list:
            return "不能同时前进和后退啦"
        if "左" in direction_list and "右" in direction_list:
            return "不能同时向两边走啦"
        direction[0] = ""
        for d in direction_list:
            direction[0] += d

    have_num = False
    for num in num_list:
        if num in text:
            have_num = True
            break
    if have_num is False:
        direction[1] = 1
    else:
        num = ""
        is_num = False
        for t in text:
            if is_num is True and t not in num_list:
                break
            elif is_num is False and t in num_list:
                num += t
            else:
                continue
        direction[1] = int(num)

    if direction[0] is None or direction[1] is None:
        logger.error("前进方向判断失败")
        logger.error(text)
        logger.error(direction)
        raise "前进方向判断失败"
    return direction


async def load_map_data(
        coordinates_real: tuple[int, int],
        self_id: str = None,
        time_now: int = time.time(),
        event_history=None,
        coordinates_relative: list = None
):
    """
    读取坐标附近的地图数据
    :param coordinates_real:要加载的坐标以及附近的地图
    :param self_id: 目前用户id
    :param time_now:
    :param event_history: 用户已发生的事件列表
    :param coordinates_relative: 要读取的相对位置
    :return:
    """
    # 读取缓存数据
    if event_history is None:
        event_history = []
    if coordinates_relative is None:
        add_list = [-3, -2, -1, 0, 1, 2, 3]
    else:
        add_list = coordinates_relative
    if coordinates_real in kn_cache["plugin_adventure"]["map_data"].keys():
        if time_now - kn_cache["plugin_adventure"]["map_data"][coordinates_real]["t"] > 60:
            return kn_cache["plugin_adventure"]["map_data"][coordinates_real]["d"]

    x, y = coordinates_real
    map_data: map_data_type = {}
    default_map_data = {"pattern": "grass", "is_margin": False, "inside": []}  # 不要用.update()优化代码，或改深复制

    conn = sqlite3.connect(f"{basepath}db/plugin_adventure_map-2411.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
    try:
        for ax in add_list:
            for ay in add_list:
                coordinates_table = f"map-{int(int(x + ax) / 100)}_{int(int(y + ay) / 100)}"
                if coordinates_table not in tables:
                    cursor.execute(
                        f'create table "{coordinates_table}"(coordinates VARCHAR, pattern VARCHAR, inside VARCHAR)')
                    tables.append(coordinates_table)

                cursor.execute(f"SELECT * FROM '{coordinates_table}' WHERE coordinates='{x + ax}_{y + ay}'")
                data = cursor.fetchone()
                if data is not None:
                    inside_text = data[2]
                    inside_list = []
                    if inside_text is not None and inside_text != "":
                        inside_text = inside_text.split(",")
                        for inside in inside_text:
                            insides = inside.split(".")
                            inside_list.append({"type": insides[0], "id": insides[1]})

                    map_data[f"{ax}_{ay}"] = {"pattern": data[1], "inside": inside_list}
                else:
                    map_data[f"{ax}_{ay}"] = {"pattern": "grass", "inside": []}
                if -1 < x + ax < 3000 and -1 < y + ay < 3000:
                    map_data[f"{ax}_{ay}"]["is_margin"] = False
                else:
                    map_data[f"{ax}_{ay}"]["is_margin"] = True
                    map_data[f"{ax}_{ay}"]["pattern"] = "dirt"
                if "inside" not in map_data[f"{ax}_{ay}"].keys():
                    map_data[f"{ax}_{ay}"]["inside"] = default_map_data["inside"]
                if "pattern" not in map_data[f"{ax}_{ay}"].keys():
                    map_data[f"{ax}_{ay}"]["pattern"] = default_map_data["pattern"]
                if not -2 <= ax <= 2 and not -2 <= ay <= 2 and coordinates_relative is None:
                    # 隐藏视线外坐标
                    map_data[f"{ax}_{ay}"]["inside"] = []
                new_inside = []
                for inside in map_data[f"{ax}_{ay}"]["inside"]:
                    if f"{x + ax}_{y + ay}-{inside['id']}" not in event_history:
                        new_inside.append(inside)

    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        raise "地图数据读取出错"
    finally:
        cursor.close()
        conn.close()

    user_map = await load_user_map(coordinates=coordinates_real, self_id=self_id)
    for coordinates_local in map_data.keys():
        c_x, c_y = [int(n) for n in coordinates_local.split("_", 1)]
        c_x += x
        c_y += y
        coordinates_real = f"{c_x}_{c_y}"
        if coordinates_real in user_map.keys():
            for user_data in user_map[coordinates_real]:
                map_data[coordinates_local]["inside"].append({
                    "type": "user",
                    "user_id": user_data[0],
                    "user_name": user_data[1],
                    "user_face": "{basepath}" + f"file/user_face/{user_data[0]}.png"
                })
    kn_cache["plugin_adventure"]["map_data"][coordinates_real] = {"t": time_now, "d": map_data}
    logger.debug(map_data)
    return map_data


async def load_user_map(coordinates: tuple[int, int] = None, self_id: str = None, time_now: int = time.time()):
    """
    读取坐标附近的地图数据
    :param time_now:
    :param coordinates:查询的坐标，如果为None则查询全部坐标
    :param self_id:目前用户的id，用户排除自己的坐标
    :return:{"coordinates": ["user_id"]}
    """
    # 读取缓存数据
    if coordinates in kn_cache["plugin_adventure"]["map_data"].keys():
        if time_now - kn_cache["plugin_adventure"]["map_data"][coordinates]["t"] > 60:
            return kn_cache["plugin_adventure"]["map_data"][coordinates]["d"]

    # 读取用户坐标
    datas = read_db(
        db_path=f"{basepath}db/plugin_adventure_map-2411.db",
        sql_text=f'SELECT * FROM "user_map"',
        table_name="user_map",
        select_all=True
    )

    user_map_data = {}
    for data in datas:
        # 跳过目前用户的坐标
        if self_id == data[0]:
            continue
        # 如果指定查找坐标，则只返回对应坐标附近用户
        if coordinates is not None:
            if not coordinates[0] - 4 < data[1] < coordinates[0] + 4:
                continue
            if not coordinates[1] - 4 < data[2] < coordinates[1] + 4:
                continue
        if f"{data[1]}_{data[2]}" not in user_map_data.keys():
            user_map_data[f"{data[1]}_{data[2]}"] = []
        user_map_data[f"{data[1]}_{data[2]}"].append([data[0], b64_to_text(data[3])])
    kn_cache["plugin_adventure"]["user_map"][coordinates] = {"t": time_now, "d": user_map_data}
    return user_map_data


async def load_event(
        user_data: dict,
        coordinates_real: tuple[int, int],
        time_h: int,
        time_now: int,
        user_id: str):
    map_data = await load_map_data(coordinates_real, event_history=user_data["event_history"])
    adventure_game_datas = await _adventure_datas()  # 插件数据
    event_datas = adventure_game_datas["event_datas"]  # 所有事件
    npc_datas = adventure_game_datas["npc_datas"]  # 所有npc数据
    prop_datas = adventure_game_datas["prop_datas"]  # 所有道具
    map_event_list = map_data["0_0"]["inside"]
    logger.debug(f"map_event_list:{map_event_list}")
    news = []
    # 检测npc
    for data in map_event_list:
        if data["type"] != "npc":
            continue
        logger.debug(f"添加{data}")
        npc_id = data["id"]
        s_time = npc_datas[npc_id]['appearance_time'].split("-", 1)
        if not int(s_time[0]) < time_h < int(s_time[1]):
            continue
        is_new = False
        npc_event_id = f"{coordinates_real[0]}_{coordinates_real[1]}-{npc_id}-{int(time_now / 259200)}"
        if npc_event_id not in user_data["event_history"]:
            user_data["event_history"].append(npc_event_id)
            is_new = True
        if is_new is False:
            continue

        if npc_datas[npc_id]["type"] == "敌人":
            if is_new is True:
                if npc_datas[npc_id]["hp"] > user_data["energy"]:
                    user_data["energy"] = 0
                    news.append({"title": f"被{npc_datas[npc_id]['name']}打倒啦", "message": "QaQ"})
                else:
                    user_data["energy"] -= npc_datas[npc_id]["hp"]

                    __code, message, __returnpath = await plugin_checkin(
                        user_id=user_id, modified=npc_datas[npc_id]["hp"])
                    if message.startswith("成功-"):
                        pass
                    elif message.startswith("薯条数量不够-"):
                        pass
                    else:
                        raise f"水母冒险返回意外情况，{message}"
                    news.append({
                        "title": f"打败了{npc_datas[npc_id]['name']}",
                        "message": f"获得了{npc_datas[npc_id]['hp']}根薯条"})
        else:
            if npc_id == "n3":
                news.append({"title": "咕咕咕？", "message": "咕咕咕！"})
    # 发生事件
    for data in map_event_list:
        if data["type"] != "event":
            continue
        logger.debug(f"添加{data}")
        event_id = data["id"]
        event_name = event_datas[event_id]["name"]
        event_message = event_datas[event_id]["message"]
        is_event = False
        if event_datas[event_id]["type"] == "单次":
            if f"event_{event_id}" not in user_data["event_history"]:
                user_data["event_history"].append(f"event_{event_id}")
                is_event = True
        elif event_datas[event_id]["type"] == "永久":
            is_event = True
        elif event_datas[event_id]["type"].endswith("天"):
            day_num = int(event_datas[event_id]["type"].removesuffix("天"))
            event_text = f"event_{event_id}_{int(time_now / 86400 / day_num)}"
            if event_text not in user_data["event_history"]:
                user_data["event_history"].append(event_text)
                is_event = True

        if is_event is True:
            # 事件分类：自动添加
            if event_id in ["e1", "e5", "e6", "e9", "e10", "e13", "e14", "e15"]:
                for prop_id in event_datas[event_id]["prop_list"]:
                    if prop_id in user_data["backpack"]["prop"].keys():
                        is_event = False
                        break
                for prop_id in event_datas[event_id]["decorate_list"]:
                    if prop_id in user_data["backpack"]["decorate"].keys():
                        is_event = False
                        break
                if is_event is False:
                    continue
                news.append({"title": event_name, "message": event_message})

            # 事件分类：获取道具
            if event_id == ["e2", "e11"]:
                choose_prop = random.choice(event_datas[event_id]["prop_list"])
                if choose_prop in user_data["backpack"]["prop"].keys():
                    user_data["backpack"]["prop"][choose_prop]["number"] += 1
                else:
                    user_data["backpack"]["prop"][choose_prop] = {"number": 1}
                news.append({"title": event_name, "message": event_message})

            # 事件分类：获取装饰
            elif event_id == ["e7", "e8", "e12"]:
                if event_datas[event_id]["decorate_list"][0] not in user_data["backpack"]["decorate"].keys():
                    news.append({"title": event_name, "message": event_message})

            # 事件分类：无
            if event_id == "e4":
                if is_event is True:
                    choose_list = [
                        {"title": "星占水母", "message": "挥舞蕴含宇宙奥秘的...魔法日记？好像不太对"},
                        {"title": "星占水母", "message": "咒语...是什么来着？我得好好查一下"},
                        {"title": "星占水母", "message": "水晶球摆这个地方会很好看。不对，应该是这边"},
                        {"title": "星占水母", "message": "今天水晶球的的颜色好像不太一样？"},
                    ]
                    news.append(random.choice(choose_list))
                else:
                    choose_list = [
                        {"title": "星占水母", "message": "挥舞蕴含宇宙奥秘的...魔法日记？好像不太对"},
                        {"title": "星占水母", "message": "咒语...是什么来着？我得好好查一下"},
                        {"title": "星占水母", "message": "水晶球摆这个地方会很好看。不对，应该是这边"},
                        {"title": "星占水母", "message": "今天水晶球的的颜色好像不太一样？"},
                    ]
                    news.append(random.choice(choose_list))

            if is_event is True:
                # 添加睡眠时间
                user_data["sleep_time"] = time_now + event_datas[event_id]["event_sleep_time"]
                # 添加薯条
                if event_datas[event_id]["add_point"] != 0:
                    __code, message, __returnpath = await plugin_checkin(
                        user_id=user_id, modified=event_datas[event_id]["add_point"])
                    if message.startswith("成功-"):
                        pass
                    elif message.startswith("薯条数量不够-"):
                        pass
                    else:
                        raise f"水母冒险返回意外情况，{message}"
                # 添加体力
                if event_datas[event_id]["add_energy"] != 0:
                    user_data["energy"] += event_datas[event_id]["add_energy"]
                    if user_data["energy"] < 0:
                        user_data["energy"] = 0

    logger.debug({"news": news})
    return {"user_data": user_data, "news": news}


async def draw_main(
        map_data: map_data_type,
        user_name: str,
        news: list = None,
        command_prompt_list: list = None,
        user_coordinates: tuple[int, int] = None,
        user_energy: int | float = None,
        user_profile: dict = None,
        time_now: int = int(time.time()),
        event_history=None
):
    if event_history is None:
        event_history = []
    image = Image.new("RGB", (2400, 1300), a_color("背景"))
    image = image.convert("RGBA")

    # 粘贴地图
    paste_image = Image.new("RGB", (1210, 1210), a_color("地图描边"))
    paste_image = circle_corner(paste_image, 80)
    paste_image = paste_image.convert("RGBA")
    image.alpha_composite(paste_image, (45, 45))
    paste_image = await draw_map(
        map_data=map_data,
        user_profile=user_profile,
        coordinates_real=user_coordinates,
        time_now=time_now,
        event_history=event_history)
    paste_image = circle_corner(paste_image, 60)
    image.alpha_composite(paste_image, (65, 65))

    # 粘贴个人信息
    paste_image = Image.new("RGBA", (1068, 262), a_color("信息面板背景"))
    paste_image = circle_corner(paste_image, 19)
    image.alpha_composite(paste_image, (1300, 33))
    font_path = await get_file_path("峰广明锐体.ttf")
    paste_image = await draw_text("水母探险", size=170, text_color=a_color("背景大字"), fontfile=font_path)
    image.alpha_composite(paste_image, (1688, 37))
    font_path = await get_file_path("SourceHanSansK-Medium.ttf")
    paste_image = await draw_text(user_name, size=150, text_color=a_color("用户名称"), fontfile=font_path)
    image.alpha_composite(paste_image, (1320, 141))

    # 粘贴消息列表
    paste_image = Image.new("RGBA", (1068, 895), a_color("内容面板背景"))

    image.alpha_composite(paste_image, (1300, 340))
    x, y = (1300, 340)
    if news:
        font_path = await get_file_path("SourceHanSansK-Medium.ttf")
        paste_image = await draw_text("事件列表", size=72, text_color=a_color("事件标题"), fontfile=font_path)
        image.alpha_composite(paste_image, (x + 16, y + 12))
        y += 80
        for new in news:
            text = f"{new['title']}: {new['message']}"
            paste_image = await draw_text(text, size=48, text_color=a_color("事件内容"), fontfile=font_path)
            image.alpha_composite(paste_image, (x + 16, y + 12))
            y += paste_image.size[1] + 10

    if command_prompt_list:
        font_path = await get_file_path("SourceHanSansK-Medium.ttf")
        paste_image = await draw_text("指令提示", size=72, text_color=a_color("事件标题"), fontfile=font_path)
        image.alpha_composite(paste_image, (x + 16, y + 12))
        y += 80
        for new in command_prompt_list:
            text = f"{new['title']}: {new['message']}"
            paste_image = await draw_text(text, size=48, text_color=a_color("事件内容"), fontfile=font_path)
            image.alpha_composite(paste_image, (x + 16, y + 12))
            y += 60

    # 粘贴地图前面板
    if True:
        info_image = Image.new("RGBA", (1170, 1170), (0, 0, 0, 0))
        # 粘贴坐标
        paste_image = Image.new("RGBA", (410, 70), a_color("地图坐标"))
        paste_image = circle_corner(paste_image, 13)
        info_image.alpha_composite(paste_image, (33, 1062))

        paste_image = await draw_text(
            f"({user_coordinates[0]}, {user_coordinates[1]})", size=48
        )
        info_image.alpha_composite(paste_image, (45, 1069))

        # 粘贴血量
        # x, y = (1082, 1018)
        # paste_image = await get_image_path(f"adventure-info_blood.png")
        # paste_image = await load_image(paste_image)
        # paste_image = paste_image.resize((70, 70))
        # num = user_energy
        # while num > 1:
        #     num -= 1
        #     info_image.alpha_composite(paste_image, (x, y))
        #     x -= 50

        # 粘贴体力
        x, y = (1082, 1097)
        paste_image = await get_image_path(f"adventure-info_energy.png")
        paste_image = await load_image(paste_image)
        paste_image = paste_image.resize((70, 70))
        num = user_energy
        while num > 1:
            num -= 1
            info_image.alpha_composite(paste_image, (x, y))
            x -= 50

        # info_image = circle_corner(info_image, 60)
        image.alpha_composite(info_image, (65, 65))
    pass

    return save_image(image)


async def draw_map(
        map_data: map_data_type,
        size: tuple[int, int] = (1170, 1170),
        coordinates_real: tuple[int, int] | list[int, int] = None,
        user_profile: dict = None,
        time_now: int = int(time.time()),
        event_history=None
):
    """

    :param map_data: 地图数据
    :param size: 绘制的图片大小
    :param coordinates_real: 用户实际坐标
    :param user_profile: 用户信息
    :param time_now: 现在时间
    :param event_history: 用户已经发生的事件列表
    :return:
    """
    if event_history is None:
        event_history = []
    image = Image.new("RGBA", size, a_color("地图底色"))
    # 绘制地图
    paste_image = await draw_map_2d(map_data=map_data, size=(size[0] * 2, size[1] * 2))
    paste_image = paste_image.resize(size)
    # 将2d地图转伪2.5d
    paste_image = transform_to_trapezoid(paste_image, 1, 1.3)
    # paste_image = paste_image.resize((paste_image.size[0], int(paste_image.size[1] / 3)))
    # image.alpha_composite(paste_image, (0, int(paste_image.size[1] * 2)))
    image.alpha_composite(paste_image, (0, 0))

    coordinates_y = [83, 250, 417, 584, 750, 917, 1084]
    transform_coordinates_data = {
        "3": [72, 243, 413, 584, 755, 925, 1096],
        "2": [50, 228, 406, 584, 762, 940, 1118],
        "1": [24, 211, 397, 584, 771, 957, 1144],
        "0": [-6, 192, 387, 584, 781, 976, 1174],
        "-1": [-40, 171, 377, 584, 791, 997, 1212],
        "-2": [-78, 148, 366, 584, 802, 1020, 1252],
        "-3": [-118, 122, 353, 584, 815, 1046, 1292],
    }
    # 添加场景物品
    for coordinates in list(map_data.keys())[::-1]:
        member_num = 0
        if coordinates == "0_0":
            member_num += 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "map":
                continue
            member_num += 1

    # 添加建筑
    for coordinates in list(map_data.keys())[::-1]:
        member_num = 0
        if coordinates == "0_0":
            member_num += 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "buliding":
                continue
            member_num += 1
            paste_image = await get_image_path(f"adventure-{data['id']}.png")
            paste_image = await load_image(paste_image)

            c_x, c_y = map(int, coordinates.split("_", 1))

            if not -2 <= c_x <= 2 or not -2 <= c_y <= 2:
                paste_none = Image.new("RGBA", paste_image.size, (0, 0, 0, 0))
                paste_dark = Image.new("RGBA", paste_image.size, (0, 0, 0, 50))
                paste_none.paste(paste_dark, (0, 0), mask=paste_image)
                paste_image.paste(paste_none, (0, 0), mask=paste_none)

            image.alpha_composite(paste_image, (
                (transform_coordinates_data[str(c_y)][c_x + 3] - 200),
                (coordinates_y[-c_y + 3] - 600 + 100 + 100)
            ))  # x:实际绘制坐标-一半宽度 y:实际绘制坐标-图片长度+定位点转为框底+图片预留底部

    # 添加其他用户
    for coordinates in list(map_data.keys())[::-1]:
        member_num = 0
        if coordinates == "0_0":
            member_num += 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "user":
                continue
            member_num += 1
            c_x, c_y = map(int, coordinates.split("_", 1))
            paste_image = await get_image_path(f"adventure-user_member_default.png")
            paste_image = await load_image(paste_image)
            # 粘贴头像
            try:
                paste_face = await load_image(data["user_face"])
                paste_face = paste_face.resize((149, 149)).convert("RGBA")
                paste_face = circle_corner(paste_face, 15)
                paste_image.alpha_composite(paste_face, (26, 108))
            except Exception as e:
                logger.warning(f"加载用户头像出错：{data['user_face']}")
            # 粘贴名称
            paste_text = await draw_text(data["user_name"], size=18, text_color=a_color("其他用户名称"))
            paste_image.alpha_composite(paste_text, (43, 78))

            add_member_coordinates = -(member_num - 1) * 10
            image.alpha_composite(paste_image, (
                (transform_coordinates_data[str(c_y)][c_x + 3] + add_member_coordinates - int(paste_image.size[0] / 2)),
                (coordinates_y[-c_y + 3] + add_member_coordinates - paste_image.size[1])
            ))

    # 添加npc
    for coordinates in list(map_data.keys())[::-1]:
        member_num = 0
        if coordinates == "0_0":
            member_num += 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "npc":
                continue
            member_num += 1
            paste_image = await get_image_path(f"adventure-{data['id']}.png")
            paste_image = await load_image(paste_image)
            c_x, c_y = map(int, coordinates.split("_", 1))

            npc_event_id = f"{coordinates_real[0] + c_x}_{coordinates_real[1] + c_y}-{data['id']}-{int(time_now / 259200)}"
            if npc_event_id in event_history:
                paste_none = Image.new("RGBA", paste_image.size, (0, 0, 0, 0))
                paste_dark = Image.new("RGBA", paste_image.size, (0, 0, 0, 150))
                paste_none.paste(paste_dark, (0, 0), mask=paste_image)
                paste_image.paste(paste_none, (0, 0), mask=paste_none)

            image.alpha_composite(paste_image, (
                (transform_coordinates_data[str(c_y)][c_x + 3] - 200),
                (coordinates_y[-c_y + 3] - 600 + 100 + 100)
            ))  # x:实际绘制坐标-一半宽度 y:实际绘制坐标-图片长度+定位点转为框底+图片预留底部

    if user_profile['main']['type'] == "card":
        paste_coordinates = (484, 234)
        user_image = await get_image_path(f"adventure-user_card_default.png")
        user_image = await load_image(user_image)
        image.alpha_composite(user_image, (
            paste_coordinates[0],
            paste_coordinates[1]))
        if user_profile['main']['id'] != "default":
            paste_image = await get_image_path(f"adventure-user_card_{user_profile['main']['id']}.png")
            paste_image = await load_image(paste_image)
            paste_image = circle_corner(paste_image, 15)
            image.alpha_composite(paste_image, (
                (paste_coordinates[0] + 24),
                paste_coordinates[1] + 59))

        if user_profile['decorate']['frame']:
            for frame in user_profile['decorate']['frame']:
                paste_image = await get_image_path(f"adventure-user_frame_{frame['id']}.png")
                paste_image = await load_image(paste_image)
                image.alpha_composite(paste_image, (
                    paste_coordinates[0],
                    paste_coordinates[1]))

        if user_profile['decorate']['decorate']:
            for decorate in user_profile['decorate']['decorate']:
                paste_image = await get_image_path(f"adventure-user_decorate_{decorate['id']}.png")
                paste_image = await load_image(paste_image)
                image.alpha_composite(paste_image, (
                    (paste_coordinates[0] - 25),
                    paste_coordinates[1] + 6))

    elif user_profile['main']['type'] == "avatar":
        paste_coordinates = (484, 284)
        user_image = await get_image_path(f"adventure-user_{user_profile['main']['type']}_default.png")
        user_image = await load_image(user_image)
        image.alpha_composite(user_image, (
            paste_coordinates[0],
            paste_coordinates[1]))
        if user_profile['main']['id'] != "default":
            try:
                paste_image = await load_image("{basepath}file/user_face/" + f"{user_profile['main']['id']}.png")
                paste_image = paste_image.resize((155, 155))
            except:
                paste_image = Image.new("RGBA", (155, 155), "#000000")
            paste_image = circle_corner(paste_image, 15)
            image.alpha_composite(paste_image, (
                (paste_coordinates[0] + 24),
                paste_coordinates[1] + 59 + 47))

        if user_profile['decorate']['frame']:
            for frame in user_profile['decorate']['frame']:
                paste_image = await get_image_path(
                    f"adventure-user_frame_{user_profile['main']['type']}_{frame['id']}.png")
                paste_image = await load_image(paste_image)
                image.alpha_composite(paste_image, (
                    paste_coordinates[0],
                    paste_coordinates[1]))

        if user_profile['decorate']['decorate']:
            for decorate in user_profile['decorate']['decorate']:
                paste_image = await get_image_path(f"adventure-user_decorate_{decorate['id']}.png")
                paste_image = await load_image(paste_image)
                image.alpha_composite(paste_image, (
                    (paste_coordinates[0] - 25), paste_coordinates[1] + 6 + 47))

    else:
        logger.error("意外绘制类型 def draw_map()")

    return image


def transform_to_trapezoid(image, top_width_ratio: int | float = None, bottom_width_ratio: int | float = None):
    """
    将矩形图片转换为梯形。
    :param image: PIL Image对象，原始矩形图片
    :param top_width_ratio: 顶部宽度比例
    :param bottom_width_ratio: 底部宽度比例
    :return: 转换后的梯形图片
    """
    # 原始图片的尺寸
    original_width, original_height = image.size

    # 计算梯形的顶部和底部宽度
    if top_width_ratio is None:
        top_width_ratio = 0.5
    top_width = original_width * top_width_ratio
    if bottom_width_ratio is None:
        bottom_width_ratio = 1
    bottom_width = original_width * bottom_width_ratio

    trapezoid_points_ = [
        -(original_width - top_width) / 2, 0,  # 左上角
        -(original_width - bottom_width) / 2, original_height,  # 左下角
        original_width + ((original_width - bottom_width) / 2), original_height,  # 右下角
        original_width + ((original_width - top_width) / 2), 0,  # 右上角
    ]
    # 转换梯形
    trapezoid = image.transform(
        (original_width, original_height),
        Image.QUAD,
        trapezoid_points_,
        Image.BILINEAR
    )
    return trapezoid


async def draw_map_2d(map_data: dict, size: tuple[int, int] = (1170, 1170), view_occlusion: bool = True):
    """
    绘制地图2D
    :param map_data: 地图数据
    :param size:绘制的尺寸
    :param view_occlusion: 是否绘制遮挡视野的阴影
    :return:
    """
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    logger.debug("计算尺寸")
    coordinates_list = []
    for coordinates in map_data.keys():
        x, y = map(int, coordinates.split("_", 1))
        if x not in coordinates_list:
            coordinates_list.append(x)
        if y not in coordinates_list:
            coordinates_list.append(y)
    image_num = len(coordinates_list)
    image_length = int(size[0] / image_num)
    logger.debug("读取图片")
    paste_margin_image = await get_image_path(f"adventure-is_margin.png")
    paste_margin_image = await load_image(paste_margin_image)
    paste_margin_image = paste_margin_image.resize((image_length, image_length))
    paste_hide_image = await get_image_path(f"adventure-is_hide.png")
    paste_hide_image = await load_image(paste_hide_image)
    paste_hide_image = paste_hide_image.resize((image_length, image_length))
    logger.debug("粘贴图片")
    x_num = -1
    loadding_image_name = ""
    loadding_image = None
    for coordinates_x in coordinates_list:
        if image_num > 30:
            logger.debug(f"正在粘贴{coordinates_x}")
        x_num += 1
        y_num = -1
        for coordinates_y in coordinates_list[::-1]:
            y_num += 1
            place_info = map_data[f"{coordinates_x}_{coordinates_y}"]
            if loadding_image_name != place_info['pattern']:
                image_path = await get_image_path(f"adventure-map_image_{place_info['pattern']}.png")
                paste_image = await load_image(image_path)
                loadding_image = paste_image
                loadding_image_name = place_info['pattern']
            else:
                paste_image = loadding_image
            paste_image = paste_image.resize((image_length, image_length))
            paste_image = paste_image.convert("RGBA")
            image.alpha_composite(paste_image, (x_num * image_length, y_num * image_length))
            if place_info["is_margin"] is True:
                image.alpha_composite(paste_margin_image, (x_num * image_length, y_num * image_length))
            elif (not -3 < coordinates_x < 3 or not -3 < coordinates_y < 3) and view_occlusion is True:
                image.alpha_composite(paste_hide_image, (x_num * image_length, y_num * image_length))

    return image


async def draw_map_inside(map_data: dict, size: tuple[int, int] = (1170, 1170), distortion=None):
    """
    绘制图片上的内容
    :param map_data: 地图数据
    :param size: 绘制的大小
    :param distortion:
    :return:
    """
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    # 计算要绘制的尺寸
    x_list = []
    y_list = []
    x_num_list = []
    y_num_list = []
    for coordinates in map_data.keys():
        x, y = coordinates.split("_")
        if x not in x_list:
            x_list.append(x)
            x_num_list.append(int(x))
        if y not in y_list:
            y_list.append(y)
            y_num_list.append(int(y))

    # 计算单格的尺寸
    x_image_len = int(size[0] / len(x_list))
    y_image_len = int(size[1] / len(y_list))
    x = int(x_image_len / 2)
    y = int(y_image_len / 2)
    deviation_position = int(0.008 * size[0])

    # 绘制内容
    # 添加建筑
    for coordinates in list(map_data.keys())[::-1]:
        c_x, c_y = map(int, coordinates.split("_", 1))
        member_num = -deviation_position
        if coordinates == "0_0":
            member_num += deviation_position * 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "buliding":
                continue
            member_num += deviation_position
            paste_image = await get_image_path(f"adventure-{data['id']}.png")
            paste_image = await load_image(paste_image)
            paste_image = paste_image.resize((2 * x_image_len, 3 * y_image_len))

            image.alpha_composite(paste_image, (
                int(x + (c_x + (len(x_list) / 2)) * x_image_len - (paste_image.size[0] * 0.5) - member_num),
                int(y + (-c_y - (len(x_list) / 2) + len(y_list)) * y_image_len - (paste_image.size[1] * 1) - member_num)
            ))

    # 添加其他用户
    for coordinates in list(map_data.keys())[::-1]:
        c_x, c_y = map(int, coordinates.split("_", 1))
        member_num = -deviation_position
        if coordinates == "0_0":
            member_num += deviation_position * 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "user":
                continue
            member_num += deviation_position
            paste_image = await get_image_path(f"adventure-user_member_default.png")
            paste_image = await load_image(paste_image)
            # 粘贴头像
            try:
                paste_face = await load_image(data["user_face"])
                paste_face = paste_face.resize((149, 149)).convert("RGBA")
                paste_face = circle_corner(paste_face, 15)
                paste_image.alpha_composite(paste_face, (26, 108))
            except Exception as e:
                logger.warning(f"加载用户头像出错：{data['user_face']}")
            # 粘贴名称
            paste_text = await draw_text(data["user_name"], size=18, text_color=a_color("其他用户名称"))
            paste_image.alpha_composite(paste_text, (43, 78))
            paste_image = paste_image.resize((1 * x_image_len, int(1.5 * y_image_len)))

            image.alpha_composite(paste_image, (
                x + int((c_x + (len(x_list) / 2)) * x_image_len - (paste_image.size[0] * 1)) - member_num,
                y + int((-c_y - (len(x_list) / 2) + len(y_list)) * y_image_len - (paste_image.size[1] * 0.5)) - member_num
            ))

    # 添加npc
    for coordinates in list(map_data.keys())[::-1]:
        c_x, c_y = map(int, coordinates.split("_", 1))
        member_num = -deviation_position
        if coordinates == "0_0":
            member_num += deviation_position * 2
        for data in map_data[coordinates]["inside"]:
            if data["type"] != "npc":
                continue
            member_num += deviation_position
            paste_image = await get_image_path(f"adventure-{data['id']}.png")
            paste_image = await load_image(paste_image)
            paste_image = paste_image.resize((2 * x_image_len, 3 * y_image_len))

            image.alpha_composite(paste_image, (
                x + int((c_x + (len(x_list) / 2)) * x_image_len - (paste_image.size[0] * 0.5)) - member_num,
                y + int((-c_y - (len(x_list) / 2) + len(y_list)) * y_image_len - (paste_image.size[1] * 1)) - member_num
            ))

    return image


async def draw_menu(draw_data: dict[str, str | list[dict]], item_list=None):
    """
    绘制一个列表，用于展示菜单或者图鉴
    :param draw_data:
    :param item_list:
    :return:
    """
    if item_list is None:
        item_list: list[dict[str, None | str | int]] = []
    font_shsk_M_path = await get_file_path("SourceHanSansK-Medium.ttf")
    if item_list:
        paste_item_image = await draw_item_list(item_list, calculate=False)
        item_y = paste_item_image.size[1]
    else:
        item_y = 0

    image_x = 900
    image_y = 200
    image_y += item_y
    for data in draw_data["datas"]:
        if "image" in data.keys() and data["image"] is not None:
            textlen = 16
        else:
            textlen = 20
        paste_image = await draw_text(
            data["title"] + data["message"],
            size=40,
            text_color=a_color("菜单文字"),
            fontfile=font_shsk_M_path,
            calculate=True,
            textlen=textlen
        )
        if paste_image.size[1] < 200 and "image" in data.keys() and data["image"] is not None:
            image_y += 200 + 10
        else:
            image_y += paste_image.size[1] + 10

    image = Image.new("RGBA", (image_x, image_y), a_color("菜单背景"))
    paste_image = await draw_text(
        draw_data["title"],
        size=60,
        text_color=a_color("菜单文字"),
        fontfile=font_shsk_M_path,
        calculate=False,
        textlen=20
    )
    image.alpha_composite(paste_image, (45, 30))

    x, y = 44, 104
    if item_list:
        draw_config = {
            "x_num": 7,
            "form_size": 116,
        }
        paste_item_image = await draw_item_list(item_list, _draw_config=draw_config)
        image.alpha_composite(paste_item_image, (x, y))
        y += paste_item_image.size[1] + 10

    for data in draw_data["datas"]:
        if "image" in data.keys() and data["image"] is not None:
            textlen = 16
        else:
            textlen = 20
        paste_image = await draw_text(
            f"{data['title']}: {data['message']}",
            size=40,
            text_color=a_color("菜单文字"),
            fontfile=font_shsk_M_path,
            calculate=False,
            textlen=textlen
        )
        if "image" in data.keys() and data["image"] is not None:
            image.alpha_composite(paste_image, (x + 210, y))

            paste_image = await load_image(data["image"])
            paste_image = paste_image.resize((200, 200))
            image.alpha_composite(paste_image, (x, y))
        else:
            image.alpha_composite(paste_image, (x, y))

        image.alpha_composite(paste_image, (x, y))
        y += paste_image.size[1] + 10

    return save_image(image)


async def draw_item_list(item_data: list[dict[str, str]], _draw_config: dict = None, calculate: bool = False):
    """
    绘制物品列表
    :param item_data: 内容数据
    :param _draw_config: 绘制配置
    :param calculate: 只计算尺寸不粘贴内容
    :return:
    """
    """
    item_data = [{"image": "path/image.png", "title": "名称", "message": "x123", }]
    """
    draw_config = {
        "draw_background": True,
        "x_num": 10,
        "form_size": 100.0,
    }

    if _draw_config is not None:
        for key in _draw_config.keys():
            draw_config[key] = _draw_config[key]

    font_shsk_M_path = await get_file_path("SourceHanSansK-Medium.ttf")

    # 自动计算格数
    if draw_config["x_num"] == 0:
        raise "未写自动计算格数"
    draw_config["y_num"], num = divmod(len(item_data), draw_config["x_num"])
    if num > 0:
        draw_config["y_num"] += 1

    x_size = draw_config["x_num"] * draw_config["form_size"]
    if draw_config["draw_background"] is True:
        image = Image.new("RGBA", (
            int(x_size), int(draw_config["y_num"] * draw_config["form_size"])), a_color("表格背景"))
        paste_image = Image.new(
            "RGBA",
            (int(draw_config["form_size"] * 0.9), int(draw_config["form_size"] * 0.9)),
            a_color("表格格子"))
        paste_image = circle_corner(paste_image, 10)
        for y_ in range(draw_config["y_num"]):
            for x_ in range(draw_config["x_num"]):
                paste_xy = [int(draw_config["form_size"] * x_), int(draw_config["form_size"] * y_)]
                image.alpha_composite(paste_image, (
                    paste_xy[0] + int(draw_config["form_size"] * 0.05),
                    paste_xy[1] + int(draw_config["form_size"] * 0.05)
                ))
    else:
        image = Image.new(
            "RGBA", (x_size, int(draw_config["y_num"] * draw_config["form_size"])), (0, 0, 0, 0))

    if calculate is True:
        return image
    x_num = -1
    y_num = 0
    frame_size = draw_config["form_size"] * 0.05
    title_size = draw_config["form_size"] * 0.15
    message_size = draw_config["form_size"] * 0.25
    for item in item_data:
        x_num += 1
        if x_num > draw_config["x_num"]:
            x_num = 0
            y_num += 1
        if "image" in item.keys() and item["image"] is not None:
            paste_image = await load_image(item["image"])
            paste_image = paste_image.resize((int(draw_config["form_size"]), int(draw_config["form_size"])))
            image.alpha_composite(paste_image, (
                int(x_num * draw_config["form_size"]), int(y_num * draw_config["form_size"])))
        if "title" in item.keys():
            paste_image = await draw_text(
                item["title"],
                size=title_size,
                text_color=a_color("菜单文字"),
                fontfile=font_shsk_M_path,
                textlen=5
            )
            image.alpha_composite(paste_image, (
                int(x_num * draw_config["form_size"] + frame_size),
                int((y_num + 1) * draw_config["form_size"] - paste_image.size[1] - frame_size)))

        if "message" in item.keys():
            paste_image = await draw_text(
                str(item["message"]),
                size=message_size,
                text_color=a_color("菜单文字"),
                fontfile=font_shsk_M_path
            )
            image.alpha_composite(paste_image, (
                int((x_num + 1) * draw_config["form_size"] - paste_image.size[0] - frame_size),
                int((y_num + 1) * draw_config["form_size"] - paste_image.size[1] - frame_size)))

    return image


async def create_map():
    """
    命令：生成地图
    :return: image
    """
    draw_map = True
    load_data_from_db = True
    save_to_db = False

    draw_add_x = 0
    draw_add_y = 0
    s = 100  # 0-3000
    map_size = [s, s]

    map_data = {}
    map_image = await load_image("./map_image.png")
    adventure_game_datas = await _adventure_datas()  # 插件数据
    event_datas = adventure_game_datas["event_datas"]  # 所有事件
    npc_datas = adventure_game_datas["npc_datas"]  # 所有npc数据
    default_map_data = {"pattern": "grass", "is_margin": False, "inside": []}

    if load_data_from_db is True:
        map_data = await load_map_data(
            coordinates_real=(int(map_size[0] / 2) + draw_add_x, int(map_size[1] / 2) + draw_add_y),
            coordinates_relative=[i - int(map_size[0] / 2) for i in range(s)]
        )
        logger.success("读取地图数据成功")
    else:
        for x in range(map_size[0]):
            logger.debug(f"创建地图数据：{x}")
            for y in range(map_size[1]):
                color_r = map_image.getpixel((x, y))[0]
                coordinates = f"{x}_{y}"
                map_data[coordinates] = {
                    "is_margin": False,
                    "inside": []}

                if color_r == 127:
                    map_data[coordinates]["pattern"] = "sea"
                elif color_r == 0:
                    map_data[coordinates]["pattern"] = "grass"
                elif color_r == 255:
                    map_data[coordinates]["pattern"] = "forest"
                    map_data[coordinates]["inside"].append({"type": "buliding", "id": "b1"})

        logger.success("创建地图数据成功")
        # 读取事件出现概率
        event_list = []
        probability_list = []
        num = 0
        for event_id in event_datas.keys():
            event_list.append(event_id)
            probability = event_datas[event_id]["probability"]
            num += probability
            probability_list.append(probability)
        for npc_id in npc_datas.keys():
            event_list.append(npc_id)
            probability = npc_datas[npc_id]["probability"]
            num += probability
            probability_list.append(probability)

        event_list.append("none")
        probability_list.append(1 - num)

        for x in range(map_size[0]):
            logger.debug(f"添加事件数据{x}")
            for y in range(map_size[1]):
                coordinates = f"{x + draw_add_x}_{y + draw_add_y}"
                event_id = numpy.random.choice(event_list, p=numpy.array(probability_list))
                if event_id == "none":
                    random_num = random.randint(0, 10)
                    if random_num == 0:
                        continue
                    map_data[coordinates]["inside"].append({"type": "buliding", "id": "b4"})
                    continue
                if event_id.startswith("e"):
                    # 判断事件是否处于概率地块
                    if map_data[coordinates]["pattern"] not in event_datas[event_id]["map_inside"]:
                        continue
                    new_list = [data for data in map_data[coordinates]["inside"]
                                if data["type"] not in ["buliding", "npc"]]
                    map_data[coordinates]["inside"] = new_list
                    # 添加事件npc
                    for npc_id in event_datas[event_id]["npc_list"]:
                        map_data[coordinates]["inside"].append({"type": "npc", "id": npc_id})

                    # 添加事件建筑
                    for buliding_id in event_datas[event_id]["building_list"]:
                        map_data[coordinates]["inside"].append({"type": "buliding", "id": buliding_id})

                    map_data[coordinates]["inside"].append({"type": "event", "id": event_id})

                else:
                    # if event_id.startswith("n"):
                    new_list = [data for data in map_data[coordinates]["inside"]
                                if data["type"] not in ["buliding", "npc"]]
                    map_data[coordinates]["inside"] = new_list
                    if map_data[coordinates]["pattern"] not in npc_datas[event_id]["map_inside"]:
                        continue
                    map_data[coordinates]["inside"].append({"type": "npc", "id": event_id})

    logger.success("添加事件数据成功")
    if draw_map is True:
        logger.debug("正在绘制")
        map_image = await draw_map_2d(map_data, view_occlusion=False, size=(2000, 2000))
        logger.success("绘制2d图片成功")
        map_info_image = await draw_map_inside(map_data, size=(2000, 2000))
        map_image.alpha_composite(map_info_image, (0, 0))
        logger.success("绘制建筑成功")

    if save_to_db is True:
        logger.debug("正在写入数据库")
        conn = sqlite3.connect(f"{basepath}db/plugin_adventure_map-2411.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
        try:
            for coordinates in map_data:
                coordinates_table = f"map-{int(int(coordinates.split('_')[0]) / 100)}_{int(int(coordinates.split('_')[1]) / 100)}"
                pattern = f"{map_data[coordinates]['pattern']}"

                inside_text = ""
                for inside in map_data[coordinates]['inside']:
                    inside_text += inside["type"] + "." + inside["id"] + ","
                inside_text = "'" + inside_text.removesuffix(",") + "'"
                if pattern == "'grass'" and inside_text == "''":
                    continue

                if coordinates_table not in tables:
                    cursor.execute(
                        f'create table "{coordinates_table}"(coordinates VARCHAR, pattern VARCHAR, inside VARCHAR)')
                    tables.append(coordinates_table)

                sql_text = f"replace into '{coordinates_table}' ('coordinates','pattern','inside') "
                sql_text += f"values('{coordinates}','{pattern}',{inside_text})"
                cursor.execute(sql_text)

            conn.commit()
        except Exception as e:
            logger.error(traceback.format_exc())
            logger.error(e)
            raise "地图数据写入出错"
        finally:
            cursor.close()
            conn.close()
        logger.success("写入数据库成功")
    return map_image


def a_color(color_name: str):
    color_data = {
        "背景": "#fef5e9",
        "地图描边": "#93785d",
        "地图底色": "#a89888",
        "其他用户名称": "#2c2c2c",
        "信息面板背景": "#c8a17c",
        "用户名称": "#f2c999",
        "背景大字": "#a17e5b",
        "内容面板背景": "#e1d5c9",
        "事件标题": "#986d3a",
        "事件内容": "#483f34",
        "地图坐标": "#e4b276",
        "菜单背景": "#fef5e9",
        "菜单文字": "#483f34",
        "表格背景": "#93785d",
        "表格格子": "#f8ca72",
        "111": "#",
        "222": "#",
        "333": "#",
        "444": "#",
        "555": "#",
        "666": "#",
        "777": "#",
        "888": "#",
    }
    return color_data[color_name]
