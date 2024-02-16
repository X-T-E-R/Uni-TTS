import gradio as gr
import requests
import os

# 定义向TTS服务发送请求的函数
def get_tts_audio(text):
    if not text:  # 检查文本是否为空
        return "文本不能为空，请输入有效文本。", None
    response = requests.post("http://localhost:5000/tts", json={
        "cha_name": "hutao",  # 根据实际情况修改
        "text": text
    })
    if response.status_code == 200:
        # 将接收到的音频数据保存到本地文件
        audio_file_path = f"audio_{os.urandom(6).hex()}.wav"  # 生成一个随机文件名
        with open(audio_file_path, 'wb') as audio_file:
            audio_file.write(response.content)
        return None, audio_file_path
    else:
        return f"Error: 请求失败，状态码 {response.status_code}", None

# 创建Gradio界面
def create_interface():
    with gr.Blocks() as demo:
        gr.Markdown("### TTS客户端")
        # 创建多个文本框和对应的按钮
        for i in range(3):  # 示例中创建3个文本框，根据需要调整
            text_input = gr.Textbox(label=f"文本 {i+1}", lines=2)
            button = gr.Button("生成音频")
            audio_output = gr.Audio(label="音频预览", type="filepath")
            error_output = gr.Textbox(visible=False)
            button.click(fn=get_tts_audio, inputs=text_input, outputs=[error_output, audio_output])

    demo.launch()

create_interface()
