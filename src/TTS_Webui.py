from datetime import datetime
import gradio as gr
import json, os
import requests
import numpy as np
from string import Template

def load_character_emotions(character_name,characters_and_emotions):
    emotion_options = ["default"]
    emotion_options = characters_and_emotions.get(character_name, ["default"])
    

            
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


def get_characters_and_emotions(character_list_url):
    try:
        response = requests.get(character_list_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"请求失败，状态码：{response.status_code}")
    except:
        raise Exception("请求失败，请检查URL是否正确")

def change_character_list(character_list_url,cha_name="", auto_emotion=False , character_emotion="default"):
    
    characters_and_emotions={}
    
    try:
        characters_and_emotions = get_characters_and_emotions(character_list_url)
        character_names = [i for i in characters_and_emotions]
        if len(character_names)!=0:
            if cha_name in character_names:
                character_name_value = cha_name
            else:
                character_name_value = character_names[0]
        else:
            character_name_value = ""
        emotions=characters_and_emotions.get(character_name_value, ["default"])
        emotion_value = character_emotion
        if auto_emotion==False and emotion_value not in emotions:
            emotion_value = "default"
    except:
        character_names = []
        character_name_value = ""
        emotions = ["default"]
        emotion_value = "default"
        characters_and_emotions={}
    if auto_emotion:
            return gr.Dropdown(character_names,value=character_name_value,label="选择角色"),gr.Checkbox(auto_emotion,label="是否自动匹配情感"), gr.Dropdown(["auto"], value="auto", label="情感列表",interactive=False),characters_and_emotions
    return gr.Dropdown(character_names,value=character_name_value,label="选择角色"),gr.Checkbox(auto_emotion,label="是否自动匹配情感"), gr.Dropdown(emotions, value=emotion_value, label="情感列表",interactive=True),characters_and_emotions

def change_endpoint(endpoint):
    return gr.Textbox(endpoint.rsplit('/', 1)[0] + "/character_list")


tts_port = 5000

# 取得模型文件夹路径
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = json.load(f)
        tts_port = _config.get("tts_port", 5000)

default_character_info_url = f"http://127.0.0.1:{tts_port}/character_list"
default_endpoint = f"http://127.0.0.1:{tts_port}/tts"
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
    
    gr.HTML("""<p>这是一个专为TTS（文本转语音）服务的前端项目，基于GPT-soVITS项目进行推理特化。</p>
            <p>使用前，请确认后端服务已启动。</p>
            <p>吞字漏字属于正常现象，太严重可通过换行或加句号解决。</p>
            <p>若有疑问或需要进一步了解，可参考文档：<a href="https://www.yuque.com/xter/zibxlp">点击查看详细文档</a>。</p>""")
    with gr.Row():
        text = gr.Textbox(value=default_text, label="输入文本",interactive=True,lines=8)
    with gr.Row():
        with gr.Column(scale=2):
            character_list_url = gr.Textbox(value=default_character_info_url, label="人物情感列表网址（改右侧的Endpoint会相应的变化）",interactive=False)
            
            text_language = gr.Dropdown(["多语种混合", "中文", "英文","日文","中英混合","日英混合"], value="多语种混合", label="文本语言")
            
            cha_name, auto_emotion_checkbox , character_emotion, characters_and_emotions_ = change_character_list(default_character_info_url)
            characters_and_emotions = gr.State(characters_and_emotions_)
            scan_character_list = gr.Button("重新扫描人物列表",variant="secondary")
            cha_name.change(load_character_emotions, inputs=[cha_name,characters_and_emotions],outputs=[character_emotion])
            character_list_url.change(change_character_list, inputs=[character_list_url,cha_name, auto_emotion_checkbox , character_emotion],outputs=[cha_name, auto_emotion_checkbox , character_emotion, characters_and_emotions])
            scan_character_list.click(change_character_list, inputs=[character_list_url,cha_name, auto_emotion_checkbox , character_emotion],outputs=[cha_name, auto_emotion_checkbox , character_emotion, characters_and_emotions])
            auto_emotion_checkbox.input(change_character_list, inputs=[character_list_url,cha_name, auto_emotion_checkbox , character_emotion],outputs=[cha_name, auto_emotion_checkbox , character_emotion, characters_and_emotions])
        with gr.Column(scale=1):    
            top_k = gr.Slider(minimum=1, maximum=30, value=6, label="Top K",step=1)
            top_p = gr.Slider(minimum=0, maximum=1, value=0.8, label="Top P")
            temperature = gr.Slider(minimum=0, maximum=1, value=0.8, label="Temperature")
        with gr.Column(scale=2):
            endpoint = gr.Textbox(value=default_endpoint, label="Endpoint")
            endpoint_data = gr.Textbox(value=default_endpoint_data, label="发送json格式")
            endpoint.blur(change_endpoint, inputs=[endpoint],outputs=[character_list_url])
    with gr.Row():
        sendData = gr.Button("发送请求",variant="primary")
        audioRecieve = gr.Audio(None, label="音频输出",type="filepath")
        sendData.click(send_request, inputs=[endpoint, endpoint_data, text, cha_name, text_language, top_k, top_p, temperature, character_emotion], outputs=[audioRecieve])
    

app.launch(server_port=9867, show_error=True)