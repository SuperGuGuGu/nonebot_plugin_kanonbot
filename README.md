![](README_md_files/3ed35ba0-07c7-11ef-8937-af21a3434079.jpeg?v=1\&type=image)

# nonebot-plugin-kanonbot

KanonBot - nb2 插件版

### 本项目不再作为nonebot插件更新，仅作为代码分享。

（理论上是可以正常跑的）

## 安装

（以下方法四选一）

默认为adapter-qq。如需其他适配器请下载文件，在adapters文件夹找到对应文件，更改名字为`__init__.py` 并覆盖插件文件中的文件

对于有能力的开发者，更建议从plugins.py导入相关功能函数到自己开发的插件来使用相关功能。

一.使用插件文件安装：（推荐）

1.下载 nonebot\_plugin\_kanonbot 文件夹，放到 plugins 文件夹内。

2.在 pyproject.toml 的 plugin\_dirs 中添加 "plugin" 使其可以顺利加载。

    plugin_dirs = ["plugins"]

二.命令行安装：

    nb plugin install nonebot-plugin-kanonbot

三.pip 安装：

1.执行此命令

    pip install nonebot-plugin-kanonbot

2.修改 pyproject.toml 使其可以加载插件

    plugins = [”nonebot-plugin-kanonbot“]

四.从plugins.py导入功能到自己编写的插件

    from nonebot_plugin_kanonbot.plugins import plugin_emoji

## 配置

在 nonebot2 项目的`.env`文件中选填配置

1.配置管理员账户

    SUPERUSERS=["12345678"] # 配置 NoneBot 超级用户

2.插件数据存放位置，默认为 “./KanonBot/”。

    kanonbot_basepath="./KanonBot/"

在 KanonBot 文件夹 的 kanon\_config.toml 文件中选填配置

```TOML
[kanon_api]
# KanonAPI的url，非必要无需修改。
url = "https://cdn.kanon.ink"
# 是否开启API来获得完整功能，默认开启。
# （理论上，目前部署kanon必须开启）
state = true

[emoji]
# 是否开启emoji的功能。默认开启。
# 需要下载emoji.db.7z文件并解压至"{kanonbot_basepath}file"文件夹才会生效
state = true
# emoji的加载方式。
# "file"：加载本地文件
mode = "file"

[plugin]
# 频道/群组黑白名单
# 要开启黑白名单的平台。例："qq", "qq_Official"
black_white_list_platform = ["qq"]
# 不在名单内则继续，同时在名单内不会运行
# 名单规则：[f"channel_{platform}_{channel_id}", f"group_{platform}_{group_id}", f"private_{platform}_{user_id}", f"group_qq_291788927"]
channel_white_list = ["group_qq_123456"]
channel_black_list = ["group_qq_123456"]
# 用户id，为unity_id，并非真实id。对应id在config.db的id_list表中查看。
# 不在名单内则继续，同时在名单内不会运行
user_black_list = ["unity_id"]  # 用户白名单
user_white_list = ["unity_id"]  # 用户黑名单

# at消息包含有机器人列表的机器人话，则不运行
bot_list = ["qq号", "123456"]
# 记录运行日志
log = false
# 文件快速缓存路径，用于加速文件访问。
file_fast_cache_path = "./file_cache/"
# 图片快速缓存路径，用于加速图片访问。
image_fast_cache_path = "./image_cache/"

[plugin_cck]
# 绘制样式，可选1：渲染图片，返回图片和文字；2：文字和图片一起渲染，只返回图片
draw_type = 1

[plugin_cck]
# 发送方式
# 为1时，文字和图片分开发送；为2时，文字绘制成图片，和cck图片一起发送
draw_type = 1

[plugin_jellyfish_box]
# 是否绘制gif。在执行指令“查看水母箱”的时候是否实时绘制动图
draw_gif = false

```

## 已有功能：

*   [x] 🔮塔罗牌

*   [x] 🍟签到

*   [x] 🪼水母箱

*   [x] 😋emoji

*   [x] 🎉喜报/悲报

*   [x] 👀猜猜看

*   [x] ✈炸飞机

*   [x] 🤺水母探险

*   [x] 🔍找不同（beta）

*   [x] 😙今日老婆

*   [x] 问好

*   [x] ❄指令冷却

*   [x] 表情：一直

*   [x] 表情：摸摸

*   [x] 表情：可爱

*   [x] 表情：逮捕

*   [x] 表情：结婚

*   [x] 表情：寄

*   [x] 表情：急

*   [x] 表情：爬

*   [x] 表情：我老婆

## 常见问题解决方法

如遇字体无法下载请搜索对应字体下载到`./KanonbBot/file/xxx.ttf`即可

## 交流

*   交流群[鸽子窝里有鸽子（291788927）](https://qm.qq.com/cgi-bin/qm/qr?k=QhOk7Z2jaXBOnAFfRafEy9g5WoiETQhy\&jump_from=webapi\&authKey=fCvx/auG+QynlI8bcFNs4Csr2soR8UjzuwLqrDN9F8LDwJrwePKoe89psqpozg/m)

*   有疑问或者建议都可以进群唠嗑唠嗑。

