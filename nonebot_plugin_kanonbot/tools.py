# coding=utf-8
import base64
import io
import re
import string
import traceback
import httpx
import toml
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as PIL_Image
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
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.tms.v20201229 import tms_client, models
from scipy.interpolate import interp1d
import numpy

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


def get_command(msg: str) -> list[str | None]:
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

    config = kn_config_data
    if kn_config_data is None or int(time.time()) - kn_config_data["update_time"] > 60:
        if not os.path.exists(path):
            config = {
                "Kanon_Config": {
                    "KanonBot": "https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot"},
                "knapi": {
                    "url": "https://cdn.kanon.ink"}}
            save_config()
            logger.info("未存在KanonBot配置文件，正在创建")
        kn_config_data = config = toml.load(path)
        kn_config_data["update_time"] = int(time.time())

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
        },
        "emoji": {
            "state": True,
            "mode": "file",
        },
        "botswift": {
            "state": False,
            "ignore_list": [],
            "platform_list": [],
        },
        "plugin": {
            "channel_white_list": [],
            "channel_black_list": [],
            "black_white_list_platform": [],
            "user_white_list": [],
            "user_black_list": [],
            "bot_list": [],
            "log": False,
            "log_trace_data": False,
            "image_markdown": None,
            "none_markdown": None,
            "state_url": None,
            "file_fast_cache_path": None,
            "image_fast_cache_path": None,
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
        "content_compliance": {
            "secret_id": None,
            "secret_key": None,
            "enabled_list": [],
            "input_ban_list": [],
        },
        "pic": {
            "eagle-path": None,
            "eagle-url": None,
            "eagle-name": "",
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
        file_path: str = None,
        timeout: int = 10
):
    logger.debug(f"connect_api请求URL：{url}")
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76"}
    if type == "json":
        if post_json is None:
            async with httpx.AsyncClient() as client:
                data = await client.get(url, headers=h, timeout=timeout)
            return json.loads(data.text)
        else:
            async with httpx.AsyncClient() as client:
                data = await client.post(url, json=post_json, headers=h, timeout=timeout)
            return json.loads(data.text)
    elif type == "image":
        if url is None or url in ["none", "None", "", " "]:
            image = await draw_text("获取图片出错", 50, 10)
        else:
            try:
                async with httpx.AsyncClient() as client:
                    data = await client.get(url, timeout=timeout)
                image = Image.open(BytesIO(data.content))
            except Exception as e:
                logger.error(url)
                raise "获取图片出错"
        return image
    elif type == "file":
        cache_file_path = file_path + "cache"
        f = open(cache_file_path, "wb")
        try:
            res = httpx.get(url, headers=h, timeout=timeout).content
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
    file_path = f"{basepath}file/{file_name}"
    os.makedirs(f"{basepath}file/", exist_ok=True)
    file_fast_cache_path = kn_config("plugin", "file_fast_cache_path")
    file_cache_path = f"{file_fast_cache_path}{file_name}"

    if file_fast_cache_path is not None:
        os.makedirs(file_fast_cache_path, exist_ok=True)
        if not os.path.exists(file_cache_path):
            if os.path.exists(file_path):
                file = open(file_path, "rb")
                file_data = file.read()
                file.close()
                file = open(file_cache_path, "wb")
                file.write(file_data)
                file.close()
                return file_cache_path
        else:
            return file_cache_path

    if not os.path.exists(f"{basepath}file/{file_name}"):
        # 如果文件未缓存，则缓存下来
        logger.debug("正在下载" + file_name)
        url = f"{kn_config('kanon_api-url')}/file/{file_name}"
        await connect_api(type="file", url=url, file_path=file_path)

        file = open(file_path, "rb")
        file_data = file.read()
        file.close()
        file = open(file_cache_path, "wb")
        file.write(file_data)
        file.close()

    return f"{basepath}file/{file_name}"


async def get_file_path_v2(file_name: str) -> str:
    """
    获取文件的路径信息，如果没下载就下载下来
    :param file_name: 文件名。例：“file.zip”
    :return: 文件路径。例："c:/bot/cache/file/file.zip"
    """
    file_path = basepath + "file/"
    os.makedirs(file_path, exist_ok=True)
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
    if "." not in image_name:
        image_name += ".png"
    os.makedirs(f"{basepath}file/image/", exist_ok=True)
    file_path = f"{basepath}file/image/{image_name}"
    image_fast_cache_path = kn_config("plugin", "image_fast_cache_path")
    file_cache_path = f"{image_fast_cache_path}{image_name}"

    if not os.path.exists(file_path):
        # 如果文件未缓存，则缓存下来
        logger.debug("正在下载" + image_name)
        url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-{image_name}"
        try:
            image = await connect_api(type="image", url=url)
            image.save(file_path)
        except Exception as e:
            logger.error(e)
            logger.error(traceback.format_exc())
            raise "图片下载错误"

    if image_fast_cache_path is not None:
        if not os.path.exists(file_cache_path):
            file = open(file_path, "rb")
            file_data = file.read()
            file.close()
            file = open(file_cache_path, "wb")
            file.write(file_data)
            file.close()

    return file_path


async def load_image(path: str, size=None, mode=None):
    """
    读取图片或请求网络图片
    :param path: 图片路径/图片url
    :param size: 出错时候返回的图片尺寸
    :param mode: 图片读取模式
    :return:image
    """
    if mode is None:
        mode = "r"
    try:
        if path.startswith("http"):
            return await connect_api("image", path)
        else:
            if path.startswith("{basepath}"):
                image_path = f"{basepath}{path.removeprefix('{basepath}')}"
                return Image.open(image_path, mode)
            return Image.open(path, mode)
    except Exception as e:
        logger.error(f"读取图片错误：{path}")
        logger.error(e)
        if size is not None:
            return Image.new("RGBA", size, (0, 0, 0, 0))
        raise "图片读取错误"


async def images_to_gif(
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
        frame = Image.open(os.path.join(gifs, '%d.png' % frame_id)).convert("RGB")
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
        relative_path=False,
        tobytes: bool = False):
    """
    保存图片文件到缓存文件夹
    :param image:要保存的图片
    :param image_path: 指定的图片所在文件夹路径，默认为缓存
    :param image_name:图片名称，不填为随机数字
    :param relative_path: 是否返回相对路径
    :param tobytes: 是否转为bytes
    :return:保存的路径
    """
    if tobytes is True and type(image) is PIL_Image:
        # 将Pillow图像数据保存到内存中
        image_stream = io.BytesIO()
        image.save(image_stream, format='JPEG')
        image_stream.seek(0)
        return image_stream.read()

    date_components = time.strftime("%Y/%m/%d", time.localtime())
    time_now = int(time.time())

    if image_path is None:
        image_path = "{basepath}" + f"cache/{date_components}/"
    real_path = image_path.replace("{basepath}", basepath)
    os.makedirs(real_path, exist_ok=True)

    if image_name is None:
        image_name = f"{time_now}_{random.randint(1000, 9999)}"
        num = 50
        while True:
            num -= 1
            random_num = str(random.randint(1000, 9999))
            if os.path.exists(f"{real_path}{image_name}_{random_num}.png"):
                continue
            image_name = f"{image_name}_{random_num}.png"
            break

    logger.debug(f"保存图片文件：{real_path}{image_name}")
    image.save(f"{real_path}{image_name}")

    if tobytes is True:
        image_file = open(f"{real_path}{image_name}", "rb")
        image = image_file.read()
        image_file.close()
        return image
    if relative_path is True:
        return f"{image_path}{image_name}"
    else:
        return f"{real_path}{image_name}"


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


async def imgpath_to_url(imgpath: str | bytes, host: str = "https://cdn.kanon.ink"):
    date_year: int = int(time.strftime("%Y", time.localtime()))
    date_month: int = int(time.strftime("%m", time.localtime()))
    date_day: int = int(time.strftime("%d", time.localtime()))
    dateshort = str(time.strftime("%Y%m%d", time.localtime()))
    timeshort = str(time.strftime("%H%M%S", time.localtime()))
    # 数据库文件 如果文件不存在，会自动在当前目录中创建
    # conn = sqlite3.connect(f"{basepath}/db/imageAPI")
    conn = sqlite3.connect("P:/local-ImgCache/imageAPI_db.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
    if "images" not in tables:
        cursor.execute('create table images (imageid varchar(10) primary key, path varchar(20))')

    cache_imageid = "image-none"
    num = 12
    while num > 0:
        num -= 1
        if num <= 2:
            cache_imageid = f"image-{dateshort}-{timeshort}-{random.randint(10000000, 99999999)}"
        else:
            cache_imageid = f"image-{dateshort}-{timeshort}-{random.randint(100000, 999999)}"
        cursor.execute(f"SELECT * FROM images WHERE imageid='{cache_imageid}'")
        data = cursor.fetchone()
        if data is None:
            break
    imageid = cache_imageid
    returnpath = f"P:/APIfile/{date_year}/{date_month}/{date_day}/"
    if not os.path.exists(returnpath):
        os.makedirs(returnpath)
    returnpath += imageid

    if type(imgpath) == str and imgpath.startswith("http"):
        image_ = await connect_api("image", imgpath)
        img_byte_arr = io.BytesIO()
        image_.save(img_byte_arr)
        image_data = img_byte_arr.getvalue()
        imageid += ".png"
    elif type(imgpath) == str:
        imgpath.replace("{basepath}", basepath)
        file = open(imgpath, "rb")
        image_data = file.read()
        file.close()
        if imgpath.endswith(".gif"):
            imageid += ".gif"
        else:
            imageid += ".png"
    else:
        # elif type(imgpath) == bytes:
        image_data = imgpath
        imageid += ".png"

    file = open(returnpath, "wb")
    file.write(image_data)
    file.close()

    cursor.execute(f'replace into images(imageid,path) values("{imageid}","{returnpath}")')
    cursor.close()
    conn.commit()
    conn.close()

    imgurl = f"{host}/v2/image/image_api/{imageid}?key=tx-image-api"
    logger.debug(f"转换图片image2url：{imgurl}")

    # 预加载图片
    try:
        pass
        # await connect_api("image", url=imgurl)
    except Exception as e:
        pass
    # await asyncio.sleep(0.5)
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
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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
        num = 1000
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
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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

    data = read_db(
        db_path="{basepath}db/config.db",
        sql_text=f'SELECT * FROM "user_data" WHERE unity_id = "{unity_user_id}"',
        table_name="user_data",
        select_all=False
    )
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

    return unity_user_data


def save_unity_user_data(unity_id: str, unity_user_data: json):
    """

    :param unity_id:
    :param unity_user_data:
    :return:
    """
    unity_user_data_str = json.dumps(unity_user_data)

    # 读取数据库列表
    if not os.path.exists(f"{basepath}db/"):
        os.makedirs(f"{basepath}db/")
    conn = sqlite3.connect(f"{basepath}db/config.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
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


async def content_compliance(type_: str = "text", text_data: str = None, user_id: str = "user_id"):
    """
    内容合规检测（腾讯云api）
    :param type_: 类型： "text", "image"
    :param text_data: 检测的内容。text: str, image: str = url
    :param user_id: 被检测的用户id
    :return: {"conclusion": "Block"}{"conclusion": "Review"}{"conclusion": "Pass"}
    """
    if text_data is None:
        return {"conclusion": "Pass", "review": True, "message": "Pass None"}
    logger.debug(f"content_compliance, typr={type_}")
    data_b64 = str(base64.b64encode(text_data.encode('UTF-8')), encoding='UTF-8')
    try:
        if type_ == "text":
            if text_data in kn_cache["content_compliance_list"]["full"]:
                logger.debug({"conclusion": "Block", "word": text_data, "message": "数据库黑名单句子"})
                return {"conclusion": "Block", "message": "数据库黑名单句子"}

            for item in kn_cache["content_compliance_list"]["part"]:
                if item in text_data:
                    logger.debug({"conclusion": "Block", "word": item, "message": "数据库黑名单词汇"})
                    return {"conclusion": "Block", "review": True, "message": "数据库黑名单词汇"}

            data = read_db(
                db_path="{basepath}db/content_compliance.db",
                sql_text=f"SELECT * FROM content_compliance WHERE text='{data_b64}'",
                table_name="content_compliance",
                select_all=False
            )

            if data is not None:
                if data[2] == "Pass":
                    logger.debug({"conclusion": "Pass", "message": "Pass by database"})
                    return {"conclusion": "Pass", "review": True, "message": "Pass by database"}
                elif data[3] is not None or data[3] != 1:
                    logger.debug({"conclusion": "Pass", "message": f"{data[2]} by database without Review"})
                    return {"conclusion": "Pass", "review": False, "message": f"{data[2]} by database without Review"}
                elif data[2] == "Review":
                    logger.debug({"conclusion": "Review", "message": "Review by database"})
                    return {"conclusion": "Review", "review": True, "message": "Review by database"}
                else:
                    logger.debug({"conclusion": "Block", "message": "Block by database"})
                    return {"conclusion": "Block", "review": True, "message": "Block by database"}
            else:
                # 插件自带白名单，防止内容合规检测误判
                whitelist_term = ["尼格"]
                for whitelist in whitelist_term:
                    text_data = text_data.replace(whitelist, "")
                data_b64 = str(base64.b64encode(text_data.encode('UTF-8')), encoding='UTF-8')

                secret_id = kn_config("content_compliance", "secret_id")
                secret_key = kn_config("content_compliance", "secret_key")
                if secret_id is None or secret_key is None:
                    raise "未配置内容合规id、key，无法使用内容合规功能。请配置后再开启内容合规审核"

                cred = credential.Credential(secret_id, secret_key)
                httpProfile = HttpProfile()
                httpProfile.endpoint = "tms.tencentcloudapi.com"
                clientProfile = ClientProfile()
                clientProfile.httpProfile = httpProfile
                client = tms_client.TmsClient(cred, "ap-guangzhou", clientProfile)
                req = models.TextModerationRequest()
                encoded_content = base64.b64encode(text_data.encode('utf-8')).decode('utf-8')
                params = {
                    "Content": encoded_content,
                    "User": {
                        "UserId": user_id
                    },
                }
                req.from_json_string(json.dumps(params))
                resp = client.TextModeration(req)
                return_data: dict = json.loads(resp.to_json_string())

                conn = sqlite3.connect(f"{basepath}db/content_compliance.db")
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
                datas = cursor.fetchall()
                tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
                # 检查是否创建数据库
                if "content_compliance" not in tables:
                    cursor.execute(
                        f"create table content_compliance(id_ INTEGER primary key AUTOINCREMENT, "
                        f"text VARCHAR(10), state VARCHAR(10), request_id VARCHAR(10), audit VARCHAR(10))")

                cursor.execute(
                    f"replace into content_compliance ('text','state','request_id','audit') "
                    f"values('{data_b64}','{return_data['Suggestion']}','{return_data['RequestId']}',0)")
                conn.commit()
                cursor.close()
                conn.close()

                if "Suggestion" not in return_data.keys() or return_data["BizType"] != "0":
                    logger.error("内容合规错误")
                    logger.error(return_data)
                    return {"conclusion": "Pass", "data": return_data}
                # return_data["conclusion"] = "Pass""Review""Block"
                # return_data["data"] = {} if return_data["conclusion"] == "合规" else text_data
                logger.debug(f"内容合规检测： {return_data}")
                return {"conclusion": return_data["Suggestion"], "data": return_data}
        elif type_ == "image":
            return {"conclusion": "Pass", "message": "图片检测未完成"}
        return {"conclusion": "error", "message": "检测类型不存在"}
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        logger.error("内容合规检测出错")
        return {
            "conclusion": "error",
            "message": "运行错误",
            "error_message": str(e).replace("'", '"'),
            "error_traceback": str(traceback.format_exc()).replace("'", '"'),
        }


def create_table_data_():
    date_year: int = time.localtime().tm_year
    date_month: int = time.localtime().tm_mon
    data = {
        "{basepath}db/config.db": {
            "user_data": 'create table "user_data"(unity_id VARCHAR(10) primary key, user_data VARCHAR(50))',
            "": "",
        },
        "{basepath}db/content_compliance.db": {
            "content_compliance": "create table content_compliance(id_ INTEGER primary key AUTOINCREMENT, "
                                  "text VARCHAR, state VARCHAR, request_id VARCHAR, audit INT, level INT)",
            "blacklist": "create table blacklist(id_ INTEGER primary key AUTOINCREMENT, "
                                  "text VARCHAR, state VARCHAR, request_id VARCHAR, audit INT, level INT)",
        },
        "{basepath}db/plugin_data.db": {
            "jellyfish_box": 'create table "jellyfish_box"(user_id VARCHAR(10) primary key, data VARCHAR(10))',
        },
    }
    return data


def read_db(
        db_path: str,
        sql_text: str,
        select_all: bool = False,
        table_name: str = None,
        create_table_text: str = None):
    """
    读取数据库
    :param db_path: 数据库路径
    :param sql_text: sql语句
    :param select_all: 是否筛选全部
    :param table_name: 表名
    :param create_table_text: 创建表的sql语句
    :return:
    """
    db_path = db_path.replace("{basepath}", basepath)
    create_table_data = create_table_data_()
    if create_table_text is not None and db_path in create_table_data.keys():
        if table_name is not None and table_name in create_table_data[db_path].keys():
            create_table_text = create_table_data[db_path][table_name]
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        tables = [data[1] for data in datas if data[1] != "sqlite_sequence"]
        # 检查是否创建数据库
        if table_name not in tables:
            if create_table_text is not None:
                cursor.execute(create_table_text)
            else:
                raise "数据库表不存在"
        # 读取内容
        cursor.execute(sql_text)
        if select_all is True:
            data = cursor.fetchall()
        else:
            data = cursor.fetchone()
    except Exception as e:
        logger.error(f"读取数据库错误{db_path}")
        logger.error(e)
        logger.error(traceback.format_exc())
        raise "数据库访问出错"
    finally:
        # 关闭数据库
        cursor.close()
        conn.close()
    return data


def text_to_b64(text: str) -> str:
    return str(base64.b64encode(text.encode('UTF-8')), encoding='UTF-8')


def b64_to_str(b64_text: str) -> str:
    return base64.b64decode(b64_text).decode('UTF-8')


async def draw_line_chart(
        datas: list[list[int, int]],
        size: tuple = (100, 100),
        color: str | tuple[int, int, int, int] = "#0c88da",
        enlarge_num: int = 1,
        mirror_x: bool = False,
        width: int = None,
        max_min_y: list[int] = None,
        dash_line: list | bool = False
):
    """
    绘制折线
    :param datas: 折线数据
    :param size: 绘制尺寸
    :param color: 折线颜色
    :param enlarge_num: 线段细分倍数
    :param mirror_x: 是否镜像x轴
    :param width: 线段宽度
    :param max_min_y: y轴最大高度，用于同步几个图统一高度
    :param dash_line: 绘制虚线。
    :return: Image
    """
    if enlarge_num == int or enlarge_num < 1:
        raise "扩大倍数必须大于等于1"
    if len(datas) < 3:
        raise "必须有2个点以上"

    w, h = size
    if width is None:
        width = int((w + h) / 121.5)
    image_bleed = 5
    w -= image_bleed * 2
    h -= image_bleed * 2
    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x_list = [data[0] for data in datas]
    if mirror_x is True:
        x_list = x_list[::-1]
    y_list = [data[1] for data in datas]
    max_x = max(x_list)
    min_x = min(x_list)
    if max_min_y is None:
        max_y = max(y_list)
        min_y = min(y_list)
    else:
        max_y, min_y = max_min_y

    if max_y - min_y == 0:
        draw.line((
            (image_bleed, h - image_bleed), (w - image_bleed, h - image_bleed)),
            fill=color, width=width)
        return image

    # 细分点数
    if enlarge_num > 1:
        enlarge_num_ = len(datas) * enlarge_num
        f = interp1d(x_list, y_list)
        x_list = numpy.linspace(max_x, min_x, enlarge_num_)
        y_list = f(x_list)

    if type(dash_line) is bool:
        if dash_line is True:
            dash_group = [True for i in range(len(x_list))]
        else:
            dash_group = [False for i in range(len(x_list))]
    else:
        # elif type(dash_line) is int:
        pass

    num_x = w / (max_x - min_x)
    num_y = h / (max_y - min_y)

    def draw_poin(p1: int, p2: int):
        point_x = (p1 - min_x) * num_x
        point_y = (p2 - min_y) * num_y
        point_y = h - point_y
        return int(point_x) + image_bleed, int(point_y) + image_bleed

    num = -1
    for i in range(len(x_list)):
        num += 1
        if num == 0:
            continue

        st_point = draw_poin(x_list[num - 1], y_list[num - 1])
        ed_point = draw_poin(x_list[num], y_list[num])
        draw.line((st_point, ed_point), fill=color, width=width)
    return image


async def draw_pie_chart(
        datas: list[int],
        size: tuple[int, int] | int = (100, 100),
        colors: list[str, tuple] = None
):
    num = 0
    for data in datas:
        num += data
    if 0.999 > num or num > 1.001:
        logger.error(datas)
        logger.error(num)
        raise "数据总和必须等于1"
    if colors is not None and len(datas) != len(colors):
        logger.error(f"datas:{len(datas)}, colors:{len(colors)}")
        raise "数据长度和颜色长度不匹配"
    if type(size) is int:
        size = (size, size)
    if colors is None:
        colors = []
        for i in range(len(datas)):
            colors.append((
                42, 100, 184,
                int(255 - int(255 / len(datas) * (i * 2))),
            ))
    colors = colors[::-1]

    image = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    datas = sorted(datas)
    num = -1
    draw_num = 0
    for data in datas:
        num += 1
        if data == 0 or (360 * data) == 0:
            continue
        draw.pieslice(
            ((0, 0), (size[0], size[1])),
            start=draw_num,
            end=draw_num + (360 * data),
            fill=colors[num],
            outline=(0, 0, 0))
        draw_num += (360 * data)

    return image


logger.debug("加载用户列表")
datas = read_db(
    db_path="{basepath}db/config.db",
    sql_text="SELECT * FROM id_list",
    table_name="id_list",
    select_all=True
)
if "user_id_list" not in kn_cache.keys():
    kn_cache["user_id_list"] = []
for data in datas:
    kn_cache["user_id_list"].append(data[1])
logger.success("加载用户列表成功")

logger.debug("加载违禁词")
datas = read_db(
    db_path="{basepath}db/content_compliance.db",
    sql_text="SELECT * FROM content_compliance WHERE state IS NOT 'Pass' AND audit IS 1",
    table_name="content_compliance",
    select_all=True
)
datas2 = read_db(
    db_path="{basepath}db/content_compliance.db",
    sql_text="SELECT * FROM blacklist WHERE state IS NOT 'Pass' AND audit IS 1",
    table_name="blacklist",
    select_all=True
)
kn_cache["content_compliance_list"] = {"part": [], "full": []}
for data in datas:
    if data[2] == "Pass" or data[4] != 1:
        continue
    text = str(base64.b64decode(data[1]), "utf-8")
    if data[5] == 5:
        kn_cache["content_compliance_list"]["full"].append(text)
    else:
        kn_cache["content_compliance_list"]["part"].append(text)
for data in datas2:
    if data[2] == "Pass" or data[4] != 1:
        continue
    text = data[1]
    if data[5] == 5:
        kn_cache["content_compliance_list"]["full"].append(text)
    else:
        kn_cache["content_compliance_list"]["part"].append(text)

logger.success("加载违禁词成功")
