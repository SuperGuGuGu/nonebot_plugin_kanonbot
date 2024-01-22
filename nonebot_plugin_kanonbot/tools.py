# coding=utf-8
import re
import string
import httpx
import requests
import toml
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import sqlite3
import random
import json
from nonebot import logger
import nonebot
import os
import shutil
import asyncio
import time

# 读取配置文件
try:
    config = nonebot.get_driver().config
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
except Exception as e:
    basepath = os.path.abspath('.') + "/KanonBot/"
    command_starts = ["/"]

if "\\" in basepath:
    basepath = basepath.replace("\\", "/")


def get_command(msg: str) -> list:
    """
    使用空格和换行进行切分1次
    :param msg: 原始字符串。"hello world"
    :return: 切分后的内容["hello", "world"]
    """
    # 去除前后空格
    while len(msg) > 0 and msg.startswith(" "):
        msg = msg.removeprefix(" ")
    while len(msg) > 0 and msg.endswith(" "):
        msg = msg.removesuffix(" ")
    if "<" in msg:
        msg = msg.replace("<", " <", 1)
    # 删除图片等内容
    msg = re.sub(u"<.*?>", "", msg)
    msg = re.sub(u"\\[.*?]", "", msg)
    # 分割命令
    commands = []
    if ' ' in msg or '\n' in msg or '<' in msg:
        messages = msg.split(' ', 1)
        for command in messages:
            if "\n" in command:
                command2 = command.split('\n', 1)
                for command in command2:
                    if not commands:
                        for command_start in command_starts:
                            if command_start != "" and command.startswith(command_start):
                                command = command.removeprefix(command_start)
                                break
                        commands.append(command)
                    else:
                        commands.append(command)
            else:
                if not commands:
                    for command_start in command_starts:
                        if command_start != "" and command.startswith(command_start):
                            command = command.removeprefix(command_start)
                            break
                    commands.append(command)
                else:
                    commands.append(command)
    else:
        command = msg
        for command_start in command_starts:
            if command_start != "" and msg.startswith(command_start):
                command = msg.removeprefix(command_start)
                break
        commands.append(command)
    return commands


