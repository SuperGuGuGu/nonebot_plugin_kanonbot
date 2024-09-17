# coding=utf-8
import io
import re
import string
import traceback

import httpx
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

kn_cache = {}


def _kanonbot_plugin_config():
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
    # kanonbot_basepath="./"
    # kanonbot_basepath="C:/kanonbot/"
    #
    # 配置3：
    # 读取自定义的命令前缀
    # COMMAND_START=["/", ""]
    #
    # 读取配置文件
    try:
        config = nonebot.get_driver().config
        # 配置1
        try:
            _superusers = list(config.superusers)
        except Exception as e:
            _superusers = []
        # 配置2：
        try:
            _basepath = config.kanonbot_basepath
            if "\\" in _basepath:
                _basepath = _basepath.replace("\\", "/")
            if _basepath.startswith("./"):
                _basepath = os.path.abspath('.') + _basepath.removeprefix(".")
                if not _basepath.endswith("/"):
                    _basepath += "/"
            else:
                if not _basepath.endswith("/"):
                    _basepath += "/"
        except Exception as e:
            _basepath = os.path.abspath('.') + "/KanonBot/"
        # 配置3：
        try:
            _command_starts = config.COMMAND_START
        except Exception as e:
            _command_starts = ["/"]
        # 配置test, 开发者选项：
        try:
            kanonbot_test = config.KanonBetaTest
        except Exception as e:
            kanonbot_test = False
    except Exception as e:
        _basepath = os.path.abspath('.') + "/KanonBot/"
        _command_starts = ["/"]
        _superusers = []
        kanonbot_test = False

    if "\\" in _basepath:
        _basepath = _basepath.replace("\\", "/")

    # 初始化文件夹
    if not os.path.exists(_basepath):
        os.makedirs(_basepath)
    cache_path = f"{_basepath}cache/"
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    cache_path = f"{_basepath}file/"
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)

    return {
        "basepath": _basepath,
        "command_starts": _command_starts,
        "superusers": _superusers,
        "kanonbot_test": kanonbot_test
    }


_config = _kanonbot_plugin_config()
basepath = _config["basepath"]
command_starts = _config["command_starts"]
kn_config_data = None


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

    if len(commands) > 1:
        command2 = commands[1]
        for _ in range(3):
            if command2.startswith(" "):
                command2 = command2.removeprefix(" ")
            else:
                break
        for _ in range(3):
            if command2.endswith(" "):
                command2 = command2.removesuffix(" ")
            else:
                break
        commands[1] = command2

    return commands


def kn_config(config_name: str, config_name2: str = None):
    """
    获取配置。
    获取"kanon_api-url"时，相当于获取"config["kanon_api"]["url"]"的配置项
    :param config_name: 获取的配置名称
    :param config_name2:
    :return: 配置内容
    """
    global kn_config_data

    path = f"{basepath}kanon_config.toml"

    def save_config():
        global kn_config_data
        with open(path, 'w') as config_file:
            toml.dump(config, config_file)
        kn_config_data = config

    kn_config_data = None
    if kn_config_data is None:
        if not os.path.exists(path):
            config = {
                "Kanon_Config": {
                    "KanonBot": "https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot"},
                "knapi": {
                    "url": "https://cdn.kanon.ink"}}
            save_config()
            nonebot.logger.info("未存在KanonBot配置文件，正在创建")
        config = toml.load(path)
    else:
        config = kn_config_data

    if config_name2 is not None:
        config_name += f"-{config_name2}"
    names = config_name.split('-', 1)
    name_1 = names[0]
    name_2 = names[1]

    # 如果存在设置，则直接回复
    if name_1 in list(config) and name_2 in list(config[name_1]):
        return config[name_1][name_2]

    # 配置默认设置
    default = {
        "kanon_api": {
            "url": "http://cdn.kanon.ink",
            "state": True,
            "unity_key": "none",
        },
        "emoji": {
            "state": True,
            "mode": "file",
        },
        "botswift": {
            "state": False,
            "ignore_list": [],
        },
        "plugin": {
            "channel_white_list": [],
            "channel_black_list": [],
            "user_white_list": [],
            "user_black_list": [],
            "bot_list": [],
            "log": True,
            "log_trace_data": False,
            "image_markdown": None,
            "none_markdown": None,
        },
        "plugin_cck": {
            "draw_type": 1,
            "send_markdown": False,
            "send_button": False,
            "button_1_id": None,
            "button_2_id": None,
        },
        "plugin_jellyfish_box": {
            "send_markdown": False,
            "send_button": False,
            "button_id": None,
            "draw_gif": False,
        },
    }

    # 保存默认设置
    if name_1 in list(default) and name_2 in list(default[name_1]):
        if name_1 in list(config):
            if name_2 not in list(config[name_1]):
                config[name_1][name_2] = default[name_1][name_2]
                save_config()
        else:
            config[name_1] = default[name_1]
            save_config()

    # 如果存在设置，则直接回复
    if name_1 in list(config) and name_2 in list(config[name_1]):
        return config[name_1][name_2]

    return None


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


