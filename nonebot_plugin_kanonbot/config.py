# coding=utf-8
import json
import time
from nonebot import logger
from .tools import get_file_path, _config, kn_cache

basepath = _config["basepath"]
adminqq = _config["superusers"]


def _config_list(qq: bool = False):
    """
    获取功能列表，可以对应地找命令名对应的功能。
    commandname: {默认状态, "'帮助'命令中显示的内容", 该功能的群组, 用于设置功能开关所识别的名字}
    """
    configs = {
        "签到": {
            "state": True, "swift_by_admin": False,
            "message": "签到 (发送：签到)", "group": "群聊功能", "name": "签到"},
        "水母箱": {
            "state": True, "swift_by_admin": False,
            "message": "水母箱功能", "group": "群聊功能", "name": "水母箱"},
        "水母探险": {
            "state": True, "swift_by_admin": False,
            "message": "水母探险（beta）", "group": "群聊功能", "name": "水母探险"},
        "emoji": {
            "state": True, "swift_by_admin": False,
            "message": "emoji合成", "group": "群聊功能", "name": "emoji"},
        "喜报": {
            "state": False, "swift_by_admin": True,
            "message": "喜报 (喜报 内容)", "group": "表情功能", "name": "喜报"},
        "一直": {
            "state": True, "swift_by_admin": False,
            "message": "一直 (发送：一直)", "group": "表情功能", "name": "一直"},
        "摸摸": {
            "state": True, "swift_by_admin": False,
            "message": "摸摸 (摸摸@群友)", "group": "表情功能", "name": "摸摸"},
        "可爱": {
            "state": True, "swift_by_admin": False,
            "message": "可爱 (可爱@群友)", "group": "表情功能", "name": "可爱"},
        "逮捕": {
            "state": True, "swift_by_admin": False,
            "message": "逮捕 (逮捕@群友)", "group": "表情功能", "name": "逮捕"},
        "结婚": {
            "state": True, "swift_by_admin": False,
            "message": "结婚 (结婚@群友)", "group": "表情功能", "name": "结婚"},
        "寄": {
            "state": True, "swift_by_admin": False,
            "message": "寄图 (发送：寄)", "group": "表情功能", "name": "寄"},
        "急": {
            "state": True, "swift_by_admin": False,
            "message": "急图 (发送：急)", "group": "表情功能", "name": "急"},
        "爬": {
            "state": True, "swift_by_admin": False,
            "message": "爬图 (发送：爬)", "group": "表情功能", "name": "爬"},
        "我老婆": {
            "state": True, "swift_by_admin": False,
            "message": "我老婆 (我老婆@群友)", "group": "表情功能", "name": "我老婆"},
        "猜猜看": {
            "state": True, "swift_by_admin": False,
            "message": "猜猜看", "group": "小游戏", "name": "猜猜看"},
        "炸飞机": {
            "state": True, "swift_by_admin": False,
            "message": "炸飞机", "group": "小游戏", "name": "炸飞机"},
        "找不同": {
            "state": True, "swift_by_admin": False,
            "message": "找不同", "group": "小游戏", "name": "找不同"},
        "commandcd": {
            "state": True, "swift_by_admin": True,
            "message": "指令冷却", "group": "群聊功能", "name": "指令冷却"},
        "今日老婆": {
            "state": True, "swift_by_admin": False,
            "message": "今日老婆 (发送：今日老婆)", "group": "群聊功能", "name": "今日老婆"},
        "图库": {
            "state": False, "swift_by_admin": True,
            "message": "来点wlp", "group": "群聊功能", "name": "图库"},
        "问好": {
            "state": True, "swift_by_admin": False,
            "message": "测试功能w", "group": "群聊功能", "name": "问好"},
    }
    configs_qq = {
        "签到": {"state": True, "swift_by_admin": False, "message": "签到", "group": "群聊功能", "name": "签到"},
        "水母箱": {"state": True, "swift_by_admin": False, "message": "水母箱", "group": "群聊功能", "name": "水母箱"},
        "emoji": {"state": True, "swift_by_admin": False, "message": "合成emoji", "group": "群聊功能", "name": "emoji"},
        "猜猜看": {"state": True, "swift_by_admin": False, "message": "猜猜看", "group": "小游戏", "name": "猜猜看"},
        "炸飞机": {"state": True, "swift_by_admin": False, "message": "炸飞机", "group": "小游戏", "name": "炸飞机"},
        "今日老婆": {"state": True, "swift_by_admin": False, "message": "今日老婆", "group": "群聊功能", "name": "今日老婆"},
        "一直": {"state": True, "swift_by_admin": False, "message": "一直 (发送：一直)", "group": "表情功能", "name": "一直"},
        "摸摸": {"state": True, "swift_by_admin": False, "message": "摸摸 (摸摸@群友)", "group": "表情功能", "name": "摸摸"},
        "可爱": {"state": True, "swift_by_admin": False, "message": "可爱 (可爱@群友)", "group": "表情功能", "name": "可爱"},
        "逮捕": {"state": True, "swift_by_admin": False, "message": "逮捕 (逮捕@群友)", "group": "表情功能", "name": "逮捕"},
        "结婚": {"state": True, "swift_by_admin": False, "message": "结婚 (结婚@群友)", "group": "表情功能", "name": "结婚"},
        "寄": {"state": True, "swift_by_admin": False, "message": "寄图 (发送：寄)", "group": "表情功能", "name": "寄"},
        "急": {"state": True, "swift_by_admin": False, "message": "急图 (发送：急)", "group": "表情功能", "name": "急"},
        "爬": {"state": True, "swift_by_admin": False, "message": "爬图 (发送：爬)", "group": "表情功能", "name": "爬"},
    }
    configs_none = {
        "塔罗牌": {"state": False, "message": "t", "group": "群聊功能", "name": "t"},
        "洗了": {"state": False, "message": "洗了 (洗@群友)", "group": "表情功能", "name": "洗了"},
        "亲亲": {"state": False, "message": "亲亲 (亲亲@群友)", "group": "表情功能", "name": "亲亲"},
        "贴贴": {"state": False, "message": "贴贴 (贴贴@群友)", "group": "表情功能", "name": "贴贴"},
        "踢": {"state": False, "message": "啊打 (啊打@群友)", "group": "表情功能", "name": "踢"},
        "咬咬": {"state": False, "message": "咬咬 (咬咬@群友)", "group": "表情功能", "name": "咬咬"},
        "指": {"state": False, "message": "指", "group": "表情功能", "name": "指"},
        "拳拳": {"state": False, "message": "拳拳", "group": "表情功能", "name": "拳拳"},
        "结婚证": {"state": False, "message": "结婚证 (结婚证@群友)", "group": "表情功能", "name": "结婚证"},
    }
    return configs if qq is False else configs_qq


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
            "查询功能": "config查询",
            "菜单": "config查询",
            "帮助": "config查询",
            "关闭": "config关闭",
            "开启": "config开启",
            "运行状态": "config状态",
            "喜报": "表情功能-喜报",
            "悲报": "表情功能-喜报",
            "一直": "表情功能-一直",
            "摸摸": "表情功能-摸摸",
            "可爱": "表情功能-可爱",
            "结婚": "表情功能-结婚",
            "合成": "表情功能-emoji",
            "逮捕": "表情功能-逮捕",
            "寄": "表情功能-寄",
            "急": "表情功能-急",
            "爬": "表情功能-爬",
            "wlp": "表情功能-我老婆",
            "我老婆": "表情功能-我老婆",
            "花音可爱": "表情功能-回复可爱",
            "花音卡哇伊": "表情功能-回复可爱",
            "cck": "小游戏-猜猜看",
            "猜猜看": "小游戏-猜猜看",
            "bzd": "小游戏-猜猜看",
            "不知道": "小游戏-猜猜看",
            "炸飞机": "小游戏-炸飞机",
            "找不同": "小游戏-找不同",
            "签到": "群聊功能-签到",
            "买薯条": "群聊功能-签到",
            "吃薯条": "群聊功能-签到",
            "水母箱": "群聊功能-水母箱",
            "查看水母箱": "群聊功能-水母箱",
            "抓水母": "群聊功能-水母箱",
            "放生": "群聊功能-水母箱",
            "抛弃": "群聊功能-水母箱",
            "丢弃": "群聊功能-水母箱",
            "水母图鉴": "群聊功能-水母箱",
            "水母统计表": "群聊功能-水母箱",
            "水母箱样式": "群聊功能-水母箱",
            "投喂": "群聊功能-水母箱",
            "设置天气": "群聊功能-水母箱",
            "水母探险": "群聊功能-水母探险",
            "塔罗牌": "群聊功能-塔罗牌",
            "今日老婆": "群聊功能-今日老婆",
            "jrlp": "群聊功能-今日老婆",
            "来点": "群聊功能-图库",
            "多来点": "群聊功能-图库",
            "wlp是": "群聊功能-图库",
        },
        "开头": {
            "炸": "小游戏-炸飞机",
            "来点": "群聊功能-图库",
            "多来点": "群聊功能-图库",
            "wlp是": "群聊功能-图库",
        },
        "结尾": {
        },
        "模糊": {
        },
        "精准2": {
        },
    }
    commands_none = {
        "精准": {
            "洗": "表情功能-洗了",
            "洗了": "表情功能-洗了",
            "要洗了": "表情功能-洗了",
            "啊打": "表情功能-ti",
            "我是谁": "表情功能-woshishei",
            "我老婆": "表情功能-wolaopo",
            "结婚证": "表情功能-jiehunzheng",
            "👊": "表情功能-quanquan",
            "给你一拳": "表情功能-quanquan",
            "拳拳": "表情功能-quanquan",
            "指": "表情功能-zhi",
            "🫵": "表情功能-zhi",
            "踢": "表情功能-ti",
            "打拳": "表情功能-quanquan",
            "wlp": "表情功能-wolaopo",
            "😡👊": "表情功能-quanquan",
            "买薯条": "群聊功能-chickin",
            "吃薯条": "群聊功能-chickin",
            "wlp是谁": "图库功能-wlp",
            "来点wlp": "图库功能-wlp",
            "多来点wlp": "图库功能-wlp",
            "成员名单": "图库功能-wlp",
            "tsugu": "群聊功能-Tsugu",
            "ycm": "群聊功能-Tsugu",
            "车来": "群聊功能-Tsugu",
            "开启个人车牌转发": "群聊功能-Tsugu",
            "关闭个人车牌转发": "群聊功能-Tsugu",
        },
        "开头": {
            "来点": "wlp",
            "多来点": "wlp",
            "wlp是": "wlp",
            "新lp是": "wlp"
        },
        "结尾": {
        },
        "模糊": {
            "亲亲": "qinqin",
            "咬咬": "yaoyao",
            "贴贴": "tietie",
            "逮捕": "daibu"
        },
        "精准2": {
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
                      "64": {"name": "圣杯侍从正位",
                             "message": "情感的表达与奉献、积极的消息即将传来、情感的追求但不成熟"},
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
                      "78": {"name": "星币侍从正位",
                             "message": "善于思考和学习、求知欲旺盛、与知识或者研究工作有关的好消息"}},
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
                     "106": {"name": "宝剑6逆位",
                             "message": "深陷于困难、鲁莽地解决却忽视背后更大的问题、需要其他人的帮助或救援"},
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


async def _jellyfish_box_weather_name_data():
    if int(time.time()) - kn_cache["jellyfish_box_weather"]["time"] < 60:
        return kn_cache["jellyfish_box_weather"]["data"]
    file_path = await get_file_path("plugin-jellyfish_box-weather_name_data.json")
    f = open(file_path, encoding="UTF-8")
    data = f.read()
    f.close()
    json_data = json.loads(data)
    kn_cache["jellyfish_box_weather"] = {"time": int(time.time()), "data": json_data}
    return json_data


async def _jellyfish_box_datas():
    if int(time.time()) - kn_cache["_jellyfish_box_datas"]["time"] < 60:
        return kn_cache["_jellyfish_box_datas"]["data"]
    file_path = await get_file_path("plugin-jellyfish_box-box_data.json")
    f = open(file_path, encoding="UTF-8")
    data = f.read()
    f.close()
    json_data = json.loads(data)
    kn_cache["_jellyfish_box_datas"] = {"time": int(time.time()), "data": json_data}
    return json_data


async def _adventure_datas():
    if int(time.time()) - kn_cache["_adventure_datas"]["time"] < 60:
        return kn_cache["_adventure_datas"]["data"]
    file_path = await get_file_path("plugin-adventure-adventure_data.json")
    f = open(file_path, encoding="UTF-8")
    data = f.read()
    f.close()
    json_data = json.loads(data)
    kn_cache["_adventure_datas"] = {"time": int(time.time()), "data": json_data}
    return json_data


def jellyfish_box_draw_config(
        draw_model: str = None,
        draw_dark_model: bool = False,
        date_m: int = int(time.strftime("%m", time.localtime())),
        date_d: int = int(time.strftime("%d", time.localtime())),
        draw_event_box: list | bool = True
):
    draw_config = {
        "normal": {
            "color": {
                "bg": "#EAEBEE",
                "背景大字": "#D5DADF",
                "box_bg": "#1b4771",
                "box_outline": "#002237",
                "card": "#FFFFFF",
                "date": "#363739",
                "name": "#2E82EE",
                "title": "#2E82EE",
                "event_title": "#000000",
                "event_message": "#333333",
                "icon_bg": "#def8ff",
                "icon_outline": "#76c9ec",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "normal_dark": {
            "color": {
                "bg": "#18171C",
                "背景大字": "#232741",
                "box_bg": "#17547b",
                "box_outline": "#002237",
                "card": "#2F2F37",
                "date": "#536DED",
                "name": "#E0E0E0",
                "title": "#EFEFEF",
                "event_title": "#EFEFEF",
                "event_message": "#E0E0E0",
                "icon_bg": "#617793",
                "icon_outline": "#365580",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "text": {
            "color": {
                "bg": "#EAEBEE",
                "背景大字": "#D5DADF",
                "box_bg": "#1b4771",
                "box_outline": "#002237",
                "card": "#FFFFFF",
                "date": "#363739",
                "name": "#2E82EE",
                "title": "#2E82EE",
                "event_title": "#000000",
                "event_message": "#333333",
                "icon_bg": "#def8ff",
                "icon_outline": "#76c9ec",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "mixieer": {
            "color": {
                "bg": "#d5b5c4",
                "背景大字": "#e7ccd9",
                "box_bg": "#645462",
                "box_outline": "#002237",
                "card": "#f7e7f0",
                "date": "#363739",
                "name": "#fe9bca",
                "title": "#fe9bcc",
                "event_title": "#000000",
                "event_message": "#333333",
                "icon_bg": "#f8ddec",
                "icon_outline": "#fe9bcc",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": ["j5"],
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "birthday_kanon": {
            "color": {
                "bg": "#a0d8ef",
                "背景大字": "#bbe7f9",
                "box_bg": "#1b4771",
                "box_outline": "#002237",
                "card": "#e0eff4",
                "date": "#363739",
                "name": "#2E82EE",
                "title": "#2E82EE",
                "event_title": "#000000",
                "event_message": "#333333",
                "icon_bg": "#def8ff",
                "icon_outline": "#76c9ec",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "Kanon",
                "新水母_标题": "新增呼诶诶",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": [
                    "jellyfish_foreground_birthday",
                    "jellyfish_foreground_birthday_2",
                    "jellyfish_foreground_birthday_3"
                ],
                "box_foreground": "box_foreground_birthday",
                "jellyfish_background": None,
                "box_background": "box_background_birthday",
                "card_background": [
                    "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"
                ],
            },
        },
        "freehand": {
            "color": {
                "bg": "#FFFFFF",
                "背景大字": "#e0e3e6",
                "box_bg": "#0d70a4",
                "box_outline": "#FFFFFF",
                "card": (255, 255, 255, 255),
                "date": "#363739",
                "name": "#2E82EE",
                "title": "#2E82EE",
                "event_title": "#000000",
                "event_message": "#333333",
                "icon_bg": "#def8ff",
                "icon_outline": "#76c9ec",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "freehand_dark": {
            "color": {
                "bg": "#282828",
                "背景大字": "#333434",
                "box_bg": "#17547b",
                "box_outline": "#FFFFFF",
                "card": (126, 126, 126, 255),
                "date": "#2e82ee",
                "name": "#91aaca",
                "title": "#589df5",
                "event_title": "#FFFFFF",
                "event_message": "#b3b3b3",
                "icon_bg": "#def8ff",
                "icon_outline": "#76c9ec",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": "水母箱",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": None,
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
        "starlight": {
            "color": {
                "bg": "#2e2c2f",
                "背景大字": "#2e2c2f",
                "box_bg": "#2e2c2f",
                "box_outline": "#2e2c2f",
                "card": "#424242",
                "date": "#aaa089",
                "name": "#bf9f60",
                "title": "#e6cc9b",
                "event_title": "#FFFFFF",
                "event_message": "#b2b2b2",
                "icon_bg": "#59564f",
                "icon_outline": "#6f5f4a",
                "group_color": {
                    "normal": "#eace5f",
                    "good": "#46eca4",
                    "great": "#f15fb2",
                    "perfect": "#935ff1",
                    "special": "#7afffa",
                    "ocean": "#5a96ef",
                },
            },
            "text": {
                "背景大字": " ",
                "新水母_标题": "新增内容",
                "事件_标题": "事件列表",
                "指令_标题": "指令提示",
            },
            "jellyfish": {
                "background": "starlight_background",
                "replace_jellyfish": None,
                "jellyfish_foreground": None,
                "box_foreground": None,
                "jellyfish_background": None,
                "box_background": None,
                "card_background": None,
            },
        },
    }

    # 读取基础配置
    if draw_model is None:
        return draw_config
    if draw_model not in draw_config.keys():
        draw_model = "normal"
    draw_config_ = draw_config[draw_model]
    if draw_dark_model is True and f"{draw_model}_dark" in draw_config.keys():
        draw_config_ = draw_config[f"{draw_model}_dark"]

    # 加载节日替换数据
    if ((type(draw_event_box) is bool and draw_event_box is True) or
        (type(draw_event_box) is list and "生日效果" in draw_event_box)):
        if date_m == 1 and date_d == 1:
            pass
        # 生日-rinko
        elif date_m == 10 and date_d == 17:
            if draw_model in ["normal", "freehand"]:
                draw_config_ = draw_config[f"{draw_model}_dark"]

            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Rinko"

            draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
            draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
            if draw_model in ["normal", "freehand"]:
                draw_config_["color"]["bg"] = "#313131"
                draw_config_["color"]["card"] = "#4a4a4a"
                draw_config_["color"]["背景大字"] = "#414141"
                draw_config_["color"]["box_bg"] = "#262626"
                draw_config_["color"]["box_outline"] = "#161616"
                draw_config_["color"]["icon_bg"] = "#262626"
                draw_config_["color"]["icon_outline"] = "#161616"
                draw_config_["color"]["title"] = "#e7cd9b"
                draw_config_["color"]["event_title"] = "#b1987c"
            if draw_model == "freehand":
                draw_config_["color"]["card"] = "#9a9a9a"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#c2ad86"

        # 生日-himari
        elif date_m == 10 and date_d == 23:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Himari"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#ffd7d7"
                    draw_config_["color"]["card"] = "#FFE7E7"
                    draw_config_["color"]["背景大字"] = "#fee5e5"
                    draw_config_["color"]["name"] = "#957575"
                    draw_config_["color"]["title"] = "#9e6262"
                    draw_config_["color"]["date"] = "#6c3434"
                    draw_config_["color"]["event_title"] = "#322323"
                    draw_config_["color"]["event_message"] = "#4e4242"
                    draw_config_["color"]["box_bg"] = "#ae8f8f"
                    draw_config_["color"]["box_outline"] = "#FF9999"
                    draw_config_["color"]["icon_bg"] = "#ae8f8f"
                    draw_config_["color"]["icon_outline"] = "#FF9999"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#1c1717"
                    draw_config_["color"]["card"] = "#413a3a"
                    draw_config_["color"]["box_bg"] = "#605151"
                    draw_config_["color"]["box_outline"] = "#3d3532"
                    draw_config_["color"]["背景大字"] = "#352b35"
                    draw_config_["color"]["icon_bg"] = "#605151"
                    draw_config_["color"]["icon_outline"] = "#3d3532"
                    draw_config_["color"]["背景大字"] = "#413a3a"
                    draw_config_["color"]["name"] = "#ae8f8f"
                    draw_config_["color"]["date"] = "#413a3a"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#909090"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-yukina
        elif date_m == 10 and date_d == 26:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Yukina"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#ac93a8"
                    draw_config_["color"]["card"] = "#cdb2c8"
                    draw_config_["color"]["背景大字"] = "#bca6b8"
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["title"] = "#881188"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["event_title"] = "#554755"
                    draw_config_["color"]["event_message"] = "#6f6272"
                    draw_config_["color"]["box_bg"] = "#976e92"
                    draw_config_["color"]["box_outline"] = "#2b0037"
                    draw_config_["color"]["icon_bg"] = "#c2a7ca"
                    draw_config_["color"]["icon_outline"] = "#9d83b3"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["card"] = "#474147"
                    draw_config_["color"]["box_bg"] = "#6f6272"
                    draw_config_["color"]["box_outline"] = "#554755"
                    draw_config_["color"]["背景大字"] = "#352b35"
                    draw_config_["color"]["icon_bg"] = "#6f6272"
                    draw_config_["color"]["icon_outline"] = "#554755"
                    draw_config_["color"]["date"] = "#881188"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-arisa
        elif date_m == 10 and date_d == 27:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Arisa"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday_arisa"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#805ab4"
                    draw_config_["color"]["card"] = "#9f80de"
                    draw_config_["color"]["背景大字"] = "#bca6b8"
                    draw_config_["color"]["name"] = "#fff3e7"
                    draw_config_["color"]["title"] = "#c9b16d"
                    draw_config_["color"]["date"] = "#f0c389"
                    draw_config_["color"]["event_title"] = "#efd4b6"
                    draw_config_["color"]["event_message"] = "#dfdcd7"
                    draw_config_["color"]["box_bg"] = "#776ea2"
                    draw_config_["color"]["box_outline"] = "#0b0047"
                    draw_config_["color"]["icon_bg"] = "#b2a7ca"
                    draw_config_["color"]["icon_outline"] = "#8d83b3"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#EFDFFF"
                    draw_config_["color"]["box_bg"] = "#413774"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["card"] = "#474150"
                    draw_config_["color"]["box_bg"] = "#5f6282"
                    draw_config_["color"]["box_outline"] = "#454765"
                    draw_config_["color"]["背景大字"] = "#302b35"
                    draw_config_["color"]["icon_bg"] = "#5f6282"
                    draw_config_["color"]["icon_outline"] = "#454765"
                    draw_config_["color"]["date"] = "#f0c389"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-maya
        elif date_m == 11 and date_d == 3:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Maya"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#b0d7b0"
                    draw_config_["color"]["card"] = "#e1f9e1"
                    draw_config_["color"]["背景大字"] = "#93c493"
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["title"] = "#99dd88"
                    draw_config_["color"]["event_title"] = "#3d8e3d"
                    draw_config_["color"]["event_message"] = "#385039"
                    draw_config_["color"]["box_bg"] = "#6f9d6f"
                    draw_config_["color"]["box_outline"] = "#385039"
                    draw_config_["color"]["icon_bg"] = "#adcaad"
                    draw_config_["color"]["icon_outline"] = "#adcaad"
                if draw_model == "freehand":
                    draw_config_["color"]["title"] = "#8fb78f"
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#303f30"
                    draw_config_["color"]["card"] = "#414e41"
                    draw_config_["color"]["背景大字"] = "#425042"
                    draw_config_["color"]["name"] = "#828282"
                    draw_config_["color"]["date"] = "#2e8238"
                    draw_config_["color"]["title"] = "#729869"
                    draw_config_["color"]["event_title"] = "#3d8e3d"
                    draw_config_["color"]["event_message"] = "#669266"
                    draw_config_["color"]["box_bg"] = "#1e321e"
                    draw_config_["color"]["box_outline"] = "#385039"
                    draw_config_["color"]["icon_bg"] = "#4c624c"
                    draw_config_["color"]["icon_outline"] = "#466946"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#0e220e"
                    draw_config_["color"]["card"] = "#717e71"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-rui
        elif date_m == 11 and date_d == 19:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Rui"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#7bac9c"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["card"] = "#9ed1c0"
                    draw_config_["color"]["title"] = "#669988"
                    draw_config_["color"]["event_title"] = "#427f6b"
                    draw_config_["color"]["event_message"] = "#58a98e"
                    draw_config_["color"]["box_bg"] = "#52967f"
                    draw_config_["color"]["box_outline"] = "#528a77"
                    draw_config_["color"]["icon_bg"] = "#6caa95"
                    draw_config_["color"]["icon_outline"] = "#579f87"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#528a77"
                    draw_config_["color"]["card"] = "#dddddd"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#467263"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#6fa794"
                    draw_config_["color"]["date"] = "#5fb899"
                    draw_config_["color"]["card"] = "#4f806f"
                    draw_config_["color"]["title"] = "#6bb098"
                    draw_config_["color"]["event_title"] = "#8ebcad"
                    draw_config_["color"]["event_message"] = "#6aa792"
                    draw_config_["color"]["box_bg"] = "#3b5b50"
                    draw_config_["color"]["box_outline"] = "#325549"
                    draw_config_["color"]["icon_bg"] = "#467867"
                    draw_config_["color"]["icon_outline"] = "#3f6b5c"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#325549"
                    draw_config_["color"]["card"] = "#8ebcad"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-tomori
        elif date_m == 11 and date_d == 22:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Tomori"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#77bbdd"
                    draw_config_["color"]["card"] = "#c1e9f4"
                    draw_config_["color"]["背景大字"] = "#9cd1eb"
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["title"] = "#55c6ff"
                    draw_config_["color"]["event_title"] = "#475155"
                    draw_config_["color"]["event_message"] = "#626b72"
                    draw_config_["color"]["box_bg"] = "#4b90b2"
                    draw_config_["color"]["box_outline"] = "#2a5970"
                    draw_config_["color"]["icon_bg"] = "#4b90b2"
                    draw_config_["color"]["icon_outline"] = "#2a5970"
                if draw_model == "freehand":
                    draw_config_["color"]["title"] = "#55c6ff"
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#29576d"
                    draw_config_["color"]["card"] = "#466a7b"
                    draw_config_["color"]["背景大字"] = "#3a6479"
                    draw_config_["color"]["name"] = "#6a8c96"
                    draw_config_["color"]["date"] = "#2f87c5"
                    draw_config_["color"]["title"] = "#518aa8"
                    draw_config_["color"]["event_title"] = "#7da2b0"
                    draw_config_["color"]["event_message"] = "#6b8b96"
                    draw_config_["color"]["box_bg"] = "#274b5c"
                    draw_config_["color"]["box_outline"] = "#274b5c"
                    draw_config_["color"]["icon_bg"] = "#274b5c"
                    draw_config_["color"]["icon_outline"] = "#274b5c"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#213d4b"
                    draw_config_["color"]["card"] = "#7e7e71"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-tae
        elif date_m == 12 and date_d == 4:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Tae"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday_tae"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#3685c8"
                    draw_config_["color"]["card"] = "#539ede"
                    draw_config_["color"]["背景大字"] = "#4999dd"
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["title"] = "#0077dd"
                    draw_config_["color"]["event_title"] = "#abd2f6"
                    draw_config_["color"]["event_message"] = "#8ac0f1"
                    draw_config_["color"]["box_bg"] = "#1e5e94"
                    draw_config_["color"]["box_outline"] = "#134b79"
                    draw_config_["color"]["icon_bg"] = "#1e5e94"
                    draw_config_["color"]["icon_outline"] = "#134b79"
                if draw_model == "freehand":
                    draw_config_["color"]["title"] = "#8fb78f"
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#2a4c70"
                    draw_config_["color"]["card"] = "#365c84"
                    draw_config_["color"]["背景大字"] = "#3a5879"
                    draw_config_["color"]["name"] = "#6a8496"
                    draw_config_["color"]["date"] = "#2f87c5"
                    draw_config_["color"]["title"] = "#517ca8"
                    draw_config_["color"]["event_title"] = "#859dbc"
                    draw_config_["color"]["event_message"] = "#6e859b"
                    draw_config_["color"]["box_bg"] = "#1f3e5e"
                    draw_config_["color"]["box_outline"] = "#21344b"
                    draw_config_["color"]["icon_bg"] = "#1f3e5e"
                    draw_config_["color"]["icon_outline"] = "#21344b"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#21344b"
                    draw_config_["color"]["card"] = "#365c84"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-chuchu
        elif date_m == 12 and date_d == 7:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Chuchu"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#7ad1ff"
                    draw_config_["color"]["card"] = "#ade1ff"
                    draw_config_["color"]["背景大字"] = "#5cc7ff"
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["title"] = "#00bbff"
                    draw_config_["color"]["event_title"] = "#386a8e"
                    draw_config_["color"]["event_message"] = "#5e809f"
                    draw_config_["color"]["box_bg"] = "#4599d6"
                    draw_config_["color"]["box_outline"] = "#1483c0"
                    draw_config_["color"]["icon_bg"] = "#89cfff"
                    draw_config_["color"]["icon_outline"] = "#73b9e9"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#2a4c70"
                    draw_config_["color"]["card"] = "#365c84"
                    draw_config_["color"]["背景大字"] = "#3a5879"
                    draw_config_["color"]["name"] = "#6a8496"
                    draw_config_["color"]["date"] = "#2f87c5"
                    draw_config_["color"]["title"] = "#517ca8"
                    draw_config_["color"]["event_title"] = "#859dbc"
                    draw_config_["color"]["event_message"] = "#6e859b"
                    draw_config_["color"]["box_bg"] = "#1f3e5e"
                    draw_config_["color"]["box_outline"] = "#21344b"
                    draw_config_["color"]["icon_bg"] = "#1f3e5e"
                    draw_config_["color"]["icon_outline"] = "#21344b"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = draw_config_["color"]["box_outline"]
                    draw_config_["color"]["card"] = "#365c84"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-toko
        elif date_m == 12 and date_d == 16:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Toko"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#eab2b2"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["card"] = "#ffcece"
                    draw_config_["color"]["title"] = "#ee6666"
                    draw_config_["color"]["event_title"] = "#b06667"
                    draw_config_["color"]["event_message"] = "#ba7f80"
                    draw_config_["color"]["box_bg"] = "#b88282"
                    draw_config_["color"]["box_outline"] = "#ac6f6f"
                    draw_config_["color"]["icon_bg"] = "#ebb1b1"
                    draw_config_["color"]["icon_outline"] = "#d39e9e"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#FFFFFF"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#865758"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#d2b0ad"
                    draw_config_["color"]["date"] = "#ee6666"
                    draw_config_["color"]["card"] = "#a27070"
                    draw_config_["color"]["title"] = "#97484a"
                    draw_config_["color"]["event_title"] = "#593333"
                    draw_config_["color"]["event_message"] = "#794147"
                    draw_config_["color"]["box_bg"] = "#6b4046"
                    draw_config_["color"]["box_outline"] = "#623237"
                    draw_config_["color"]["icon_bg"] = "#7c4b51"
                    draw_config_["color"]["icon_outline"] = "#6b4046"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#909090"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

        # 生日-aya
        elif date_m == 12 and date_d == 27:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                        "jellyfish_foreground_birthday",
                        "jellyfish_foreground_birthday_2",
                        "jellyfish_foreground_birthday_3", None, None, None]
            draw_config_["jellyfish"]["card_background"] = [
                        "card_background_birthday", "card_background_birthday_2", "card_background_birthday_3"]
            draw_config_["text"]["背景大字"] = "Aya"
            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_birthday"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_birthday"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#f9afcf"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#e8e8e8"
                    draw_config_["color"]["date"] = "#363739"
                    draw_config_["color"]["card"] = "#ffc2dc"
                    draw_config_["color"]["title"] = "#ff88bb"
                    draw_config_["color"]["event_title"] = "#b85882"
                    draw_config_["color"]["event_message"] = "#b97391"
                    draw_config_["color"]["box_bg"] = "#e397b8"
                    draw_config_["color"]["box_outline"] = "#e397b8"
                    draw_config_["color"]["icon_bg"] = "#e7a5c2"
                    draw_config_["color"]["icon_outline"] = "#e397b8"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#c47b9b"
                    draw_config_["color"]["card"] = "#dddddd"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["bg"] = "#a86683"
                    draw_config_["color"]["背景大字"] = (0, 0, 0, 60)
                    draw_config_["color"]["name"] = "#cd99af"
                    draw_config_["color"]["date"] = "#ff88bb"
                    draw_config_["color"]["card"] = "#bd809b"
                    draw_config_["color"]["title"] = "#c44e81"
                    draw_config_["color"]["event_title"] = "#7d3d58"
                    draw_config_["color"]["event_message"] = "#904967"
                    draw_config_["color"]["box_bg"] = "#94506e"
                    draw_config_["color"]["box_outline"] = "#8d4766"
                    draw_config_["color"]["icon_bg"] = "#a76381"
                    draw_config_["color"]["icon_outline"] = "#a75c7d"
                if draw_model == "freehand":
                    draw_config_["color"]["box_bg"] = "#8d4766"
                    draw_config_["color"]["card"] = "#cd99af"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"

    if ((type(draw_event_box) is bool and draw_event_box is True) or
            (type(draw_event_box) is list and "节日效果" in draw_event_box)):
        # 万圣节
        if (date_m == 10 and date_d == 30) or (date_m == 10 and date_d == 31) or (date_m == 11 and date_d == 1):
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                "jellyfish_foreground_halloween",
                "jellyfish_foreground_halloween_2",
                None, None]
            draw_config_["jellyfish"]["box_background"] = "box_background_halloween"
            draw_config_["jellyfish"]["box_foreground"] = "box_foreground_halloween"
            if date_m == 10 and date_d == 31:
                draw_config_["text"]["背景大字"] = "万圣夜"
            elif date_m == 11 and date_d == 1:
                draw_config_["text"]["背景大字"] = "万圣节"

            if draw_model in ["normal", "freehand"]:
                draw_config_["color"]["title"] = "#FBFBFB"
                draw_config_["color"]["event_title"] = "#FB913A"
                draw_config_["color"]["name"] = "#FB913A"
                draw_config_["color"]["bg"] = "#292644"
                draw_config_["color"]["card"] = "#3a3053"
                draw_config_["color"]["背景大字"] = "#322E53"
                draw_config_["color"]["event_message"] = "#E0E0E0"
                draw_config_["color"]["box_bg"] = "#1B2855"
                draw_config_["color"]["box_outline"] = "#111111"
                draw_config_["color"]["icon_bg"] = "#2b2144"
                draw_config_["color"]["icon_outline"] = "#1A0435"
            if draw_model == "freehand":
                draw_config_["color"]["card"] = "#5C4D81"
            if draw_model == "starlight":
                # draw_config_["color"]["背景大字"] = "#202023"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_halloween_starlight"
                draw_config_["jellyfish"]["box_background"] = "box_background_halloween_starlight"

        # 圣诞节
        if date_m == 12 and 20 <= date_d <= 25:
            draw_config_["jellyfish"]["jellyfish_foreground"] = [
                "jellyfish_foreground_chirstmas",
                None, None]
            if date_m == 12 and date_d == 24:
                draw_config_["text"]["背景大字"] = "平安夜"
            elif date_m == 12 and date_d == 25:
                draw_config_["text"]["背景大字"] = "圣诞节"

            if draw_dark_model is False:
                draw_config_["jellyfish"]["box_background"] = "box_background_christmas"
                draw_config_["jellyfish"]["box_foreground"] = "box_foreground_christmas"
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["title"] = "#dd9200"
                    draw_config_["color"]["event_title"] = "#5d5349"
                    draw_config_["color"]["event_message"] = "#aca298"
                    draw_config_["color"]["name"] = "#e9af52"
                    draw_config_["color"]["bg"] = "#f6f0e6"
                    draw_config_["color"]["card"] = "#fbfaf3"
                    draw_config_["color"]["背景大字"] = "#f1e3cb"
                    draw_config_["color"]["box_bg"] = "#d9d2c6"
                    draw_config_["color"]["box_outline"] = "#d9d2c6"
                    draw_config_["color"]["icon_bg"] = "#d9d2c6"
                    draw_config_["color"]["icon_outline"] = "#d9d2c6"
                    draw_config_["jellyfish"]["background"] = "christmas_background"
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#ffffff"
                    draw_config_["color"]["box_bg"] = "#aba499"
                    draw_config_["color"]["box_outline"] = "#aba499"
            else:
                if draw_model in ["normal", "freehand"]:
                    draw_config_["color"]["name"] = "#bbb7b4"
                    draw_config_["color"]["date"] = "#c2762f"
                    draw_config_["color"]["bg"] = "#504c4a"
                    draw_config_["color"]["背景大字"] = "#625651"
                    draw_config_["color"]["box_bg"] = "#3d3a39"
                    draw_config_["color"]["box_outline"] = "#3d3a39"
                    draw_config_["color"]["title"] = "#9b8b7b"
                    draw_config_["color"]["event_title"] = "#c3b9b3"
                    draw_config_["color"]["event_message"] = "#9b9490"
                    draw_config_["color"]["card"] = "#686360"
                    draw_config_["color"]["icon_bg"] = "#3d3a39"
                    draw_config_["color"]["icon_outline"] = "#3d3a39"
                    draw_config_["jellyfish"]["background"] = None
                if draw_model == "freehand":
                    draw_config_["color"]["card"] = "#888888"
                    draw_config_["color"]["box_bg"] = "#aba499"
                    draw_config_["color"]["box_outline"] = "#aba499"
            if draw_model == "starlight":
                draw_config_["color"]["背景大字"] = "#53514c"
                draw_config_["jellyfish"]["box_background"] = None
                draw_config_["jellyfish"]["box_foreground"] = None
                draw_config_["jellyfish"]["background"] = "starlight_background_christmas"

    return draw_config_


def state(name: str):
    match name:
        case "time_h":
            return ""
    return None


def greet_list_():
    data = [
        {
            "ask": ["早安", "早上好", "早上", "早", "哦哈哟"],
            "answer": {
                "0-5": [
                    "凌晨时分，{user_name}还在熬夜吗？要注意身体哦。",
                    "凌晨就起床啦？真勤奋呀，花音还是想多睡会儿...",
                    "水母..嘿嘿..水母软软的...诶，是梦啊...",
                    "呼诶诶诶诶~~有只水母搁浅啦！原来是梦啊，还好水母没事",
                ],
                "0-7": [
                    "早..好....让我再稍微睡一下，昨晚hhw练习有点晚了",
                    "嗯...好困，再让我眯一会儿，早上还要去快餐店兼职呢",
                ],
                "5-11": [
                    "早上好，早起的水母有丰年虾吃，今天也要加油哦！",
                    "早安，新的一天开始了，今天也要加油哦！",
                    "早上好，今天的阳光很温暖，适合开始新的一天。",
                    "早哦，我已经迫不及待想要开始今天的练习了。",
                    "早哦，大家今天也要元气满满哦。",
                    "嗯，今天的天气适合出门吗？我要和千圣一起去喝咖啡",
                    "早安，新的一天，希望一切顺利！",
                    "早安，今天要去快餐店兼职了，不知道彩彩今天有没有去兼职",
                    "早安，愿今天的每一刻都充满温馨和快乐。",
                    "早哦，待会打算去山吹面包房买个面包，你要来一个么",
                    "早安，今天也要努力爵士鼓呢"
                ],
                "7-10": [
                    "呼诶诶诶诶~~已经早上来啦，我得赶紧起来，今天约了薰同学一起去咖啡店",
                ],
                "12-20": [
                    "不早啦，已经{time_h}点啦，真是的",
                ],
                "12-14": [
                    "中午时间到啦，是时候吃午餐啦，今天我打算尝试新的食谱。",
                    "中午啦，今天的午餐有什么好推荐的吗？",
                    "唔..现在才起床么，已经不早啦",
                    "午安，今天的午餐是什么呢？好期待"
                ],
                "14-16": [
                    "都已经下午啦，赶紧起床，真是的，下午茶时间快到了呢",
                    "下午好，今天下午打算和千圣一起去咖啡店呢",
                    "起床起床，已经{time_h}点啦"
                ],
                "17-18": [
                    "快到吃晚饭的时候了哦，快起来啦",
                    "傍晚了，今天的夕阳真美，适合散步哦"
                ],
                "19-21": [
                    "现在是晚上吧，是晚上好啦，今天晚上的星星也很亮呢",
                    "晚好哦，看，那边的星星组成了一个水母图案"
                ],
                "22-24": [
                    "唔..这个点应该要碎觉啦，你也早点休息吧"
                ]
            }
        },
        {
            "ask": ["晚上好", "晚上", "晚", "空帮哇"],
            "answer": {
                "0-5": [
                    "水母..嘿嘿..水母软软的...诶，是梦啊...",
                    "呼诶诶诶诶~~有只水母搁浅啦！原来是梦啊，还好水母没事",
                    "晚..好....我先睡一步了，晚上hhw练习有点晚了",
                    "唔...好困，眼睛已经张不开了，明早还要去快餐店兼职呢",
                    "晚安，千圣已经睡啦，花音也要去睡觉了",
                    "已经很晚啦，快点睡吧",
                    "诶，{user_name}还没睡么，快睡啦",
                    "..这只水母...好软...抱着好舒服..",
                ],
                "5-7": [
                    "诶，{user_name}还没睡么，快睡啦",
                    "太阳要出来了诶...{user_name}还没睡么，快睡啦",
                ],
                "8-12": [
                    "现在是...早上啦",
                    "早安！这个点应该说早安",
                ],
                "11-13": [
                    "现在是{time_h}点，是中午时间啦",
                    "花音这里是中午哦，中午好",
                ],
                "14-16": [
                    "现在才{time_h}点，是下午好哦",
                    "花音这里是下午哦，下午好",
                ],
                "17-18": [
                    "花音这里是傍晚哦，傍晚好",
                    "好早的说，花音才刚准备吃晚饭",
                ],
                "19-22": [
                    "晚上好，今天的夜空也很美，适合欣赏。",
                    "晚上好啦，今天晚上的星星也很亮呢",
                    "晚上好哦，今天应该过得很充实吧",
                ],
                "23-24": [
                    "唔..这个点应该要碎觉啦，{user_name}也早点休息吧",
                    "晚..好....我先睡一步了，晚上hhw练习有点晚了",
                    "唔...好困，眼睛已经张不开了，明早还要去快餐店兼职呢",
                    "晚安，千圣已经睡啦，花音也要去睡觉了",
                    "已经很晚啦，快点睡吧"
                    "诶，{user_name}还没睡么，快睡啦",
                ],
            }
        },
        {
            "ask": ["晚安", "哦呀粟米", "哦呀斯密", "哦呀粟米那赛", "哦呀斯密那赛"],
            "answer": {
                "0-5": [
                    "水母..嘿嘿..水母软软的...诶，是梦啊...",
                    "呼诶诶诶诶~~有只水母搁浅啦！原来是梦啊，还好水母没事",
                    "晚..安....我先睡一步了，晚上hhw练习有点晚了",
                    "唔...好困，眼睛已经张不开了，明早还要去快餐店兼职呢",
                    "晚安，千圣已经睡啦，花音也要去睡觉了",
                    "已经很晚啦，快点睡吧",
                    "诶，{user_name}还没睡么，快睡啦",
                    "..这只水母...好软...抱着好舒服..",
                ],
                "5-7": [
                    "诶，{user_name}还没睡么，快睡啦",
                    "太阳要出来了诶...{user_name}还没睡么，快睡啦",
                ],
                "8-12": [
                    "现在是...早上啦",
                    "早安！这个点应该说早安",
                ],
                "12-13": [
                    "花音这里是中午哦，要睡午觉啦",
                ],
                "14-16": [
                    "花音这里是下午哦，下午好",
                ],
                "17-18": [
                    "花音这里是傍晚哦，傍晚好",
                    "好早的说，花音才刚准备吃晚饭",
                ],
                "19-22": [
                    "晚上好，花音也准备睡觉啦，晚安",
                    "晚上好，花音还在准备着睡前的事情，{user_name}先休息吧",
                ],
                "23-24": [
                    "已经很晚了，早点休息吧，明天还要继续努力。",
                    "唔..这个点应该要碎觉啦，{user_name}也早点休息吧",
                    "晚..好....我先睡一步了，晚上hhw练习有点晚了",
                    "唔...好困，眼睛已经张不开了，明早还要去快餐店兼职呢",
                    "晚安，千圣已经睡啦，花音也要去睡觉了",
                    "已经很晚啦，快点睡吧",
                    "诶，{user_name}还没睡么，快睡啦",
                    "晚安，愿你的梦里都是美好的旋律和水母的舞蹈。",
                    "夜深了，是时候说晚安了，愿明天会更好。"
                ],
            }
        },
        {
            "ask": ["中午好"],
            "answer": {
                "0-5": [
                    "凌晨时分，{user_name}还在熬夜吗？要注意身体哦。",
                    "晚..好....我先睡一步了，晚上hhw练习有点晚了",
                    "水母..嘿嘿..水母软软的...诶，是梦啊...",
                    "已经很晚啦，快点睡吧",
                    "..这只水母...好软...抱着好舒服..",
                    "呼诶诶诶诶~~有只水母搁浅啦！原来是梦啊，还好水母没事",
                ],
                "4-7": [
                    "早..好....让我再稍微睡一下，昨晚hhw练习有点晚了",
                    "嗯...好困，再让我眯一会儿，早上还要去快餐店兼职呢",
                ],
                "5-11": [
                    "早安，新的一天开始了，今天也要加油哦！",
                    "早哦，大家今天也要元气满满哦。",
                    "嗯，今天的天气适合出门吗？我要和千圣一起去喝咖啡",
                    "早安，新的一天，希望一切顺利！",
                    "中..午....诶，现在不是还早着么！",
                    "早哦，现在是早上时间啦",
                    "还早啦，现在才{time_h}点，真是的",
                    "花音这里是早上哦，早上好",
                ],
                "7-10": [
                    "呼诶诶诶诶~~已经早上来啦，我得赶紧起来，今天约了薰同学一起去咖啡店",
                ],
                "11-14": [
                    "中午好哦，是时候吃午餐啦，今天我打算尝试新的食谱。",
                    "中午好，今天的午餐有什么好推荐的吗？",
                    "午安，今天的午餐是什么呢？好期待",
                    "中午好哦，忙碌了一个早上，可以休息一下啦"
                ],
                "15-17": [
                    "已经{time_h}点啦，是下午好哦",
                    "下午好，今天下午打算和千圣一起去咖啡店呢",
                    "花音这里是下午哦，下午好",
                ],
                "17-18": [
                    "快到吃晚饭的时候啦，不早啦",
                    "傍晚了，今天的夕阳真美，适合散步哦"
                ],
                "19-21": [
                    "现在是晚上吧，是晚上好啦，今天晚上的星星也很亮呢",
                    "晚好哦，看，那边的星星组成了一个水母图案",
                    "花音这里是晚上哦，晚好",
                ],
                "22-24": [
                    "唔..这个点应该要碎觉啦，你也早点休息吧"
                ]
            }
        },
        {
            "ask": ["你好", "你好呀", "您好", "hello", "Hello", "扣你吉瓦", "哈喽"],
            "answer": {
                "0-24": [
                    "你好，这里是花音Kanon。指令相关帮助请发送“/菜单”查看。"
                ]
            }
        },
        {
            "ask": ["Noneeeeee"],
            "answer": {
                "0-24": [
                    "晚..好....我先睡一步了，晚上hhw练习有点晚了",
                    "唔...好困，眼睛已经张不开了，明早还要去快餐店兼职呢",
                    "晚安，千圣已经睡啦，花音也要去睡觉了",
                    "已经很晚啦，快点睡吧"
                ]
            }
        }
    ]
    return data
