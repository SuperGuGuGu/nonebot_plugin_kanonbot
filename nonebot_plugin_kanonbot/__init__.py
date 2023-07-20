import shutil
from nonebot import require, logger
from nonebot.plugin import PluginMetadata
import nonebot
import os
import requests
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
import sqlite3
import re
import time

require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler


def connect_api(type: str, url: str, post_json=None, file_path: str = None):
    # 把api调用的代码放在一起，方便下一步进行异步开发
    if type == "json":
        if post_json is None:
            return json.loads(requests.get(url).text)
        else:
            return json.loads(requests.post(url, json=post_json).text)
    elif type == "image":
        return Image.open(BytesIO(requests.get(url).content))
    elif type == "file":
        cache_file_path = file_path + "cache"
        try:
            with open(cache_file_path, "wb") as f, requests.get(url) as res:
                f.write(res.content)
            logger.info("下载完成")
            shutil.copyfile(cache_file_path, file_path)
            os.remove(cache_file_path)
        except Exception as e:
            logger.error(f"文件下载出错-{file_path}")
    return


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

# 配置1：
try:
    adminqq = config.superusers
    adminqq = list(adminqq)
except Exception as e:
    adminqq = []
# 配置2：
try:
    basepath = config.bilipush_basepath
    if "\\" in basepath:
        basepath = basepath.replace("\\", "/")
    if basepath.startswith("./"):
        basepath = os.path.abspath('.') + "/" + basepath.removeprefix(".")
        if not basepath.endswith("/"):
            basepath += "/"
    else:
        basepath += "/"
except Exception as e:
    basepath = os.path.abspath('.') + "/"

# 插件元信息，让nonebot读取到这个插件是干嘛的
__plugin_meta__ = PluginMetadata(
    name="KanonBot",
    description="KanonBot for Nonebot2",
    usage="/菜单",
    type="application",
    # 发布必填，当前有效类型有：`library`（为其他插件编写提供功能），`application`（向机器人用户提供功能）。
    homepage="https://github.com/SuperGuGuGu/nonebot_plugin_bili_push",
    # 发布必填。
    supported_adapters={"~onebot.v11"},
    # 支持的适配器集合，其中 `~` 在此处代表前缀 `nonebot.adapters.`，其余适配器亦按此格式填写。
    # 若插件可以保证兼容所有适配器（即仅使用基本适配器功能）可不填写，否则应该列出插件支持的适配器。
)

# 创建基础参数
returnpath = ""
plugin_dbpath = basepath + 'db/bili_push/'
if not os.path.exists(plugin_dbpath):
    os.makedirs(plugin_dbpath)
livedb = plugin_dbpath + "bili_push.db"
heartdb = plugin_dbpath + "heart.db"
half_text = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
             "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
             "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", ",",
             ".", "/", "\\", "[", "]", "(", ")", "!", "+", "-", "*", "！", "？", "。", "，", "{", "}", "、", "‘", "“",
             '"', "'", "！", " "]

run_kanon = on_message(priority=10, block=False)

@run_kanon.handle()
async def kanon(event: Event, bot: Bot):
    # 插件内容
    await run_kanon.finish()



