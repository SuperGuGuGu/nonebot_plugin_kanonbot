from PIL import Image
from bridge.tomorin import on_event, SessionExtension, h
from plugins.xibao_plugin.plugins import plugin_emoji_xibao
from tools import get_command
"""
发送喜报的插件

其他功能可使用类似加载方法。其他功能加载方法：
1.下载 plugins.py、tools.py、config.py 三个文件
2.替换现有文件夹内这三个插件
3.修改19行指令名称 以及 34行导入的插件名称
4.修改39-40行消息的发送方式，让消息正确发送
注意：导入的其他插件由于设置上不同，需要在 tools.py 的 _kanonbot_plugin_config 函数中 except 的位置修改默认位置
"""


@on_event.message_created
def kanon_xibao_created(session: SessionExtension):
    session.function.register(["喜报", "xibao"])
    session.action(k_plugin)


async def k_plugin(session: SessionExtension):
    # 读取消息内容
    msg = session.message.command.text
    commands = get_command(msg)
    command = commands[0]
    if len(commands) == 1:
        command2 = ""
    else:
        command2 = commands[1]

    # 运行插件
    return_data = await plugin_emoji_xibao(command, command2)

    # 发送消息
    # return_data = "./cache_file/cache/2024/02/01/17000_000.png"
    # 该插件返回了一个图片路径，直接发送图片路径
    image = Image.open(return_data, "r")
    session.send(h.image(image))

    # 例：发送图片消息的方式
    # image = Image.open(return_data, "r")
    # session.send(h.image(image))

    # 例：发送文字消息的方式
    # session.send(return_data)
