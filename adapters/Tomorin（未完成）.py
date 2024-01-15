import asyncio
import os

from bridge.tomorin import on_event, SessionExtension
from bot_run import botrun
from tools import get_command, get_unity_user_id, get_unity_user_data, connect_api


@on_event.message_created
def kanon_xibao_created(session: SessionExtension):
    session.function.register(["喜报"])
    session.action(kanon)


async def kanon(session: SessionExtension):
    print("name插件")
    # 读取消息内容
    msg = session.message.command.text
    commands = get_command(msg)
    command = commands[0]
    if len(commands) == 1:
        command2 = ""
    else:
        command2 = commands[1]

    user_id = session.user.id
    unity_user_id = get_unity_user_id("tomorin", user_id)
    unity_user_data = get_unity_user_data(unity_user_id)
    unity_user_data["avatar"] = session.user.avatar
    unity_user_data["username"] = session.user.name
    unity_user_data["nick_name"] = session.user.nick
    if "avatar" not in list(unity_user_data):
        unity_user_data["avatar"] = None
        save = True
    if "face_image" not in list(unity_user_data) and unity_user_data["avatar"] is not None:
        image_path = f"{basepath}file/user_face/"
        if not os.path.exists(image_path):
            os.makedirs(image_path)
        image_path += f"{unity_user_id}.png"
        image = await connect_api("image", unity_user_data["avatar"])
        image.save(image_path)
        unity_user_data["face_image"] = image_path
        save = True

    msg_info = {
        "msg": msg,
        "commands": commands,
        "commandname": commandname,
        "bot_id": session.self_id,
        "channel_id": session.message.channel,
        "guild_id": session.message.guild,
        "at_datas": [],
        "user": unity_user_data,
        "imgmsgs": [],
        "event_name": "message_event",
        "friend_list": [],
        "channel_member_datas": {}
    }

    # 全局默认变量
    return_data = {"code": 0,
            "message": "None",
            "returnpath": "None",
            "returnpath2": "None",
            "returnpath3": "None"
            }

    return_data = await botrun(msg_info)

    # 貌似不需要另外异步
    # # 添加异步运行函数
    # async def run_plugins():
    #     global return_data
    #     return_data = await botrun(msg_info)
    #     return
    #
    # # 运行插件
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(run_plugins())

    # 总结与发送
    print(return_data)
    code = int(return_data["code"])
    if code in [1, 3, 4, 5]:
        msg = return_data["message"]
        session.send(msg)
