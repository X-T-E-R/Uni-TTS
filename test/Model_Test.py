import requests, json, os
from string import Template
from urllib.parse import quote
import time

def send_request(endpoint, endpoint_data, text, cha_name, character_emotion, text_language, top_k=6, top_p=0.8, temperature=0.8):
    urlencoded_text = requests.utils.quote(text)

    # 使用Template填充变量
    endpoint_template = Template(endpoint)
    final_endpoint = endpoint_template.substitute(chaName=cha_name, speakText=urlencoded_text,textLanguage=text_language, topK=top_k, topP=top_p, temperature=temperature, characterEmotion=character_emotion)

    endpoint_data_template = Template(endpoint_data)
    filled_json_str = endpoint_data_template.substitute(chaName=cha_name, speakText=urlencoded_text,textLanguage=text_language, topK=top_k, topP=top_p, temperature=temperature, characterEmotion=character_emotion)
    # 解析填充后的JSON字符串
    request_data = json.loads(filled_json_str)
    body = request_data["body"]

    # 发送POST请求
    response = requests.post(final_endpoint, json=body)

    # 检查请求是否成功
    if response.status_code == 200:
    # 生成保存路径
        
        save_path = f"tmp_audio/{cha_name}/{quote(character_emotion)}.wav"

        # 检查保存路径是否存在
        if not os.path.exists(f"tmp_audio/{cha_name}/"):
            os.makedirs(f"tmp_audio/{cha_name}/")

        # 保存音频文件到本地
        with open(save_path, "wb") as f:
            f.write(response.content)

       
            
       
    else:
        print(f"请求失败，状态码：{response.status_code}")


global models_path
models_path = r"D:\123pan\Downloads\准备重新封包"

def load_info_config(character_name):
    emotion_options = ["default"]
    try:
        with open(f"{models_path}/{character_name}/infer_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        emotion_list=config.get('emotion_list', None)
        if emotion_list is not None:
            emotion_options = []
            for emotion, details in emotion_list.items():
                emotion_options.append(emotion)
    except:
        pass
    return emotion_options


default_endpoint = "http://127.0.0.1:5000/tts"
default_endpoint_data = """{
    "method": "POST",
    "body": {
        "cha_name": "${chaName}",
        "character_emotion": "${characterEmotion}",
        "text": "${speakText}",
        "text_language": "${textLanguage}",
        "top_k": ${topK},
        "top_p": ${topP},
        "temperature": ${temperature}
    }
}
"""
default_text="""
 我可太激动了！跑近一看，居然是一群小动物组成的戏团！牵着火焰小马的猴子、指挥戏团的兔子、双脚站立不停跳舞的大猫…
它们唱唱跳跳地
带我走出了森林，还让我务必收下这个面具！它们说，这个就是他们看到我时的样子！但你看，这面具明明是只狐狸，怎么可能是我呢？"""

character_name = "花火"

emotion_options = load_info_config(character_name)


for emotion in emotion_options:
    print(emotion)
    send_request(default_endpoint, default_endpoint_data, default_text, character_name, emotion, "多语种混合")
    time.sleep(20)
    