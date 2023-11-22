# nonebot-plugin-kanonbot

KanonBot - nb2 插件版

目前仍在移植中

## 安装

（以下方法三选一）

一.命令行安装：

    nb plugin install nonebot-plugin-kanonbot

二.pip 安装：

1.执行此命令

    pip install nonebot-plugin-kanonbot

2.修改 pyproject.toml 使其可以加载插件

    plugins = [”nonebot-plugin-kanonbot“]

三.使用插件文件安装：（不推荐）

1.下载插件文件，放到 plugins 文件夹。

2.修改 pyproject.toml 使其可以加载插件

## 配置

在 nonebot2 项目的`.env`文件中选填配置

1.配置管理员账户

    SUPERUSERS=["12345678"] # 配置 NoneBot 超级用户

2.插件数据存放位置，默认为 “./KanonBot/”。

    kanonbot_basepath="./KanonBot/"

在 KanonBot 文件夹 的 kanon_config.toml 文件中选填配置

```
[kanon_api]
# KanonAPI的url，非必要无需修改。
url = "http://cdn.kanon.ink"
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

[botswift]
# 是否开启仅1个bot响应功能。默认关闭。
# 开启后，同一个群内仅1个bot会响应。只有在第一个bot在10次没回应的时候，第二个bot才会开始响应。
# 注：10次为所有群总计
state = false
# 忽略该功能的群号/子频道号
ignore_list = ["123456"]

[chat]
# 聊天功能配置。需要填写tocken才能使用
# 聊天模型。默认为百度文心一言模型（）。
model = "model"
# tocken
tocken = "file"
# tocken
tocken = "file"
# tocken
tocken = "file"
# tocken
tocken = "file"
# tocken
tocken = "file"

```

## 已移植内容：

- [x] 占卜

- [x] emoji

- [x] 指令冷却

## 交流

- 交流群[鸽子窝里有鸽子（291788927）](https://qm.qq.com/cgi-bin/qm/qr?k=QhOk7Z2jaXBOnAFfRafEy9g5WoiETQhy&jump_from=webapi&authKey=fCvx/auG+QynlI8bcFNs4Csr2soR8UjzuwLqrDN9F8LDwJrwePKoe89psqpozg/m)

- 有疑问或者建议都可以进群唠嗑唠嗑。
