# coding=utf-8
import json
import random
import time
from nonebot import logger
import nonebot
import os
import sqlite3
from .config import kn_config, _zhanbu_datas, _config_list
from .tools import connect_api, save_image, image_resize2, draw_text, get_file_path, new_background, circle_corner
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


async def plugin_zhanbu(user_id, cachepath):
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
                    try:
                        image = await connect_api("image", url)
                        image.save(returnpath)
                    except Exception as e:
                        image = await draw_text("获取图片出错", 50, 10)
                        logger.error(f"获取图片出错:{e}")
                        returnpath = save_image(image)
                    message = f"抽到了一张牌子：{zhanbu_name}\n{zhanbu_message}"
            else:
                # 使用本地数据
                # message = f"抽到了一张牌子：{zhanbu_data['title']}\n{zhanbu_data['message']}"
                message = f"抽到了一张牌子：{zhanbu_name}\n{zhanbu_message}"
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

            message = f"抽到了一张牌子：{zhanbu_name}\n{zhanbu_message}"
            if kn_config("kanon_api-state"):
                # 如果开启了api，则从服务器下载占卜数据
                returnpath = f"{basepath}image/占卜2/"
                if not os.path.exists(returnpath):
                    os.makedirs(returnpath)
                returnpath += f"{zhanbu_name}.jpg"
                if not os.path.exists(returnpath):
                    # 如果文件未缓存，则缓存下来
                    url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-zhanbu2-{zhanbu_id}"
                    try:
                        image = await connect_api("image", url)
                        image.save(returnpath)
                    except Exception as e:
                        image = await draw_text("获取图片出错", 50, 10)
                        logger.error(f"获取图片出错:{e}")
                        returnpath = save_image(image)
    except:
        logger.error("KanonBot插件出错-plugin-zhanbu")
    finally:
        conn.commit()
        cursor.close()
        conn.close()

    return message, returnpath


