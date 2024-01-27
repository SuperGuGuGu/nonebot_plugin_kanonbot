# coding=utf-8
from nonebot.plugin import PluginMetadata
import nonebot
import os
import re
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from nonebot import on_message, logger
from nonebot.adapters.kaiheila import (
    Bot,
    MessageSegment,
    Event
    )
import time
from .config import command_list, _config_list
from .bot_run import botrun
from .tools import kn_config, get_file_path, get_command, imgpath_to_url, draw_text, mix_image, connect_api, get_unity_user_id, \
    get_unity_user_data, save_unity_user_data, get_user_id, get_qq_face

try:
    config = nonebot.get_driver().config
    # 读取配置
    # -》无需修改代码文件，请在“.env”文件中改。《-
    #
    # 配置1：
    # 管理员账号SUPERUSERS
    # 需要添加管理员权限，参考如下：
    # SUPERUSERS=["12345678"]
    #
    # 配置2：
    # 文件存放目录
    # 该目录是存放插件数据的目录，参考如下：
    # bilipush_basepath="./"
    # bilipush_basepath="C:/"
    #
    # 配置3：
    # 读取自定义的命令前缀
    # COMMAND_START=["/", ""]
    #

    # 配置1
    try:
        adminqq = list(config.superusers)
    except Exception as e:
        adminqq = []
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
    # 配置3：
    try:
        command_starts = config.COMMAND_START
    except Exception as e:
        command_starts = ["/"]
    # 配置test：
    try:
        kanon_test = config.KanonBetaTest
    except Exception as e:
        kanon_test = False
except Exception as e:
    adminqq = []
    basepath = os.path.abspath('.') + "/KanonBot/"
    command_starts = ["/"]
    kanon_test = False

if "\\" in basepath:
    basepath = basepath.replace("\\", "/")

