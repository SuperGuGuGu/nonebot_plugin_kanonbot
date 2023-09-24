# coding=utf-8
import toml
import nonebot
import os

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

    # 下面这堆代码自己都快看不懂了，有空再重构一下
    # 用“-”来分段
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
    """
    获取功能列表，可以对应地找命令名对应的功能。
    commandname: {默认状态, "'帮助'命令中显示的内容", 该功能的群组, 用于设置功能开关所识别的名字}
    """
    configs = {
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
        "jinrilaopo": {"state": True, "message": "今日老婆", "group": "群聊功能", "name": "今日老婆"},
        "caicaikan": {"state": True, "message": "猜猜看", "group": "小游戏", "name": "猜猜看"},
        "blowplane": {"state": False, "message": "炸飞机", "group": "小游戏", "name": "炸飞机"}
    }
    return configs


def command_list():
    """
    获取关键词，进行匹配对应的功能
    匹配方式: {关键字: commandname}
    精准2也是精准，只是需要在匹配不到其他功能再尝试匹配
    """
    commands = {
        "精准": {
            "help": "config查询",
            "使用说明": "config查询",
            "帮助": "config查询",
            "查询功能": "config查询",
            "菜单": "config查询",
            "关闭": "config关闭",
            "开启": "config开启",
            "占卜": "群聊功能-zhanbu",
            "合成": "群聊功能-emoji",
            "买薯条": "群聊功能-chickin",
            "吃薯条": "群聊功能-chickin",
            "签到": "群聊功能-chickin",
            "今日老婆": "群聊功能-jinrilaopo",
            "jrlp": "群聊功能-jinrilaopo",
            "wlp是谁": "图库功能-wlp",
            "来点wlp": "图库功能-wlp",
            "多来点wlp": "图库功能-wlp",
            "成员名单": "图库功能-wlp",
            "一直": "表情功能-yizhi",
            "啊打": "表情功能-ti",
            "喜报": "表情功能-xibao",
            "寄": "表情功能-ji",
            "急": "表情功能-ji2",
            "我是谁": "表情功能-woshishei",
            "我老婆": "表情功能-wolaopo",
            "爬": "表情功能-pa",
            "结婚": "表情功能-jiehun",
            "结婚证": "表情功能-jiehunzheng",
            "👊": "表情功能-quanquan",
            "给你一拳": "表情功能-quanquan",
            "拳拳": "表情功能-quanquan",
            "指": "表情功能-zhi",
            "🫵": "表情功能-zhi",
            "踢": "表情功能-ti",
            "打拳": "表情功能-quanquan",
            "悲报": "表情功能-beibao",
            "wlp": "表情功能-wolaopo",
            "😡👊": "表情功能-quanquan",
            "cck": "小游戏-caicaikan",
            "bzd": "小游戏-caicaikan",
            "猜猜看": "小游戏-caicaikan",
            "炸飞机": "小游戏-blowplane",
            "结束炸飞机": "小游戏-blowplane",
        },
        "开头": {
            "来点": "图库功能-wlp",
            "多来点": "图库功能-wlp",
            "wlp是": "图库功能-wlp",
            "新lp是": "图库功能-wlp",
            "是": "小游戏-caicaikan",
            "炸": "小游戏-blowplane",
        },
        "结尾": {
        },
        "模糊": {
            "亲亲": "表情功能-qinqin",
            "可爱": "表情功能-keai",
            "咬咬": "表情功能-yaoyao",
            "摸摸": "表情功能-momo",
            "贴贴": "表情功能-tietie",
            "逮捕": "表情功能-daibu"
        },
        "精准2": {
            "不知道": "小游戏-caicaikan"
        },
    }
    return commands


