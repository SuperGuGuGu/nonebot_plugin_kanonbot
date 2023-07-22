#coding=utf-8
import toml
import nonebot
import os

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


def kn_config(config_name):
    """
    获取配置。
    获取"kanon_api-url"时，相当于获取"config["kanon_api"]["url"]"的配置项
    :param config_name: 获取的配置名称
    :return: 配置内容
    """
    path = basepath + "kanon_config.toml"

    def save_config():
        with open(path, 'w') as config_file:
            toml.dump(config, config_file)

    if not os.path.exists(path):
        config = {
            "Kanon_Config": {
                "KanonBot": "https://github.com/SuperGuGuGu/nonebot_plugin_kanonbot"},
            "kanon_api": {
                "url": "http://cdn.kanon.ink"}}
        save_config()
        nonebot.logger.info("未存在KanonBot配置文件，正在创建")
    config = toml.load(path)

    if config_name == "kanon_api-url":
        if "kanon_api" in list(config):
            if "url" in list(config["kanon_api"]):
                return config["kanon_api"]["url"]
            else:
                config["kanon_api"] = {"url": "http://cdn.kanon.ink"}
                save_config()
        else:
            config["kanon_api"]["url"] = "http://cdn.kanon.ink"
            save_config()
        return config["kanon_api"]["url"]
    elif config_name == "kanon_api-state":
        if "kanon_api" in list(config):
            if "url" in list(config["kanon_api"]):
                return config["kanon_api"]["state"]
            else:
                config["kanon_api"] = {"state": True}
                save_config()
        else:
            config["kanon_api"]["state"] = True
            save_config()
        return config["kanon_api"]["state"]
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    elif config_name == "":
        return
    return True


def command_list():
    commands = {
        "精准": {
            "help": "config查询",
            "使用说明": "config查询",
            "查询功能": "config查询",
            "菜单": "config查询",
            "关闭": "config关闭",
            "开启": "config开启",
            "一直": "yizhi",
            "举牌": "jupai",
            "买薯条": "chickin",
            "占卜": "zhanbu",
            "吃薯条": "minpoints",
            "合成": "emoji",
            "啊打": "ti",
            "喜报": "xibao",
            "寄": "ji",
            "急": "ji2",
            "我是谁": "woshishei",
            "我老婆": "wolaopo",
            "欢迎": "welcome",
            "爬": "pa",
            "签到": "chickin",
            "结婚": "jiehun",
            "结婚证": "jiehunzheng",
            "👊": "quanquan",
            "wlp是谁": "wlp",
            "来点wlp": "wlp",
            "多来点wlp": "wlp",
            "成员名单": "wlp",
            "悲报": "beibao",
            "😡👊": "quanquan",
            "wlp": "wolaopo",
            "今日老婆": "jinrilaopo",
            "jrlp": "jinrilaopo",
            "cck": "caicaikan",
            "bzd": "caicaikan",
            "猜猜看": "caicaikan",
            "问": "addreply",
            "给你一拳": "quanquan",
            "拳拳": "quanquan",
            "指": "zhi",
            "🫵": "zhi",
            "踢": "ti",
            "打拳": "quanquan",
            "炸飞机": "blowplane",
            "结束炸飞机": "blowplane",
        },
        "模糊": {
            "亲亲": "qinqin",
            "可爱": "keai",
            "咬咬": "yaoyao",
            "摸摸": "momo",
            "贴贴": "tietie",
            "逮捕": "daibu"
        },
        "开头": {
            "来点": "wlp",
            "多来点": "wlp",
            "wlp是": "wlp",
            "新lp是": "wlp",
            "是": "caicaikan",
            "炸": "blowplane",
            "☝️": "shangzhi",
            "☝🏻": "shangzhi",
            "☝🏼": "shangzhi",
            "☝🏽": "shangzhi",
            "☝🏾": "shangzhi",
            "👆🏻": "shangzhi",
            "👆🏼": "shangzhi",
            "👆🏽": "shangzhi",
            "👆🏾": "shangzhi",
            "👆🏿": "shangzhi",
            "☝🏿": "shangzhi",
            "👆": "shangzhi"
        },
        "结尾": {
        },
        "精准2": {
            "不知道": "caicaikan"
        },
    }
    return commands
