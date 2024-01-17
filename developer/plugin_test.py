import asyncio
import sys
import time
from nonebot import logger
sys.path.append("..")
from plugins.plugin_kanonbot_for_Kook.plugins import plugin_jellyfish_box

# #########################
# 无需运行bot就能测试插件的小工具
# 方便进行插件调试
# 运行此工具会在此文件所在文件夹生成一份新配置文件夹
# #########################


async def run():
    data = await plugin_jellyfish_box(
        user_id="KnTest",
        user_name="KnTest",
        channel_id="test_channel",
        msg="水母箱",
        time_now=int(time.time()),
    )
    logger.info(data)
    return data

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(run())
