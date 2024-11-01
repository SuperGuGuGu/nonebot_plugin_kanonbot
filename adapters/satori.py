# coding=utf-8
import asyncio
import json
import random
import os
import re
import sqlite3
import traceback
from nonebot.adapters import Event
from nonebot.plugin import PluginMetadata
from nonebot import on_message, logger, require
# from nonebot import get_driver
import time
from nonebot_plugin_saa import Text as saaText, MessageFactory
from nonebot_plugin_saa import Image as saaImage
from .auto_run import suto_run_kanonbot_1hour, suto_run_kanonbot_1day
from .config import command_list, _config_list, greet_list_
from .bot_run import botrun
from .tools import kn_config, get_file_path, get_command, get_unity_user_id, get_unity_user_data, connect_api, \
    save_unity_user_data, _config, get_user_id, lockst, locked, kn_cache, save_image, load_image

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="*/1", id="job_0")
async def suto_run_kanonbot_1hour_():
    try:
        await suto_run_kanonbot_1hour()
    except Exception as e:
        logger.error("定时任务运行异常：1hour")
        logger.error(e)
        logger.error(traceback.format_exc())


@scheduler.scheduled_job("cron", day="*/1", id="job_1")
async def suto_run_kanonbot_1day_():
    try:
        await suto_run_kanonbot_1day()
    except Exception as e:
        logger.error("定时任务运行异常：1day")
        logger.error(e)
        logger.error(traceback.format_exc())


# nonebot_config = get_driver().config.dict()
basepath = _config["basepath"]
command_starts = _config["command_starts"]