def kn_config(config_name: str):
    """
    获取配置。
    获取"kanon_api-url"时，相当于获取"config["kanon_api"]["url"]"的配置项
    :param config_name: 获取的配置名称
    :return: 配置内容
    """
    path = basepath + "kanon_config.toml"

    def save_config():
        with open(path, 'w') as config_file:
            toml.dump(config, config_file)

    if not os.path.exists(path):
        config = {
            "Kanon_Config": {
                "KanonBot": "https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot"},
            "knapi": {
                "url": "http://cdn.kanon.ink"}}
        save_config()
        nonebot.logger.info("未存在KanonBot配置文件，正在创建")
    config = toml.load(path)

    # 下面这堆代码自己都快看不懂了，有空再重构一下
    # 用“-”来分段
    config_group = config_name
    if config_name == "kanon_api-url":
        if "kanon_api" in list(config):
            if "url" not in list(config["kanon_api"]):
                config["kanon_api"]["url"] = "http://cdn.kanon.ink"
                save_config()
        else:
            config["kanon_api"] = {"url": "http://cdn.kanon.ink"}
            save_config()
        return config["kanon_api"]["url"]
    elif config_name == "kanon_api-state":
        if "kanon_api" in list(config):
            if "state" not in list(config["kanon_api"]):
                config["kanon_api"]["state"] = True
                save_config()
        else:
            config["kanon_api"] = {"state": True}
            save_config()
        return config["kanon_api"]["state"]
    elif config_name == "kanon_api-unity_key":
        if "kanon_api" in list(config):
            if "unity_key" not in list(config["kanon_api"]):
                config["kanon_api"]["unity_key"] = "none"
                save_config()
        else:
            config["kanon_api"] = {"unity_key": "none"}
            save_config()
        return config["kanon_api"]["unity_key"]
    elif config_name == "emoji-state":
        if "emoji" in list(config):
            if "state" not in list(config["emoji"]):
                config["emoji"]["state"] = True
                save_config()
        else:
            config["emoji"] = {"state": True}
            save_config()
        return config["emoji"]["state"]
    elif config_name == "emoji-mode":
        if "emoji" in list(config):
            if "mode" not in list(config["emoji"]):
                config["emoji"]["mode"] = "file"
                save_config()
        else:
            config["emoji"] = {"mode": "file"}
            save_config()
        return config["emoji"]["mode"]
    elif config_name == "botswift-state":
        if "botswift" in list(config):
            if "state" not in list(config["botswift"]):
                config["botswift"]["state"] = False
                save_config()
        else:
            config["botswift"] = {"state": False}
            save_config()
        return config["botswift"]["state"]
    elif config_name == "botswift-ignore_list":
        if "botswift" in list(config):
            if "ignore_list" not in list(config["botswift"]):
                config["botswift"]["ignore_list"] = []
                save_config()
        else:
            config["botswift"] = {"ignore_list": []}
            save_config()
        return config["botswift"]["ignore_list"]
    elif config_name == "plugin-channel_white_list":
        if "plugin" in list(config):
            if "channel_white_list" not in list(config["plugin"]):
                config["plugin"]["channel_white_list"] = []
                save_config()
        else:
            config["plugin"] = {"channel_white_list": []}
            save_config()
        return config["plugin"]["channel_white_list"]
    elif config_name == "plugin-channel_black_list":
        if "plugin" in list(config):
            if "channel_black_list" not in list(config["plugin"]):
                config["plugin"]["channel_black_list"] = []
                save_config()
        else:
            config["plugin"] = {"channel_black_list": []}
            save_config()
        return config["plugin"]["channel_black_list"]
    elif config_name == "plugin-user_white_list":
        if "plugin" in list(config):
            if "user_white_list" not in list(config["plugin"]):
                config["plugin"]["user_white_list"] = []
                save_config()
        else:
            config["plugin"] = {"user_white_list": []}
            save_config()
        return config["plugin"]["user_white_list"]
    elif config_name == "plugin-user_black_list":
        if "plugin" in list(config):
            if "user_black_list" not in list(config["plugin"]):
                config["plugin"]["user_black_list"] = []
                save_config()
        else:
            config["plugin"] = {"user_black_list": []}
            save_config()
        return config["plugin"]["user_black_list"]
    elif config_name == "plugin-bot_list":
        if "plugin" in list(config):
            if "bot_list" not in list(config["plugin"]):
                config["plugin"]["bot_list"] = []
                save_config()
        else:
            config["plugin"] = {"bot_list": []}
            save_config()
        return config["plugin"]["bot_list"]
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    return False


def get_qq_face(qq, size: int = 640):
    """
    获取q头像
    :param qq: int。例："123456", 123456
    :param size: int。例如: 100, 200, 300
    """
    faceapi = f"https://q1.qlogo.cn/g?b=qq&nk={qq}&s=640"
    response = httpx.get(faceapi)
    image_face = Image.open(BytesIO(response.content))
    image_face = image_face.resize((size, size))
    return image_face


def list_in_list(list_1: list, list_2: list):
    """
    判断数列是否在数列内
    :param list_1: list or str。例：["a", "b"], "abc"
    :param list_2: list。例：["a", "b"]
    """
    for cache_list_2 in list_2:
        if cache_list_2 in list_1:
            return True
    return False


def start_with_list(msg: str, texts: list)  -> bool:
    for text in texts:
        if msg.startswith(text):
            return True
    return False


