# coding=utf-8
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
            if "state" not in list(config["kanon_api"]):
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
        "chickin": {"state": True, "message": "签到 (发送：签到)", "group": "群聊功能", "name": "签到"},
        "jiehun": {"state": True, "message": "结婚 (结婚@群友)", "group": "表情功能", "name": "结婚"},
        "qinqin": {"state": True, "message": "亲亲 (亲亲@群友)", "group": "表情功能", "name": "亲亲"},
        "tietie": {"state": True, "message": "贴贴 (贴贴@群友)", "group": "表情功能", "name": "贴贴"},
        "daibu": {"state": True, "message": "逮捕 (逮捕@群友)", "group": "表情功能", "name": "逮捕"},
        "ti": {"state": True, "message": "啊打 (啊打@群友)", "group": "表情功能", "name": "啊打"},
        "yaoyao": {"state": True, "message": "咬咬 (咬咬@群友)", "group": "表情功能", "name": "咬咬"},
        "wlp": {"state": True, "message": "来点wlp", "group": "图库功能", "name": "图库"},
        "ji": {"state": True, "message": "寄图 (发送：寄)", "group": "表情功能", "name": "寄图"},
        "pa": {"state": True, "message": "爬图 (发送：爬)", "group": "表情功能", "name": "爬图"},
        "yizhi": {"state": True, "message": "一直 (发送：一直)", "group": "表情功能", "name": "一直"},
        "zhanbu": {"state": True, "message": "占卜 (发送：占卜)", "group": "群聊功能", "name": "占卜"},
        "keai": {"state": True, "message": "可爱 (可爱@群友)", "group": "表情功能", "name": "可爱"},
        "wolaopo": {"state": True, "message": "我老婆 (我老婆@群友)", "group": "表情功能", "name": "我老婆"},
        "zhi": {"state": True, "message": "指", "group": "表情功能", "name": "指"},
        "quanquan": {"state": True, "message": "拳拳", "group": "表情功能", "name": "拳拳"},
        "jiehunzheng": {"state": True, "message": "结婚证 (结婚证@群友)", "group": "表情功能", "name": "结婚证"},
        "emoji": {"state": True, "message": "emoji", "group": "群聊功能", "name": "emoji"},
        "ji2": {"state": True, "message": "急", "group": "表情功能", "name": "急"},
        "momo": {"state": True, "message": "摸摸 (摸摸@群友)", "group": "表情功能", "name": "摸摸"},
        "commandcd": {"state": True, "message": "指令冷却", "group": "群聊功能", "name": "指令冷却"},
        "xibao": {"state": True, "message": "喜报 (喜报 内容)", "group": "表情功能", "name": "喜报"},
        "autorply": {"state": True, "message": "词条回复", "group": "群聊功能", "name": "词条回复"},
        "jinrilaopo": {"state": True, "message": "今日老婆", "group": "群聊功能", "name": "今日老婆"},
        "caicaikan": {"state": True, "message": "猜猜看", "group": "小游戏", "name": "猜猜看"},
        "blowplane": {"state": False, "message": "炸飞机", "group": "小游戏", "name": "炸飞机"}
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



