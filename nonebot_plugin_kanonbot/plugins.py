# coding=utf-8
import random
import time
from nonebot import logger
import nonebot
import os
import sqlite3
from .config import kn_config, _zhanbu_datas, _config_list
from .tools import connect_api, save_image, image_resize2, draw_text, get_file_path
from PIL import Image, ImageDraw, ImageFont

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

run = True


async def plugins_zhanbu(user_id, cachepath):
    message = ""
    returnpath = None

    zhanbudb = cachepath + 'zhanbu/'
    if not os.path.exists(zhanbudb):
        os.makedirs(zhanbudb)
    zhanbudb = f"{zhanbudb}zhanbu.db"

    conn = sqlite3.connect(zhanbudb)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        datas = cursor.fetchall()
        # 数据库列表转为序列
        tables = []
        for data in datas:
            if data[1] != "sqlite_sequence":
                tables.append(data[1])
        if "zhanbu" not in tables:
            cursor.execute('create table zhanbu (userid varchar(10) primary key, id varchar(20))')
        cursor.execute(f'select * from zhanbu where userid = "{user_id}"')
        data = cursor.fetchone()
        if data is None:
            # 随机卡牌的好坏。1/3是坏，2/3是好
            # 但是貌似有些是混在一起的，有空再去琢磨一下概率（下次一定，咕咕咕
            zhanbu_type = random.randint(0, 2)
            if zhanbu_type == 0:
                zhanbu_type = "bad"
            else:
                zhanbu_type = "good"
            zhanbu_id = random.choice(list(_zhanbu_datas()[zhanbu_type]))
            zhanbu_data = _zhanbu_datas()[zhanbu_type][zhanbu_id]
            zhanbu_name = zhanbu_data["name"]
            zhanbu_message = zhanbu_data["message"]
            # 写入占卜结果
            cursor.execute(f'replace into zhanbu("userid","id") values("{user_id}", "{zhanbu_id}")')

            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    image = await connect_api("image", url)
                    image.save(returnpath)
                    message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            else:
                # 使用本地数据
                # message = f"今日占卜结果：{zhanbu_data['title']}\n{zhanbu_data['message']}"
                message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            pass
        else:
            zhanbu_name = ""
            zhanbu_message = ""
            zhanbu_id = str(data[1])
            zhanbu_datas = _zhanbu_datas()
            for ids in zhanbu_datas["good"]:
                if ids == zhanbu_id:
                    zhanbu_data = zhanbu_datas["good"]
                    zhanbu_name = zhanbu_data[ids]["name"]
                    zhanbu_message = zhanbu_data[ids]["message"]
                    break
            for ids in zhanbu_datas["bad"]:
                if ids == zhanbu_id:
                    zhanbu_data = zhanbu_datas["bad"]
                    zhanbu_name = zhanbu_data[ids]["name"]
                    zhanbu_message = zhanbu_data[ids]["message"]
                    break

            message = f"今日占卜结果：{zhanbu_name}\n{zhanbu_message}"
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    image = await connect_api("image", url)
                    image.save(returnpath)
    except:
        logger.error("KanonBot插件出错-plugin-zhanbu")
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return message, returnpath


