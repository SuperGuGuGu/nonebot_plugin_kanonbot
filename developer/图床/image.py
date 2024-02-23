import time
from fastapi import FastAPI, File, UploadFile, Response
from fastapi.responses import FileResponse
import os
from starlette import status
import sqlite3
import random
import string


app = FastAPI()

path = "./file"  # 存图片的文件夹
del_cache = False  # 是否自动清除2天前的缓存


@app.get("/image/{image_id}")
def image(response: Response, image_id: str = None):
    if image_id is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status_code": status.HTTP_404_NOT_FOUND}
    conn = sqlite3.connect(f"{path}/image.db")
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
            '(id INTEGER primary key AUTOINCREMENT, image_path VARCHAR(10), image_id VARCHAR(10))')
    # 读取数据
    cursor.execute(f'select * from id_list where image_id = "{image_id}"')
    data = cursor.fetchone()
    if data is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"status_code": status.HTTP_404_NOT_FOUND}
    image_path = data[1]
    return FileResponse(f"{path}{image_path}", headers={"Content-type": "image/png"})


@app.post("/upload/")
async def upload(file: UploadFile = File()):
    date_year = int(time.strftime("%Y", time.localtime()))
    date_month = int(time.strftime("%m", time.localtime()))
    date_day = int(time.strftime("%d", time.localtime()))
    file_path = f"/{date_year}/{date_month}/{date_day}"
    if not os.path.exists(f"{path}{file_path}"):
        os.makedirs(f"{path}{file_path}")

    # 清除缓存
    if del_cache is True:

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

        # 清除缓存
        if os.path.exists(f"/{path}/{date_year - 2}"):
            filenames = os.listdir(f"/{path}/{date_year - 2}")
            if filenames:
                del_files2(f"/{path}/{date_year - 2}")
        elif os.path.exists(f"/{path}/{date_year}/{date_month - 2}"):
            filenames = os.listdir(f"/{path}/{date_year}/{date_month - 2}")
            if filenames:
                del_files2(f"/{path}/{date_year}/{date_month - 2}")
        elif os.path.exists(f"/{path}/{date_year}/{date_month}/{date_day - 2}"):
            filenames = os.listdir(f"/{path}/{date_year}/{date_month}/{date_day - 2}")
            if filenames:
                del_files2(f"/{path}/{date_year}/{date_month}/{date_day - 2}")

    conn = sqlite3.connect(f"{path}/image.db")
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
            '(id INTEGER primary key AUTOINCREMENT, image_path VARCHAR(10), image_id VARCHAR(10))')

    # 创建一个id并保存
    num = 100
    random_str = "none"
    while num > 0:
        num -= 1
        random_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

        cursor.execute(f'SELECT * FROM "id_list" WHERE image_id = "{random_str}"')
        data = cursor.fetchone()
        if data is None:
            image_path = f"{file_path}/{random_str}.png"
            cursor.execute(
                f'replace into id_list ("image_path","image_id") values("{image_path}","{random_str}")')
            conn.commit()
            break
        else:
            continue

    # 关闭数据库
    cursor.close()
    conn.close()

    f = open(f"{path}{file_path}/{random_str}.png", 'wb')
    data = await file.read()
    f.write(data)
    f.close()

    return {
        "code": 0,
        "msg": "upload success",
        "image_id": random_str,
        "image_path": f"/image/{random_str}"
    }