def _zhanbu_datas():
    datas = {"good": {"1": {"name": "愚者正位", "message": "新的开始、冒险、自信、乐观、好的时机"},
                      "2": {"name": "魔术师正位", "message": "创造力、主见、激情、发展潜力"},
                      "3": {"name": "女祭司正位", "message": "潜意识、洞察力、知性、研究精神"},
                      "4": {"name": "女皇正位", "message": "母性、女性特质、生命力、接纳"},
                      "5": {"name": "皇帝正位", "message": "控制、意志、领导力、权力、影响力"},
                      "6": {"name": "教皇正位", "message": "值得信赖的、顺从、遵守规则"},
                      "7": {"name": "恋人正位", "message": "爱、肉体的连接、新的关系、美好时光、互相支持"},
                      "8": {"name": "战车正位", "message": "高效率、把握先机、坚韧、决心、力量、克服障碍"},
                      "9": {"name": "力量正位", "message": "勇气、决断、克服阻碍、胆识过人"},
                      "10": {"name": "隐士正位", "message": "内省、审视自我、探索内心、平静"},
                      "11": {"name": "命运之轮正位", "message": "把握时机、新的机会、幸运降临、即将迎来改变"},
                      "12": {"name": "正义正位", "message": "公平、正直、诚实、正义、表里如一"},
                      "13": {"name": "倒吊人正位", "message": "进退两难、接受考验、因祸得福、舍弃行动追求顿悟"},
                      "14": {"name": "死神正位", "message": "失去、舍弃、离别、死亡、新生事物的来临"},
                      "15": {"name": "节制正位", "message": "平衡、和谐、治愈、节制"},
                      "16": {"name": "恶魔正位", "message": "负面影响、贪婪的欲望、物质主义、固执己见"},
                      "17": {"name": "高塔正位", "message": "急剧的转变、突然的动荡、毁灭后的重生、政权更迭"},
                      "18": {"name": "星星正位", "message": "希望、前途光明、曙光出现"},
                      "19": {"name": "月亮正位", "message": "虚幻、不安与动摇、迷惘、欺骗"},
                      "20": {"name": "太阳正位", "message": "活力充沛、生机、远景明朗、积极"},
                      "21": {"name": "审判正位", "message": "命运好转、复活的喜悦、恢复健康"},
                      "22": {"name": "世界正位", "message": "愿望达成、获得成功、到达目的地"},
                      "23": {"name": "宝剑ACE正位", "message": "有进取心和攻击性、敏锐、理性、成功的开始"},
                      "24": {"name": "宝剑2正位", "message": "想法的对立、选择的时机、意见不合且暗流汹涌"},
                      "25": {"name": "宝剑3正位", "message": "感情受到伤害、生活中出现麻烦、自怜自哀"},
                      "26": {"name": "宝剑4正位", "message": "养精蓄锐、以退为进、放缓行动、留意总结"},
                      "27": {"name": "宝剑5正位", "message": "矛盾冲突、不择手段伤害对方、赢得比赛却失去关系"},
                      "28": {"name": "宝剑6正位", "message": "伤口迟迟没能痊愈、现在没有很好的对策、未来存在更多的艰难"},
                      "29": {"name": "宝剑7正位", "message": "疏忽大意、有隐藏很深的敌人、泄密、非常手段或小伎俩无法久用"},
                      "30": {"name": "宝剑8正位", "message": "孤立无助、陷入艰难处境、受困于想法导致行动受阻"},
                      "31": {"name": "宝剑9正位", "message": "精神上的恐惧、害怕、焦虑、前路不顺的预兆"},
                      "32": {"name": "宝剑10正位", "message": "进展严重受阻、无路可走、面临绝境、重新归零的机会"},
                      "33": {"name": "宝剑国王正位", "message": "公正、权威、领导力、冷静"},
                      "34": {"name": "宝剑皇后正位", "message": "理性、思考敏捷、有距离感、公正不阿"},
                      "35": {"name": "宝剑骑士正位", "message": "勇往直前的行动力、充满激情"},
                      "36": {"name": "宝剑侍从正位", "message": "思维发散、洞察力、谨慎的判断"},
                      "37": {"name": "权杖ACE正位", "message": "新的开端、新的机遇、燃烧的激情、创造力"},
                      "38": {"name": "权杖2正位", "message": "高瞻远瞩、规划未来、在习惯与希望间做选择"},
                      "39": {"name": "权杖3正位", "message": "探索的好时机、身心灵的契合、领导能力、主导地位"},
                      "40": {"name": "权杖4正位", "message": "和平繁荣、关系稳固、学业或事业发展稳定"},
                      "41": {"name": "权杖5正位", "message": "竞争、冲突、内心的矛盾、缺乏共识"},
                      "42": {"name": "权杖6正位", "message": "获得胜利、成功得到回报、进展顺利、有望水到渠成"},
                      "43": {"name": "权杖7正位", "message": "坚定信念、态度坚定、内芯的权衡与决断、相信自己的观点与能力"},
                      "44": {"name": "权杖8正位", "message": "目标明确、一鼓作气、进展神速、趁热打铁、旅行"},
                      "45": {"name": "权杖9正位", "message": "做好准备以应对困难、自我防御、蓄势待发、力量的对立"},
                      "46": {"name": "权杖10正位", "message": "责任感、内芯的热忱、过重的负担、过度劳累"},
                      "47": {"name": "权杖国王正位", "message": "行动力强、态度明确、运筹帷幄、领袖魅力"},
                      "48": {"name": "权杖皇后正位", "message": "刚柔并济、热情而温和、乐观而活泼"},
                      "49": {"name": "权杖骑士正位", "message": "行动力、精力充沛、新的旅程、对现状不满足的改变"},
                      "50": {"name": "权杖侍从正位", "message": "新计划的开始、尝试新事物、好消息传来"},
                      "51": {"name": "圣杯ACE正位", "message": "新恋情或新友情、精神愉悦、心灵满足"},
                      "52": {"name": "圣杯2正位", "message": "和谐对等的关系、情侣间的相互喜爱、合作顺利"},
                      "53": {"name": "圣杯3正位", "message": "达成合作、努力取得成果"},
                      "54": {"name": "圣杯4正位", "message": "身心俱疲、缺乏动力、对事物缺乏兴趣、情绪低潮"},
                      "55": {"name": "圣杯5正位", "message": "过度注意失去的事物、自责、自我怀疑、因孤傲而拒绝外界帮助"},
                      "56": {"name": "圣杯6正位", "message": "思乡、美好的回忆、纯真的情感、简单的快乐、安全感"},
                      "57": {"name": "圣杯7正位", "message": "不切实际的幻想、不踏实的人际关系、虚幻的情感、生活混乱"},
                      "58": {"name": "圣杯8正位", "message": "离开熟悉的人事物、不沉醉于目前的成果、经考虑后的行动"},
                      "59": {"name": "圣杯9正位", "message": "愿望极有可能实现、满足现状、物质与精神富足"},
                      "60": {"name": "圣杯10正位", "message": "团队和谐、人际关系融洽、家庭和睦"},
                      "61": {"name": "圣杯国王正位", "message": "创造力、决策力、某方面的专家、有条件的分享或交换"},
                      "62": {"name": "圣杯皇后正位", "message": "感情丰富而细腻、重视直觉、感性的思考"},
                      "63": {"name": "圣杯骑士正位", "message": "在等待与行动之间做出决定、新的机会即将到来"},
                      "64": {"name": "圣杯侍从正位", "message": "情感的表达与奉献、积极的消息即将传来、情感的追求但不成熟"},
                      "65": {"name": "星币ACE正位", "message": "新的机遇、顺利发展、物质回报"},
                      "66": {"name": "星币2正位", "message": "收支平衡、财富的流通、生活的波动与平衡"},
                      "67": {"name": "星币3正位", "message": "团队合作、沟通顺畅、工作熟练、关系稳定"},
                      "68": {"name": "星币4正位", "message": "安于现状、吝啬、守财奴、财富停滞、精神匮乏"},
                      "69": {"name": "星币5正位", "message": "经济危机、同甘共苦、艰难时刻"},
                      "70": {"name": "星币6正位", "message": "慷慨、给予、礼尚往来、财务稳定且乐观"},
                      "71": {"name": "星币7正位", "message": "等待时机成熟、取得阶段性成果、思考计划"},
                      "72": {"name": "星币8正位", "message": "工作专注、技能娴熟、进取心、做事有条理"},
                      "73": {"name": "星币9正位", "message": "事业收获、持续为自己创造有利条件、懂得理财储蓄"},
                      "74": {"name": "星币10正位", "message": "团队和谐、成功的事业伙伴、家族和谐"},
                      "75": {"name": "星币国王正位", "message": "成功人士、追求物质、善于经营、值得信赖、成熟务实"},
                      "76": {"name": "星币皇后正位", "message": "成熟、繁荣、值得信赖、温暖、安宁"},
                      "77": {"name": "星币骑士正位", "message": "讲究效率、责任感赖、稳重、有计划"},
                      "78": {"name": "星币侍从正位", "message": "善于思考和学习、求知欲旺盛、与知识或者研究工作有关的好消息"}},
             "bad": {"79": {"name": "愚者逆位", "message": "时机不对、鲁莽、轻信、承担风险"},
                     "80": {"name": "魔术师逆位", "message": "缺乏创造力、优柔寡断、才能平庸、计划不周"},
                     "81": {"name": "女祭司逆位", "message": "自我封闭、内向、神经质、缺乏理性"},
                     "82": {"name": "女皇逆位", "message": "生育问题、不安全感、敏感、困扰于细枝末节"},
                     "83": {"name": "皇帝逆位", "message": "混乱、固执、暴政、管理不善、不务实"},
                     "84": {"name": "教皇逆位", "message": "失去信赖、固步自封、质疑权威、恶意的规劝"},
                     "85": {"name": "恋人逆位", "message": "纵欲过度、不忠、违背诺言、情感的抉择"},
                     "86": {"name": "战车逆位", "message": "失控、挫折、诉诸暴力、冲动"},
                     "87": {"name": "力量逆位", "message": "恐惧、精力不足、自我怀疑、懦弱"},
                     "88": {"name": "隐士逆位", "message": "孤独、孤立、过分慎重、逃避"},
                     "89": {"name": "命运之轮逆位", "message": "厄运、时机未到、计划泡汤"},
                     "90": {"name": "正义逆位", "message": "失衡、偏见、不诚实、表里不一"},
                     "91": {"name": "倒吊人逆位", "message": "无畏的牺牲、利己主义、内心抗拒、缺乏远见"},
                     "92": {"name": "死神逆位", "message": "起死回生、回心转意、逃避现实"},
                     "93": {"name": "节制逆位", "message": "失衡、失谐、沉溺愉悦、过度放纵"},
                     "94": {"name": "恶魔逆位", "message": "逃离束缚、拒绝诱惑、治愈病痛、直面现实"},
                     "95": {"name": "高塔逆位", "message": "悬崖勒马、害怕转变、发生内讧、风暴前的寂静"},
                     "96": {"name": "星星逆位", "message": "好高骛远、异想天开、事与愿违、失去目标"},
                     "97": {"name": "月亮逆位", "message": "状况逐渐好转、疑虑渐消、排解恐惧"},
                     "98": {"name": "太阳逆位", "message": "意志消沉、情绪低落、无助、消极"},
                     "99": {"name": "审判逆位", "message": "一蹶不振、尚未开始便已结束、自我怀疑、不予理睬"},
                     "100": {"name": "世界逆位", "message": "无法投入、不安现状、半途而废、盲目接受"},
                     "101": {"name": "宝剑ACE逆位", "message": "易引起争端、逞强而招致灾难、偏激专横、不公正的想法"},
                     "102": {"name": "宝剑2逆位", "message": "做出选择但流言与欺诈会浮出水面、犹豫不决导致错失机会"},
                     "103": {"name": "宝剑3逆位", "message": "心理封闭、情绪不安、逃避、伤害周边的人"},
                     "104": {"name": "宝剑4逆位", "message": "即刻行动、投入生活、未充分准备却慌忙应对"},
                     "105": {"name": "宝剑5逆位", "message": "找到应对方法、冲突有解决的可能性、双方愿意放下武器"},
                     "106": {"name": "宝剑6逆位", "message": "深陷于困难、鲁莽地解决却忽视背后更大的问题、需要其他人的帮助或救援"},
                     "107": {"name": "宝剑7逆位", "message": "意想不到的好运、计划不周全、掩耳盗铃"},
                     "108": {"name": "宝剑8逆位", "message": "摆脱束缚、脱离危机、重新起步"},
                     "109": {"name": "宝剑9逆位", "message": "事情出现转机、逐渐摆脱困境、沉溺于过去、正视现实"},
                     "110": {"name": "宝剑10逆位", "message": "绝处逢生、东山再起的希望、物极必反"},
                     "111": {"name": "宝剑国王逆位", "message": "思想偏颇、强加观念、极端、不择手段"},
                     "112": {"name": "宝剑皇后逆位", "message": "固执、想法偏激、高傲、盛气凌人"},
                     "113": {"name": "宝剑骑士逆位", "message": "计划不周、天马行空、缺乏耐心、做事轻率、自负"},
                     "114": {"name": "宝剑侍从逆位", "message": "短见、做事虎头蛇尾、对信息不加以过滤分析"},
                     "115": {"name": "权杖ACE逆位", "message": "新行动失败的可能性比较大、开端不佳、意志力薄弱"},
                     "116": {"name": "权杖2逆位", "message": "犹豫不决、行动受阻、花费太多时间在选择上"},
                     "117": {"name": "权杖3逆位", "message": "合作不顺、欠缺领导能力、团队不和谐"},
                     "118": {"name": "权杖4逆位", "message": "局势失衡、稳固的基础被打破、人际关系不佳、收成不佳"},
                     "119": {"name": "权杖5逆位", "message": "不公平的竞争、达成共识"},
                     "120": {"name": "权杖6逆位", "message": "短暂的成功、骄傲自满、失去自信"},
                     "121": {"name": "权杖7逆位", "message": "对自己的能力产生怀疑、缺乏自信与动力、缺乏意志力"},
                     "122": {"name": "权杖8逆位", "message": "方向错误、行动不一致、急躁冲动、计划延误"},
                     "123": {"name": "权杖9逆位", "message": "遭遇逆境、失去自信、士气低落"},
                     "124": {"name": "权杖10逆位", "message": "难以承受的压力、高估自身的能力、调整自己的步调、逃避责任"},
                     "125": {"name": "权杖国王逆位", "message": "独断专行、严苛、态度傲慢"},
                     "126": {"name": "权杖皇后逆位", "message": "情绪化、信心不足、热情消退、孤独"},
                     "127": {"name": "权杖骑士逆位", "message": "有勇无谋、鲁莽、行动延迟、计划不周、急躁"},
                     "128": {"name": "权杖侍从逆位", "message": "三分钟热度、规划太久导致进展不顺、坏消息传来"},
                     "129": {"name": "圣杯ACE逆位", "message": "情感缺失、缺乏交流、虚情假意"},
                     "130": {"name": "圣杯2逆位", "message": "两性关系趋于极端、情感的割裂、双方不平等、冲突"},
                     "131": {"name": "圣杯3逆位", "message": "乐极生悲、无法达成共识、团队不和"},
                     "132": {"name": "圣杯4逆位", "message": "新的人际关系、有所行动、脱离低潮期"},
                     "133": {"name": "圣杯5逆位", "message": "走出悲伤、破釜沉舟、东山再起"},
                     "134": {"name": "圣杯6逆位", "message": "沉溺于过去、不美好的回忆、不甘受束缚"},
                     "135": {"name": "圣杯7逆位", "message": "看清现实、对物质的不满足、做出明智的选择"},
                     "136": {"name": "圣杯8逆位", "message": "犹豫不决、失去未来的规划、维持现状"},
                     "137": {"name": "圣杯9逆位", "message": "物质受损失、不懂节制、寻求更高层次的快乐"},
                     "138": {"name": "圣杯10逆位", "message": "团队不和、人际关系不和、冲突"},
                     "139": {"name": "圣杯国王逆位", "message": "表里不一、行为另有所图、对自我创造力的不信任"},
                     "140": {"name": "圣杯皇后逆位", "message": "过度情绪化、用情不专、心灵的孤立"},
                     "141": {"name": "圣杯骑士逆位", "message": "用情不专、消极的等待、对于情感的行动错误"},
                     "142": {"name": "圣杯侍从逆位", "message": "情感的追求但错误、感情暧昧、过度执着于情感或问题"},
                     "143": {"name": "星币ACE逆位", "message": "金钱上的损失、发展不顺、物质丰富但精神虚空"},
                     "144": {"name": "星币2逆位", "message": "用钱过度、难以维持平衡、面临物质的损失"},
                     "145": {"name": "星币3逆位", "message": "分工不明确、人际关系不和、专业技能不足"},
                     "146": {"name": "星币4逆位", "message": "入不敷出、奢侈无度、挥霍"},
                     "147": {"name": "星币5逆位", "message": "居住问题、生活混乱、劳燕分飞"},
                     "148": {"name": "星币6逆位", "message": "自私、暗藏心机、负债或在情义上亏欠于人"},
                     "149": {"name": "星币7逆位", "message": "事倍功半、投资失利、踟蹰不决"},
                     "150": {"name": "星币8逆位", "message": "精力分散、工作乏味、工作产出不佳"},
                     "151": {"name": "星币9逆位", "message": "失去财富、舍弃金钱追求生活、管理能力欠缺"},
                     "152": {"name": "星币10逆位", "message": "团队不和、投资合伙暂缓、家庭陷入不和"},
                     "153": {"name": "星币国王逆位", "message": "缺乏经济头脑、缺乏信任、管理不善、失去信赖"},
                     "154": {"name": "星币皇后逆位", "message": "爱慕虚荣、生活浮华、态度恶劣"},
                     "155": {"name": "星币骑士逆位", "message": "懈怠、思想保守、发展停滞不前"},
                     "156": {"name": "星币侍从逆位", "message": "知识贫乏、自我认知不足、金钱上面临损失、视野狭窄"}}}
    return datas
