# coding=utf-8
from nonebot.plugin import PluginMetadata
import nonebot
import os
import re
import sqlite3
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageSegment,
    Event,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER
)
import time
from .config import command_list, _config_list
from .bot_run import botrun
from .tools import kn_config, get_file_path, get_command, get_unity_user_id, get_unity_user_data, connect_api, \
    save_unity_user_data

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

run_kanon = on_message(priority=10, block=False)


@run_kanon.handle()
async def kanon(event: Event, bot: Bot):
    # 获取消息基础信息
    botid = str(bot.self_id)
    user_id = str(event.get_user_id())
    platform = "qq"

    # 获取群号
    if isinstance(event, GroupMessageEvent):
        # 群消息
        unity_guild_id = unity_channel_id = f"group_{platform}_{event.group_id}"
        guild_id = channel_id = event.group_id
    else:
        # 私聊
        unity_guild_id = unity_channel_id = f"private_{platform}_{user_id}"
        guild_id = channel_id = user_id

    # 黑白名单
    if unity_channel_id in kn_config("plugin-channel_black_list"):
        await run_kanon.finish()  # 黑名单直接退出
    elif unity_channel_id in kn_config("plugin-channel_white_list"):
        pass  # 白名单继续运行
    else:
        pass  # 继续运行

    msg = str(event.get_message())
    msg = re.sub(u"\\[.*?]", "", msg)  # 去除cq码
    msg = msg.replace('"', "“").replace("'", "‘")  # 转换同义符
    msg = msg.replace("(", "（").replace(")", "）")  # 转换同义符
    msg = msg.replace("{", "（").replace("}", "）")  # 转换同义符
    msg = msg.replace("[", "【").replace("]", "】")  # 转换同义符
    msg = msg.replace('"', "'")  # 转换同义符
    commands = get_command(msg)
    command = commands[0]

    date = str(time.strftime("%Y-%m-%d", time.localtime()))
    date_year = str(time.strftime("%Y", time.localtime()))
    date_month = str(time.strftime("%m", time.localtime()))
    date_day = str(time.strftime("%d", time.localtime()))
    time_now = str(int(time.time()))

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
                           f'values("{user_id}", "0", "{time_now}")')
            conn.commit()
        cursor.close()
        conn.close()

    # 判断是否响应
    commandname = ""
    commandlist = command_list()
    config_list = _config_list()
    run = False

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
            commandname = "emoji"
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
    if run:
        # 创建变量内容
        code = 0

        # 获取用户信息
        unity_user_id = get_unity_user_id(platform, user_id)
        unity_user_data = get_unity_user_data(unity_user_id)
        save = False

        if unity_user_id in kn_config("plugin-user_black_list"):
            await run_kanon.finish()  # 黑名单直接退出
        elif unity_user_id in kn_config("plugin-user_white_list"):
            pass  # 白名单继续运行
        else:
            pass  # 继续运行

        try:
            data = await bot.get_stranger_info(user_id=int(user_id), no_cache=False)
            unity_user_data["username"] = data["nickname"]
            unity_user_data["sex"] = data["sex"]
            save = True
        except Exception as e:
            logger.error("用户信息接口失效")

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
        unity_user_data["avatar"] = f"https://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
        if "face_image" not in list(unity_user_data):
            image_path = f"{basepath}file/user_face/"
            if not os.path.exists(image_path):
                os.makedirs(image_path)
            image_path += f"{unity_user_id}.png"
            image = await connect_api("image", unity_user_data["avatar"])
            image.save(image_path)
            unity_user_data["face_image"] = image_path
            save = True
        if save is True:
            unity_user_data = save_unity_user_data(unity_user_id, unity_user_data)

        # 获取at内容
        atmsg = event.get_message()["at"]
        at_datas = []
        if len(atmsg) >= 1:
            for i in atmsg:
                atmsgg = str(i.data["qq"])
                atmsgg.removeprefix('[CQ:at,qq=')
                atmsgg.removesuffix(']')
                at_datas.append({"id": atmsgg, "platform": "qq"})

        # 获取消息内容
        friend_list = []
        group_member_list = []
        channel_member_datas = {}
        if isinstance(event, GroupMessageEvent):
            # 群消息
            commandname_list = ["jinrilaopo"]
            if commandname in commandname_list:
                try:
                    group_member_list = await bot.get_group_member_list(group_id=int(channel_id))
                except Exception as e:
                    logger.error("获取群成员列表出错")
                    group_member_list = []
            for group_member in group_member_list:
                channel_member_datas[group_member] = {
                    "user_id": user_id,
                }

            # 获取用户权限
            if await GROUP_ADMIN(bot, event):
                info_premission = '5'  # 管理员
            elif await GROUP_OWNER(bot, event):
                info_premission = '10'  # 群主
            else:
                info_premission = '0'  # 群员
            # 如果群聊内at机器人，则添加at信息。
            if event.is_tome():
                at_datas.append({"id": botid, "platform": platform})
        else:
            # 私聊
            pass

        # 获取消息包含的图片
        imgmsgmsg = event.get_message()["image"]
        imgmsgs = []
        if len(imgmsgmsg) >= 1:
            for i in imgmsgmsg:
                imgmsgg = str(i.data["url"])
                imgmsgs.append(imgmsgg)
        else:
            imgmsgs = []

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
            "channel_member_datas": channel_member_datas
        }
        logger.info(msg_info)
        data = await botrun(msg_info)
        logger.info(data)
        # 获取返回信息，进行回复
        code = int(data["code"])

        if code == 0:
            pass
        elif code == 1:
            message = data["message"]
            msg = MessageSegment.text(message)
            at = data["at"]
            if at is not False:
                msgat = MessageSegment.at(at)
                msgn = MessageSegment.text('\n')
                msg = msgat + msgn + msg
            await run_kanon.finish(msg)
        elif code == 2:
            imgpath = data["returnpath"]
            msg = MessageSegment.image(r"file:///" + imgpath)
            at = data["at"]
            if at is not False:
                msgat = MessageSegment.at(at)
                msg = msgat + msg
            await run_kanon.finish(msg)
        elif code == 3:
            at = data["at"]
            message = data["message"]
            imgpath = data["returnpath"]
            msg1 = MessageSegment.text(message)
            msg2 = MessageSegment.image(r"file:///" + imgpath)
            if at is not False:
                msgat = MessageSegment.at(at)
                msgn = MessageSegment.text('\n')
                msg = msgat + msgn + msg1 + msg2
            else:
                msg = msg1 + msg2
            await run_kanon.finish(msg)
        elif code == 4:
            imgpath = data["returnpath"]
            imgpath2 = data["returnpath2"]
            msg1 = MessageSegment.image(r"file:///" + imgpath)
            msg2 = MessageSegment.image(r"file:///" + imgpath2)
            message = data["message"]
            msg0 = MessageSegment.text(message)
            msg = msg0 + msg1 + msg2
            await run_kanon.finish(msg)
        elif code == 5:
            imgpath = data["returnpath"]
            imgpath2 = data["returnpath2"]
            imgpath3 = data["returnpath3"]
            msg1 = MessageSegment.image(r"file:///" + imgpath)
            msg2 = MessageSegment.image(r"file:///" + imgpath2)
            msg3 = MessageSegment.image(r"file:///" + imgpath3)
            message = data["message"]
            msg0 = MessageSegment.text(message)
            msg = msg0 + msg1 + msg2 + msg3
            await run_kanon.finish(msg)
        else:
            pass
    await run_kanon.finish()
