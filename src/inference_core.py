import os, sys
now_dir = os.getcwd()
sys.path.append(now_dir)
sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))

import os, re, logging, json
logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)
import pdb
import torch


if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]

is_half = eval(os.environ.get("is_half", "True"))


from TTS_infer_pack.TTS import TTS, TTS_Config


os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'  # 确保直接启动推理UI时也能够设置。

if torch.cuda.is_available():
    device = "cuda"
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
            if device == "cpu":
                is_half = False
        if _config.get("half_precision", "auto") != "auto":
            is_half = _config["half_precision"].lower() == "true"
        locale_language = str(_config.get("locale", "auto"))
        locale_language = None if locale_language.lower() == "auto" else locale_language
        

        
print(f"device: {device}, is_half: {is_half}")

from tools.i18n.i18n import I18nAuto

i18n = I18nAuto(locale_language,os.path.join(os.path.dirname(os.path.dirname(__file__)), "i18n/locale"))


dict_language = {
    "中文": "all_zh",#全部按中文识别
    "英文": "en",#全部按英文识别#######不变
    "日文": "all_ja",#全部按日文识别
    "中英混合": "zh",#按中英混合识别####不变
    "日英混合": "ja",#按日英混合识别####不变
    "多语种混合": "auto",#多语种启动切分识别语种
    "auto": "auto",
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "all_zh": "all_zh",
    "all_ja": "all_ja",
}

tts_config = TTS_Config("")
tts_config.device = device
tts_config.is_half = is_half
tts_pipline = TTS(tts_config)
gpt_path = tts_config.t2s_weights_path
sovits_path = tts_config.vits_weights_path

def inference(text, text_lang, 
              ref_audio_path, prompt_text, 
              prompt_lang, top_k, 
              top_p, temperature, 
              text_split_method, batch_size, 
              speed_factor, ref_text_free,
              split_bucket,
              return_fragment,
              seed
              ):
    try:
        text_lang = dict_language[text_lang.lower()]
        prompt_lang = dict_language[prompt_lang.lower()]
    except:
        text_lang = "auto"
        prompt_lang = "auto"
    inputs={
        "text": text,
        "text_lang": text_lang,
        "ref_audio_path": ref_audio_path,
        "prompt_text": prompt_text if not ref_text_free else "",
        "prompt_lang": prompt_lang,
        "top_k": top_k,
        "top_p": top_p,
        "temperature": temperature,
        "text_split_method": text_split_method,
        "batch_size":int(batch_size),
        "speed_factor":float(speed_factor),
        "split_bucket":split_bucket,
        "return_fragment":return_fragment,
        "seed":seed
    }
    return tts_pipline.run(inputs)

# from https://github.com/RVC-Boss/GPT-SoVITS/pull/448

import tempfile, io, wave
from pydub import AudioSegment

# from https://huggingface.co/spaces/coqui/voice-chat-with-mistral/blob/main/app.py
def wave_header_chunk(frame_input=b"", channels=1, sample_width=2, sample_rate=32000):
    # This will create a wave header then append the frame input
    # It should be first on a streaming wav file
    # Other frames better should not have it (else you will hear some artifacts each chunk start)
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as vfout:
        vfout.setnchannels(channels)
        vfout.setsampwidth(sample_width)
        vfout.setframerate(sample_rate)
        vfout.writeframes(frame_input)

    wav_buf.seek(0)
    return wav_buf.read()


def get_streaming_tts_wav(params):
    chunks = inference(**params)
    byte_stream = True
    if byte_stream:
        yield wave_header_chunk()
        for sr, chunk in chunks:
            if chunk is not None:
                chunk = chunk.tobytes()
                yield chunk
            else:
                print("None chunk")
                pass

    else:
        pass
        # Send chunk files
        # i = 0
        # format = "wav"
        # for chunk in chunks:
        #     i += 1
        #     file = f"{tempfile.gettempdir()}/{i}.{format}"
        #     segment = AudioSegment(chunk, frame_rate=32000, sample_width=2, channels=1)
        #     segment.export(file, format=format)
        #     yield file
