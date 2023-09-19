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

    bilipush_basepath="./KanonBot/"

在 KanonBot 文件夹 的 kanon_config.toml 文件中选填配置

    [kanon_api]
    # KanonAPI的url，非必要无需修改。
    url = "http://cdn.kanon.ink"
    # 是否开启API，默认开启。（理论上，目前部署kanon必须开启）
    state = True

    [emoji]
    # 是否开启emoji的功能。默认开启。
    state = True
    # emoji的加载方式。
    # "file"：下载emoji的数据库文件。
    mode = "file"

    [botswift]
    # 是否开启bot心跳的功能。默认关闭。
    state = False
    # 忽略该功能的群
    ignore_list = ["123456"]

## To-Do

🔵 接下来：

- [ ] 新建更多文件夹

- [ ] 新建更多更多更多更多文件夹

- [ ] q 头像加缓存

- [ ] 自动删除缓存

- [ ] botswift 功能代码

- [ ] 指令冷却功能代码

- [ ] 优化锁定

🟢 已完成：

- [x] 新建文件夹

## 更新日志

### 0.0.1

新建文件夹

## 交流

- 交流群[鸽子窝里有鸽子（291788927）](https://qm.qq.com/cgi-bin/qm/qr?k=QhOk7Z2jaXBOnAFfRafEy9g5WoiETQhy&jump_from=webapi&authKey=fCvx/auG+QynlI8bcFNs4Csr2soR8UjzuwLqrDN9F8LDwJrwePKoe89psqpozg/m)

- 有疑问或者建议都可以进群唠嗑唠嗑。