def list_in_list(list_1: list | str, list_2: list | str) -> bool:
    """
    判断数列是否在数列内
    :param list_1: list or str。例：["a", "b"], "abc"
    :param list_2: list。例：["a", "b"], "abc"
    :return bool
    """
    for cache_list_2 in list_2:
        if cache_list_2 in list_1:
            return True
    return False


def start_with_list(msg: str, texts: list) -> bool:
    for text in texts:
        if msg.startswith(text):
            return True
    return False


async def connect_api(
        type: str,
        url: str,
        post_json=None,
        file_path: str = None):
    logger.debug(f"connect_api请求URL：{url}")
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"}
    if type == "json":
        if post_json is None:
            return json.loads(httpx.get(url, headers=h).text)
        else:
            return json.loads(httpx.post(url, json=post_json, headers=h).text)
    elif type == "image":
        if url is None or url in ["none", "None", "", " "]:
            image = await draw_text("获取图片出错", 50, 10)
        else:
            try:
                image = Image.open(BytesIO(httpx.get(url).content))
            except Exception as e:
                logger.error(url)
                raise "获取图片出错"
        return image
    elif type == "file":
        cache_file_path = file_path + "cache"
        f = open(cache_file_path, "wb")
        try:
            res = httpx.get(url, headers=h).content
            f.write(res)
            logger.debug(f"下载完成-{file_path}")
        except:
            raise Exception
        finally:
            f.close()
        shutil.copyfile(cache_file_path, file_path)
        os.remove(cache_file_path)
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
        logger.debug("正在下载" + file_name)
        url = f"{kn_config('kanon_api-url')}/file/{file_name}"
        await connect_api(type="file", url=url, file_path=file_path)
    return file_path


async def get_file_path_v2(file_name: str) -> str:
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
        logger.debug("正在下载" + file_name)
        names = file_name.split("》")
        url = f"{kn_config('kanon_api-url')}/v2/file"
        for name in names:
            url += f"/{name}" if name != "" else ""
        logger.debug("url: " + url)
        await connect_api(type="file", url=url, file_path=file_path)
    return file_path


async def get_image_path(image_name) -> str:
    """
    获取图片的路径信息，如果没下载就下载下来
    :param image_name: 文件名。例：“jellyfish_box-j1.png”
    :return: 文件路径。例："c:/bot/cache/file/file.zip"
    """
    file_path = basepath + "file/image/"
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    file_path += image_name
    if "." not in image_name:
        file_path += ".png"
    if not os.path.exists(file_path):
        # 如果文件未缓存，则缓存下来
        logger.debug("正在下载" + image_name)
        url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-{image_name}"
        image = await connect_api(type="image", url=url)
        image.save(file_path)
    return file_path


async def load_image(path: str, size=None):
    """
    读取图片或请求网络图片
    :param path: 图片路径/图片url
    :param size: 出错时候返回的图片尺寸
    :return:image
    """
    try:
        if path.startswith("http"):
            return await connect_api("image", path)
        else:
            if path.startswith("{basepath}"):
                image_path = f"{basepath}{path.removeprefix('{basepath}')}"
                return Image.open(image_path, "r")
            return Image.open(path, "r")
    except Exception as e:
        logger.error(f"读取图片错误：{path}")
        logger.error(e)
        if size is not None:
            return Image.new("RGBA", size, (0, 0, 0, 0))
        raise "图片读取错误"


def images_to_gif(
        gifs: str,
        gif_path: str,
        duration: int | float
    ):
    """
    图片保存为gif
    :param gifs:图片文件夹路径
    :param gif_path:保存的gif路径
    :param duration:gif速度
    :return:
    """
    frames = []
    png_files = os.listdir(gifs)
    for frame_id in range(1, len(png_files) + 1):
        frame = Image.open(os.path.join(gifs, '%d.png' % frame_id))
        frames.append(frame)
    frames[0].save(
        gif_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        disposal=2
    )
    return "success"


