# coding=utf-8
import httpx
from PIL import Image
from io import BytesIO
import sqlite3
import random
import json
from nonebot import logger
import nonebot
import os
import shutil
from .config import kn_config
import asyncio

# 读取配置文件
config = nonebot.get_driver().config
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
    """
    连接api以获取内容
    :param type: 下载类型。例：“json”, "image", "file"
    :param url: url。例："http://cdn.kanon.ink/json/config?name=ping"
    :param post_json: post获取时的内容。例：{"data": "data_here"}
    :param file_path: 文件保存位置。例："C:/file.zip"
    """
    # logger.info(f"connect-{url}")
    # 把api调用的代码放在一起，也许未来改为异步调取
    if type == "json":
        if post_json is None:
            return json.loads(httpx.get(url).text)
        else:
            return json.loads(httpx.post(url, json=post_json).text)
    elif type == "image":
        return Image.open(BytesIO(httpx.get(url).content))
    elif type == "file":
        cache_file_path = file_path + "cache"
        try:
            with open(cache_file_path, "wb") as f, httpx.get(url) as res:
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
        await connect_api(type="file", url=url, file_path=file_path)
    return file_path


async def lockst(lockdb):
    """
    如有其他指令在运行，则暂停该函数
    :param lockdb:
    :return:
    """
    import time
    sleeptime = random.randint(1, 200)
    sleeptime = float(sleeptime) / 100
    time.sleep(sleeptime)
    # 读取锁定

    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
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
    cursor.close()
    conn.close()

    # 判断锁定
    if locking == 'on':
        num = 100
        while num >= 1:
            num -= 1
            conn = sqlite3.connect(lockdb)
            cursor = conn.cursor()
            cursor.execute('select * from lock where name = "lock"')
            locking = cursor.fetchone()
            cursor.close()
            conn.close()
            if locking == 'on':
                await asyncio.sleep(0.2)
                if num == 0:
                    logger.info("等待超时")
            else:
                num = 0

    else:
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



def command_cd(qq, groupcode, timeshort, coolingdb):
    cooling = 'off'
    # 冷却时间，单位S
    coolingtime = '60'
    # 冷却数量，单位条
    coolingnum = 7
    # 冷却长度，单位S
    coolinglong = 200

    # 尝试创建数据库
    coolingnumber = str('0')

    conn = sqlite3.connect(coolingdb)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    # 数据库列表转为序列
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
    cursor.execute('select * from ' + groupcode + ' where userid = ' + qq)
    data = cursor.fetchone()
    if data is None:
        coolingnumber = '1'
        cooling = 'off'
        cursor.execute(
            f'replace into {groupcode}(userid,number,time,cooling) '
            f'values("{qq}","{coolingnumber}","{timeshort}","{cooling}")')
    else:
        # 判断是否正在冷却
        cooling = data[3]
        if cooling == 'off':
            #  判断时间，time-冷却时间再判断
            timeshortdata = int(data[2]) + int(coolingtime)
            timeshort = int(timeshort)
            if timeshortdata >= timeshort:
                # 小于冷却时间，冷却次数+1
                coolingnumber = int(data[1]) + 1
                #    判断冷却次数，次数>=冷却数量
                if coolingnumber >= coolingnum:
                    cooling = 'on'
                    # 大于次数，开启冷却,写入
                    coolingnumber = str(coolingnumber)
                    timeshort = str(timeshort)
                    cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{qq}","{coolingnumber}","{timeshort}","{cooling}")')
                    timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
                    coolingtime = str(timeshortdata - int(timeshort))
                else:
                    # 小于写入

                    cooling = 'off'
                    coolingnumber = str(coolingnumber)
                    timeshort = str(timeshort)
                    cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{qq}","{coolingnumber}","{timeshort}","{cooling}")')
            else:
                # 大于冷却时间，重新写入
                coolingnumber = '1'
                cooling = 'off'
                timeshort = str(timeshort)
                cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{qq}","{coolingnumber}","{timeshort}","{cooling}")')
        else:
            timeshortdata = int(data[2]) + int(coolingtime) + coolinglong
            timeshort = int(timeshort)
            if timeshortdata >= timeshort:
                coolingtime = str(timeshortdata - timeshort)
            else:
                coolingnumber = '1'
                cooling = 'off'
                timeshort = str(timeshort)
                cursor.execute(
                        f'replace into {groupcode}(userid,number,time,cooling) '
                        f'values("{qq}","{coolingnumber}","{timeshort}","{cooling}")')
    if cooling != 'off':
        cooling = str(coolingtime)

    cursor.close()
    conn.close()
    return cooling