async def connect_api(
        type: str,
        url: str,
        post_json=None,
        file_path: str = None,
        failure_message: str = None):
    logger.debug(f"connect_api请求URL：{url}")
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"}
    if type == "json":
        if post_json is None:
            return json.loads(httpx.get(url, headers=h).text)
        else:
            return json.loads(httpx.post(url, json=post_json, headers=h).text)
    elif type == "image":
        if url in ["none", "None"] or url is None:
            image = await draw_text("获取图片出错", 50, 10)
        else:
            image = Image.open(BytesIO(httpx.get(url).content))
        return image
    elif type == "file":
        cache_file_path = file_path + "cache"
        try:
            f = open(cache_file_path, "wb")
            res = httpx.get(url, headers=h).content
            f.write(res)
            f.close()
            logger.debug(f"下载完成-{file_path}")
            shutil.copyfile(cache_file_path, file_path)
            os.remove(cache_file_path)
        except Exception as e:
            logger.error(f"文件下载出错-{e}, {file_path}")
    return


async def get_file_path(file_name) -> str:
    """
    获取文件的路径信息，如果没下载就下载下来
    :param file_name: 文件名。例：“file.zip”
    :return: 文件路径。例："c:/bot/cache/file/file.zip"
    """
    file_path = basepath + "file/"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_path += file_name
    if not os.path.exists(file_path):
        # 如果文件未缓存，则缓存下来
        logger.info("正在下载" + file_name)
        url = f"{kn_config('kanon_api-url')}/file/{file_name}"
        await connect_api(type="file", url=url, file_path=file_path)
    return file_path


async def lockst(lockdb):
    """
    如有其他指令在运行，则暂停该函数
    :param lockdb: 数据库路径
    :return:
    """
    sleeptime = random.randint(1, 200)
    sleeptime = float(sleeptime) / 100
    # 随机随眠0.01-2秒，避免同时收到消息进行处理
    await asyncio.sleep(sleeptime)
    # 读取锁定
    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "lock" not in tables:
            cursor.execute('create table lock (name VARCHAR(10) primary key, lock VARCHAR(20))')
        # 查询数据
        cursor.execute('select * from lock where name = "lock"')
        locking = cursor.fetchone()
    except Exception as e:
        logger.error("")
        locking = ["lock", "off"]
    finally:
        cursor.close()
        conn.close()

    # 判断锁定
    if locking is not None:
        if locking[1] == 'on':
            num = 50
            while num >= 1:
                num -= 1
                conn = sqlite3.connect(lockdb)
                cursor = conn.cursor()
                try:
                    cursor.execute('select * from lock where name = "lock"')
                    locking = cursor.fetchone()
                except Exception as e:
                    logger.error("线程锁读取错误")
                    num = 0
                cursor.close()
                conn.close()
                if locking[1] == 'on':
                    await asyncio.sleep(0.3)
                    if num == 0:
                        logger.error("等待超时")
                else:
                    num = 0

    # 锁定
    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
    cursor.execute('replace into lock(name,lock) values("lock","on")')
    cursor.close()
    conn.commit()
    conn.close()

    return locking


def locked(lockdb):
    # 解锁
    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
    cursor.execute('replace into lock(name,lock) values("lock","off")')
    cursor.close()
    conn.commit()
    conn.close()
    locking = 'off'
    return locking


