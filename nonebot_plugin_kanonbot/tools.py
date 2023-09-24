# coding=utf-8
import httpx
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import sqlite3
import random
import json
from nonebot import logger
import nonebot
import os
import shutil
import time
from .config import kn_config
import asyncio

# 读取配置文件
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


def get_command(msg) -> list:
    """
    使用空格和换行进行切分1次
    :param msg: 原始字符串。"hello world"
    :return: 切分后的内容["hello", "world"]
    """
    commands = []
    if ' ' in msg or '\n' in msg:
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


def get_face(qq, size: int = 640):
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


def connect_api(type: str, url: str, post_json=None, file_path: str = None):
    # 把api调用的代码放在一起，方便下一步进行异步开发
    if type == "json":
        if post_json is None:
            return json.loads(httpx.get(url).text)
        else:
            return json.loads(httpx.post(url, json=post_json).text)
    elif type == "image":
        try:
            image = Image.open(BytesIO(httpx.get(url).content))
        except Exception as e:
            logger.error("图片获取出错")
            logger.error(url)
            image = Image.open(BytesIO(httpx.get(url).content))
        return image
    elif type == "file":
        cache_file_path = file_path + "cache"
        try:
            # 这里不能用httpx。用就报错。
            with open(cache_file_path, "wb") as f, requests.get(url) as res:
                f.write(res.content)
            logger.info("下载完成")
            shutil.copyfile(cache_file_path, file_path)
            os.remove(cache_file_path)
        except Exception as e:
            logger.error(f"文件下载出错-{file_path}")
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
        url = kn_config("kanon_api-url") + "/file/" + file_name
        connect_api(type="file", url=url, file_path=file_path)
    return file_path


async def lockst():
    """
    如有其他指令在运行，则暂停该函数
    :param lockdb:
    :return:
    """
    lockdb = f"{basepath}db/"
    if not os.path.exists(lockdb):
        os.makedirs(lockdb)
    lockdb += "lock.db"
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
                if locking == 'on':
                    await asyncio.sleep(0.2)
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


def locked():
    """
    解除锁
    :param lockdb:
    :return:
    """
    lockdb = f"{basepath}db/"
    if not os.path.exists(lockdb):
        os.makedirs(lockdb)
    lockdb += "lock.db"
    # 解锁
    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
    cursor.execute('replace into lock(name,lock) values("lock","off")')
    cursor.close()
    conn.commit()
    conn.close()
    locking = 'off'
    return locking


