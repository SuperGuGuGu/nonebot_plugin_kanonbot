# coding=utf-8
import httpx
from nonebot.plugin import PluginMetadata
import os
import re
import sqlite3
from nonebot import on_message, logger
from nonebot.adapters.feishu import (
    Bot,
    MessageSegment,
    Event,
    GroupMessageEvent,
    MessageEvent
)
import time
from .config import command_list, _config_list
from .bot_run import botrun
from .tools import (kn_config, get_file_path, get_command, imgpath_to_url, draw_text, mix_image, connect_api,
                    get_unity_user_id, get_unity_user_data, save_unity_user_data, get_user_id, get_qq_face, _config)


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
    supported_adapters={"~feishu"},
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

run_kanon = on_message(priority=10, block=False)


@run_kanon.handle()
async def kanon(
        message_event: MessageEvent,
        event: Event,
        bot: Bot
    ):
    # 获取消息基础信息
    botid = str(bot.self_id)

    event_name = message_event.get_event_name()
    user_id = message_event.get_user_id()
    platform = "feishu"

    # 获取群号
    if isinstance(message_event, GroupMessageEvent):
        # 群消息才有群号
        guild_id = channel_id = message_event.get_session_id().split("_")[1]
        unity_guild_id = unity_channel_id = f"group_{platform}_{channel_id}"
    else:
        # 这是用户id
        guild_id = channel_id = user_id
        unity_guild_id = unity_channel_id = f"private_{platform}_{channel_id}"

    msg = str(message_event.get_message())
    msg = msg.replace('"', "“").replace("'", "‘")
    msg = msg.replace("(", "（").replace(")", "）")
    msg = msg.replace("{", "（").replace("}", "）")
    msg = msg.replace("[", "【").replace("]", "】")
    commands = get_command(msg)
    command = commands[0]
    now = int(time.time())

    # ## 心跳服务相关 ##
    if kn_config("botswift-state"):
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
    run = True
    if run:
        # 创建变量内容
        code = 0

        # 获取用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)

        # 获取用户信息
        save = False
        data = await bot.call_api(f"contact/v3/users/{user_id}",method="get")
        if data["code"] == 0:
            user_data = data["data"]["user"]
            unity_user_data["avatar"] = user_data["avatar"]["avatar_origin"]
            unity_user_data["username"] = user_data["name"]
            unity_user_data["is_bot"] = False
            save = True
        else:
            logger.error("用户详情api请求失败")
            logger.error(data)

        # 同步unity数据
        if "user_id" not in list(unity_user_data):
            unity_user_data["user_id"] = unity_user_id
            save = True
        if "username" not in list(unity_user_data):
            unity_user_data["username"] = "user"
            save = True
        if "nick_name" not in list(unity_user_data):
            unity_user_data["nick_name"] = None
            save = True
        if "permission" not in list(unity_user_data):
            unity_user_data["permission"] = 5
            save = True
        if "avatar" not in list(unity_user_data):
            unity_user_data["avatar"] = None
            save = True
        if "face_image" not in list(unity_user_data) and unity_user_data["avatar"] is not None:
            image_path = f"{basepath}file/user_face/"
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            image_path += f"{unity_user_id}.png"
            image = await connect_api("image", unity_user_data["avatar"])
            image.save(image_path)
            unity_user_data["face_image"] = image_path
            save = True
        if "face_image" not in list(unity_user_data) and unity_user_data["avatar"] is None:
            cache_user_id = get_user_id("qq", unity_user_id)
            if cache_user_id is not None:
                image_path = f"{basepath}file/user_face/"
                if not os.path.exists(image_path):
                    os.makedirs(image_path)
                image_path += f"{unity_user_id}.png"
                image = get_qq_face(cache_user_id)
                image.save(image_path)
                image_path = "{basepath}" + f"file/user_face/{unity_user_id}.png"
                unity_user_data["face_image"] = image_path
                save = True
        if save:
            unity_user_data = save_unity_user_data(unity_user_id, unity_user_data)

        # 获取消息包含的图片
        imgmsgs = []
        image_key = str(message_event.get_message()['image'])
        image_key = image_key.removeprefix("[image:").removesuffix("]")
        # 待完善：缓存收到的图片文件，并转为路径
        if image_key != "":
            msg = msg.replace(f"【image:{image_key}】", "")
            imgmsgs.append(f"{image_key}")

        # 获取at内容
        atids = []
        num = -1
        for m in msg:
            num += 1
            if m == "@":
                test_num = 5  # 跳过前面"@ou_"的前缀
                while test_num < 50:
                    test_num += 1
                    at_id = msg[num:(num + test_num)]
                    if not re.match("^[a-z0-9]+", msg[(num + test_num):(num + test_num + 1)]):
                        atids.append(at_id.removeprefix("@"))

        # 删除原始消息中at的内容
        for at_user_id in atids:
            msg = msg.replace(f"@{at_user_id} ", "")

        # 获取at对象用户的信息
        at_datas = []
        for at_user_id in atids:
            try:
                data = await bot.call_api(f"contact/v3/users/{at_user_id}", method="get")
                at_data = {
                    "id": at_user_id,
                    "username": data["data"]["user"]["name"],
                    "avatar": data["data"]["user"]["avatar"]["avatar_origin"],
                }
                at_datas.append(at_data)
            except Exception as e:
                logger.error("获取at内容失败")

        # 获取成员名单
        friend_datas = {}
        channel_member_datas = {}

        commands = get_command(msg)
        # 组装信息，进行后续响应
        msg_info = {
            "msg": msg,
            "commands": commands,
            "commandname": commandname,
            "bot_id": botid,
            "channel_id": unity_channel_id,
            "guild_id": unity_guild_id,
            "at_datas": at_datas,
            "user": unity_user_data,
            "imgmsgs": imgmsgs,
            "event_name": event_name,
            "platform": platform,
            "friend_list": [],  # 兼容内容，未来将删除
            "friend_datas": friend_datas,
            "channel_member_datas": channel_member_datas
        }
        logger.debug(msg_info)
        data = await botrun(msg_info)
        logger.debug(data)
        # 获取返回信息，进行回复
        code = int(data["code"])

        if code == 0:
            await run_kanon.finish()

        async def upload_image(image_path):
            params = {
                "method": "POST",
                "data": {"image_type": "message"},
                "files": {"image": ("file", open(image_path, "rb"))}
            }
            result = await bot.call_api("im/v1/images", **params)
            return result["data"]["image_key"]

        if code == 1:
            message = data["message"]
            msg = MessageSegment.text(message)
            await run_kanon.send(msg)

        elif code == 2:
            img_key = await upload_image(data["returnpath"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

        elif code == 3:
            message = data["message"]
            msg = MessageSegment.text(message)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

        elif code == 4:
            message = data["message"]
            msg = MessageSegment.text(message)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath2"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

        elif code == 5:
            message = data["message"]
            msg = MessageSegment.text(message)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath2"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

            img_key = await upload_image(data["returnpath3"])
            msg = MessageSegment.image(img_key)
            await run_kanon.send(msg)

        else:
            pass

    await run_kanon.finish()

