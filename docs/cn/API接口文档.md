## 概述
本文档旨在介绍如何使用我们的文本转语音的API，包括通过GET和POST方法进行请求。本API支持将文本转换为指定角色的语音，并支持不同的语言和情感表达。
## 角色列表
要获取支持的角色及其对应的情感，请访问以下URL：

- URL：`http://127.0.0.1:5000/character_list`
- 返回：JSON格式的角色列表和对应情感
## 语音转文本

- URL：`http://127.0.0.1:5000/tts`
- 返回：成功时返回wav音频。失败时返回错误原因。
- 支持的方法：`GET`/`POST`
### GET方法
#### 格式
```
http://127.0.0.1:5000/tts?cha_name={{characterName}}&text={{text}}
```

- 参数说明：
   - `cha_name`：角色文件夹的名字，需注意大小写、全半角及语言（中英文）。
   - `text`：要转换的文本，建议使用URL编码。
   - 可选参数包括`text_language`、`top_k`、`top_p`、`temperature`、`character_emotion`、`save_temp`和`stream`，具体解释见下方POST。
#### 示例
```
http://127.0.0.1:5000/tts?cha_name=胡桃&text=%E8%BF%99%E6%98%AF%E4%B8%80%E6%AE%B5%E5%AE%9E%E4%BE%8B%E9%9F%B3%E9%A2%91
```
### POST方法
#### json包格式
##### 所有参数
```json
{
    "method": "POST",
    "body": {
        "cha_name": "${chaName}",
        "character_emotion": "${characterEmotion}",
        "text": "${speakText}",
        "text_language": "${textLanguage}",
        "top_k": "${topK}",
        "top_p": "${topP}",
        "temperature": "${temperature}",
        "save_temp": "${saveTemp}",
        "stream": "${stream}"
    }
}

```
可省略一项或多项
##### 最少数据：
```json
{
    "method": "POST",
    "body": {
        "cha_name": "${chaName}",
        "text": "${speakText}"
    }
}

```
##### 参数解释

- **text**：要转换的文本，建议进行URL编码。
- **cha_name**：角色文件夹名称，注意大小写、全半角、语言。
- **character_emotion**：角色情感，需为角色实际支持的情感，否则将调用默认情感。
- **text_language**：文本语言（中文、英文、日文、中英混合、日英混合、多语种混合），默认为多语种混合。
- **top_k**、**top_p**、**temperature**：GPT模型参数，不了解时无需修改。
- **save_temp**：是否保存临时文件，为true时，后端会保存生成的音频，下次相同请求会直接返回该数据，默认为false。
- **stream**：是否流式传输，为true时，会按句返回音频，默认为false。
### 示例：
```
{
    "method": "POST",
    "body": {
        "cha_name": "胡桃",
        "character_emotion": "default",
        "text": "%E8%BF%99%E6%98%AF%E4%B8%80%E6%AE%B5%E5%AE%9E%E4%BE%8B%E9%9F%B3%E9%A2%91",
        "text_language": "多语种混合"
    }
}
```

### 使用说明

- 对于text参数，建议在传输前进行URL编码，以避免特殊字符导致的请求错误。
- 选择正确的cha_name和character_emotion对于生成期望的音频非常重要。
- 当save_temp设置为true时，可减少重复请求的处理时间。
- stream选项适用于需要实时播放音频的场景。