def command_cd(user_id, groupcode, timeshort: int, coolingdb):
    cooling = 'off'
    # 冷却时间，单位S
    coolingtime = '60'
    # 冷却数量，单位条
    coolingnum = 12
    # 冷却长度，单位S
    coolinglong = 150

    # 尝试创建数据库
    coolingnumber = str('0')

    conn = sqlite3.connect(coolingdb)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if groupcode not in tables:
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        cursor.execute(
            f'create table {groupcode} (userid VARCHAR(10) primary key,'
            f' number VARCHAR(20), time VARCHAR(30), cooling VARCHAR(30))')
    # 读取数据库内容：日期文件，群号表，用户数据
    # 查询数据
    cursor.execute(f'select * from "{groupcode}" where userid = "{user_id}"')
    data = cursor.fetchone()
    try:
        if data is None:
            coolingnumber = '1'
            cooling = 'off'
            cursor.execute(
                f'replace into {groupcode}(userid,number,time,cooling) '
                f'values("{user_id}","{coolingnumber}","{timeshort}","{cooling}")')
        else:
            # 判断是否正在冷却
            cooling = data[3]
            if cooling == 'off':
                #  判断时间，time-冷却时间再判断
                timeshortdata = int(data[2]) + int(coolingtime)
                if timeshortdata >= timeshort:
                    # 小于冷却时间，冷却次数+1
                    coolingnumber = int(data[1]) + 1
                    #    判断冷却次数，次数>=冷却数量
                    if coolingnumber >= coolingnum:
                        cooling = 'on'
                        # 大于次数，开启冷却,写入
                        coolingnumber = str(coolingnumber)
                        cursor.execute(
                            f'replace into {groupcode}(userid,number,time,cooling) '
                            f'values("{user_id}","{coolingnumber}","{timeshort}","{cooling}")')
                        timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
                        coolingtime = str(timeshortdata - timeshort)
                    else:
                        # 小于写入

                        cooling = 'off'
                        coolingnumber = str(coolingnumber)
                        cursor.execute(
                            f'replace into {groupcode}(userid,number,time,cooling) '
                            f'values("{user_id}","{coolingnumber}","{timeshort}","{cooling}")')
                else:
                    # 大于冷却时间，重新写入
                    coolingnumber = '1'
                    cooling = 'off'
                    cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{user_id}","{coolingnumber}","{timeshort}","{cooling}")')
            else:
                timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
                if timeshortdata >= timeshort:
                    coolingtime = str(timeshortdata - timeshort)
                else:
                    coolingnumber = '1'
                    cooling = 'off'
                    cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{user_id}","{coolingnumber}","{timeshort}","{cooling}")')
        if cooling != 'off':
            cooling = str(coolingtime)
    except Exception as e:
        logger.error("冷却数据库操作出错")
        logger.error(coolingdb)
        cooling = "off"
    finally:
        conn.commit()
        cursor.close()
        conn.close()
    return cooling


