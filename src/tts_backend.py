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

params_config = {}

def get_params_config():
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "params_config.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        raise FileNotFoundError("params_config.json not found.")
        
params_config = get_params_config()        
            

@app.route('/tts', methods=['GET', 'POST'])
@app.route('/voice/vits', methods=['GET', 'POST'])
@app.route('/text2audio', methods=['GET', 'POST'])
@app.route('/t2s', methods=['GET', 'POST'])
@auth.login_required
def tts():
    global character_name
    global models_path

    def get_param_value(param_config):
        for alias in param_config['alias']:
            if alias in data:
                if param_config['type'] == 'int':
                    return int(data[alias])
                elif param_config['type'] == 'float':
                    return float(data[alias])
                elif param_config['type'] == 'bool':
                    return str(data[alias]).lower() in ('true', '1', 't', 'y', 'yes', "allow", "allowed")
                else:  # 默认为字符串
                    return urllib.parse.unquote(data[alias]).lower()
        return param_config['default']
    # 尝试从JSON中获取数据，如果不是JSON，则从查询参数中获取
    if request.is_json:
        data = request.json
    else:
        data = request.args
        
    if params_config is None:
        raise FileNotFoundError("params_config.json not found.")
    
    # 参数提取
    text = get_param_value(params_config['text'])
    
    cha_name = get_param_value(params_config['cha_name'])
    expected_path = os.path.join(models_path, cha_name) if cha_name else None

    # 检查cha_name和路径
    if cha_name and cha_name != character_name and expected_path and os.path.exists(expected_path):
        character_name = cha_name
        print(f"Loading character {character_name}")
        load_character(character_name)  
    elif expected_path and not os.path.exists(expected_path):
        return jsonify({"error": f"Directory {expected_path} does not exist. Using the current character."}), 400

    text_language = get_param_value(params_config['text_language'])
    batch_size = get_param_value(params_config['batch_size'])
    speed = get_param_value(params_config['speed'])
    top_k = get_param_value(params_config['top_k'])
    top_p = get_param_value(params_config['top_p'])
    temperature = get_param_value(params_config['temperature'])
    seed = get_param_value(params_config['seed'])
    stream = get_param_value(params_config['stream'])
    save_temp = get_param_value(params_config['save_temp'])
    cut_method = get_param_value(params_config['cut_method'])
    character_emotion = get_param_value(params_config['character_emotion'])
    format = get_param_value(params_config['format'])
    
   
    # 下面是已经获得了参数后进行的操作
    if cut_method == "auto_cut":
        cut_method = f"auto_cut_{default_word_count}"
    text = text.replace("……","。").replace("…","。").replace("\n\n","\n").replace("。\n","\n").replace("\n", "。\n")
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
        params["speed_factor"] = speed
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
