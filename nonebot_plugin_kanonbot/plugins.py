import random
import random
from nonebot import logger
import nonebot
import os
import sqlite3
from .config import kn_config, _zhanbu_datas
from .tools import get_file_path, connect_api

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

def plugins_zhanbu(qq, cachepath):
    message = ""
    returnpath = None

    zhanbudb = cachepath + 'zhanbu/'
    if not os.path.exists(zhanbudb):
        os.makedirs(zhanbudb)
    zhanbudb = f"{zhanbudb}zhanbu.db"

    conn = sqlite3.connect(zhanbudb)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    # 数据库列表转为序列
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "zhanbu" not in tables:
        cursor.execute('create table zhanbu (userid varchar(10) primary key, id varchar(20))')
    cursor.execute(f'select * from zhanbu where userid = "{qq}"')
    data = cursor.fetchone()
    if data is None:
        # zhanbu_datas = _zhanbu_datas()
        # zhanbu_id = random.choice(list(zhanbu_datas))
        zhanbu_id = str(random.randint(0, 116))
        # zhanbu_data = zhanbu_datas[zhanbu_id]
        if kn_config("kanon_api-state"):
            # 如果开启了api，则从服务器下载占卜数据
            returnpath = f"{basepath}image/占卜1/"
            if not os.path.exists(returnpath):
                os.makedirs(returnpath)
            returnpath += f"{zhanbu_id}.png"
            if not os.path.exists(returnpath):
                # 如果文件未缓存，则缓存下来
                url = kn_config("kanon_api-url") + f"api/image?imageid=knapi-zhanbu1-{zhanbu_id}"
                image = connect_api("image", url)
                image.save(f"{cachepath}占卜1/{zhanbu_id}.png")
        else:
            # 使用本地数据
            # message = f"今日占卜结果：{zhanbu_data['title']}\n{zhanbu_data['message']}"
            message = f"今日占卜结果：{zhanbu_id}"
        pass
    else:
        message = "今日占卜结果是："
    cursor.close()
    conn.close()

    return message, returnpath


