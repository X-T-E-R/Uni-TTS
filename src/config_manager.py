__version__ = "2.4.3 240414"

import os,  json
import torch

import logging
logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)

class Inference_Config():
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
        self.models_path = "trained"
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config:dict = json.load(f)
                self.workers = config.get("workers", 10)
                self.models_path = config.get("models_path", "trained")
                self.tts_host = config.get("tts_host", "0.0.0.0")
                self.tts_port = config.get("tts_port", 5000)
                self.default_batch_size = config.get("batch_size", 1)
                self.default_word_count = config.get("max_word_count", 50)
                self.enable_auth = config.get("enable_auth", "false").lower() == "true"
                self.is_classic = config.get("classic_inference", "false").lower() == "true"
                self.is_share = config.get("is_share", "false").lower() == "true"
                self.max_text_length = config.get("max_text_length", -1)
                self.disabled_features = config.get("disabled_features", [])
                self.allowed_adapters = config.get("allowed_adapters", ["gsv_fast", "gsv_classic", "azure"])
                self.save_prompt_cache = config.get("save_prompt_cache", "false").lower() == "true"
                locale_language = str(config.get("locale", "auto"))
                self.locale_language = None if locale_language.lower() == "auto" else locale_language
                if self.enable_auth:
                    self.users = config.get("user", {})

global inference_config
inference_config = Inference_Config()

models_path = inference_config.models_path

def load_infer_config(character_path):
    config_path = os.path.join(character_path, "infer_config.json")
    """加载环境配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def auto_generate_infer_config(character_path):
    ## TODO: Auto-generate wav-list and prompt-list from character_path
    ##     
    # Initialize variables for file detection

    print(f"正在自动生成配置文件: {character_path}")
    ckpt_file_found = None
    pth_file_found = None
    wav_file_found = None

    # Iterate through files in character_path to find matching file types
    for dirpath, dirnames, filenames in os.walk(character_path):
        for file in filenames:
            # 构建文件的完整路径
            full_path = os.path.join(dirpath, file)
            # 从full_path中移除character_path部分
            relative_path = remove_character_path(full_path,character_path)
            # 根据文件扩展名和变量是否已赋值来更新变量
            if file.lower().endswith(".ckpt") and ckpt_file_found is None:
                ckpt_file_found = relative_path
            elif file.lower().endswith(".pth") and pth_file_found is None:
                pth_file_found = relative_path
            elif file.lower().endswith(".wav") and wav_file_found is None:
                wav_file_found = relative_path
            elif file.lower().endswith(".mp3"):
                import pydub
                # Convert mp3 to wav
                wav_file_path = os.path.join(dirpath,os.path.splitext(file)[0] + ".wav")


                pydub.AudioSegment.from_mp3(full_path).export(wav_file_path, format="wav")
                if wav_file_found is None:
                    wav_file_found = remove_character_path(os.path.join(dirpath,os.path.splitext(file)[0] + ".wav"),character_path)
                    

    # Initialize infer_config with gpt_path and sovits_path regardless of wav_file_found
    infer_config = {
        "gpt_path": ckpt_file_found,
        "sovits_path": pth_file_found,
        "software_version": "1.1",
        r"简介": r"这是一个配置文件适用于https://github.com/X-T-E-R/TTS-for-GPT-soVITS，是一个简单好用的前后端项目"
    }

    # If wav file is also found, update infer_config to include ref_wav_path, prompt_text, and prompt_language
    if wav_file_found:
        wav_file_name = os.path.splitext(os.path.basename(wav_file_found))[0]  # Extract the filename without extension
        infer_config["emotion_list"] = {
            "default": {
                "ref_wav_path": wav_file_found,
                "prompt_text": wav_file_name,
                "prompt_language": "多语种混合"
            }
        }
    else:
        raise Exception("找不到wav参考文件！请把有效wav文件放置在模型文件夹下。")
        pass
    # Check if the essential model files were found
    if ckpt_file_found and pth_file_found:
        infer_config_path = os.path.join(character_path, "infer_config.json")
        try:
            with open(infer_config_path , 'w', encoding='utf-8') as f:
                json.dump(infer_config, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"无法写入文件: {infer_config_path}. 错误: {e}")

        return infer_config_path
    else:
        return "Required model files (.ckpt or .pth) not found in character_path directory."

def update_character_info(models_path:str=None):
    # try:
    #     with open(os.path.join(models_path, "character_info.json"), "r", encoding='utf-8') as f:
    #         default_character = json.load(f).get("deflaut_character", None)
    # except:
    if models_path in [None, ""]:
        models_path = inference_config.models_path
    default_character = ""
    characters_and_emotions = {}
    for character_subdir in [f for f in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, f))]:
        character_subdir = character_subdir
        if os.path.exists(os.path.join(models_path, character_subdir, "infer_config.json")):
            try:
                with open(os.path.join(models_path, character_subdir, "infer_config.json"), "r", encoding='utf-8') as f:
                    config = json.load(f)
                    emotion_list=[emotion for emotion in config.get('emotion_list', None)]
                    if emotion_list is not None:
                        characters_and_emotions[character_subdir] = emotion_list
                    else:
                        characters_and_emotions[character_subdir] = ["default"]
            except:
                characters_and_emotions[character_subdir] = ["default"]
        else:
            characters_and_emotions[character_subdir] = ["default"]

    return {"deflaut_character": default_character, "characters_and_emotions": characters_and_emotions}

def test_fp16_computation():
    # 检查CUDA是否可用
    if not torch.cuda.is_available():
        return False, "CUDA is not available. Please check your installation."

    try:
        # 创建一个简单的半精度张量计算任务
        # 例如，执行一个半精度的矩阵乘法
        a = torch.randn(3, 3, dtype=torch.float16).cuda()  # 将张量a转换为半精度并移动到GPU
        b = torch.randn(3, 3, dtype=torch.float16).cuda()  # 将张量b转换为半精度并移动到GPU
        c = torch.matmul(a, b)  # 执行半精度的矩阵乘法
        # 如果没有发生错误，我们认为GPU支持半精度运算
        return True, "Your GPU supports FP16 computation."
    except Exception as e:
        # 如果执行过程中发生异常，我们认为GPU不支持半精度运算
        return False, f"Your GPU does not support FP16 computation. Error: {e}"


def get_device_info():
    global device, is_half
    try:
        return device, is_half
    except:
        if torch.cuda.is_available():
            device = "cuda"
            is_half = True
        else:
            device = "cpu"
            is_half = False

        # 取得模型文件夹路径
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                _config = json.load(f)
                if _config.get("device", "auto") != "auto":
                    device = _config["device"]
                    is_half = (device == "cpu")
                if _config.get("half_precision", "auto") != "auto":
                    is_half = _config["half_precision"].lower() == "true"

        supports_fp16, message = test_fp16_computation()
        if not supports_fp16 and is_half:
            is_half = False
            print(message)

        return device, is_half


def get_params_config():
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "params_config.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        raise FileNotFoundError("params_config.json not found.")
    
    
global params_config
params_config = get_params_config()

def get_deflaut_character_name(models_path:str=None):
    global default_character
    try:
        return default_character
    except:
        
        default_character = params_config["character"]["default"]

        if default_character in ["", None, "default"]:
            default_character=None
            
        if default_character is None:
            characters_and_emotions = update_character_info(models_path)["characters_and_emotions"]
            default_character = list(characters_and_emotions.keys())[0]

        return default_character

def remove_character_path(full_path,character_path):
    # 从full_path中移除character_path部分
    return os.path.relpath(full_path, character_path)