async def plugin_checkin(user_id: str, group_id: str, date: str):
    """
    签到功能，state=0,message="签到成功" state=1,message="签到失败"
    :param user_id: 用户id
    :param group_id: 群id
    :param date: 今日日期
    :return: {"state": state, "message": message}
    """
    state = "success"
    message = ""
    date: str = time.strftime("%Y-%m-%d", time.localtime())

    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    if not os.path.exists(f"{basepath}db/"):
        # 数据库文件 如果文件不存在，会自动在当前目录中创建
        os.makedirs(f"{basepath}db/")
        cursor.execute(f"CREATE TABLE checkin(user_id VARCHAR (10) PRIMARY KEY, point BOOLEAN(20))")
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "checkin" not in tables:
        cursor.execute(f"create table checkin(user_id VARCHAR(10) primary key, date VARCHAR(10), point INT(20))")
    cursor.execute(f'select * from checkin where user_id = "{user_id}"')
    data = cursor.fetchone()
    add_point = random.randint(2, 3)
    if data is None:
        # 未有数据，签到并返回成功
        point = add_point
        cursor.execute(f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
        conn.commit()
        state = 0
    else:
        last_data = data[1]
        point = data[2]
        if date == last_data:
            # 已经签到过，不再签到
            state = 1
        else:
            # 今日未签到，正常签到
            point = int(point) + add_point
            cursor.execute(f'replace into checkin ("user_id","date","point") values("{user_id}","{date}",{point})')
            conn.commit()
            state = 0
    cursor.close()
    conn.close()

    # 创建返回的消息
    if state == 0:
        message = f"签到成功，获得{add_point}根薯条，现在有{point}根薯条"
    else:
        message = f"今天签到过啦，{point}根薯条还不够吃嘛…QAQ…"

    return state, message


def plugin_config(command_name: str, config_name, groupcode: str):
    message = ""
    returnpath = None
    command_name = command_name.removeprefix("config")
    if command_name == "开启":
        command_state = True
        if config_name is None:
            return "请添加要关闭的功能名字，例：“开启 猜猜看”", None
    elif command_name == "关闭":
        command_state = False
        if config_name is None:
            return "请添加要关闭的功能名字，例：“关闭 猜猜看”", None
    else:
        command_state = "查询"
    config_list = _config_list()
    config_real_name = ""
    for name in config_list:
        config = config_list[name]
        if config_name == config["name"]:
            config_real_name = name
            break

    # 初始化数据库
    dbpath = basepath + "db/"
    if not os.path.exists(dbpath):
        os.makedirs(dbpath)
    db_path = dbpath + "config.db"
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

    # 检查开关状态
    if command_name is None:
        message = f"未添加功能名。请输入“{command_name}+功能名来开启与关闭对应功能”"
    elif command_state is True or command_state is False:
        # 开启或关闭功能
        cursor.execute(f'SELECT * FROM {groupcode} WHERE command = "{config_real_name}"')
        data = cursor.fetchone()
        if data is not None:
            state = data[1]
            if state == command_state:
                message = f"{config_name}已{command_name}"
            else:
                cursor.execute(
                    f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
                conn.commit()
            message = f"{config_name}已{command_name}"
        else:
            cursor.execute(f'replace into {groupcode} ("command","state") values("{config_real_name}",{command_state})')
            conn.commit()
            message = f"{config_name}已{command_name}"
    else:
        # 查询开启的功能
        message = ("功能列表："
                   "\n现支持的功能列表"
                   "\n1.合成emoji"
                   "\n2.一直"
                   "\n3.猜猜看"
                   "\n4.炸飞机"
                   "\n5.签到"
                   " ")

    cursor.close()
    conn.close()
    return message, returnpath


async def plugin_emoji_emoji(command):
    message = None

    returnpath = f"{basepath}cache/emoji/"
    if not os.path.exists(returnpath):
        os.makedirs(returnpath)
    returnpath += f"{command}.png"

    if not os.path.exists(returnpath):
        url = f"{kn_config('kanon_api-url')}/json/emoji?imageid={command}"
        return_json = await connect_api("json", url)
        if return_json["code"] == 0:
            url = f"{kn_config('kanon_api-url')}/api/emoji?imageid={command}"
            image = await connect_api("image", url)
            image.save(returnpath)
        else:
            message = f"{command}不支持合成"
    return message, returnpath


async def plugin_emoji_xibao(command, command2, imgmsgs):
    if imgmsgs:
        url = imgmsgs[0]
        try:
            image = await connect_api("image", url)
        except Exception as e:
            image = await draw_text("获取图片出错", 50, 10)
            logger.error(f"获取图片出错:{e}")
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
        file_path = f"{basepath}cache/plugin_image/"
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        if command == "喜报":
            file_path += "喜报.png"
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-xibao"
        else:
            file_path += "悲报.png"
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-meme-beibao"
        if os.path.exists(file_path):
            xibao_image = Image.open(file_path, "r")
        else:
            try:
                xibao_image = await connect_api("image", url)
                image.save(file_path)
            except Exception as e:
                image = await draw_text("获取图片出错", 50, 10)
                logger.error(f"获取图片出错:{e}")
                return save_image(image)
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

    elif command2 != " ":
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
        image = image_resize2(image, (500, 300), overturn=False)
        w, h = image.size
        xibao_image_w, xibao_image_h = xibao_image.size
        x = int((xibao_image_w - w) / 2)
        y = int((xibao_image_h - h) / 2 + 30)
        xibao_image.paste(image, (x, y), mask=image)
        image = Image.new(mode='RGB', size=(w, h), color=text_color3)
        mask_image = Image.new("RGBA", (w, h), (0, 0, 0, 15))
        xibao_image.paste(image, (x, y), mask=mask_image)

    return save_image(xibao_image)


async def plugin_emoji_yizhi(user_avatar:str):
    try:
        if user_avatar in [None, "None", "none"]:
            user_image = await draw_text("图片", 50, 10)
        elif user_avatar.startswith("http"):
            user_image = await connect_api("image", user_avatar)
        else:
            user_image = Image.open(user_avatar, "r")
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    imageyizhi = Image.new(mode='RGB', size=(768, 950), color="#FFFFFF")
    draw = ImageDraw.Draw(imageyizhi)

    imageyizhi.paste(user_image, (64, 64), mask=user_image)
    image_face = image_resize2(user_image, (100, 100), overturn=False)
    imageyizhi.paste(image_face, (427, 800), mask=image_face)

    file_path = await get_file_path("SourceHanSansK-Bold.ttf")
    font = ImageFont.truetype(font=file_path, size=85)
    draw.text(xy=(60, 805), text='要我一直        吗？', fill=(0, 0, 0), font=font)

    return save_image(imageyizhi)


async def plugin_emoji_keai(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    image = Image.new(mode='RGB', size=(768, 950), color="#FFFFFF")
    draw = ImageDraw.Draw(image)
    w, h = user_image.size
    image.paste(user_image, (int((768 - w) / 2), int((854 - h) / 2)))

    text = f'请问你们看到{user_name}了吗？'
    image_paste = await draw_text(text, 50, 30)
    u, v = image_paste.size
    y = 48
    x = int(y / v * u)
    image_paste.resize((x, y))
    image.paste(image_paste, (9, 9), mask=image_paste)

    font_file = await get_file_path("SourceHanSansK-Bold.ttf")
    font = ImageFont.truetype(font=font_file, size=60)
    draw.text(xy=(20, 810), text='非常可爱！简直就是小天使', fill=(0, 0, 0), font=font)

    font = ImageFont.truetype(font=font_file, size=32)
    draw.text(xy=(30, 900), text='ta没失踪也没怎么样，我只是觉得你们都该看一下', fill=(0, 0, 0),
              font=font)

    return save_image(image)


async def plugin_emoji_jiehun(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    image = Image.new("RGB", (640, 640), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    path = await get_file_path("plugin-jiehun-jiehun.png")
    paste_image = Image.open(path, mode="r")
    image.paste(paste_image, (0, 0), mask=paste_image)

    # 添加名字1
    textlen = len(user_name)
    if textlen >= 10:
        user_name = str(user_name[0:9])
        user_name += "..."

    imagetext = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    paste_image = await draw_text(user_name, 17, 13)
    imagetext.paste(paste_image, (0, 90), mask=paste_image)

    imagetext = imagetext.rotate(-18.5)
    image.paste(imagetext, (0, 100), mask=imagetext)

    return save_image(image)


async def plugin_emoji_momo(user_avatar):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    # 开始绘图
    filepath = await get_file_path("plugin-emoji-momo-0.png")
    pic = Image.open(filepath, mode="r")

    date_year = time.strftime("%Y", time.localtime())
    date_month = time.strftime("%m", time.localtime())
    date_day = time.strftime("%d", time.localtime())
    timestamp = str(time.time())
    returnpath = f"{basepath}cache/{date_year}/{date_month}/{date_day}/摸摸/"
    gifcache = f"{returnpath}{timestamp}_{random.randint(1000, 9999)}gifcache/"
    if not os.path.exists(gifcache):
        os.makedirs(gifcache)

    image_x = [75, 74, 76, 78, 77]
    image_y = [83, 84, 82, 80, 81]
    imagepace_x = [33, 33, 33, 33, 33]
    imagepace_y = [37, 35, 33, 36, 40]

    image_face_clown = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    image_face_clown = circle_corner(image_face_clown, 30)

    imagenum = len(image_x)
    num = 1
    while num <= imagenum:
        print_imagepace_x = imagepace_x[num - 1]
        print_imagepace_y = imagepace_y[num - 1]
        print_image_x = image_x[num - 1]
        print_image_y = image_y[num - 1]
        print_image_face = user_image.resize((print_image_x, print_image_y))
        print_image_face_clown = image_face_clown.resize((print_image_x, print_image_y))

        pic1 = pic
        filepath = await get_file_path("plugin-emoji-momo-0.png")
        pic = Image.open(filepath, mode="r")
        filepath = await get_file_path(f"plugin-emoji-momo-{num}.png")
        paste_image = Image.open(filepath, mode="r")

        pic1.paste(pic, (0, 0))
        pic1.paste(print_image_face, (print_imagepace_x, print_imagepace_y),
                   mask=print_image_face_clown)
        pic1.paste(paste_image, (0, 0), mask=paste_image)

        pic1.save(f"{gifcache}/{num}.png")
        num += 1

    returnpath = f"{returnpath}{timestamp}_{random.randint(1000, 9999)}.gif"
    frames = []
    png_files = os.listdir(gifcache)
    for frame_id in range(1, len(png_files) + 1):
        frame = Image.open(os.path.join(gifcache, '%d.png' % frame_id))
        frames.append(frame)
    frames[0].save(returnpath, save_all=True, append_images=frames[1:], duration=70, loop=0,
                   disposal=2)

    return returnpath


async def plugin_emoji_qinqin(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_tietie(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_daibu(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_ti(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_yaoyao(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_pa(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_ji(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_quanquan(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_wolaopo(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_zhi(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_jiehunzheng(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_ji2(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji_autorply(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_emoji(user_avatar, user_name):
    try:
        user_image = await connect_api("image", user_avatar)
    except Exception as e:
        user_image = await draw_text("图片", 50, 10)
        logger.error(f"获取图片出错:{e}")
    user_image = image_resize2(user_image, (640, 640), overturn=False)

    pass

    return save_image(image)


async def plugin_game_cck(command, channel_id):
    """
    cck插件内容
    返回：
    当code = 0时，不做任何回复；
    当code = 1时，回复message消息；
    当code = 2时，回复returnpath目录中的图片
    当code = 3时，回复message消息和returnpath目录中的图片
    :param command: 命令
    :param channel_id: 频道号
    :return: code, message, returnpath
    """
    time_now = int(time.time())
    code = 0
    message = " "
    returnpath = None
    returnpath2 = None
    returnpath3 = None
    if not kn_config("kanon_api-state"):
        logger.error("未开启api，已经退出cck")
        return 0, message, returnpath

    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "gameinglist" not in tables:
        cursor.execute(
            'CREATE TABLE gameinglist (channelid VARCHAR (10) PRIMARY KEY, gamename VARCHAR (10), '
            'lasttime VARCHAR (10), gameing BOOLEAN (10), gamedata VARCHAR (10))')
    cursor.execute(f'select * from gameinglist where channelid = "{channel_id}"')
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"该群正在进行的游戏{data}")

    game_state = None
    if data is not None:
        # 有game数据
        gameing = data[3]
        if gameing == 1:
            # 有正在进行的game
            gamename = data[1]
            if gamename == "小游戏-猜猜看":
                # 正在进行的是猜猜看
                if int(time_now) <= (int(data[2]) + 600):
                    # 正在运行的cck最后一次运行时间相隔现在5分钟内
                    if command == "猜猜看":
                        message = "已经在cck了"
                        code = 1
                    else:
                        game_state = "gameing"
                else:
                    # 正在运行的cck最后一次运行时间相隔现在5分钟后
                    if command == "猜猜看":
                        game_state = "new"
                    else:
                        game_state = "exit"
                        code = 1
                        message = "时间超时，请重新开始"
            else:
                # 正在进行其他游戏
                code = 1
                message = f"正在进行{gamename}，请先结束{gamename}。\n结束指令“/{gamename} 结束”"
        else:
            # 没有正在进行的game
            if command == '猜猜看':
                game_state = "new"
            else:
                code = 1
                message = "没有在猜猜看哦"
    else:
        # data is None
        if command == "猜猜看":
            game_state = "new"
        elif command in ["不知道", "是"]:
            code = 1
            message = "没有在进行猜猜看哦"
        else:
            code = 1
            message = "没有在猜猜看哦。"

    if game_state == "new":
        logger.info('新建游戏')
        # 获取游戏基本数据（卡牌列表）
        filepath = await get_file_path("plugin-cck-member_list.json")
        data = open(filepath, 'r', encoding='utf8')
        json_data = json.load(data)
        member_ids = list(json_data["member_data"])
        member_id = random.choice(member_ids)  # 选择一个角色
        image_name = random.choice(json_data["member_data"][member_id]["images"])  # 选择一张卡牌
        member_name = json_data["member_data"][member_id]["member_name"]
        member_alias = json_data["member_data"][member_id]["alias"]

        # 收集本次游戏数据
        gameinfo = {
            "member_id": member_id,  # 角色id
            "member_name": member_name,  # 角色名称
            "image_name": image_name,  # 卡牌的文件名
            "member_alias": member_alias  # 角色别称
        }

        # 获取卡牌png文件
        returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/"
        if not os.path.exists(returnpath):
            os.makedirs(returnpath)
        returnpath += image_name
        if not os.path.exists(returnpath):
            url = f"{kn_config('kanon_api-url')}/api/image?imageid=knapi-cck-{member_id}-{image_name}"
            try:
                image = await connect_api("image", url)
                image.save(returnpath)
            except Exception as e:
                logger.error(f"获取图片出错:{e}")
                return 1, "图片下载出错"

        # 保存数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","小游戏-猜猜看","{time_now}",True,"{gameinfo}")')
        cursor.close()
        conn.commit()
        conn.close()

        # 切分卡牌为3张，并保存为1张
        cck_card = Image.open(returnpath, mode="r")
        x = 1334
        y = 1002

        # 切分1
        cck_imane1 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane1)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane1.paste(cck_card, (trimx, trimy))

        # 切分2
        cck_imane2 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane2)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane2.paste(cck_card, (trimx, trimy))

        # 切分3
        cck_imane3 = Image.new(mode='RGB', size=(300, 100), color="#FFFFFF")
        ImageDraw.Draw(cck_imane3)
        trimx = 0 - random.randint(0, x - 300)
        trimy = 0 - random.randint(0, y - 100)
        cck_imane3.paste(cck_card, (trimx, trimy))

        # 合并1
        cck_imane = Image.new("RGB", (150, 150), "#FFFFFF")
        cck_imane1 = cck_imane1.resize((150, 50))
        cck_imane.paste(cck_imane1, (0, 0))

        # 合并2
        cck_imane2 = cck_imane2.resize((150, 50))
        cck_imane.paste(cck_imane2, (0, 50))

        # 合并3
        cck_imane3 = cck_imane3.resize((150, 50))
        cck_imane.paste(cck_imane3, (0, 100))
        returnpath = save_image(cck_imane)

        # 添加回复的句子
        num = random.randint(1, 5)
        if num == 1:
            message = '那个女人是谁呢？好美'
        elif num == 2:
            message = '猜猜wlp是谁～'
        elif num == 3:
            message = '猜猜她是谁～'
        elif num == 4:
            message = '猜猜她是谁～'
        elif num == 5:
            message = '猜猜她是谁～'
        message += ("\n游戏限制5分钟内"
                    "\n@bot并发送/猜猜看+名字"
                    "\n例：“@kanon/猜猜看 花音”"
                    "\n发送/猜猜看+不知道结束游戏")
        code = 3  # 添加回复的类型
    elif game_state == "gameing":
        # 正在游戏中，判断不是”不知道“，否则为判断角色名是否符合
        if command == "不知道":
            # 读取游戏数据
            gamedata = json.loads(data[4].replace("'", '"'))
            member_id = gamedata["member_id"]
            member_name = gamedata["member_name"]
            image_name = gamedata["image_name"]

            # 返回卡牌图片和句子
            returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/{image_name}"
            message = f"是{member_name}哦"
            code = 3

            # 将”结束游戏状态“写入到数据库
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            cursor.execute(
                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                f'"{channel_id}","none","0",False,"none")')
            cursor.close()
            conn.commit()
            conn.close()
        else:
            # 读取游戏内容
            gamedata = json.loads(data[4].replace("'", '"'))
            member_id = gamedata["member_id"]
            member_name = gamedata["member_name"]
            image_name = gamedata["image_name"]
            member_alias = gamedata["member_alias"]

            # 判断用户发送词是否符合
            if command in member_alias:
                # 添加回复句子与图
                message = f"恭喜猜中，她就是{command}"
                returnpath = f"{basepath}cache/plugin/cck-card/{member_id}/{image_name}"
                code = 3

                # 将”结束游戏状态“写入到数据库
                conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                cursor = conn.cursor()
                cursor.execute(
                    f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                    f'"{channel_id}","none","0",False,"none")')
                cursor.close()
                conn.commit()
                conn.close()
            else:
                message = f"猜错了哦，她不是{command}"
                code = 1

    elif game_state == "exit":
        # 手动退出game状态
        # 将”结束游戏状态“写入到数据库
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","none","0",False,"none")')
        cursor.close()
        conn.commit()
        conn.close()
    return code, message, returnpath


async def plugin_game_blowplane(command: str, channel_id: str):
    """
    炸飞机插件内容
    返回：
    当code = 0时，不做任何回复；
    当code = 1时，回复message消息；
    当code = 2时，回复returnpath目录中的图片
    当code = 3时，回复message消息和returnpath目录中的图片
    :param command: 命令
    :param channel_id: 频道号
    :return: code, message, returnpath
    """
    code = 0
    message = ""
    returnpath = ""
    time_now = str(int(time.time()))

    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
    datas = cursor.fetchall()
    tables = []
    for data in datas:
        if data[1] != "sqlite_sequence":
            tables.append(data[1])
    if "gameinglist" not in tables:
        cursor.execute(
            'CREATE TABLE gameinglist (channelid VARCHAR (10) PRIMARY KEY, gamename VARCHAR (10), '
            'lasttime VARCHAR (10), gameing BOOLEAN (10), gamedata VARCHAR (10))')
    cursor.execute(f'select * from gameinglist where channelid = "{channel_id}"')
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    logger.debug(f"该群正在进行的游戏{data}")

    game_state = None
    if data is not None:
        # 有game数据
        gameing = data[3]
        if gameing == 1:
            # 有正在进行的game
            gamename = data[1]
            if gamename == "小游戏-炸飞机":
                # 正在进行的是炸飞机
                if int(time_now) <= (int(data[2]) + 300):
                    # 正在运行的炸飞机最后一次运行时间相隔现在5分钟内
                    if command == "炸飞机":
                        message = "已经在炸飞机了"
                        code = 1
                    else:
                        game_state = "gameing"
                else:
                    # 正在运行的炸飞机最后一次运行时间相隔现在5分钟后
                    if command == "炸飞机":
                        game_state = "new"
                    else:
                        game_state = "exit"
                        code = 1
                        message = "时间超时，请重新开始"
            else:
                # 正在进行其他游戏
                code = 1
                message = f"正在进行{gamename}，请先结束{gamename}。\n结束指令“/{gamename} 结束”"
        else:
            # 没有正在进行的game
            if command == "炸飞机":
                game_state = "new"
            else:
                code = 1
                message = "没有在炸飞机哦"
    else:
        # data is None
        if command == "炸飞机":
            game_state = "new"
        elif command.startswith("炸") or command == "结束":
            code = 1
            message = "没有在进行炸飞机哦"
        else:
            code = 1
            message = "没有在炸飞机哦。"

    if game_state == "new":
        # 生成游戏数据
        #  生成飞机位置
        plantnum = 3
        num = plantnum
        plants_info = []
        while num >= 1:
            num -= 1
            plant_info = []
            plant_dection = random.randint(0, 3)
            if plant_dection == 0:  # 向下
                plantx1 = 3
                plantx2 = 8
                planty1 = 1
                planty2 = 7
            elif plant_dection == 1:  # 向左
                plantx1 = 1
                plantx2 = 7
                planty1 = 3
                planty2 = 8
            elif plant_dection == 2:  # 向上
                plantx1 = 3
                plantx2 = 8
                planty1 = 4
                planty2 = 10
            else:  # 向右
                plantx1 = 4
                plantx2 = 10
                planty1 = 3
                planty2 = 8
            plantx = random.randint(plantx1, plantx2)
            planty = random.randint(planty1, planty2)
            plant_info.append(plantx)
            plant_info.append(planty)
            plant_info.append(plant_dection)

            # 计算出飞机各个坐标
            plantxys = []
            if plant_dection == 0:  # 向上
                plantxys.append((plantx, planty))
                plantxys.append((plantx - 2, planty + 1))
                plantxys.append((plantx - 1, planty + 1))
                plantxys.append((plantx, planty + 1))
                plantxys.append((plantx + 1, planty + 1))
                plantxys.append((plantx + 2, planty + 1))
                plantxys.append((plantx, planty + 2))
                plantxys.append((plantx - 1, planty + 3))
                plantxys.append((plantx, planty + 3))
                plantxys.append((plantx + 1, planty + 3))
            elif plant_dection == 1:  # 向左
                plantxys.append((plantx, planty))
                plantxys.append((plantx + 1, planty - 2))
                plantxys.append((plantx + 1, planty - 1))
                plantxys.append((plantx + 1, planty))
                plantxys.append((plantx + 1, planty + 1))
                plantxys.append((plantx + 1, planty + 2))
                plantxys.append((plantx + 2, planty))
                plantxys.append((plantx + 3, planty - 1))
                plantxys.append((plantx + 3, planty))
                plantxys.append((plantx + 3, planty + 1))
            elif plant_dection == 2:  # 向下
                plantxys.append((plantx, planty))
                plantxys.append((plantx + 2, planty - 1))
                plantxys.append((plantx + 1, planty - 1))
                plantxys.append((plantx, planty - 1))
                plantxys.append((plantx - 1, planty - 1))
                plantxys.append((plantx - 2, planty - 1))
                plantxys.append((plantx, planty - 2))
                plantxys.append((plantx + 1, planty - 3))
                plantxys.append((plantx, planty - 3))
                plantxys.append((plantx - 1, planty - 3))
            else:  # 向右
                plantxys.append((plantx, planty))
                plantxys.append((plantx - 1, planty - 2))
                plantxys.append((plantx - 1, planty - 1))
                plantxys.append((plantx - 1, planty))
                plantxys.append((plantx - 1, planty + 1))
                plantxys.append((plantx - 1, planty + 2))
                plantxys.append((plantx - 2, planty))
                plantxys.append((plantx - 3, planty - 1))
                plantxys.append((plantx - 3, planty))
                plantxys.append((plantx - 3, planty + 1))

            # 检查是否合理
            plane_save = True
            for cache_plant_info in plants_info:
                cache_plant_dection = cache_plant_info[2]
                cache_plantx = cache_plant_info[0]
                cache_planty = cache_plant_info[1]

                cache_plantxys = []
                if cache_plant_dection == 0:  # 向上
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                elif cache_plant_dection == 1:  # 向左
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                elif cache_plant_dection == 2:  # 向下
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                else:  # 向右
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                for cache_plantxy in cache_plantxys:
                    for plantxy in plantxys:
                        if plantxy == cache_plantxy:
                            plane_save = False
            if plane_save is True:
                plants_info.append(plant_info)
            else:
                num += 1

        # 创建底图
        image = new_background(900, 900)
        filepath = await get_file_path("plugin-zfj-farme.png")
        paste_image = Image.open(filepath, mode="r")
        image.paste(paste_image, (0, 0), mask=paste_image)

        returnpath = save_image(image)

        boms_list = []

        # 收集本次游戏数据
        gameinfo = {
            "plants_info": plants_info,  # 飞机数据
            "boms_list": boms_list,  # 炸弹数据
        }

        # 保存数据
        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
        cursor = conn.cursor()
        cursor.execute(
            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
            f'"{channel_id}","小游戏-炸飞机","{time_now}",True,"{gameinfo}")')
        cursor.close()
        conn.commit()
        conn.close()

        message = '游戏已生成，发送/炸飞机+坐标进行游戏。' \
                  '\n例：“@kanon/炸飞机 a1”' \
                  '\n请在10分钟内完成游戏。' \
                  '\n你拥有13颗炸弹' \
                  '\n发送“/炸飞机 结束”可以提前结束游戏'
        code = 3
    elif game_state == "gameing":
        # 读取游戏数据
        gamedata = json.loads(data[4].replace("'", '"'))
        plants_info = gamedata["plants_info"]
        boms_list = gamedata["boms_list"]

        if command == "结束":
            # 创建底图
            image = new_background(900, 900)
            filepath = await get_file_path("plugin-zfj-farme.png")
            paste_image = Image.open(filepath, mode="r")
            image.paste(paste_image, (0, 0), mask=paste_image)

            # 获取飞机图片
            filepath = await get_file_path("plugin-zfj-plane1.png")
            paste_image_1 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-plane2.png")
            paste_image_2 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-plane3.png")
            paste_image_3 = Image.open(filepath, mode="r")

            # 绘制飞机的位置
            num = 0
            for plant_info in plants_info:
                if num == 0:
                    paste_image_0 = paste_image_1
                elif num == 1:
                    paste_image_0 = paste_image_2
                else:
                    paste_image_0 = paste_image_3
                num += 1

                cache_plantx = int(plant_info[0])
                cache_planty = int(plant_info[1])
                cache_plant_dection = int(plant_info[2])
                cache_plantxy = (cache_plantx, cache_planty)

                cache_plantxys = []
                if cache_plant_dection == 0:  # 向上
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                elif cache_plant_dection == 1:  # 向左
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                elif cache_plant_dection == 2:  # 向下
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                else:  # 向右
                    cache_plantxys.append((cache_plantx, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                for cache_plantxy in cache_plantxys:
                    plantx = cache_plantxy[0]
                    planty = cache_plantxy[1]
                    printx = -16 + plantx * 78
                    printy = -16 + planty * 78
                    image.paste(paste_image_0, (printx, printy), mask=paste_image_0)

            # 获取状态图片
            filepath = await get_file_path("plugin-zfj-miss.png")
            paste_image_0 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-injured.png")
            paste_image_1 = Image.open(filepath, mode="r")
            filepath = await get_file_path("plugin-zfj-crash.png")
            paste_image_2 = Image.open(filepath, mode="r")

            # 绘制现在状态图
            for bom in boms_list:
                printx = -16 + (int(bom[0]) * 78)
                printy = -16 + (int(bom[1]) * 78)
                bom_state = int(bom[2])
                if bom_state == 0:
                    image.paste(paste_image_0, (printx, printy), mask=paste_image_0)
                elif bom_state == 1:
                    image.paste(paste_image_1, (printx, printy), mask=paste_image_1)
                elif bom_state == 2:
                    image.paste(paste_image_2, (printx, printy), mask=paste_image_2)

            # 保存图片
            returnpath = save_image(image)
            message = "游戏已结束"
            code = 3

            # 将”结束游戏状态“写入到数据库
            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
            cursor = conn.cursor()
            cursor.execute(
                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                f'"{channel_id}","none","0",False,"none")')
            cursor.close()
            conn.commit()
            conn.close()
        else:
            if command.startswith("炸"):
                command = command.removeprefix('炸')
            # 转换坐标为数字
            bomx = 0
            if "a" in command:
                bomx = 1
            elif "b" in command:
                bomx = 2
            elif "c" in command:
                bomx = 3
            elif "d" in command:
                bomx = 4
            elif "e" in command:
                bomx = 5
            elif "f" in command:
                bomx = 6
            elif "g" in command:
                bomx = 7
            elif "h" in command:
                bomx = 8
            elif "i" in command:
                bomx = 9
            elif "j" in command:
                bomx = 10

            bomy = 0
            if "10" in command:
                bomy = 10
            elif "1" in command:
                bomy = 1
            elif "2" in command:
                bomy = 2
            elif "3" in command:
                bomy = 3
            elif "4" in command:
                bomy = 4
            elif "5" in command:
                bomy = 5
            elif "6" in command:
                bomy = 6
            elif "7" in command:
                bomy = 7
            elif "8" in command:
                bomy = 8
            elif "9" in command:
                bomy = 9

            if bomx == 0 or bomy == 0:
                code = 1
                message = "错误，请检查拼写。只能使用小写字母和数字来表示位置"
            else:
                if len(boms_list) >= 14:
                    # 炸弹用完，结束游戏
                    # 创建底图
                    image = new_background(900, 900)
                    filepath = await get_file_path("plugin-zfj-farme.png")
                    paste_image = Image.open(filepath, mode="r")
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取飞机图片
                    filepath = await get_file_path("plugin-zfj-plane1.png")
                    plane_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = Image.open(filepath, mode="r")

                    # 绘制飞机的位置
                    num = 0
                    for plant_info in plants_info:
                        if num == 0:
                            paste_image = plane_image_1
                        elif num == 1:
                            paste_image = plane_image_2
                        else:
                            paste_image = plane_image_3
                        num += 1

                        cache_plantx = int(plant_info[0])
                        cache_planty = int(plant_info[1])
                        cache_plant_dection = int(plant_info[2])
                        cache_plantxy = (cache_plantx, cache_planty)

                        cache_plantxys = []
                        if cache_plant_dection == 0:  # 向上
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                            cache_plantxys.append((cache_plantx, cache_planty + 2))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                            cache_plantxys.append((cache_plantx, cache_planty + 3))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                        elif cache_plant_dection == 1:  # 向左
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                            cache_plantxys.append((cache_plantx + 2, cache_planty))
                            cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 3, cache_planty))
                            cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                        elif cache_plant_dection == 2:  # 向下
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                            cache_plantxys.append((cache_plantx, cache_planty - 2))
                            cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                            cache_plantxys.append((cache_plantx, cache_planty - 3))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                        else:  # 向右
                            cache_plantxys.append((cache_plantx, cache_planty))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                            cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                            cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                            cache_plantxys.append((cache_plantx - 2, cache_planty))
                            cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                            cache_plantxys.append((cache_plantx - 3, cache_planty))
                            cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                        for cache_plantxy in cache_plantxys:
                            plantx = cache_plantxy[0]
                            planty = cache_plantxy[1]
                            printx = -16 + plantx * 78
                            printy = -16 + planty * 78
                            image.paste(paste_image, (printx, printy), mask=paste_image)

                    # 获取状态图片
                    filepath = await get_file_path("plugin-zfj-miss.png")
                    state_image_0 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = Image.open(filepath, mode="r")

                    # 绘制现在状态图
                    for bom in boms_list:
                        printx = -16 + (int(bom[0]) * 78)
                        printy = -16 + (int(bom[1]) * 78)
                        bom_state = int(bom[2])
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 保存图片
                    returnpath = save_image(image)
                    message = "炸弹已用光，游戏结束"
                    code = 3

                    # 将”结束游戏状态“写入到数据库
                    conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                        f'"{channel_id}","none","0",False,"none")')
                    cursor.close()
                    conn.commit()
                    conn.close()
                else:
                    # 创建底图
                    image = new_background(900, 900)
                    filepath = await get_file_path("plugin-zfj-farme.png")
                    paste_image = Image.open(filepath, mode="r")
                    image.paste(paste_image, (0, 0), mask=paste_image)

                    # 获取状态图片
                    filepath = await get_file_path("plugin-zfj-miss.png")
                    state_image_0 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-injured.png")
                    state_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-crash.png")
                    state_image_2 = Image.open(filepath, mode="r")

                    # 绘制现在状态图
                    for bom in boms_list:
                        printx = -16 + (int(bom[0]) * 78)
                        printy = -16 + (int(bom[1]) * 78)
                        bom_state = int(bom[2])
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 获取飞机图片
                    filepath = await get_file_path("plugin-zfj-plane1.png")
                    plane_image_1 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane2.png")
                    plane_image_2 = Image.open(filepath, mode="r")
                    filepath = await get_file_path("plugin-zfj-plane3.png")
                    plane_image_3 = Image.open(filepath, mode="r")

                    bomstate = -1
                    for bom in boms_list:
                        printx = int(bom[0])
                        printy = int(bom[1])
                        if printx == bomx and printy == bomy:
                            bomstate = 3
                    if bomstate != 3:
                        bomxy = (bomx, bomy)
                        for plant_info in plants_info:
                            cache_plantx = int(plant_info[0])
                            cache_planty = int(plant_info[1])
                            cache_plant_dection = int(plant_info[2])
                            cache_plantxy = (cache_plantx, cache_planty)
                            if bomxy == cache_plantxy:
                                bomstate = 2
                            else:
                                cache_plantxys = []
                                if cache_plant_dection == 0:  # 向上
                                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                                elif cache_plant_dection == 1:  # 向左
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                                elif cache_plant_dection == 2:  # 向下
                                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                                else:  # 向右
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                                for cache_plantxy in cache_plantxys:
                                    if bomxy == cache_plantxy:
                                        bomstate = 1
                        if bomstate == -1:
                            bomstate = 0
                    if bomstate != 3:
                        printx = -16 + (bomx * 78)
                        printy = -16 + (bomy * 78)
                        bom_state = int(bomstate)
                        if bom_state == 0:
                            image.paste(state_image_0, (printx, printy), mask=state_image_0)
                        elif bom_state == 1:
                            image.paste(state_image_1, (printx, printy), mask=state_image_1)
                        elif bom_state == 2:
                            image.paste(state_image_2, (printx, printy), mask=state_image_2)

                    # 保存数据
                    if bomstate == 0 or bomstate == 1 or bomstate == 2:
                        boom_data = [bomx, bomy, bomstate]
                        boms_list.append(boom_data)

                        # 收集本次游戏数据
                        gameinfo = {
                            "plants_info": plants_info,  # 飞机数据
                            "boms_list": boms_list,  # 炸弹数据
                        }

                        # 保存数据
                        conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                        cursor = conn.cursor()
                        cursor.execute(
                            f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                            f'"{channel_id}","小游戏-炸飞机","{time_now}",True,"{gameinfo}")')
                        cursor.close()
                        conn.commit()
                        conn.close()

                    if bomstate == 3:
                        code = 1
                        message = "出错!炸弹必须设置在未炸过的地方"
                    elif bomstate == 0:
                        code = 3
                        message = "引爆成功，该地方为空"
                    elif bomstate == 1:
                        code = 3
                        message = "成功炸伤飞机"
                    elif bomstate == 2:
                        code = 3
                        message = "成功炸沉飞机"

                    if bomstate == 2:
                        num = 0
                        for bom in boms_list:
                            bomstate = bom[2]
                            if bomstate == 2:
                                num += 1
                        if num >= 3:
                            # 绘制飞机的位置
                            num = 0
                            for plant_info in plants_info:
                                if num == 0:
                                    paste_image = plane_image_1
                                elif num == 1:
                                    paste_image = plane_image_2
                                else:
                                    paste_image = plane_image_3
                                num += 1

                                cache_plantx = int(plant_info[0])
                                cache_planty = int(plant_info[1])
                                cache_plant_dection = int(plant_info[2])
                                cache_plantxy = (cache_plantx, cache_planty)

                                cache_plantxys = []
                                if cache_plant_dection == 0:  # 向上
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx, cache_planty + 3))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 3))
                                elif cache_plant_dection == 1:  # 向左
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty))
                                    cache_plantxys.append((cache_plantx + 3, cache_planty + 1))
                                elif cache_plant_dection == 2:  # 向下
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx + 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx + 1, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx, cache_planty - 3))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 3))
                                else:  # 向右
                                    cache_plantxys.append((cache_plantx, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 2))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 1))
                                    cache_plantxys.append((cache_plantx - 1, cache_planty + 2))
                                    cache_plantxys.append((cache_plantx - 2, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty - 1))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty))
                                    cache_plantxys.append((cache_plantx - 3, cache_planty + 1))

                                for cache_plantxy in cache_plantxys:
                                    plantx = cache_plantxy[0]
                                    planty = cache_plantxy[1]
                                    printx = -16 + plantx * 78
                                    printy = -16 + planty * 78
                                    image.paste(paste_image, (printx, printy), mask=paste_image)

                            # 将”结束游戏状态“写入到数据库
                            conn = sqlite3.connect(f"{basepath}db/plugin_data.db")
                            cursor = conn.cursor()
                            cursor.execute(
                                f'replace into gameinglist ("channelid","gamename","lasttime","gameing","gamedata") values('
                                f'"{channel_id}","none","0",False,"none")')
                            cursor.close()
                            conn.commit()
                            conn.close()

                            message = '恭喜炸沉所有飞机，游戏结束。'

                    returnpath = save_image(image)

    return code, message, returnpath
