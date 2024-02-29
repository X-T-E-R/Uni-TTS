import soundfile as sf
from flask import Flask, request, Response, jsonify
import io, os
import urllib.parse,sys

# 将当前文件所在的目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from load_infer_info import load_character, character_name, get_wav_from_text_api, models_path, update_character_info

app = Flask(__name__)


@app.route('/character_list', methods=['GET'])
def character_list():
    return jsonify(update_character_info()['characters_and_emotions'])

@app.route('/tts', methods=['GET', 'POST'])
def tts():
    global character_name
    global models_path

    # 尝试从JSON中获取数据，如果不是JSON，则从查询参数中获取
    if request.is_json:
        data = request.json
    else:
        data = request.args

    text = urllib.parse.unquote(data.get('text', ''))
    cha_name = data.get('cha_name', None)

    # 构建期望的目录路径
    expected_path = os.path.join(models_path, cha_name) if cha_name else None

    # 检查是否提供了cha_name，且与当前全局变量不同，以及路径是否存在
    if cha_name and cha_name != character_name and expected_path and os.path.exists(expected_path):
        character_name = cha_name  # 更新全局变量
        print(f"Loading character {character_name}")
        load_character(character_name)  # 加载新角色
    elif expected_path and not os.path.exists(expected_path):
        return jsonify({"error": f"Directory {expected_path} does not exist. Using the current character."}), 400

    text_language = data.get('text_language', '多语种混合')
     # 强制转换为适当的类型
    try:
        top_k = int(data.get('top_k', 6))
        top_p = float(data.get('top_p', 0.8))
        temperature = float(data.get('temperature', 0.8))
    except ValueError:
        return jsonify({"error": "Invalid parameters for top_k, top_p, or temperature. They must be numbers."}), 400
    character_emotion = data.get('character_emotion', 'default')
    sample_rate, audio_data = get_wav_from_text_api(text, text_language, top_k=top_k, top_p=top_p, temperature=temperature, character_emotion=character_emotion)
    # 将音频数据转换为二进制流
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, sample_rate, format='WAV')
    buffer.seek(0)
    return Response(buffer.getvalue(), mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')