def command_cd(qq, groupcode, coolingtime: int = 60, coolingnum: int = 7, coolinglong: int = 200):
    """
    指令冷却时间
    :param qq: 成员id
    :param groupcode: 群号码
    :param coolinglong: 触发冷却后，需要冷却的时间
    :param coolingnum: coolingtime分钟内发送超过coolingnum条消息就触发冷却
    :param coolingtime: coolingtime分钟内发送超过coolingnum条消息就触发冷却
    :return: "off" 或者 ”100“。off为不进行冷却，数字为冷却剩余时间。
    """
    cooling = "off"
    # coolingtime：冷却时间，单位S
    # coolingnum：冷却数量，单位条
    # coolinglong：冷却长度，单位S

    now = int(time.time())
    # 尝试创建数据库
    coolingnumber = str('0')

    db_path = f"{basepath}db/cooling.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if groupcode not in tables:
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        cursor.execute(f'create table {groupcode} (userid VARCHAR(10) primary key,'
                       f' number VARCHAR(20), time VARCHAR(30), cooling VARCHAR(30))')
    # 读取数据库内容：日期文件，群号表，用户数据
    # 查询数据
    cursor.execute(f"select * from {groupcode} where userid = {qq}")
    data = cursor.fetchone()
    try:
        if data is None:
            coolingnumber = '1'
            cooling = 'off'
            cursor.execute(f'replace into {groupcode}(userid,number,time,cooling) '
                           f'values("{qq}","{coolingnumber}","{now}","{cooling}")')
        else:
            # 判断是否正在冷却
            cooling = data[3]
            if cooling == 'off':
                #  判断时间，time-冷却时间再判断
                timeshortdata = int(data[2]) + int(coolingtime)
                if timeshortdata >= now:
                    # 小于冷却时间，冷却次数+1
                    coolingnumber = int(data[1]) + 1
                    #    判断冷却次数，次数>=冷却数量
                    if coolingnumber >= coolingnum:
                        cooling = 'on'
                        # 大于次数，开启冷却,写入
                        coolingnumber = str(coolingnumber)

                        cursor.execute(f'replace into {groupcode}(userid,number,time,cooling) '
                                       f'values("{qq}","{coolingnumber}","{now}","{cooling}")')
                        timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
                        coolingtime = str(timeshortdata - now)
                    else:
                        # 小于写入
                        cooling = 'off'
                        coolingnumber = str(coolingnumber)
                        cursor.execute(f'replace into {groupcode}(userid,number,time,cooling) '
                                       f'values("{qq}","{coolingnumber}","{now}","{cooling}")')
                else:
                    # 大于冷却时间，重新写入
                    coolingnumber = '1'
                    cooling = 'off'
                    cursor.execute(f'replace into {groupcode}(userid,number,time,cooling) '
                                   f'values("{qq}","{coolingnumber}","{now}","{cooling}")')
            else:
                timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
                if timeshortdata >= now:
                    coolingtime = str(timeshortdata - now)
                else:
                    coolingnumber = '1'
                    cooling = 'off'
                    cursor.execute(f'replace into {groupcode}(userid,number,time,cooling) '
                                   f'values("{qq}","{coolingnumber}","{now}","{cooling}")')
        if cooling != 'off':
            cooling = str(coolingtime)
    except Exception as e:
        logger.error("冷却数据库操作出错")
        logger.error(db_path)
        cooling = "off"
    finally:
        conn.commit()
        cursor.close()
        conn.close()
    return cooling


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


async def new_background2(image_x, image_y, draw_name, draw_title):
    """
    创建背景图v2
    :param image_x: 背景图宽
    :param image_y: 背景图长
    :param draw_name:  图片名称（左）
    :param draw_title:  图片标题（上）
    :return:  image
    """
    # 创建背景
    draw_image = Image.new("RGB", (image_x, image_y), "#c4e6fe")
    mask_image = Image.new("RGB", (190, 975))
    mask_image = circle_corner(mask_image, 34)
    if kn_config("kanon_api-state"):
        # 如果开启了api，则从服务器下载图片数据
        filepath = await get_file_path("kanonbot-draw-蓝色渐变.png")
        paste_image = Image.open(filepath, "r")
        paste_image = paste_image.resize((190, 975))
    else:
        paste_image = Image.new("RGB", (190, 975), "#")
    draw_image.paste(paste_image, (37, 68), mask=mask_image)

    # 添加卡片名称
    paste_image = Image.new("RGBA", (975, 975) ,(0, 0, 0, 0))
    draw2 = ImageDraw.Draw(paste_image)
    fortlen = 142
    if kn_config("kanon_api-state"):
        # 如果开启了api，则从服务器下载字体数据
        fontfile = await get_file_path("SourceHanSansK-ExtraLight.ttf")
    else:
        fontfile = None
    font = ImageFont.truetype(font=fontfile, size=fortlen)
    draw2.text((487-fortlen, 97), text=draw_name, font=font, fill=(193, 211, 255))
    paste_image = paste_image.rotate(90)
    draw_image.paste(paste_image, (0, 332), mask=paste_image)

    # 添加卡片标题
    draw = ImageDraw.Draw(draw_image)
    if kn_config("kanon_api-state"):
        # 如果开启了api，则从服务器下载字体数据
        fontfile = await get_file_path("SourceHanSansK-Normal.ttf")
    else:
        fontfile = None
    font = ImageFont.truetype(font=fontfile, size=56)
    draw.text((270, 68), text=draw_title, font=font, fill=(24, 148, 227))

    # 添加主体框
    w, h = draw_image.size
    paste_image = Image.new("RGB", (w-308, h-216), color="#e7f6ff")
    paste_image = circle_corner(paste_image, 34)
    draw_image.paste(paste_image, (268, 156), mask=paste_image)
    return draw_image
