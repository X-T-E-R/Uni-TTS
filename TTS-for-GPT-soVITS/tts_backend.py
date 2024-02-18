import soundfile as sf
from flask import Flask, request, Response, jsonify
import io, os
import urllib.parse,sys

# 将当前文件所在的目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from character_manage import load_character, character_name, get_wav_from_text_api

app = Flask(__name__)


@app.route('/tts', methods=['POST'])
def tts():
    global character_name
    if request.is_json:
        # 使用 request.json 来访问 JSON 数据
        data = request.json

        text = urllib.parse.unquote(data.get('text', ''))
        cha_name = data.get('cha_name', None)

        # 构建期望的目录路径
        expected_path = f"./trained/{cha_name}/" if cha_name else None

        # 检查是否提供了cha_name，且与当前全局变量不同，以及路径是否存在
        if cha_name and cha_name != character_name and expected_path and os.path.exists(expected_path):
            character_name = cha_name  # 更新全局变量
            load_character(character_name)  # 加载新角色
        elif expected_path and not os.path.exists(expected_path):
            return jsonify({"error": f"Directory {expected_path} does not exist. Using the current character."}), 400

        text_language = data.get('text_language', '多语种混合')
        top_k = data.get('top_k', 3)
        top_p = data.get('top_p', 0.6)
        temperature = data.get('temperature', 0.6)
        sample_rate, audio_data = get_wav_from_text_api(text,text_language, top_k=top_k, top_p=top_p, temperature=temperature)
                # 将音频数据转换为二进制流
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format='WAV')
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype='audio/wav')
    else:
        return jsonify({"error": "Request must be JSON"}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')