def plugins_config(command_name: str, config_name: str, groupcode: str):
    message = " "
    returnpath = None
    command_name = command_name.removeprefix("config")
    if command_name == "开启":
        command_state = True
    elif command_name == "关闭":
        command_state = False
    else:
        command_state = "查询"
    config_list = _config_list()
    config_real_name = ""
    for name in config_list:
        config = config_list[name]
        if config_name == config["name"]:
            config_real_name = name
            break

    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db_path = dbpath + "comfig.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    if not os.path.exists(db_path):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if groupcode not in tables:
        cursor.execute(f"create table {groupcode}(command VARCHAR(10) primary key, state BOOLEAN(20))")

    if command_state is True or command_state is False:
        # 开启或关闭功能
        cursor.execute(f'SELECT * FROM {groupcode} WHERE command = "{config_real_name}"')
        data = cursor.fetchone()
        if data is not None:
            state = data[1]
            if state == command_state:
                message = f"{config_name}已{command_name}"
            else:
                cursor.execute(f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
                conn.commit()
            message = f"{config_name}已{command_name}"
        else:
            cursor.execute(f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
            conn.commit()
            message = f"{config_name}已{command_name}"
    else:
        # 查询开启的功能
        code = 1
        message = "查询功能"
        pass
    cursor.close()
    conn.close()
    return message, returnpath


async def plugins_emoji_xibao(command, command2, imgmsgs):
    if imgmsgs:
        url = imgmsgs[0]
        image = await connect_api("image", url)
    else:
        image = None

    if command2 is None:
        command2 = " "

    if command == "喜报":
        text_color1 = "#FFFF00"
        text_color2 = "#FF0000"
        text_color3 = "#EC5307"
    else:
        text_color1 = "#FFFFFF"
        text_color2 = "#000000"
        text_color3 = "#ECECEC"

    if kn_config("kanon_api-state"):
        if command == "喜报":
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-xibao"
        else:
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-beibao"
        xibao_image = await connect_api("image", url)
    else:
        xibao_image = Image.new("RGB", (600, 450), (0, 0, 0))

    if command2 != " " and imgmsgs:
        image = image_resize2(image, (200, 200), overturn=False)
        w, h = image.size
        x = int((600 - w) / 2 + 130)
        y = int((450 - h) / 2 + 30)
        xibao_image.paste(image, (x, y), mask=image)

        textlen = len(command2)
        fortlen = 40
        x = 190
        if textlen <= 6:
            x = int(x - ((textlen / 2) * fortlen))
        else:
            x = x - (3 * fortlen)
        y = 200 - int(textlen * 0.05 * fortlen)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            textlen=6,
            text_color=text_color1,
            draw_qqemoji=False,
            calculate=False
        )
        box = (x + 2, y + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x - 2, y + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x + 2, y - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (x - 2, y - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            text_color=text_color2,
            textlen=6,
            draw_qqemoji=True,
            calculate=False
        )
        box = (x, y)
        xibao_image.paste(paste_image, box, mask=paste_image)

    elif command2 != '':
        textlen = len(command2)
        if textlen <= 6:
            fortlen = 200 - (textlen * 25)
        else:
            fortlen = 40

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            textlen=12,
            text_color=text_color1,
            draw_qqemoji=False,
            calculate=False
        )
        w, h = paste_image.size
        x, y = xibao_image.size
        box = (int((x - w) / 2) + 2, int((y - h) / 2) + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) - 2, int((y - h) / 2) + 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) + 2, int((y - h) / 2) - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)
        box = (int((x - w) / 2) - 2, int((y - h) / 2) - 2)
        xibao_image.paste(paste_image, box, mask=paste_image)

        paste_image = await draw_text(
            texts=command2,
            size=fortlen,
            text_color=text_color2,
            textlen=12,
            draw_qqemoji=True,
            calculate=False
        )
        w, h = paste_image.size
        x, y = xibao_image.size
        box = (int((x - w) / 2), int((y - h) / 2))
        xibao_image.paste(paste_image, box, mask=paste_image)

    elif imgmsgs:
        w, h = image.size
        x = int((600 - w) / 2)
        y = int((450 - h) / 2 + 30)
        xibao_image.paste(image, (x, y, int(x + w), int(y + h)), mask=image)
        image = Image.new(mode='RGB', size=(w, h), color=text_color3)
        mask_image = Image.new("RGBA", (w, h), (0, 0, 0, 15))
        xibao_image.paste(image, (x, y, int(x + w), int(y + h)), mask=mask_image)

    return save_image(xibao_image)


async def plugins_emoji_yizhi(user_avatar):
    user_image = await connect_api("image", user_avatar)
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    imageyizhi = Image.new(mode='RGB', size=(768, 950), color="#FFFFFF")
    draw = ImageDraw.Draw(imageyizhi)

    imageyizhi.paste(user_image, (64, 64))
    image_face = user_image.resize((100, 100))
    imageyizhi.paste(image_face, (427, 800))

    file_path = await get_file_path("SourceHanSansK-Bold.ttf")
    font = ImageFont.truetype(font=file_path, size=85)
    draw.text(xy=(60, 805), text='要我一直        吗？', fill=(0, 0, 0), font=font)

    return save_image(imageyizhi)
