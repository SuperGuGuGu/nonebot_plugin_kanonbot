#coding=utf-8
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


def get_file_path(file_name):
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


def lockst(lockdb):
    import time
    sleeptime = random.randint(1, 200)
    sleeptime = float(sleeptime) / 100
    time.sleep(sleeptime)
    # 读取锁定
    try:
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        conn = sqlite3.connect(lockdb)
        cursor = conn.cursor()
        cursor.execute('create table lock (name VARCHAR(10) primary key, lock VARCHAR(20))')
        cursor.close()
        conn.close()
    except:
        print('已存在锁定数据库，开始读取数据')
    # 查询数据
    conn = sqlite3.connect(lockdb)
    cursor = conn.cursor()
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
                time.sleep(0.1)
                if num == 0:
                    print('超时')
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