def save_image(
        image,
        image_path: str = None,
        image_name: int | str = None,
        relative_path=False):
    """
    保存图片文件到缓存文件夹
    :param image:要保存的图片
    :param image_path: 指定的图片所在文件夹路径，默认为缓存
    :param image_name:图片名称，不填为随机数字
    :param relative_path: 是否返回相对路径
    :return:保存的路径
    """
    local_time = time.localtime()
    date_year = local_time.tm_year
    date_month = local_time.tm_mon
    date_day = local_time.tm_mday
    time_now = int(time.time())

    if image_path is None:
        image_path = "{basepath}" + f"cache/{date_year}/{date_month}/{date_day}/"
    real_path = image_path.replace("{basepath}", basepath)

    os.makedirs(real_path, exist_ok=True)

    if image_name is None:
        image_name = f"{time_now}_{random.randint(1000, 9999)}"
        num = 50
        while num > 0:
            num -= 1
            random_num = str(random.randint(100000, 999999))
            if os.path.exists(f"{real_path}{image_name}_{random_num}.png"):
                continue
            image_name += f"_{random_num}.png"
            break

    logger.debug(f"保存图片文件：{real_path}{image_name}")
    image.save(f"{real_path}{image_name}")

    if relative_path is True:
        return "{basepath}" + image_path + image_name
    else:
        return real_path + image_name


async def lockst(lockdb=None):
    """
    如有其他指令在运行，则暂停该函数
    :param lockdb: 数据库路径
    :return:
    """
    global kn_cache
    if "lock" not in kn_cache:
        kn_cache["lock"] = False

    # 随机随眠0.01-2秒，避免同时收到消息进行处理
    await asyncio.sleep(float(random.randint(1, 200)) / 100)

    # 锁定
    num = 20
    while num > 1:
        num -= 1
        if kn_cache["lock"] is True:
            await asyncio.sleep(0.2)
        else:
            break

    kn_cache["lock"] = True
    return True


def locked(text=None):
    kn_cache["lock"] = False
    return True


def command_cd(cd_id: str, time_now: int, cd_type: str = "channel"):
    """
    指令冷却
    :param time_now: 现在时间码
    :param cd_id: 群号
    :param cd_type: 冷却方式："user", "channel"
    :return: False | str: [{冷却间隔}s/{冷却条数}次]{冷却秒数}
    """
    global kn_cache
    t = cd_type = "channel" if cd_type not in ["channel", "user"] else cd_type
    c = config = {
        "user": {
            "5": {"msg_num": 3, "cool_time": 20},
            "10": {"msg_num": 5, "cool_time": 30},
            "30": {"msg_num": 10, "cool_time": 70},
            "120": {"msg_num": 20, "cool_time": 300},
            "3600": {"msg_num": 50, "cool_time": 7200},
            "4000": {"msg_num": 70, "cool_time": 7200},
        },
        "channel": {
            "3": {"msg_num": 5, "cool_time": 20},
            "10": {"msg_num": 10, "cool_time": 30},
            "30": {"msg_num": 13, "cool_time": 50},
            "60": {"msg_num": 20, "cool_time": 100},
            "120": {"msg_num": 40, "cool_time": 210},
        }
    }
    if "cd" not in list(kn_cache):
        kn_cache["cd"] = {cd_id: {}}
    if cd_id not in list(kn_cache["cd"]):
        kn_cache["cd"][cd_id] = {}
    data = kn_cache["cd"][cd_id]
    # 判断是否正在冷却
    for interval in list(c[t]):
        if interval not in list(data):
            data[interval] = {"last": time_now, "num": 0}
        data[interval]["num"] += 1

    for interval in list(c[t]):
        if interval not in list(data):
            data[interval] = {"last": time_now, "num": 0}
            continue

        # 判断符合数量
        if data[interval]["num"] > c[t][interval]['msg_num']:
            # 超过冷却事件，恢复
            if int(time_now - data[interval]['last']) > c[t][interval]['cool_time']:
                data[interval] = {"last": time_now, "num": 0}
                continue
            s = int(c[t][interval]['cool_time'] - int(time_now - data[interval]['last']))
            # 时间转换秒数
            h = 0
            m = 0
            if s > 3600:
                h = int(s / 3600)
                s -= h * 3600
            if s > 60:
                m = int(s / 60)
                s -= m * 60
            msg = ""
            if h > 0:
                msg += f"{h}时"
            if m > 0:
                msg += f"{m}分"
            msg += f"{s}秒"

            if t == "channel":
                return f"群[{interval}s/{c[t][interval]['msg_num']}次]{msg}"
            else:
                return f"[{interval}s/{c[t][interval]['msg_num']}次]{msg}"

        if int(time_now - data[interval]["last"]) > c[t][interval]["cool_time"]:
            data[interval] = {"last": time_now, "num": 0}
            continue

    return False


