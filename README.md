<div align="center">
  <p><img src="http://cdn.kanon.ink/api/image?key=899178&imageid=image-20230618-220942-65085441" width="150" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-kanonbot
KanonBot - nb2插件版
</div>

## 前言
与其天天与（）作斗争，不如做成插件。反正代码写也写了。

## 安装
（以下方法三选一）

~~一.命令行安装：~~（未上架，无法使用此命令） 

    nb plugin install nonebot-plugin-kanonbot
    
二.pip安装：（目前处于测试版本，pip也许不是最新的） 

1.执行此命令

    pip install nonebot-plugin-kanonbot
    
2.修改pyproject.toml使其可以加载插件

    plugins = [”nonebot-plugin-kanonbot“]
    
 三.使用插件文件安装：
 （目前唯一可用方案，但推荐等待正式版后再使用此插件。）
 
 1.下载插件文件，放到plugins文件夹。

2.修改pyproject.toml使其可以加载插件

 
## 配置
在 nonebot2 项目的`.env`文件中选填配置

1.配置管理员账户

    SUPERUSERS=["12345678"] # 配置 NoneBot 超级用户
    
2.插件数据存放位置，默认为 “./KanonBot/”。

    bilipush_basepath="./KanonBot/"

## To-Do
🔵接下来：
 - [ ] 新建更多文件夹
 - [ ] q头像加缓存
 - [ ] 自动删除缓存
 
 🟢已完成：
 - [x] 新建文件夹
 
## 更新日志
### 0.0.1
新建文件夹

## 交流
-   交流群[鸽子窝里有鸽子（291788927）](https://qm.qq.com/cgi-bin/qm/qr?k=QhOk7Z2jaXBOnAFfRafEy9g5WoiETQhy&jump_from=webapi&authKey=fCvx/auG+QynlI8bcFNs4Csr2soR8UjzuwLqrDN9F8LDwJrwePKoe89psqpozg/m)
-   有疑问或者建议都可以进群唠嗑唠嗑。
