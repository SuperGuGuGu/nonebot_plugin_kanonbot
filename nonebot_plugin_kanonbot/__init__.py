#coding=utf-8
from nonebot import require, logger
from nonebot.plugin import PluginMetadata
import nonebot
import os
import httpx
import re
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import json
import sqlite3
import random
from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageSegment,
    Event,
    GroupMessageEvent,
    GROUP_ADMIN,
    GROUP_OWNER
)
import time
from .config import kn_config, command_list
from .bot_run import botrun



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
    adminqq = config.superusers
    adminqq = list(adminqq)
except Exception as e:
    adminqq = []
# 配置2：
try:
    basepath = config.kanon_basepath
    if "\\" in basepath:
        basepath = basepath.replace("\\", "/")
    if basepath.startswith("./"):
        basepath = os.path.abspath('.') + basepath.removeprefix(".")
        if not basepath.endswith("/"):
            basepath += "/"
    else:
        basepath += "/"
except Exception as e:
    basepath = os.path.abspath('.') + "/KanonBot/"
# 配置3：
try:
    command_starts = config.COMMAND_START
except Exception as e:
    command_starts = ["/"]

# 插件元信息，让nonebot读取到这个插件是干嘛的
__plugin_meta__ = PluginMetadata(
    name="KanonBot",
    description="KanonBot for Nonebot2",
    usage="/help",
    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。
    homepage="https://github.com/SuperGuGuGu/nonebot_plugin_bili_push",
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
    atmsg = event.get_message()["at"]
    atmsgs = []
    if len(atmsg) >= 1:
        print(str(len(atmsg)))
        for i in atmsg:
            atmsgg = str(i.data["qq"])
            atmsgg.removeprefix('[CQ:at,qq=')
            atmsgg.removesuffix(']')
            atmsgs.append(atmsgg)
    if event.is_tome():
        atmsgs.append(botid)
    msg = str(event.get_message())
    qq = event.get_user_id()
    timelong = str(time.strftime("%Y%m%d%H%M%S", time.localtime()))
    msg = re.sub(u"\\[.*?]", "", msg)
    commands = []
    if ' ' in msg:
        messages = msg.split(' ', 1)
        for command in messages:
            if not commands:
                for command_start in command_starts:
                    if command_start != "" and command.startswith(command_start):
                        command = command.removeprefix(command_start)
                        break
                commands.append(command)
            else:
                commands.append(command)
    else:
        for command_start in command_starts:
            if command_start != "" and msg.startswith(command_start):
                command = msg.removeprefix(command_start)
                break
        commands.append(msg)
    command = commands[0]

    # 创建变量内容
    code = 0
    run = "off"
    commandname = ""
    dbpath = basepath + "db/"
    configdb = dbpath + 'config.db'
    emojidbname = dbpath + 'emoji/emoji.db'
    autoreplydb = dbpath + 'autoreply/autoreply.db'

    # 判断是否响应
    commandlist = command_list()
    run = False
    if not run:
        cache_commandlist = commandlist["精准"]
        if command in cache_commandlist:
            run = True
    if not run:
        cache_commandlist = commandlist["模糊"]
        for cache_command in cache_commandlist:
            if cache_command in command:
                run = True
    if not run:
        cache_commandlist = commandlist["开头"]
        for cache_command in cache_commandlist:
            if command.startswith(cache_command):
                run = True
    if not run:
        cache_commandlist = commandlist["结尾"]
        for cache_command in cache_commandlist:
            if command.endswith(cache_command):
                run = True
    if not run:
        cache_commandlist = commandlist["精准2"]
        if command in cache_commandlist:
            run = True

    return_data = botrun()
    await run_kanon.finish()