async def draw_text(
        texts: str,
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
    url = kn_config("image_api", "url")
    if url is None:
        """
        这里会运行报错，因为图片转链接功能需要图床的支持。请用户自行适配。
        QQ适配器发送图片需要发送url让qq请求。
        """
        raise "未配置图床地址"
    try:
        files = {"file": open(imgpath, "rb")}
        post_url = f"{url}/upload/"
        response = httpx.post(post_url, files=files)
        json_data = json.loads(response.text)
        if json_data["code"] != 0:
            raise "图片上传失败"
        image_path = json_data["image_path"]
        imgurl = f"{url}{image_path}"
    except Exception as e:
        logger.error("图片上传失败")
        raise e
    return imgurl


def mix_image(image_1, image_2, mix_type=1):
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


def image_resize2(image, size: [int, int], overturn=False):
    """
    重缩放图像
    :param image: 要缩放的图像
    :param size: 缩放后的大小
    :param overturn: 是否放大到全屏
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
            for strr in ["KN", "Kn", "kN", "kn", "KA", "Ka", "kA", "ka", "SG", "sg", "0", "444", "41", "S1", "S8",
                         "SB", "250", "69", "79", "NC", "58", "5B", "64", "63", "SX", "NT", "n7"]:
                if strr in random_str:
                    # 重新选
                    pass_str = True
                    break
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
    :param unity_user_id: 统一id
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
    text = json.dumps(json_data)
    # text = str(json_data)

    # 替换同义词
    # text = text.replace("'", '\\-code-replace-code-\\')
    # text = text.replace('"', "'")
    # text = text.replace("\\-code-replace-code-\\", '"')
    # text = text.replace("None", "null")
    # text = text.replace("True", "true")
    # text = text.replace("False", "false")

    return text


def del_files2(dir_path):
    """
    删除文件夹下所有文件和路径，保留要删的父文件夹
    """
    for root, dirs, files in os.walk(dir_path, topdown=False):
        # 第一步：删除文件
        for name in files:
            os.remove(os.path.join(root, name))  # 删除文件
        # 第二步：删除空文件夹
        for name in dirs:
            os.rmdir(os.path.join(root, name))  # 删除一个空目录


def statistics_list(input: list) -> dict:
    """
    统计字符出现次数
    :param input: 输入数列
    :return: 统计数
    """
    data = {}
    for d in input:
        d = str(d)
        if d not in list(data):
            data[d] = 1
        else:
            data[d] += 1
    return data


async def content_compliance(type_: str = "text", data: str = None, user_id: str = "user_id"):
    """
    内容合规检测（百度api）
    :param type_: 类型： "text", "image"
    :param data: 检测的内容。text: str, image: str = url
    :param user_id: 被检测的用户id
    :return: {"conclusion": "合规"}
    """
    try:
        if type_ == "text":
            access_token = kn_config("content_compliance", "token")
            request_url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined"
            params = {"text": data, "strategyId	": 36222, "userId": user_id}
            request_url += f"?access_token={access_token}"
            headers = {'content-type': 'application/x-www-form-urlencoded'}
            # return_data["conclusion"] = "合规""疑似""不合规"
            # return_data["data"] = {} if return_data["conclusion"] == "合规" else data
            raturn_data = httpx.post(request_url, data=params, headers=headers)
            logger.debug(f"内容合规检测： {raturn_data}")
            return raturn_data.json()
        elif type_ == "image":
            return {"conclusion": "合规", "message": "图片检测未完成"}
        return {"conclusion": "error", "message": "检测类型不存在"}
    except Exception as e:

        return {
            "conclusion": "error",
            "message": "运行错误",
            "error_message": str(e).replace("'", '"'),
            "error_traceback": str(traceback.format_exc()).replace("'", '"'),
        }