async def draw_text(texts: str,
              size: int,
              textlen: int = 20,
              fontfile: str = "",
              text_color="#000000",
              biliemoji_infos=None,
              draw_qqemoji=False,
              calculate=False
              ):
    """
    - 文字转图片

    :param texts: 输入的字符串
    :param size: 文字尺寸
    :param textlen: 一行的文字数量
    :param fontfile: 字体文字
    :param text_color: 字体颜色，例："#FFFFFF"、(10, 10, 10)
    :param biliemoji_infos: 识别emoji
    :param draw_qqemoji: 识别qqemoji
    :param calculate: 计算长度。True时只返回空白图，不用粘贴文字，加快速度。

    :return: 图片文件（RGBA）
    """

    def get_font_render_w(text):
        if text == " ":
            return 20
        none = ["\n", ""]
        if text in none:
            return 1
        canvas = Image.new('RGB', (500, 500))
        draw = ImageDraw.Draw(canvas)
        draw.text((0, 0), text, font=font, fill=(255, 255, 255))
        bbox = canvas.getbbox()
        # 宽高
        # size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
        if bbox is None:
            return 0
        return bbox[2]

    async def is_emoji(emoji):
        if kn_config("kanon_api-state") is not True:
            return False
        else:
            try:
                conn = sqlite3.connect(await get_file_path("emoji_1.db"))
                cursor = conn.cursor()
                cursor.execute(f'select * from emoji where emoji = "{emoji}"')
                data = cursor.fetchone()
                cursor.close()
                conn.close()
                if data is not None:
                    return True
                else:
                    return False
            except Exception as e:
                return False

    async def get_emoji(emoji):
        cachepath = basepath + "cache/emoji/"
        if not os.path.exists(cachepath):
            os.makedirs(cachepath)
        cachepath = cachepath + emoji + ".png"
        if not os.path.exists(cachepath):
            if kn_config("kanon_api-state") is True and (await is_emoji(emoji)) is True:
                url = f"{kn_config('kanon_api-url')}/api/emoji?imageid={emoji}"
                try:
                    return_image = await connect_api("image", url)
                    return_image.save(cachepath)
                except Exception as e:
                    logger.info("api出错，请联系开发者")
                    # api出错时直接打印文字
                    return_image = Image.new("RGBA", (100, 100), color=(0, 0, 0, 0))
                    draw = ImageDraw.Draw(return_image)
                    draw.text((0, 0), emoji, fill="#000000", font=font)
                    return_image.paste(return_image, (0, 0), mask=return_image)
            else:
                # 不使用api，直接打印文字
                return_image = Image.new("RGBA", (100, 100), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(return_image)
                draw.text((0, 0), emoji, fill="#000000", font=font)
                return_image.paste(return_image, (0, 0), mask=return_image)
        else:
            return_image = Image.open(cachepath, mode="r")
        return return_image

    fortsize = size
    if kn_config("kanon_api-state") is True:
        if fontfile == "":
            fontfile = await get_file_path("腾祥嘉丽中圆.ttf")
    else:
        fontfile = await get_file_path("NotoSansSC[wght].ttf")
    font = ImageFont.truetype(font=fontfile, size=fortsize)

    # 计算图片尺寸
    print_x = 0
    print_y = 0
    jump_num = 0
    text_num = -1
    for text in texts:
        text_num += 1
        if jump_num > 0:
            jump_num -= 1
        else:
            if (textlen * fortsize) < print_x or text == "\n":
                print_x = 0
                print_y += 1.3 * fortsize
                if text == "\n":
                    continue
            biliemoji_name = None
            if biliemoji_infos is not None:
                # 检测biliemoji
                if text == "[":
                    emoji_len = 0
                    while emoji_len < 50:
                        emoji_len += 1
                        emoji_end = text_num + emoji_len
                        if texts[emoji_end] == "[":
                            # 不是bili emoji，跳过
                            emoji_len = 60
                        elif texts[emoji_end] == "]":
                            biliemoji_name = texts[text_num:emoji_end + 1]
                            jump_num = emoji_len
                            emoji_len = 60
            if biliemoji_name is not None:
                for biliemoji_info in biliemoji_infos:
                    emoji_name = biliemoji_info["emoji_name"]
                    if emoji_name == biliemoji_name:
                        print_x += fortsize
            else:
                if (await is_emoji(text)) is True:
                    print_x += fortsize
                elif text in ["\n", " "]:
                    if text == " ":
                        print_x += get_font_render_w(text) + 2
                else:
                    print_x += get_font_render_w(text) + 2

    x = int((textlen + 1.5) * size)
    y = int(print_y + 1.2 * size)

    image = Image.new("RGBA", size=(x, y), color=(0, 0, 0, 0))  # 生成透明图片
    draw_image = ImageDraw.Draw(image)

    # 绘制文字
    if calculate is False:
        print_x = 0
        print_y = 0
        jump_num = 0
        text_num = -1
        for text in texts:
            text_num += 1
            if jump_num > 0:
                jump_num -= 1
            else:
                if (textlen * fortsize) < print_x or text == "\n":
                    print_x = 0
                    print_y += 1.3 * fortsize
                    if text == "\n":
                        continue
                biliemoji_name = None
                if biliemoji_infos is not None:
                    # 检测biliemoji
                    if text == "[":
                        emoji_len = 0
                        while emoji_len < 50:
                            emoji_len += 1
                            emoji_end = text_num + emoji_len
                            if texts[emoji_end] == "[":
                                # 不是bili emoji，跳过
                                emoji_len = 60
                            elif texts[emoji_end] == "]":
                                biliemoji_name = texts[text_num:emoji_end + 1]
                                jump_num = emoji_len
                                emoji_len = 60
                if biliemoji_name is not None:
                    for biliemoji_info in biliemoji_infos:
                        emoji_name = biliemoji_info["emoji_name"]
                        if emoji_name == biliemoji_name:
                            emoji_url = biliemoji_info["url"]
                            try:
                                paste_image = await connect_api("image", emoji_url)
                            except Exception as e:
                                paste_image = await draw_text("获取图片出错", 50, 10)
                                logger.error(f"获取图片出错:{e}")
                            paste_image = paste_image.resize((int(fortsize * 1.2), int(fortsize * 1.2)))
                            image.paste(paste_image, (int(print_x), int(print_y)))
                            print_x += fortsize
                else:
                    if (await is_emoji(text)) is True:
                        paste_image = await get_emoji(text)
                        paste_image = paste_image.resize((int(fortsize * 1.1), int(fortsize * 1.1)))
                        image.paste(paste_image, (int(print_x), int(print_y)), mask=paste_image)
                        print_x += fortsize
                    elif text in ["\n", " "]:
                        if text == " ":
                            print_x += get_font_render_w(text) + 2
                    else:
                        draw_image.text(xy=(int(print_x), int(print_y)),
                                        text=text,
                                        fill=text_color,
                                        font=font)
                        print_x += get_font_render_w(text) + 2
        # 把输出的图片裁剪为只有内容的部分
        bbox = image.getbbox()
        if bbox is None:
            box_image = Image.new("RGBA", (2, fortsize), (0, 0, 0, 0))
        else:
            box_image = Image.new("RGBA", (bbox[2] - bbox[0], bbox[3] - bbox[1]), (0, 0, 0, 0))
            box_image.paste(image, (0 - int(bbox[0]), 0 - int(bbox[1])), mask=image)
        image = box_image
    return image


async def imgpath_to_url(imgpath):
    """
    图片路径转url
    :param imgpath: 图片的路径
    :return: 图片的url
    """
    if read == me:
        pass
    """
    这里会运行报错，因为图片转链接功能需要图床的支持。请用户自行适配。
    QQ适配器发送图片需要发送url让qq请求。
    """
    return imgurl


def mix_image(image_1, image_2, mix_type = 1):
    """
    将两张图合并为1张
    :param image_1: 要合并的图像1
    :param image_2: 要合并的图像2
    :param mix_type: 合成方式。1：竖向
    :return:
    """
    images = Image.new("RGB", (10, 10), "#FFFFFF")
    if mix_type == 1:
        x1, y1 = image_1.size
        x2, y2 = image_2.size
        if image_1.mode == "RGB":
            image_1 = image_1.convert("RGBA")
        if image_2.mode == "RGB":
            image_2 = image_2.convert("RGBA")

        if x1 > x2:
            x2_m = x1
            y2_m = int(x2_m * x1 / y1)
            images = Image.new("RGB", (x2_m, y2_m + y1), "#EEEEEE")
            image_2_m = image_2.resize((x2_m, y2_m))
            images.paste(image_1, (0, 0), mask=image_1)
            images.paste(image_2_m, (0, y1), mask=image_2_m)
        else:  # x1 < x2
            x1_m = x2
            y1_m = int(x1_m * x2 / y2)
            images = Image.new("RGB", (x1_m, y1_m + y2), "#EEEEEE")
            image_1_m = image_1.resize((x1_m, y1_m))
            images.paste(image_1_m, (0, 0), mask=image_1_m)
            images.paste(image_2, (0, y1_m), mask=image_2)
    return images


def save_image(image, user_id: str = str(random.randint(1000, 9999))):
    """
    保存图片文件到缓存文件夹
    :param image:要保存的图片
    :param user_id:用户id，减少路径上的冲突，不填为随机数字
    :return:保存的路径
    """
    date_year = str(time.strftime("%Y", time.localtime()))
    date_month = str(time.strftime("%m", time.localtime()))
    date_day = str(time.strftime("%d", time.localtime()))
    time_now = str(int(time.time()))
    returnpath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/"
    if not os.path.exists(returnpath):
        os.makedirs(returnpath)
    returnpath += f"{time_now}_{user_id}"
    num = 10
    while num > 0:
        num -= 1
        random_num = str(random.randint(1000, 9999))
        if os.path.exists(f"{returnpath}_{random_num}.png"):
            continue
        else:
            returnpath = f"{returnpath}_{random_num}.png"
            break
    logger.debug(f"保存图片文件：{returnpath}")
    image.save(returnpath)
    return returnpath


def image_resize2(image, size: [int, int], overturn=False):
    """
    重缩放图像
    :param image: 要缩放的图像
    :param size: 缩放后的大小
    :param overturn:
    :return: 缩放后的图像
    """
    image_background = Image.new("RGBA", size=size, color=(0, 0, 0, 0))
    image_background = image_background.resize(size)
    w, h = image_background.size
    x, y = image.size
    if overturn:
        if w / h >= x / y:
            rex = w
            rey = int(rex * y / x)
            paste_image = image.resize((rex, rey))
            image_background.paste(paste_image, (0, 0))
        else:
            rey = h
            rex = int(rey * x / y)
            paste_image = image.resize((rex, rey))
            x = int((w - rex) / 2)
            image_background.paste(paste_image, (x, 0))
    else:
        if w / h >= x / y:
            rey = h
            rex = int(rey * x / y)
            paste_image = image.resize((rex, rey))
            x = int((w - rex) / 2)
            y = 0
            image_background.paste(paste_image, (x, y))
        else:
            rex = w
            rey = int(rex * y / x)
            paste_image = image.resize((rex, rey))
            x = 0
            y = int((h - rey) / 2)
            image_background.paste(paste_image, (x, y))

    return image_background


def new_background(image_x: int, image_y: int):
    """
    创建背景图
    :param image_x: 背景图宽 int
    :param image_y: 背景图长 int
    :return: 返回一张背景图 image

    """
    image_x = int(image_x)
    image_y = int(image_y)

    # 创建 背景_背景
    new_image = Image.new(mode='RGB', size=(image_x, image_y), color="#d7f2ff")

    # 创建 背景_描边
    image_x -= 56
    image_y -= 56
    image_paste = Image.new(mode='RGB', size=(image_x, image_y), color="#86d6ff")
    image_paste = circle_corner(image_paste, radii=25)
    paste_x = int(int(new_image.width - image_paste.width) / 2)
    paste_y = int(int(new_image.height - image_paste.height) / 2)
    new_image.paste(image_paste, (paste_x, paste_y), mask=image_paste)

    # 创建 背景_底色
    image_x -= 3
    image_y -= 3
    image_paste = Image.new(mode='RGB', size=(image_x, image_y), color="#eaf6fc")
    image_paste = circle_corner(image_paste, radii=25)
    paste_x = int(int(new_image.width - image_paste.width) / 2)
    paste_y = int(int(new_image.height - image_paste.height) / 2)
    new_image.paste(image_paste, (paste_x, paste_y), mask=image_paste)

    return new_image


def circle_corner(img, radii):
    """
    圆角处理
    :param img: 源图象。
    :param radii: 半径，如：30。
    :return: 返回一个圆角处理后的图象。
    """

    # 画圆（用于分离4个角）
    circle = Image.new('L', (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形

    # 原图
    img = img.convert("RGBA")
    w, h = img.size

    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new('L', img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角
    # alpha.show()

    img.putalpha(alpha)  # 白色区域透明可见，黑色区域不可见
    return img


def get_unity_user_id(platform: str, user_id: str):
    """
    获取统一id
    :param platform: 现在id平台
    :param user_id: 现在id
    :return: 统一id
    """
    platform = str(platform)
    user_id = str(user_id)
    # 读取数据库列表
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    # 检查是否创建数据库
    if "id_list" not in tables:
        cursor.execute(
            'create table "id_list"'
            '(id INTEGER primary key AUTOINCREMENT, unity_id VARCHAR(10), platform VARCHAR(10), user_id VARCHAR(10))')

    # 开始读取数据
    cursor.execute(f'SELECT * FROM "id_list" WHERE platform = "{platform}" AND user_id = "{user_id}"')
    data = cursor.fetchone()
    if data is None:
        # 无数据，创建一个unity_id
        num = 100
        while num > 0:
            num -= 1
            if num > 10:
                random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
            else:
                random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

            # 保留号段
            pass_str = False
            for strr in ["KN", "Kn", "kN", "kn", "KA", "Ka", "kA", "ka", "SG", "sg", "0",  "444",  "41",  "S1",  "S8",
                         "SB", "250", "69", "79", "NC", "58",  "5B",  "64",  "63",  "SX",  "NT",  "n7"]:
                if strr in random_str:
                    # 重新选
                    pass_str = True
            if pass_str:
                continue

            cursor.execute(f'SELECT * FROM "id_list" WHERE unity_id = "{random_str}"')
            data = cursor.fetchone()

            if data is None:
                cursor.execute(
                    f'replace into id_list ("unity_id","platform","user_id") '
                    f'values("{random_str}","{platform}","{user_id}")')
                conn.commit()
                break
            else:
                continue

        # 读取unity_user_id
        cursor.execute(f'SELECT * FROM id_list WHERE platform = "{platform}" AND user_id = "{user_id}"')
        data = cursor.fetchone()
        unity_user_id = data[1]

    else:
        # 读取unity_user_id
        unity_user_id = data[1]

    # 关闭数据库
    cursor.close()
    conn.close()

    return str(unity_user_id)


def get_user_id(platform: str, unity_user_id: str):
    """
    获取用户对应平台的id
    :param platform:平台名称
    :param unity_user_id:用户unity_user_id
    :return:
    """
    platform = str(platform)
    unity_user_id = str(unity_user_id)
    # 读取数据库列表
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    # 检查是否创建数据库
    if "id_list" not in tables:
        cursor.execute(
            'create table "id_list"'
            '(id INTEGER primary key AUTOINCREMENT, unity_id VARCHAR(10), platform VARCHAR(10), user_id VARCHAR(10))')

    # 开始读取数据
    cursor.execute(f'SELECT * FROM "id_list" WHERE platform = "{platform}" AND unity_id = "{unity_user_id}"')
    data = cursor.fetchone()
    if data is None:
        user_id = None
    else:
        user_id = data[3]

    # 关闭数据库
    cursor.close()
    conn.close()

    return user_id


def get_unity_user_data(unity_user_id: str):
    """
    获取统一id
    :param unity_id: 统一id
    :return: 用户数据
    """
    unity_user_id = str(unity_user_id)
    # 读取数据库列表
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    # 检查是否创建数据库
    if "user_data" not in tables:
        cursor.execute('create table "user_data"(unity_id VARCHAR(10) primary key, user_data VARCHAR(50))')

    # 开始读取数据
    cursor.execute(f'SELECT * FROM "user_data" WHERE unity_id = "{unity_user_id}"')
    data = cursor.fetchone()
    if data is None:
        # 默认数据
        unity_user_data = {}
    else:
        data: str = data[1]
        # 转为json格式
        try:
            unity_user_data = json.loads(data)
        except Exception as e:
            logger.error(f"读取json数据出错,json:{data}")
            unity_user_data = {}

    # 关闭数据库
    cursor.close()
    conn.close()

    for data in list(unity_user_data):
        if type(unity_user_data[data]) is str:
            if "{basepath}" in unity_user_data[data]:
                unity_user_data[data] = unity_user_data[data].replace("{basepath}", basepath)
    return unity_user_data


def save_unity_user_data(unity_id: str, unity_user_data: json):
    """

    :param unity_id:
    :param unity_user_data:
    :return:
    """
    unity_user_data_str = json_to_str(unity_user_data)

    # 读取数据库列表
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    # 检查是否创建数据库
    if "user_data" not in tables:
        cursor.execute('create table "user_data"(unity_id VARCHAR(10) primary key, user_data VARCHAR(50))')

    # 写入数据
    cursor.execute(f"replace into 'user_data' ('unity_id','user_data') values('{unity_id}','{unity_user_data_str}')")
    conn.commit()

    # 关闭数据库
    cursor.close()
    conn.close()

    return unity_user_data


def json_to_str(json_data):
    text = str(json_data)

    # 替换同义词
    text = text.replace("'", '\\-code-replace-code-\\')
    text = text.replace('"', "'")
    text = text.replace("\\-code-replace-code-\\", '"')
    text = text.replace("None", "null")
    text = text.replace("True", "true")
    text = text.replace("False", "false")

    return text
