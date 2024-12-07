# coding=utf-8
import asyncio
import json
import random
import string
import traceback
from nonebot.adapters.qq.models import MessageKeyboard, MessageMarkdown
from nonebot.plugin import PluginMetadata
import os
import re
import sqlite3
from nonebot import on_message, logger, require
from nonebot.adapters.qq import Bot, MessageSegment, MessageEvent, Event
import time
from .auto_run import auto_run_kanonbot_1hour, auto_run_kanonbot_1day
from .config import command_list, _config_list, greet_list_
from .bot_run import botrun
from .tools import (kn_config, get_file_path, get_command, imgpath_to_url, draw_text, mix_image, connect_api,
                    get_unity_user_id, get_unity_user_data, save_unity_user_data, get_user_id, get_qq_face, _config,
                    lockst, locked, kn_cache, load_image, save_image, read_db)

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


@scheduler.scheduled_job("cron", hour="*/1", id="job_0")
async def auto_run_kanonbot_1hour_():
    try:
        await auto_run_kanonbot_1hour()
    except Exception as e:
        logger.error("定时任务运行异常：1hour")
        logger.error(e)
        logger.error(traceback.format_exc())


@scheduler.scheduled_job("cron", day="*/1", id="job_1")
async def auto_run_kanonbot_1day_():
    try:
        await auto_run_kanonbot_1day()
    except Exception as e:
        logger.error("定时任务运行异常：1day")
        logger.error(e)
        logger.error(traceback.format_exc())


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
    supported_adapters={"~qq"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

# 初始化文件
os.makedirs(f"{basepath}cache/", exist_ok=True)
os.makedirs(f"{basepath}file/", exist_ok=True)
os.makedirs(f'{basepath}db/', exist_ok=True)

# 读取缓存的群员列表
path = f"{basepath}cache/channel_member_list.json"
if os.path.exists(path):
    file = open(path, "r", encoding="UTF-8")
    try:
        kn_cache["channel_member_list"] = json.loads(file.read())
    except Exception as e:
        logger.error(e)
        logger.error("读取群成员列表失败")
        kn_cache["channel_member_list"] = {}
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
    try:
        kn_cache["channel_data"] = json.loads(file.read())
    except Exception as e:
        logger.error(e)
        logger.error("读取群列表失败")
        kn_cache["channel_data"] = {}
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
async def kanon(
        message_event: MessageEvent,
        bot: Bot,
        event: Event
):
    msg_time: float = time.time()
    await lockst()
    # 获取消息基础信息
    botid = str(bot.self_id)
    event_dict = event.dict()
    event_name = message_event.get_event_name()
    user_id = event_dict["author"]["id"]
    # user_id = event_dict["author"]["member_openid"]
    platform = "qq_Official"

    # 获取群号
    if event_name == "GROUP_AT_MESSAGE_CREATE":
        guild_id = channel_id = event_dict["group_id"]
        # guild_id = channel_id = event_dict["group_openid"]
        unity_guild_id = unity_channel_id = f"group_{platform}_{channel_id}"

        if unity_channel_id in channel_replace_data.keys():
            unity_guild_id = unity_channel_id = channel_replace_data[unity_channel_id]
        chat_type = "group"
    elif event_name == "AT_MESSAGE_CREATE":
        channel_id = message_event.channel_id
        guild_id = message_event.guild_id
        unity_channel_id = f"channel_{platform}_{channel_id}"
        unity_guild_id = f"channel_{platform}_{guild_id}"
        if unity_channel_id in channel_replace_data.keys():
            unity_channel_id = channel_replace_data[unity_channel_id]
            unity_guild_id = channel_replace_data[unity_channel_id]
        chat_type = "channel"
    elif event_name == "C2C_MESSAGE_CREATE":
        channel_id = guild_id = user_id
        unity_channel_id = f"private_{platform}_{user_id}"
        unity_guild_id = f"private_{platform}_{user_id}"
        chat_type = "private"
    else:
        channel_id = guild_id = user_id
        unity_channel_id = unity_guild_id = f"else_{platform}_{user_id}"
        chat_type = "None_chat_type"

    msg = str(message_event.get_message())
    msg = msg.replace('"', "“").replace("'", "‘")
    msg = msg.replace("(", "（").replace(")", "）")
    msg = msg.replace("{", "（").replace("}", "）")
    msg = msg.replace("[", "【").replace("]", "】")
    commands = get_command(msg)
    command = commands[0]
    now = int(time.time())

    # 获取消息包含的图片
    imgmsgs = []
    image_datas = message_event.get_message()['image']
    for image_data in image_datas:
        image_data = str(image_data)
        img_url = f"{image_data.removeprefix('<attachment[image]:').removesuffix('>')}"
        imgmsgs.append(img_url)

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
        bots_list = []
        for data in datas:
            bots_list.append(data[0])
        # 如果发消息的用户为bot，则刷新心跳
        if user_id in bots_list:
            cursor.execute(f'SELECT * FROM heart WHERE "botid" = "{user_id}"')
            data = cursor.fetchone()
            cache_times = int(data[1])
            cache_hearttime = int(data[2])
            cursor.execute(f'replace into heart("botid", "times", "hearttime") '
                           f'values("{user_id}", "0", "{now}")')
            conn.commit()
        cursor.close()
        conn.close()

    # 判断是否响应
    commandname = ""
    commandlist = command_list()
    config_list = _config_list()
    run = False
    time_now = int(time.time())

    if run is False:
        # 识别绑定
        if run is False:
            if command == "绑定":
                unity_user_id = get_unity_user_id(platform, user_id)
                if not os.path.exists(f"{basepath}db/"):
                    os.makedirs(f"{basepath}db/")
                conn = sqlite3.connect(f"{basepath}db/config.db")
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                    datas = cursor.fetchall()
                    tables = []
                    for data in datas:
                        if data[1] != "sqlite_sequence":
                            tables.append(data[1])
                    # 检查是否创建数据库
                    if "connect_list" not in tables:
                        cursor.execute(
                            'create table "connect_list"(id INTEGER primary key AUTOINCREMENT, '
                            'unity_id VARCHAR(10), qq VARCHAR(10), message VARCHAR(10))')
                    # 创建绑定id
                    message = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
                    num = 50
                    while num > 1:
                        num -= 1
                        message = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(20))
                        for strr in ["kn", "ka", "sg", "0", "444", "41", "s1s", "s8", "sb", "250", "69", "79", "nc",
                                     "58", "5b", "64", "63", "sx", "nt", "n7"]:
                            if strr in message.lower():
                                continue
                        break

                    cursor.execute(
                        f'replace into connect_list ("unity_id","message") values("{unity_user_id}","{message}")')
                    conn.commit()
                except Exception as e:
                    message = "获取绑定id错误"
                cursor.close()
                conn.close()

                msg = MessageSegment.text(f"{message}")
                await run_kanon.send(msg)

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
            emoji_test = command.replace('"', "”")
            if len(emoji_test) < 5:
                conn = sqlite3.connect(await get_file_path("emoji_1.db"))
                cursor = conn.cursor()
                cursor.execute(f'select * from emoji where emoji = "{emoji_test}"')
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
            cursor.execute(f'select * from gameinglist where channelid = "{unity_channel_id}"')
            data = cursor.fetchone()
            cursor.close()
            conn.close()
            logger.debug(f"该群正在进行的聊天{data}")
            if data is not None:
                # 有聊天数据
                gameing = data[3]
                if gameing == 1:
                    # 有正在进行的聊天
                    commandname = data[1]
                    run = True

        # 识别问好
        if run is False:
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

    # if command in ["test4"]:
    #     run = True

    # 开始处理消息
    if run:
        # 创建变量内容
        # date = str(time.strftime("%Y-%m-%d", time.localtime()))
        # date_year: int = int(time.strftime("%Y", time.localtime()))
        # date_month = int(time.strftime("%m", time.localtime()))
        # date_day = int(time.strftime("%d", time.localtime()))
        time_now = int(time.time())

        # 获取用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)

        # 获取用户信息
        save = False
        if event_name == "AT_MESSAGE_CREATE":
            # q频道
            try:
                data = await bot.get_member(guild_id=guild_id, user_id=user_id)
                unity_user_data["avatar"] = data.user.avatar
                unity_user_data["username"] = data.user.username
                unity_user_data["nick_name"] = data.nick
                unity_user_data["union_openid"] = data.user.union_openid
                unity_user_data["is_bot"] = data.user.bot
                save = True
            except:
                logger.error(f"get_member API请求失败guild_id：{guild_id}， user_id：{user_id}")
        elif event_name == "GROUP_AT_MESSAGE_CREATE":
            pass
        else:
            pass

        # 同步unity数据
        if unity_user_data.get("user_id") is None:
            unity_user_data["user_id"] = unity_user_id
            save = True
        if unity_user_data.get("name") is None:
            unity_user_data["name"] = "user"
            save = True
        if "nick_name" not in unity_user_data.keys():
            unity_user_data["nick_name"] = None
            save = True
        if "permission" not in unity_user_data.keys():
            unity_user_data["permission"] = 5
            save = True
        if unity_user_data.get("avatar") is None:
            unity_user_data["avatar"] = f"https://thirdqq.qlogo.cn/qqapp/{botid}/{user_id}/640"
            save = True
        if unity_user_data.get("use_markdown") is None:
            unity_user_data["use_markdown"] = False
        unity_user_data["avatar"] = f"https://thirdqq.qlogo.cn/qqapp/{botid}/{user_id}/640"
        if unity_user_data.get("face_image") is not None:
            # 如果图像不存在，则删除记录，并触发重新下载
            if not os.path.exists(unity_user_data.get("face_image").replace("{bacepath}", basepath)):
                unity_user_data["face_image"] = None
        if unity_user_data.get("face_image") is None and unity_user_data.get("avatar") is not None:
            image = await load_image(unity_user_data["avatar"])
            unity_user_data["face_image"] = save_image(
                image,
                image_path="{basepath}file/user_face/",
                image_name=f"{unity_user_id}.png",
                relative_path=True)
            save = True

        # 更新头像
        if unity_user_data.get("avatar") is not None:
            if "update_face_image" not in unity_user_data.keys():
                unity_user_data["update_face_image"] = 0
            if (time_now - int(unity_user_data["update_face_image"])) > (86400 * 3):  # 超过3天没更新
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

        if save:
            unity_user_data = save_unity_user_data(unity_user_id, unity_user_data)

        # 获取at内容
        atmsgs = []
        num = -1
        jump_num = 0
        for m in msg:
            num += 1
            if jump_num > 0:
                jump_num -= 1
            elif m == "<":
                num_test = 2  # 起始计算数
                while num_test <= 50:  # 终止计算数
                    num_test += 1
                    text = msg[num:(num + num_test)]
                    if text.startswith("<attachment:"):
                        num_test = 99999
                    if text.endswith(">") and text.startswith("<@"):
                        num_test = 99999
                        atmsgs.append(text.removeprefix("<@").removesuffix(">"))
                        jump_num = len(text) - 2
        at_datas = []
        for id in atmsgs:
            try:
                data = await bot.get_member(guild_id=guild_id, user_id=id)
                at_data = {
                    "id": id,
                    "name": data.user.username,
                    "nick_name": data.nick,
                    "avatar": data.user.avatar,
                    "union_openid": data.user.union_openid,
                    "is_bot": data.user.bot
                }
                at_datas.append(at_data)
            except Exception as e:
                logger.error("获取at内容失败")

        if len(commands) == 2:
            command2 = commands[1]
            if 6 < len(command2) < 13:
                try:
                    data = int(command2)
                    at_unity_user_id = get_unity_user_id("qq", command2)
                    at_unity_user_data = get_unity_user_data(at_unity_user_id)
                    if len(list(at_unity_user_data)) == 0:
                        at_data = {
                            "id": at_unity_user_id,
                            "username": "user",
                            "nick_name": None,
                            "avatar": f"https://q1.qlogo.cn/g?b=qq&nk={command2}&s=640",
                            "qq": command2
                        }
                        at_datas.append(at_data)
                    else:
                        at_unity_user_data["id"] = command2
                        at_datas.append(at_unity_user_data)
                except:
                    pass

        # 记录群列表
        if "channel_member_list" not in kn_cache.keys():
            kn_cache["channel_member_list"] = {}
        if unity_channel_id not in kn_cache["channel_member_list"].keys():
            kn_cache["channel_member_list"][unity_channel_id] = {}
        kn_cache["channel_member_list"][unity_channel_id][unity_user_id] = unity_user_data
        channel_member_datas = kn_cache["channel_member_list"][unity_channel_id]

        # 获取成员名单
        friend_datas = {}

        to_me = event_dict["to_me"]

        # 获取群信息
        channel_name = None
        if unity_channel_id in kn_cache["channel_data"].keys():
            if unity_channel_id not in kn_cache["channel_data"][unity_channel_id]["id_list"]:
                kn_cache["channel_data"][unity_channel_id]["id_list"].append(unity_channel_id)
        else:
            kn_cache["channel_data"][unity_channel_id] = {
                "name": channel_name,
                "id_list": [unity_channel_id]
            }

        msg = re.sub(u"<.*?>", "", msg)
        commands = get_command(msg)
        # 组装信息，进行后续响应
        msg_info = {
            "msg": msg,
            "msg_time": msg_time,
            "commands": commands,
            "commandname": commandname,
            "bot_id": botid,
            "channel_id": unity_channel_id,
            "guild_id": unity_guild_id,
            "at_datas": at_datas,
            "user": unity_user_data,
            "imgmsgs": imgmsgs,
            "to_me": to_me,
            "event_name": event_name,
            "platform": platform,
            "chat_type": chat_type,
            "friend_datas": friend_datas,
            "channel_member_datas": channel_member_datas
        }
        # logger.debug(msg_info)
        data = await botrun(msg_info)
        logger.debug(data)
        # 获取返回信息，进行回复
        code = int(data["code"])

        if data.get("returnpath") is not None and type(data["returnpath"]) == str:
            data["returnpath"] = data["returnpath"].replace("{basepath}", basepath)
        if data.get("returnpath2") is not None and type(data["returnpath2"]) == str:
            data["returnpath2"] = data["returnpath2"].replace("{basepath}", basepath)
        if data.get("returnpath3") is not None and type(data["returnpath3"]) == str:
            data["returnpath3"] = data["returnpath3"].replace("{basepath}", basepath)

        if code == -1 and platform == "qq_Official":
            msg = MessageSegment.text("发生了错误，请稍后再试( ≧Д≦)")
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"message:{msg},code:{e.code},message:{e.message},trace_id:{e.trace_id}")
        if code == 0:
            pass
        elif code == 1:
            message = data["message"]
            msg = MessageSegment.text(message)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"message:{msg},code:{e.code},message:{e.message},trace_id:{e.trace_id}")
        elif code == 2:
            image_file = open(data["returnpath"], "rb")
            image = image_file.read()
            image_file.close()
            msg = MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                await asyncio.sleep(0.5)
                try:
                    await run_kanon.send(msg)
                except Exception as e:
                    logger.error(e)
                    img_url = await imgpath_to_url(data["returnpath"], host="https://cdn.kanon.ink")
                    await run_kanon.send(f"图片发送失败，请点击链接查看图片")
                    await run_kanon.send(f"{img_url}")
        elif code == 3:
            message = data["message"]
            image_file = open(data["returnpath"], "rb")
            image = image_file.read()
            image_file.close()

            msg = MessageSegment.text(message) + MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                await run_kanon.send(MessageSegment.text(message))
                try:
                    await run_kanon.send(MessageSegment.file_image(image))
                except Exception as er:
                    img_url = await imgpath_to_url(data["returnpath"], host="https://cdn.kanon.ink")
                    await run_kanon.send(f"图片发送失败，请点击链接查看图片")
                    await run_kanon.send(f"{img_url}")

                logger.error(f"message:{msg},code:{e.code},message:{e.message},trace_id:{e.trace_id}")
        elif code == 4:
            message = data["message"]
            image_file = open(data["returnpath"], "rb")
            image = image_file.read()
            image_file.close()

            msg = MessageSegment.text(message) + MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"code:{e.code},message:{e.message},trace_id:{e.trace_id}")
                img_url = await imgpath_to_url(data["returnpath"], host="https://cdn.kanon.ink")
                await run_kanon.send(f"请点击链接查看图片")
                await run_kanon.send(f"{img_url}")

            image_file = open(data["returnpath2"], "rb")
            image2 = image_file.read()
            image_file.close()

            msg = MessageSegment.file_image(image2)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"code:{e.code},message:{e.message},trace_id:{e.trace_id}")
                img_url = await imgpath_to_url(data["returnpath2"], host="https://cdn.kanon.ink")
                await run_kanon.send(f"请点击链接查看图片")
                await run_kanon.send(f"{img_url}")
        elif code == 5:
            message = data["message"]
            image_file = open(data["returnpath"], "rb")
            image = image_file.read()
            image_file.close()

            msg = MessageSegment.text(message) + MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"code:{e.code},message:{e.message},trace_id:{e.trace_id}")
                img_url = await imgpath_to_url(data["returnpath"], host="https://cdn.kanon.ink")
                await run_kanon.send(f"请点击链接查看图片")
                await run_kanon.send(f"{img_url}")

            image_file = open(data["returnpath2"], "rb")
            image = image_file.read()
            image_file.close()
            msg = MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"code:{e.code},message:{e.message},trace_id:{e.trace_id}")
                img_url = await imgpath_to_url(data["returnpath2"], host="https://cdn.kanon.ink")
                await run_kanon.send(f"请点击链接查看图片")
                await run_kanon.send(f"{img_url}")

            image_file = open(data["returnpath3"], "rb")
            image = image_file.read()
            image_file.close()
            msg = MessageSegment.file_image(image)
            try:
                await run_kanon.send(msg)
            except Exception as e:
                logger.error(f"code:{e.code},message:{e.message},trace_id:{e.trace_id}")
                img_url = await imgpath_to_url(data["returnpath3"], host="https://cdn.kanon.ink")
                await run_kanon.send(f"请点击链接查看图片")
                await run_kanon.send(f"{img_url}")
        else:
            pass

        if "markdown" in list(data) and data["markdown"] is not None:
            md_data = MessageMarkdown(
                custom_template_id=data["markdown"]["id"],
                params=data["markdown"]["params"] if "params" in list(data["markdown"]) else None
            )
            msg = MessageSegment.markdown(md_data)

            if "keyboard" in list(data) and data["keyboard"] is not None:
                kb_data = MessageKeyboard(id=data["keyboard"]["id"])
                msg += MessageSegment.keyboard(kb_data)

            await run_kanon.send(msg)

    # 消息留言
    date_time: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if unity_channel_id.startswith("channel_") or unity_channel_id.startswith("channel_"):
        receive_type = "channel"
    elif unity_channel_id.startswith("group_") or unity_channel_id.startswith("group_"):
        receive_type = "group"
    else:
        receive_type = "private"
    msg = msg.replace("'", "‘").replace('"', "”") if msg is not None and type(msg) is str else ""

    # 非指令收集列表
    if not run and msg != "":
        conn = sqlite3.connect(f"{basepath}db/chat_bot.db")
        cursor = conn.cursor()

        cursor.execute(
            f'replace into receive_message '
            f'("time","bot_id","type","group","user","message") '
            f'values("{date_time}","{botid}","{receive_type}","{channel_id}","{user_id}","{msg}")')
        conn.commit()

        cursor.close()
        conn.close()

    conn = sqlite3.connect(f"{basepath}db/chat_bot.db")
    cursor = conn.cursor()

    cursor.execute(f'SELECT * FROM send WHERE '
                   f'"bot_id" = "{botid}" AND '
                   f'"type" = "{receive_type}" AND '
                   f'"group" = "{channel_id}" AND '
                   f'"user" = "{user_id}" AND '
                   f'"send" = "false"')
    datas = cursor.fetchall()

    for data in datas:
        message = data[5]
        msg = MessageSegment.text(message)

        cursor.execute(
            f'replace into send '
            f'("id","bot_id","type","group","user","message","send") '
            f'values("{data[0]}","{data[1]}","{data[2]}","{data[3]}","{data[4]}","{data[5]}","true")')
        conn.commit()
        await run_kanon.send(msg)

    cursor.close()
    conn.close()

    await locked()
    await run_kanon.finish()
