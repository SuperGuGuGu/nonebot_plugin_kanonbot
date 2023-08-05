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
            "knapi": {
                "url": "http://cdn.kanon.ink"}}
        save_config()
        nonebot.logger.info("未存在KanonBot配置文件，正在创建")
    config = toml.load(path)

    # 下面这堆代码我都快看不懂了，有空重构一下
    # 用“-”来分段。
    if config_name == "kanon_api-url":
        if "kanon_api" in list(config):
            if "url" not in list(config["kanon_api"]):
                config["kanon_api"]["url"] = "http://cdn.kanon.ink"
                save_config()
        else:
            config["kanon_api"] = {"url": "http://cdn.kanon.ink"}
            save_config()
        return config["kanon_api"]["url"]
    elif config_name == "kanon_api-state":
        if "kanon_api" in list(config):
            if "url" not in list(config["kanon_api"]):
                config["kanon_api"]["state"] = True
                save_config()
        else:
            config["kanon_api"] = {"state": True}
            save_config()
        return config["kanon_api"]["state"]
    elif config_name == "kanon_api-unity_key":
        if "kanon_api" in list(config):
            if "unity_key" not in list(config["kanon_api"]):
                config["kanon_api"]["unity_key"] = "none"
                save_config()
        else:
            config["kanon_api"] = {"unity_key": "none"}
            save_config()
        return config["kanon_api"]["unity_key"]
    elif config_name == "emoji-state":
        if "emoji" in list(config):
            if "state" not in list(config["emoji"]):
                config["emoji"]["state"] = True
                save_config()
        else:
            config["emoji"] = {"state": True}
            save_config()
        return config["emoji"]["state"]
    elif config_name == "emoji-mode":
        if "emoji" in list(config):
            if "mode" not in list(config["emoji"]):
                config["emoji"]["mode"] = "file"
                save_config()
        else:
            config["emoji"] = {"mode": "file"}
            save_config()
        return config["emoji"]["mode"]
    elif config_name == "botswift-state":
        if "botswift" in list(config):
            if "state" not in list(config["botswift"]):
                config["botswift"]["state"] = False
                save_config()
        else:
            config["botswift"] = {"state": False}
            save_config()
        return config["botswift"]["state"]
    elif config_name == "botswift-ignore_list":
        if "botswift" in list(config):
            if "ignore_list" not in list(config["botswift"]):
                config["botswift"]["ignore_list"] = []
                save_config()
        else:
            config["botswift"] = {"ignore_list": []}
            save_config()
        return config["botswift"]["ignore_list"]
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
    return False


def _config_list():
    configs = {
        "welcome": {"state": True, "message": "入群欢迎（正在维护）", "group": "群聊功能", "name": "入群欢迎"},
        "chickin": {"state": True, "message": "", "group": "", "name": ""},
        "jiehun": {"state": True, "message": "", "group": "", "name": ""},
        "qinqin": {"state": True, "message": "", "group": "", "name": ""},
        "tietie": {"state": True, "message": "", "group": "", "name": ""},
        "daibu": {"state": True, "message": "", "group": "", "name": ""},
        "ti": {"state": True, "message": "", "group": "", "name": ""},
        "yaoyao": {"state": True, "message": "", "group": "", "name": ""},
        "wlp": {"state": True, "message": "", "group": "", "name": ""},
        "ji": {"state": True, "message": "", "group": "", "name": ""},
        "pa": {"state": True, "message": "", "group": "", "name": ""},
        "yizhi": {"state": True, "message": "", "group": "", "name": ""},
        "zhanbu": {"state": True, "message": "", "group": "", "name": ""},
        "keai": {"state": True, "message": "", "group": "", "name": ""},
        "wolaopo": {"state": True, "message": "", "group": "", "name": ""},
        "zhi": {"state": True, "message": "", "group": "", "name": ""},
        "quanquan": {"state": True, "message": "", "group": "", "name": ""},
        "?": {"state": True, "message": "", "group": "", "name": ""}
    }
    return configs


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


def _zhanbu_datas():
    datas = {
        "1": {"title": "", "message": ""}
    }
    return datas



