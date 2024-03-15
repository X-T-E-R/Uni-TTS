backend_version = "2.2.3 240316"
print(f"Backend version: {backend_version}")

# 在开头加入路径
import os, sys
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))

import soundfile as sf
from flask import Flask, request, Response, jsonify, stream_with_context,send_file
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS
import io
import urllib.parse
import tempfile
import hashlib, json

# 将当前文件所在的目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 从配置文件读取配置
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
enable_auth = False
USERS = {}

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = json.load(f)
        tts_port = _config.get("tts_port", 5000)
        default_batch_size = _config.get("batch_size", 1)
        default_word_count = _config.get("max_word_count", 50)
        enable_auth = _config.get("enable_auth", "false").lower() == "true"
        is_classic = _config.get("classic_inference", "false").lower() == "true"
        if enable_auth:
            print("启用了身份验证")
            USERS = _config.get("user", {})

try:
    from TTS_infer_pack.TTS import TTS
except ImportError:
    is_classic = True

if not is_classic:
    from load_infer_info import load_character, character_name, get_wav_from_text_api, models_path, update_character_info
else:
    from classic_inference.classic_load_infer_info import load_character, character_name, get_wav_from_text_api, models_path, update_character_info

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


# 存储临时文件的字典
temp_files = {}

# 用于防止重复请求
def generate_file_hash(*args):
    """生成基于输入参数的哈希值，用于唯一标识一个请求"""
    hash_object = hashlib.md5()
    for arg in args:
        hash_object.update(str(arg).encode())
    return hash_object.hexdigest()



auth = HTTPBasicAuth()
CORS(app, resources={r"/*": {"origins": "*"}})

@auth.verify_password
def verify_password(username, password):
    if not enable_auth:
        return True  # 如果没有启用验证，则允许访问
    return USERS.get(username) == password


@app.route('/character_list', methods=['GET'])
@auth.login_required
def character_list():
    res = jsonify(update_character_info()['characters_and_emotions'])
    return res


@app.route('/tts', methods=['GET', 'POST'])
@auth.login_required
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
    expected_path = os.path.join(models_path, cha_name) if cha_name else None

    # 检查cha_name和路径
    if cha_name and cha_name != character_name and expected_path and os.path.exists(expected_path):
        character_name = cha_name
        print(f"Loading character {character_name}")
        load_character(character_name)  
    elif expected_path and not os.path.exists(expected_path):
        return jsonify({"error": f"Directory {expected_path} does not exist. Using the current character."}), 400

    text_language = str(data.get('text_language', '多语种混合')).lower()
    try:
        batch_size = int(data.get('batch_size', default_batch_size))
        speed_factor = float(data.get('speed', 1.0))
        top_k = int(data.get('top_k', 6))
        top_p = float(data.get('top_p', 0.8))
        temperature = float(data.get('temperature', 0.8))
        seed = int(data.get('seed', -1))
    except ValueError:
        return jsonify({"error": "Invalid parameters. They must be numbers."}), 400
    stream = str(data.get('stream', 'False')).lower() in ('true', '1', 't', 'y', 'yes')
    save_temp = str(data.get('save_temp', 'False')).lower() in ('true', '1', 't', 'y', 'yes')
    cut_method = str(data.get('cut_method', 'auto_cut')).lower()
    character_emotion = data.get('character_emotion', 'default')

    if cut_method == "auto_cut":
        cut_method = f"auto_cut_{default_word_count}"
    
    params = {
        "text": text,
        "text_language": text_language,
        
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "character_emotion": character_emotion,
        "cut_method": cut_method,
        "stream": stream
    }
    # 如果不是经典模式，则添加额外的参数
    if not is_classic:
        params["batch_size"] = batch_size
        params["speed_factor"] = speed_factor
        params["seed"] = seed
    request_hash = generate_file_hash(text, text_language, top_k, top_p, temperature, character_emotion, character_name, seed)
    
    format = data.get('format', 'wav')
    if not format in ['wav', 'mp3', 'ogg']:
        return jsonify({"error": "Invalid format. It must be one of 'wav', 'mp3', or 'ogg'."}), 400
    
   
    if stream == False:
        if save_temp:
            if request_hash in temp_files:
                return send_file(temp_files[request_hash], mimetype=f'audio/{format}')
            else:
                gen = get_wav_from_text_api(**params)
                sampling_rate, audio_data = next(gen)
                temp_file_path = tempfile.mktemp(suffix=f'.{format}')
                with open(temp_file_path, 'wb') as temp_file:
                    sf.write(temp_file, audio_data, sampling_rate, format=format)
                temp_files[request_hash] = temp_file_path
                return send_file(temp_file_path, mimetype=f'audio/{format}')
        else:
            gen = get_wav_from_text_api(**params)
            sampling_rate, audio_data = next(gen)
            wav = io.BytesIO()
            sf.write(wav, audio_data, sampling_rate, format=format)
            wav.seek(0)
            return Response(wav, mimetype=f'audio/{format}')
    else:
        gen = get_wav_from_text_api(**params)
        return Response(stream_with_context(gen),  mimetype='audio/wav')


if __name__ == '__main__':
    app.run( host='0.0.0.0', port=tts_port)