# 插件元信息，让nonebot读取到这个插件是干嘛的
__plugin_meta__ = PluginMetadata(
    name="KanonBot",
    description="KanonBot for Nonebot2",
    usage="/help",
    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。
    homepage="https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot",
    # 发布必填。
    supported_adapters={"~onebot.v11"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

# 初始化文件
if not os.path.exists(basepath):
    os.makedirs(basepath)
cache_path = basepath + "cache/"
if not os.path.exists(cache_path):
    os.makedirs(cache_path)
cache_path = basepath + "file/"
if not os.path.exists(cache_path):
    os.makedirs(cache_path)

# 创建基础参数
returnpath = ""
plugin_dbpath = basepath + 'db/'
if not os.path.exists(plugin_dbpath):
    os.makedirs(plugin_dbpath)

# 读取缓存的群员列表
path = f"{basepath}cache/channel_member_list.json"
if os.path.exists(path):
    file = open(path, "r", encoding="UTF-8")
    kn_cache["channel_member_list"] = json.loads(file.read())
    file.close()
else:
    kn_cache["channel_member_list"] = {}
    file = open(path, "w", encoding="UTF-8")
    file.write(json.dumps({}))
    file.close()
logger.success(f"加载群友列表成功，共{len(kn_cache['channel_member_list'])}个群")

# 读取缓存的群信息列表
path = f"{basepath}cache/channel_data.json"
if os.path.exists(path):
    file = open(path, "r", encoding="UTF-8")
    kn_cache["channel_data"] = json.loads(file.read())
    file.close()
else:
    kn_cache["channel_data"] = {}
    file = open(path, "w", encoding="UTF-8")
    file.write(json.dumps({}, ensure_ascii=False, indent=2))
    file.close()

channel_replace_data = {}
for channel_id in kn_cache["channel_data"].keys():
    for channel_name in kn_cache["channel_data"][channel_id]["id_list"]:
        channel_replace_data[channel_name] = channel_id

logger.success(f"加载群信息列表成功，共{len(kn_cache['channel_data'])}个群")

run_kanon = on_message(priority=10, block=False)


@run_kanon.handle()
async def kanon(event: Event):
    # 获取消息基础信息
    time_now = int(time.time())
    await lockst()
    event_data: dict = event.dict()
    if time_now - int(event_data["timestamp"].timestamp()) > 10:
        logger.warning("跳过过时的消息")
        await run_kanon.finish()
    botid = event_data["self_id"]
    user_id = event_data["user"]["id"]
    platform = "qq"
    # 获取消息内容
    to_me = event_data["to_me"]

    # 判断消息事件
    if not event.get_type().startswith("message"):
        await run_kanon.finish()

    # 获取群号
    session_id: str = event.get_session_id()
    if session_id.startswith("private:"):
        # 私聊
        unity_guild_id = unity_channel_id = f"private_{platform}_{user_id}"
        guild_id = channel_id = user_id
    else:
        guild_id = session_id.split('/')[0]
        channel_id = session_id.split('/')[1]
        unity_guild_id = f"group_{platform}_{guild_id}"
        unity_channel_id = f"group_{platform}_{channel_id}"

    # 获取引用的消息
    pass

    # 获取消息
    msg = str(event.get_message().copy())
    msg = re.sub(u"\\[.*?]", "", msg)  # 去除cq码
    msg = re.sub(u"<.*?>", "", msg)  # 去除图片内容
    msg = msg.replace('"', "“").replace("'", "‘")  # 转换同义符
    msg = msg.replace("(", "（").replace(")", "）")  # 转换同义符
    msg = msg.replace("{", "（").replace("}", "）")  # 转换同义符
    msg = msg.replace("[", "【").replace("]", "】")  # 转换同义符
    msg = msg.replace('"', "'")  # 转换同义符

    commands = get_command(msg)
    command = commands[0]

    # ## 心跳服务相关 ##
    if kn_config("botswift-state") and platform in kn_config("botswift", "platform_list"):
        botswift_db = f"{basepath}db/botswift.db"
        conn = sqlite3.connect(botswift_db)
        cursor = conn.cursor()
        # 检查表格是否存在，未存在则创建
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "heart" not in tables:
            cursor.execute(f'create table "heart"'
                           f'("botid" VARCHAR(10) primary key, times VARCHAR(10), hearttime VARCHAR(10))')
        # 读取bot名单
        cursor.execute(f'select * from heart')
        datas = cursor.fetchall()
        bots_list = [data[0] for data in datas]
        # 如果发消息的用户为bot，则刷新心跳
        if user_id in bots_list:
            # cursor.execute(f'SELECT * FROM heart WHERE "botid" = "{user_id}"')
            # data = cursor.fetchone()
            # cache_times = int(data[1])
            # cache_hearttime = int(data[2])
            cursor.execute(f'replace into heart("botid", "times", "hearttime") '
                           f'values("{user_id}", "0", "{time_now}")')
            conn.commit()
        cursor.close()
        conn.close()

    # 判断是否响应
    commandname = ""
    commandlist = command_list()
    config_list = _config_list()
    run = False

    # 识别
    if run is False:
        # 识别绑定
        if run is False:
            if command == "bdkn" and user_id == "2854207213":
                # 获取at内容
                atmsg = event.get_message().copy()["at"]
                if len(atmsg) >= 1:
                    connect_msg = None
                    atmsgg = None
                    for i in atmsg:
                        atmsgg = str(i.data["qq"])
                        atmsgg.removeprefix('[CQ:at,qq=')
                        atmsgg.removesuffix(']')
                        atmsgg = str(atmsgg)
                        break
                    if atmsgg is None:
                        connect_msg = "绑定失败，请稍后再试（e：nat）"
                    elif len(commands) < 2:
                        connect_msg = "绑定失败，请稍后再试（e：nid）"
                    else:
                        # 开始同步数据
                        await asyncio.sleep(random.randint(1, 200) / 100)
                        await lockst()

                        conn = sqlite3.connect(f"{basepath}db/config.db")
                        cursor = conn.cursor()

                        id_unity = None
                        id_unity_old = None
                        # 获取uid
                        id_unity = get_unity_user_id("qq", atmsgg)  # 新uid
                        id_unity_old = commands[1]  # 旧uid
                        logger.warning(f"绑定{id_unity} - {id_unity_old}")
                        if id_unity is None or id_unity_old is None:
                            connect_msg = "绑定出错，请稍后再试（e：ind）"
                        elif id_unity == id_unity_old:
                            # 账号已绑定
                            connect_msg = "账号已绑定，无需重复绑定"
                        else:
                            # 记录绑定
                            cursor.execute(
                                f'replace into connect_list ("unity_id","qq","message") '
                                f'values("{id_unity}","{atmsgg}","id_unity_old:{id_unity_old}")')
                            conn.commit()

                            # 更新旧id
                            cursor.execute(f'SELECT * FROM id_list WHERE "unity_id" = "{id_unity_old}"')
                            data = cursor.fetchone()

                            if data is not None:
                                cursor.execute(f'replace into id_list("id", "unity_id", "platform", "user_id") '
                                               f'values("{data[0]}", "{id_unity}", "{data[2]}", "{data[3]}")')
                                cursor.execute(f'replace into id_list("unity_id", "platform", "user_id") '
                                               f'values("{id_unity_old}", "del", "del_by_connect")')
                                conn.commit()

                        cursor.close()
                        conn.close()

                        # 同步签到、水母箱
                        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                        cursor = conn.cursor()

                        if connect_msg is None:

                            if id_unity is None and id_unity_old is None:
                                connect_msg = "绑定失败，请稍后再试（e：db_nid）"
                            else:
                                # 同步签到
                                cursor.execute(f'SELECT * FROM checkin WHERE "user_id" = "{id_unity_old}"')
                                data = cursor.fetchone()
                                if data is None:
                                    point_old = 0
                                else:
                                    point_old = int(data[2])

                                cursor.execute(f'SELECT * FROM checkin WHERE "user_id" = "{id_unity}"')
                                data = cursor.fetchone()
                                if data is None:
                                    point = 0
                                    data = [str(id_unity), "000"]
                                else:
                                    point = int(data[2])

                                cursor.execute(f'replace into checkin("user_id", "date", "point") '
                                               f'values("{data[0]}", "{data[1]}", "{point + point_old}")')
                                conn.commit()

                                # 同步水母箱
                                cursor.execute(f'SELECT * FROM "jellyfish_box" WHERE user_id = "{id_unity_old}"')
                                data = cursor.fetchone()

                                if data is not None:  # 如果旧箱有数据
                                    box_data_old = json.loads(data[1])

                                    cursor.execute(f'SELECT * FROM "jellyfish_box" WHERE user_id = "{id_unity}"')
                                    data = cursor.fetchone()

                                    if data is None:  # 如果旧箱有数据、新箱无数据
                                        box_data = box_data_old
                                        box_data["info"]["oner"] = id_unity

                                        cursor.execute(f'replace into jellyfish_box("user_id", "data") '
                                                       f'values("{id_unity}", ' + f"'{json.dumps(box_data)}')")
                                        conn.commit()

                                    else:  # 如果旧箱有数据、新箱有数据
                                        box_data = json.loads(data[1])
                                        for j_id in list(box_data_old["jellyfish"]):
                                            j_num = box_data_old["jellyfish"][j_id]["number"]
                                            if j_id in list(box_data["jellyfish"]):
                                                box_data["jellyfish"][j_id]["number"] += j_num
                                            else:
                                                box_data["jellyfish"][j_id] = {"number": j_num}

                                        cursor.execute(f'replace into jellyfish_box("user_id", "data") '
                                                       f'values("{id_unity}", ' + f"'{json.dumps(box_data)}')")
                                        conn.commit()

                        cursor.close()
                        conn.close()

                        locked()

                    if connect_msg is None:
                        connect_msg = "绑定完成"
                    await saaText(connect_msg).send()

        # 识别精准
        if run is False:
            cache_commandlist = commandlist["精准"]
            if command in list(cache_commandlist):
                commandname = cache_commandlist[command]
                run = True

        # 识别开头
        if run is False:
            cache_commandlist = commandlist["开头"]
            for cache_command in list(cache_commandlist):
                if command.startswith(cache_command):
                    commandname = cache_commandlist[cache_command]
                    msg = f"{cache_command} {command.removeprefix(cache_command)}"
                    run = True
                    break

        # 识别结尾
        if run is False:
            cache_commandlist = commandlist["结尾"]
            for cache_command in list(cache_commandlist):
                if command.endswith(cache_command):
                    commandname = cache_commandlist[cache_command]
                    run = True
                    break

        # 识别模糊
        if run is False:
            cache_commandlist = commandlist["模糊"]
            for cache_command in list(cache_commandlist):
                if cache_command in command:
                    commandname = cache_commandlist[command]
                    run = True
                    break

        # 识别精准2
        if run is False:
            cache_commandlist = commandlist["精准2"]
            if command in list(cache_commandlist):
                commandname = cache_commandlist[command]
                run = True

        # 识别emoji
        if run is False and kn_config("emoji-state"):
            conn = sqlite3.connect(await get_file_path("emoji_1.db"))
            cursor = conn.cursor()
            cursor.execute(f'select * from emoji where emoji = "{command}"')
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            if data is not None:
                commandname = "表情功能-emoji"
                run = True

        # 识别对话
        if run is False:
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
            logger.debug(f"该群正在进行的聊天{data}")
            if data is not None:
                # 有聊天数据
                gameing = data[3]
                if gameing == 1:
                    logger.debug("if gameing == 1:")
                    # 有正在进行的聊天
                    commandname = data[1]
                    run = True

        # 识别问好
        if run is False and to_me is True:
            greet_list = greet_list_()
            for group in greet_list:
                if command in group["ask"]:
                    run = True
                    commandname = "群聊功能-问好"
                    break

        # 排除部分相应词
        if run is True:
            if commandname == 'caicaikan':
                if len(command) >= 7:
                    run = False
            if commandname == 'blowplane':
                if len(command) >= 7:
                    run = False
            if commandname in ["亲亲", "可爱", "咬咬", "摸摸", "贴贴", "逮捕"]:
                if len(command) >= 7:
                    run = False

    # 开始处理消息
    if run:
        # 创建变量内容
        code = 0
        date_year: str = time.strftime("%Y", time.localtime())
        date_month: str = time.strftime("%m", time.localtime())

        # 获取回复的消息
        reply_data = None

        # 获取unity用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)
        save = False

        # 同步unity数据
        if "user_id" not in list(unity_user_data) or unity_user_data["user_id"] != unity_user_id:
            unity_user_data["user_id"] = unity_user_id
            save = True

        if event_data["user"]["name"] is not None:
            if "name" not in list(unity_user_data) or unity_user_data["name"] != event_data["user"]["name"]:
                unity_user_data["name"] = event_data["user"]["name"]
        else:
            unity_user_data["name"] = "user"

        if event_data["user"]["nick"] is not None:
            if "nick_name" not in list(unity_user_data) or unity_user_data["nick_name"] != event_data["user"]["nick"]:
                unity_user_data["nick_name"] = event_data["user"]["nick"]
        else:
            unity_user_data["nick_name"] = None

        if "avatar" not in list(unity_user_data) and event_data["user"]["avatar"] is not None:
            # unity_user_data["avatar"] = f"https://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
            # unity_user_data["avatar"] = f"http://thirdqq.qlogo.cn/headimg_dl?dst_uin={user_id}&spec=640"
            unity_user_data["avatar"] = event_data["user"]["avatar"]

        if unity_user_data["avatar"] != event_data["user"]["avatar"]:
            if not unity_user_data["avatar"].startswith("https://thirdqq.qlogo.cn/qqapp/"):
                unity_user_data["avatar"] = event_data["user"]["avatar"]

        if "face_image" not in list(unity_user_data):
            os.makedirs(f"{basepath}file/user_face/", exist_ok=True)
            image = await load_image(unity_user_data["avatar"])
            unity_user_data["face_image"] = save_image(
                image,
                image_path="{basepath}file/user_face/",
                image_name=f"{unity_user_id}.png",
                relative_path=True)
            save = True

        # 更新头像
        if "avatar" in list(unity_user_data):
            if "update_face_image" not in list(unity_user_data):
                unity_user_data["update_face_image"] = 0
            if (time_now - unity_user_data["update_face_image"]) > (86400 * 3):  # 超过7天没更新
                try:
                    # 尝试更新头像
                    image = await load_image(unity_user_data["avatar"])
                    save_image(
                        image,
                        image_path="{basepath}file/user_face/",
                        image_name=f"{unity_user_id}.png",
                        relative_path=True)
                except Exception as e:
                    logger.error("更新头像失败")
                unity_user_data["update_face_image"] = time_now

            save = True

        if save is True:
            unity_user_data = save_unity_user_data(unity_user_id, unity_user_data)

        # 获取消息包含的图片
        imgmsgs = []
        for i in event_data["original_message"]:
            if i["type"] != "img":
                continue
            image_url = i["data"]["src"]
            # for cc_config in nonebot_config["satori_clients"]:
            #     if f"127.0.0.1:{cc_config['port']}" in image_url:
            #     image_url = image_url.replace(f"127.0.0.1:{cc_config['port']}", f"10.10.10.40:{cc_config['port']}")

            image_url = image_url.replace("http://127.0.0.1:", "http://10.10.10.40:")
            imgmsgs.append(image_url)

        # 获取at内容
        at_datas = []
        for i in event_data["original_message"]:
            if i["type"] != "at":
                continue
            atmsgg = i["data"]["id"]

            at_unity_id = get_unity_user_id("qq", atmsgg)
            at_unity_data = get_unity_user_data(at_unity_id)
            at_unity_data["id"] = atmsgg

            # 同步unity数据
            if "user_id" not in list(at_unity_data):
                at_unity_data["user_id"] = at_unity_id
                save = True

            # 更新头像
            at_unity_data["avatar"] = f"https://q1.qlogo.cn/g?b=qq&nk={atmsgg}&s=640"
            if "face_image" not in list(at_unity_data):
                os.makedirs(f"{basepath}file/user_face/", exist_ok=True)
                image = await load_image(at_unity_data["avatar"])
                at_unity_data["face_image"] = save_image(
                    image,
                    image_path="{basepath}file/user_face/",
                    image_name=f"{at_unity_id}.png",
                    relative_path=True)
                at_unity_data["update_face_image"] = time_now
                save = True

            elif "avatar" in list(at_unity_data):
                if "update_face_image" not in list(at_unity_data):
                    at_unity_data["update_face_image"] = 0
                if (time_now - at_unity_data["update_face_image"]) > (86400 * 4):  # 超过4天没更新
                    try:
                        # 尝试更新头像
                        os.makedirs(f"{basepath}file/user_face/", exist_ok=True)
                        image = await load_image(at_unity_data["avatar"])
                        at_unity_data["face_image"] = save_image(
                            image,
                            image_path="{basepath}file/user_face/",
                            image_name=f"{at_unity_id}.png",
                            relative_path=True)
                    except Exception as e:
                        logger.error("更新头像失败")
                    at_unity_data["update_face_image"] = time_now
                    save = True

            if save is True:
                save_unity_user_data(at_unity_id, at_unity_data)

            if "name" not in list(at_unity_data):
                at_unity_data["name"] = "user"
            if "nick_name" not in list(at_unity_data):
                at_unity_data["nick_name"] = None
            if "permission" not in list(at_unity_data):
                at_unity_data["permission"] = 5

            at_datas.append(at_unity_data)

        # 获取好友列表
        friend_datas = {}

        # 获取群员列表
        if "channel_member_list" not in kn_cache.keys():
            kn_cache["channel_member_list"] = {}
        if unity_channel_id not in kn_cache["channel_member_list"].keys():
            kn_cache["channel_member_list"][unity_channel_id] = {}
        kn_cache["channel_member_list"][unity_channel_id][unity_user_id] = unity_user_data
        # 更新群数据
        channel_member_datas = kn_cache["channel_member_list"][unity_channel_id]

        # 获取群信息
        channel_name = event_data["channel"]["name"]
        if unity_channel_id in kn_cache["channel_data"].keys():
            if unity_channel_id not in kn_cache["channel_data"]["id_list"]:
                kn_cache["channel_data"]["id_list"].append(unity_channel_id)
            if kn_cache["channel_data"]["name"] is None:
                kn_cache["channel_data"]["name"] = channel_name
        else:
            kn_cache["channel_data"][channel_id] = {
                "name": channel_name,
                "id_list": [unity_channel_id]
            }

        # 组装信息，进行后续响应
        msg_info = {
            "msg": msg,
            "msg_time": event_data["timestamp"].timestamp(),
            "commands": commands,
            "commandname": commandname,
            "bot_id": botid,
            "channel_id": unity_channel_id,
            "guild_id": unity_guild_id,
            "at_datas": at_datas,
            "user": unity_user_data,
            "imgmsgs": imgmsgs,
            "to_me": to_me,
            "event_name": "message_event",
            "platform": platform,
            "reply_data": reply_data,
            "friend_datas": friend_datas,
            "channel_member_datas": channel_member_datas
        }
        # logger.info(msg_info)
        data = await botrun(msg_info)
        logger.info(data)
        # 获取返回信息，进行回复
        message_id_list: list = []
        message_list: list = []
        if type(data) is list:
            message_list = data
            at = False
            for i in message_list:
                if type(i) is str and i == "at_sender":
                    message_list.remove("at_sender")
                    at = True
                    break
        elif type(data) is dict:
            code = int(data["code"])

            if code == -1:
                pass
                # return_message.append("内部错误")
            elif code == 0:
                pass
            elif code == 1:
                message_list.append(saaText(data["message"]))
            elif code == 2:
                image_file = open(data["returnpath"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
            elif code == 3:
                message_list.append(saaText(data["message"]))
                image_file = open(data["returnpath"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
            elif code == 4:
                message_list.append(saaText(data["message"]))
                image_file = open(data["returnpath"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
                image_file = open(data["returnpath2"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
            elif code == 5:
                message_list.append(saaText(data["message"]))
                image_file = open(data["returnpath"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
                image_file = open(data["returnpath2"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
                image_file = open(data["returnpath3"], "rb")
                image = image_file.read()
                image_file.close()
                message_list.append(saaImage(image))
            else:
                pass

            at = data.get("at")
        else:
            raise "插件返回错误"

        msg_builder = MessageFactory(message_list)
        if at is True:
            msg_data = await msg_builder.send(at_sender=True)
        else:
            msg_data = await msg_builder.send()

        try:
            for data in msg_data.dict()["messages"]:
                message_id_list.append(data["id"])
        except Exception as e:
            logger.warning("保存消息id错误")
            logger.warning(msg_data.dict())
        if "reply_trace" in list(data) and data['reply_trace'] is not None and message_id_list:
            conn = sqlite3.connect(f"{basepath}db/send_msg_log_{date_year}-{date_month}.db")
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                tables = []
                for i in datas:
                    if i[1] != "sqlite_sequence":
                        tables.append(i[1])
                if "send_msg_log" not in tables:
                    cursor.execute(
                        f"create table send_msg_log(id INTEGER primary key AUTOINCREMENT, "
                        f"msg_id VARCHAR(10), msg_data VARCHAR(10))")

                for message_id in message_id_list:
                    cursor.execute(
                        f"replace into send_msg_log ('msg_id','msg_data') "
                        f"values('{message_id}','{json.dumps(data['reply_trace'])}')")

                conn.commit()

            except Exception as e:
                logger.error("写入send_msg_log.db失败")
                logger.error(e)
            cursor.close()
            conn.close()
    await locked()
    await run_kanon.finish()


@scheduler.scheduled_job("cron", hour="*/1", id="job_0")
async def run_bili_push():
    logger.debug(f"kanonbot_auto_run")

    # 保存群员列表
    logger.debug("开始保存群员列表")
    path = f"{basepath}cache/channel_member_list.json"
    file = open(path, "r", encoding="UTF-8")
    channel_member_list: dict = json.loads(file.read())
    file.close()

    if "channel_member_list" not in kn_cache.keys():
        kn_cache["channel_member_list"] = channel_member_list
    else:
        for channel_id in kn_cache["channel_member_list"]:
            if channel_id not in channel_member_list.keys():
                channel_member_list[channel_id] = kn_cache["channel_member_list"][channel_id]
            else:
                channel_member_list[channel_id].update(kn_cache["channel_member_list"][channel_id])
        kn_cache["channel_member_list"] = channel_member_list

        file = open(path, "w", encoding="UTF-8")
        file.write(json.dumps(channel_member_list, ensure_ascii=False, indent=2))
        file.close()

    logger.success("保存群员列表成功")

    # 保存群数据列表
    logger.debug("开始保存群数据列表")
    path = f"{basepath}cache/channel_data.json"
    file = open(path, "r", encoding="UTF-8")
    channel_data: dict = json.loads(file.read())
    file.close()

    if "channel_data" not in kn_cache.keys():
        kn_cache["channel_data"] = channel_data
    else:
        for channel_id in kn_cache["channel_data"].keys():
            if channel_id not in channel_data.keys():
                channel_data[channel_id] = kn_cache["channel_data"][channel_id]
            else:
                if kn_cache["channel_data"][channel_id]["name"] is not None:
                    channel_data[channel_id]["name"] = kn_cache["channel_data"][channel_id]["name"]
        kn_cache["channel_data"] = channel_data

        file = open(path, "w", encoding="UTF-8")
        file.write(json.dumps(channel_data, ensure_ascii=False, indent=2))
        file.close()

        logger.debug("更新群id替换列表")
        channel_replace_data = {}
        for channel_id in kn_cache["channel_data"].keys():
            for channel_name in kn_cache["channel_data"][channel_id]["id_list"]:
                channel_replace_data[channel_name] = channel_id

    logger.success("保存群数据列表成功")
