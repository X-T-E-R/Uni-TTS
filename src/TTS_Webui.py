from datetime import datetime
import gradio as gr
import json, os
import requests
import numpy as np
from string import Template


# 取得模型文件夹路径
global models_path
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        models_path = config.get("models_path", "trained")
else:
    models_path = "trained"


def get_character_names():
    trained_folders = [f for f in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, f))]
    return trained_folders

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
            
    return gr.Dropdown(emotion_options, value="default")

def send_request(endpoint, endpoint_data, text, cha_name, text_language, top_k, top_p, temperature, character_emotion):
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
        save_path = f"tmp_audio/{cha_name}{datetime.now().strftime('%Y%m%d%H%M%S%f')}.wav"

        # 检查保存路径是否存在
        if not os.path.exists("tmp_audio"):
            os.makedirs("tmp_audio")

        # 保存音频文件到本地
        with open(save_path, "wb") as f:
            f.write(response.content)

        # 返回给gradio
        return gr.Audio(save_path, type="filepath")
            
       
    else:
        print(f"请求失败，状态码：{response.status_code}")


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
default_text="我是一个粉刷匠，粉刷本领强。我要把那新房子，刷得更漂亮。刷了房顶又刷墙，刷子像飞一样。哎呀我的小鼻子，变呀变了样。"

with gr.Blocks() as app:
    with gr.Row():
        text = gr.Textbox(value=default_text, label="输入文本",interactive=True,lines=8)
    with gr.Row():
        with gr.Column(scale=2):
            text_language = gr.Dropdown(["多语种混合", "中文", "英文","日文","中英混合","中日混合"], value="多语种混合", label="文本语言")
            character_names=get_character_names()
            cha_name = gr.Dropdown(character_names,value=character_names[0], label="选择角色")
            character_emotion = gr.Dropdown(["default"], value="default", label="情感列表",interactive=True)  
            cha_name.input(load_info_config, inputs=[cha_name],outputs=[character_emotion])
        with gr.Column(scale=1):    
            top_k = gr.Slider(minimum=1, maximum=30, value=6, label="Top K",step=1)
            top_p = gr.Slider(minimum=0, maximum=1, value=0.8, label="Top P")
            temperature = gr.Slider(minimum=0, maximum=1, value=0.8, label="Temperature")
        with gr.Column(scale=2):
            endpoint = gr.Textbox(value=default_endpoint, label="Endpoint")
            endpoint_data = gr.Textbox(value=default_endpoint_data, label="发送json格式")
    with gr.Row():
        sendData = gr.Button("发送请求",variant="primary")
        audioRecieve = gr.Audio(None, label="音频输出",type="filepath")
        sendData.click(send_request, inputs=[endpoint, endpoint_data, text, cha_name, text_language, top_k, top_p, temperature, character_emotion], outputs=[audioRecieve])

app.launch(server_port=9867, show_error=True)