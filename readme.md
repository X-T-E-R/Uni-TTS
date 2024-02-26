## 介绍
这是一个后端项目

基于[https://github.com/RVC-Boss/GPT-SoVITS](https://github.com/RVC-Boss/GPT-SoVITS)

对推理进行了特化，前后端分离，支持快速切换人物、模型管理等功能

可以实现快速切换人物
## 有关于更新
2024.2.26进行了大更新，请重新覆盖安装
并且，十分建议查看这个中文文档
[https://www.yuque.com/xter/zibxlp/nqi871glgxfy717e](https://www.yuque.com/xter/zibxlp/nqi871glgxfy717e)

## 安装方式

对于安装

我们可以看看
[https://www.yuque.com/xter/zibxlp/nqi871glgxfy717e](https://www.yuque.com/xter/zibxlp/nqi871glgxfy717e)

这个中文文档会更加详细

### 推荐做法：
对于一个已经能正常运行的GPT-soVITS项目

将项目文件拷入根目录

我们希望的层级结构是

```ini
----main_project
--------GPT_SoVITS（原始项目文件）
------------s1_train.py
------------s2_train.py
------------...
--------trianed
------------character_model_folders
------------character_info.json
--------TTS-for-GPT-soVITS
------------src
----------------tts_backend.py
----------------TTS_Webui.py
----------------...
------------readme.md
------------requirements.txt
------------bat_files
```

然后依次运行这些bat文件即可

### 独立安装：

不推荐！！！

这个东西更多请当成插件使用

### 整合包：
在弄，等一等
## 导入模型
！注意，这个不同于主项目，而是将模型以人物卡的形式导入

在主项目的trained文件夹，通过子文件夹的形式导入人物

### 文件夹要求
文件夹名称就是人物名称

![image.png](https://cdn.nlark.com/yuque/0/2024/png/35975318/1708088625419-3e47692d-ca75-4202-9d72-538550a1806b.png#averageHue=%23f9f8f8&clientId=ue190b2a0-f82e-4&from=paste&height=108&id=u1b07e1fb&originHeight=216&originWidth=1012&originalType=binary&ratio=2&rotation=0&showTitle=false&size=19455&status=done&style=none&taskId=u31fe83d2-1cb0-44d1-a666-26cef7b5f1a&title=&width=506)

里面应该至少有3个文件

以`pth`/`ckpt`/`wav`后缀名结尾

### *如何指定默认角色
在`trained`文件夹下有一个`character_info.json`
通过修改它可以改变默认角色
```json
{
"deflaut_character":"hutao"
}
```
### 如何管理模型

我写了一个模型管理界面`Character_Manager.py`，可以通过bat启动

在里面可以方便的管理模型，添加情绪等

## 如何使用

直接双击bat即可
![image.png](https://cdn.nlark.com/yuque/0/2024/png/35975318/1708089147914-5b703fac-770e-47d5-b928-47389da6d7b3.png#averageHue=%231e1d1c&clientId=ue190b2a0-f82e-4&from=paste&height=207&id=axeUa&originHeight=413&originWidth=859&originalType=binary&ratio=2&rotation=0&showTitle=false&size=46567&status=done&style=none&taskId=ub1efa501-62d6-4b60-889a-fdacb64f703&title=&width=429.5)

### 阅读3.0配置使用例
比如用阅读3.0

[https://github.com/gedoor/legado](https://github.com/gedoor/legado)

![image.png](https://cdn.nlark.com/yuque/0/2024/png/35975318/1708089393043-b3665805-a77b-49c5-9207-04c52b92ccbd.png#averageHue=%23272626&clientId=ue190b2a0-f82e-4&from=paste&height=278&id=u9921c858&originHeight=555&originWidth=558&originalType=binary&ratio=2&rotation=0&showTitle=false&size=66151&status=done&style=none&taskId=ue357c9d2-b7d6-4368-8ea2-a328262f646&title=&width=279)

在朗读引擎中加入对应人名的朗读引擎

如图配置
![image.png](https://cdn.nlark.com/yuque/0/2024/png/35975318/1708089464053-fb6f72f5-929c-408e-9dec-4f63b7c32bf8.png#averageHue=%23653727&clientId=ue190b2a0-f82e-4&from=paste&height=308&id=u7a77de52&originHeight=615&originWidth=566&originalType=binary&ratio=2&rotation=0&showTitle=false&size=117815&status=done&style=none&taskId=u1f7aa5c3-075f-4086-be5b-46d38dd4fed&title=&width=283)
```json
http://192.168.0.106:5000/tts,
{
    "method": "POST",
    "body": {
        "cha_name": "hutao",
        "text": "{{java.encodeURI(speakText)}}"
    }
}
```
调整链接为你的挂载点
### api
它默认运行在5000端口，挂载点是例如`[http://192.168.0.106:5000/tts](http://192.168.0.106:5000/tts,)`

#### 接受的数据
最少项：
```json
{
    "method": "POST",
    "body": {
       
        "text": "{{java.encodeURI(speakText)}}"
    }
}
```
详细选项
```json
{
    "method": "POST",
    "body": {
        "cha_name": "hutao",
        "text": "{{java.encodeURI(speakText)}}",
        "top_k": 3,
        "top_p": 0.6,
        "temperature": 0.6
    }
}
```
其中`text`是必要项

`cha_name`可选，请确保在`trained`中存在对应模型，不指定则使用默认模型

其它参数如果不知道怎么指定，可以不指定


#### 返回的数据
返回`audio/wav`
