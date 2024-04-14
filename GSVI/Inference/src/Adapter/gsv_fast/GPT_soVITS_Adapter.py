import io, wave
import os, json, sys
import threading

from Inference.src.TTS_Task import TTS_Task
from .ssml_dealer import SSML_Dealer

import hashlib  

now_dir = os.getcwd()
sys.path.append(now_dir)
# sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))

from Inference.src.config_manager import load_infer_config, auto_generate_infer_config, inference_config, get_device_info, get_deflaut_character_name, params_config, update_character_info
disabled_features = inference_config.disabled_features

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

from GPT_SoVITS.TTS_infer_pack.TTS import TTS, TTS_Config


class GSV_Instance:
    def __init__(self, models_path=None, default_character=None, **kwargs):
        tts_config = TTS_Config("")
        tts_config.device , tts_config.is_half = get_device_info()
        self.tts_pipline = TTS(tts_config)
        self.models_path = models_path if models_path is not None else inference_config.models_path
        if default_character is not None:
            character = default_character
            self.default_character = default_character
        else:
            character = get_deflaut_character_name(self.models_path)
        self.character = None
        self.lock = threading.Lock()
        self.load_character(character)

    def inference(self, text, text_language, 
              ref_audio_path, prompt_text, 
              prompt_lang, top_k, 
              top_p, temperature, 
              text_split_method, batch_size, 
              speed_factor, ref_text_free,
              split_bucket,
              return_fragment,
              seed
              ):

        inputs={
            "text": text,
            "text_lang": text_language,
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
        return self.tts_pipline.run(inputs)

    # from https://github.com/RVC-Boss/GPT-SoVITS/pull/448
    def get_streaming_tts_wav(self, params):
        # from https://huggingface.co/spaces/coqui/voice-chat-with-mistral/blob/main/app.py
        def wave_header_chunk(frame_input=b"", channels=1, sample_width=2, sample_rate=32000):
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, "wb") as vfout:
                vfout.setnchannels(channels)
                vfout.setsampwidth(sample_width)
                vfout.setframerate(sample_rate)
                vfout.writeframes(frame_input)

            wav_buf.seek(0)
            return wav_buf.read()
        chunks = self.tts_pipline.run(params)
        yield wave_header_chunk()
        # chunk is tuple[int, np.ndarray], 代表了sample_rate和音频数据
        for chunk in chunks:
            sample_rate, audio_data = chunk
            if audio_data is not None:
                yield audio_data.tobytes()

    def load_character_id(self, speaker_id):
        character = list(update_character_info()['characters_and_emotions'])[speaker_id]
        return self.load_character(character)

    def load_character(self, character):
        if character in ["", None] and self.character in ["", None]:
            character = get_deflaut_character_name(self.models_path)
        if self.character not in ["", None]:
            if type(character) != str:
                raise Exception(f"The type of character name should be str, but got {type(character)}")
            if self.character.lower() == character.lower():
                return
        character_path=os.path.join(self.models_path, character)
        if not os.path.exists(character_path):
            print(f"找不到角色文件夹: {character}，已自动切换到默认角色")
            character = get_deflaut_character_name(self.models_path)
            return self.load_character(character)
            # raise Exception(f"Can't find character folder: {character}")
        try:
            # 加载配置
            config = load_infer_config(character_path)

            # 尝试从环境变量获取gpt_path，如果未设置，则从配置文件读取
            gpt_path = os.path.join(character_path,config.get("gpt_path"))
            # 尝试从环境变量获取sovits_path，如果未设置，则从配置文件读取
            sovits_path = os.path.join(character_path,config.get("sovits_path"))
        except:
            try:
                # 尝试调用auto_get_infer_config
                auto_generate_infer_config(character_path)
                self.load_character(character)
                return 
            except:
                # 报错
                raise Exception("找不到模型文件！请把有效模型放置在模型文件夹下，确保其中至少有pth、ckpt和wav三种文件。")
        # 修改权重
        self.character = character
        with self.lock:
            self.tts_pipline.init_t2s_weights(gpt_path)
            self.tts_pipline.init_vits_weights(sovits_path)
            print(f"加载角色成功: {character}")

    def match_character_emotion(self, character_path):
        if not os.path.exists(os.path.join(character_path, "reference_audio")):
            # 如果没有reference_audio文件夹，就返回None
            return None, None, None

    def generate_from_text(self, task: TTS_Task):
        character = task.character
        self.load_character(character)
        return self.get_wav_from_text_api(**task.to_dict())

    def generate_from_ssml(self, task: TTS_Task):
        dealer = SSML_Dealer()
        return dealer.generate_from_ssml(task.ssml, self)
    
    def generate(self, task: TTS_Task):
        if task.task_type == "text":
            return self.generate_from_text(task)
        elif task.task_type == "ssml":
            return self.generate_from_ssml(task)

    def get_wav_from_text_api(
        self,
        text,
        text_language="auto",
        batch_size=1,
        speed=1.0,
        top_k=12,
        top_p=0.6,
        temperature=0.6,
        character_emotion="default",
        cut_method="auto_cut",
        seed=-1,
        stream=False,
        **kwargs
    ):

        text = text.replace("\r", "\n").replace("<br>", "\n").replace("\t", " ")
        text = text.replace("……","。").replace("…","。").replace("\n\n","\n").replace("。\n","\n").replace("\n", "。\n")
        # 加载环境配置
        config: dict = load_infer_config(os.path.join(self.models_path, self.character))

        # 尝试从配置中提取参数，如果找不到则设置为None
        relative_path: str = None
        ref_wav_path: str = None
        prompt_text: str = None
        prompt_language: str = None
        if character_emotion == "auto":
            # 如果是auto模式，那么就自动决定情感
            ref_wav_path, prompt_text, prompt_language = self.match_character_emotion(os.path.join(self.models_path, self.character))
        if ref_wav_path is None:
            # 未能通过auto匹配到情感，就尝试使用指定的情绪列表
            emotion_list:dict=config.get('emotion_list', None)# 这是新版的infer_config文件，如果出现错误请删除infer_config.json文件，让系统自动生成 
            now_emotion="default"
            for emotion, details in emotion_list.items():
                print(emotion)
                if emotion==character_emotion:
                    now_emotion=character_emotion
                    break
            for emotion, details in emotion_list.items():
                if emotion==now_emotion:
                    relative_path = details['ref_wav_path']
                    ref_wav_path = os.path.join(os.path.join(self.models_path,self.character), relative_path)
                    prompt_text = details['prompt_text']
                    prompt_language = details['prompt_language']
                    break
            if ref_wav_path is None:
                print("找不到ref_wav_path！请删除infer_config.json文件，让系统自动生成")

        prompt_cache_path = ""
        
        if inference_config.save_prompt_cache:
            md5 = hashlib.md5()
            md5.update(relative_path.encode())
            md5.update(prompt_text.encode())
            md5.update(prompt_language.encode())
            short_md5 = md5.hexdigest()[:8]
            prompt_cache_path = f"cache/prompt_cache/prompt_cache_{short_md5}.pickle"

        try:
            text_language = dict_language[text_language]
            prompt_language = dict_language[prompt_language]
            if "-" in text_language:
                text_language = text_language.split("-")[0]
            if "-" in prompt_language:
                prompt_language = prompt_language.split("-")[0]
        except:
            text_language = "auto"
            prompt_language = "auto"
        ref_free = False

        params = {
            "text": text,
            "text_lang": text_language.lower(),
            "prompt_cache_path": prompt_cache_path,
            "ref_audio_path": ref_wav_path,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_language.lower(),
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": cut_method, 
            "batch_size": batch_size,
            "speed_factor": speed,
            "ref_text_free": ref_free,
            "split_bucket":True,
            "return_fragment":stream,
            "seed": seed,
        }
        # 调用原始的get_tts_wav函数
        # 注意：这里假设get_tts_wav函数及其所需的其它依赖已经定义并可用
        with self.lock:
            if stream == False:
                return self.tts_pipline.run(params)
            else:
                return self.get_streaming_tts_wav(params)