# 插件元信息，让nonebot读取到这个插件是干嘛的
__plugin_meta__ = PluginMetadata(
    name="KanonBot",
    description="KanonBot for Nonebot2",
    usage="/help",
    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。
    homepage="https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot",
    # 发布必填。
    supported_adapters={"~kaiheila"},
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
        message_event: Event,
        bot: Bot
    ):
    # 获取消息基础信息
    logger.info("bot run")
    botid = str(bot.self_id)
    user_id = message_event.get_user_id()
    platform = "Kook"

    # 获取群号
    session_id = message_event.get_session_id()  # group_频道id_用户id 或 p*_用户id
    if session_id.startswith("group"):
        channel_id = message_event.target_id
        guild_id = message_event.extra.guild_id
        unity_channel_id = f"channel_{platform}_{message_event.target_id}"
        unity_guild_id = f"channel_{platform}_{message_event.extra.guild_id}"
    else:
        guild_id = channel_id = user_id
        unity_guild_id = unity_channel_id = f"private_{platform}_{user_id}"

    msg = str(message_event.get_message())
    msg = msg.replace('"', "“").replace("'", "‘")
    msg = msg.replace("(", "（").replace(")", "）")
    msg = msg.replace("{", "（").replace("}", "）")
    msg = msg.replace("[", "【").replace("]", "】")
    commands = get_command(msg)
    command = commands[0]
    now = int(time.time())

    # 获取消息包含的图片
    # 暂无法获取图片
    imgmsgs = []
    # image_datas = message_event.get_message()['image']
    # for image_data in image_datas:
    #     image_data = str(image_data)
    #     img_url = f"{image_data.removeprefix('[').removesuffix(']')}"
    #     imgmsgs.append(img_url)

    # ## 心跳服务相关 ##
    if kn_config("botswift-state"):
        conn = sqlite3.connect(f"{basepath}db/botswift.db")
        cursor = conn.cursor()
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

        if user_id in bots_list:
            # 不相应bot的消息
            await run_kanon.finish()

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
        cursor.execute(f'select * from gameinglist where channelid = "{channel_id}"')
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
        # 获取用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)

        # 获取用户信息
        save = False
        # q频道
        # 所有用户默认5普通用户权限
        unity_user_data["permission"] = 5
        if run:
            member_data = await bot.call_api(
                "/api/v3/user/view", guild_id=guild_id, user_id=user_id
            )
            # print(f"member_data{member_data}")

            unity_user_data["avatar"] = member_data.avatar
            unity_user_data["username"] = member_data.username
            unity_user_data["nick_name"] = member_data.nickname
            unity_user_data["union_openid"] = member_data.id_
            unity_user_data["is_bot"] = member_data.bot
            save = True
        else:
            logger.error(f"get_member API请求失败guild_id：{unity_guild_id}， user_id：{user_id}")

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
        for id_ in atmsgs:
            try:
                data = await bot.get_member(guild_id=guild_id, user_id=id_)
                at_data = {
                    "id": id_,
                    "username": data.user.username,
                    "nick_name": data.nick,
                    "avatar": data.user.avatar,
                    "union_openid": data.user.union_openid,
                    "is_bot": data.user.bot
                }
                at_datas.append(at_data)
            except Exception as e:
                logger.error("获取at内容失败")

        # 获取成员名单
        friend_list = []
        group_member_list = []

        # 特定功能获取消息
        channel_member_datas = {}
        if commandname in ["群聊功能-jinrilaopo"]:
            allgroupmember_data = await bot.call_api("/api/v3/guild/user-list", guild_id=guild_id)
            print("allgroupmember_data")
            for data in allgroupmember_data.users:
                user_id = data.id_
                user_name = data.username
                nickname = data.nickname
                is_bot = data.bot
                face_url = data.avatar
                user_status = data.status  # 貌似是权限

                channel_member_datas[user_id] = {
                    "user_id": user_id,
                    "user_name": user_name,
                    "nickname": nickname,
                    "is_bot": is_bot,
                    "face_url": face_url,
                    "user_status": user_status
                    }

        msg = re.sub(u"<.*?>", "", msg)
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
            "event_name": "message_event",
            "platform": platform,
            "friend_list": friend_list,
            "channel_member_datas": channel_member_datas,
        }
        logger.info(msg_info)
        data = await botrun(msg_info)
        logger.info(data)
        # 获取返回信息，进行回复
        code = int(data["code"])
        if code in [1, 3, 4, 5]:
            msg = MessageSegment.text(data["message"])
            if channel_id.startswith("private"):
                await bot.send_msg(
                    message_type="private",
                    user_id=user_id,
                    message=msg
                )
            else:
                await bot.send_msg(
                    message_type="channel",
                    channel_id=channel_id,
                    message=msg
                )
        if code in [2, 3, 4, 5]:
            imageurl = await bot.upload_file(data["returnpath"])
            msg = MessageSegment.image(imageurl)
            if channel_id.startswith("private"):
                await bot.send_msg(
                    message_type="private",
                    user_id=user_id,
                    message=msg
                )
            else:
                await bot.send_msg(
                    message_type="channel",
                    channel_id=channel_id,
                    message=msg
                )
        if code in [4, 5]:
            imageurl = await bot.upload_file(data["returnpath2"])
            msg = MessageSegment.image(imageurl)
            if channel_id.startswith("private"):
                await bot.send_msg(
                    message_type="private",
                    user_id=user_id,
                    message=msg
                )
            else:
                await bot.send_msg(
                    message_type="channel",
                    channel_id=channel_id,
                    message=msg
                )
        if code in [5]:
            imageurl = await bot.upload_file(data["returnpath3"])
            msg = MessageSegment.image(imageurl)
            if channel_id.startswith("private"):
                await bot.send_msg(
                    message_type="private",
                    user_id=user_id,
                    message=msg
                )
            else:
                await bot.send_msg(
                    message_type="channel",
                    channel_id=channel_id,
                    message=msg
                )
    await run_kanon.finish()
