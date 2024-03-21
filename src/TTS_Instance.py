

import io, wave
import os, json, sys
import threading

now_dir = os.getcwd()
sys.path.append(now_dir)
# sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))

from Inference.src.config_manager import load_infer_config, auto_generate_infer_config, models_path, get_device_info, get_deflaut_character_name
        

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

class TTS_instance:
    def __init__(self, character_name = None):
        tts_config = TTS_Config("")
        tts_config.device , tts_config.is_half = get_device_info()
        self.tts_pipline = TTS(tts_config)
        if character_name is None:
            character_name = get_deflaut_character_name()
        self.character = None
        self.lock = threading.Lock()
        self.load_character(character_name)
        
        
    def inference(self, text, text_lang, 
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
        for sr, chunk in chunks:
            if chunk is not None:
                chunk = chunk.tobytes()
                yield chunk
            else:
                print("None chunk")
                pass

    def load_character(self, cha_name):
        if cha_name in ["", None]:
            return
        if self.character is not None:
            if type(cha_name) != str:
                raise Exception(f"The type of character name should be str, but got {type(cha_name)}")
            if self.character.lower() == cha_name.lower():
                return
        character_path=os.path.join(models_path,cha_name)
        if not os.path.exists(character_path):
            raise Exception(f"Can't find character folder: {cha_name}")
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
                self.load_character(cha_name)
                return 
            except:
                # 报错
                raise Exception("找不到模型文件！请把有效模型放置在模型文件夹下，确保其中至少有pth、ckpt和wav三种文件。")
        # 修改权重
        self.character = cha_name
        with self.lock:
            self.tts_pipline.init_t2s_weights(gpt_path)
            self.tts_pipline.init_vits_weights(sovits_path)
            print(f"加载角色成功: {cha_name}")


    def match_character_emotion(self, character_path):
        if not os.path.exists(os.path.join(character_path, "reference_audio")):
            # 如果没有reference_audio文件夹，就返回None
            return None, None, None


    def get_wav_from_text_api(
        self,
        text,
        text_language,
        batch_size=1,
        speed_factor=1.0,
        top_k=12,
        top_p=0.6,
        temperature=0.6,
        character_emotion="default",
        cut_method="auto_cut",
        seed=-1,
        stream=False,
    ):
        
        text = text.replace("\r", "\n").replace("<br>", "\n").replace("\t", " ")
        text = text.replace("……","。").replace("…","。").replace("\n\n","\n").replace("。\n","\n").replace("\n", "。\n")
        # 加载环境配置
        config = load_infer_config(os.path.join(models_path, self.character))

        # 尝试从配置中提取参数，如果找不到则设置为None
        ref_wav_path =  None
        prompt_text = None
        prompt_language = None
        if character_emotion == "auto":
            # 如果是auto模式，那么就自动决定情感
            ref_wav_path, prompt_text, prompt_language = self.match_character_emotion(os.path.join(models_path, self.character))
        if ref_wav_path is None:
            # 未能通过auto匹配到情感，就尝试使用指定的情绪列表
            emotion_list=config.get('emotion_list', None)# 这是新版的infer_config文件，如果出现错误请删除infer_config.json文件，让系统自动生成 
            now_emotion="default"
            for emotion, details in emotion_list.items():
                print(emotion)
                if emotion==character_emotion:
                    now_emotion=character_emotion
                    break
            for emotion, details in emotion_list.items():
                if emotion==now_emotion:
                    ref_wav_path = os.path.join(os.path.join(models_path,self.character), details['ref_wav_path'])
                    prompt_text = details['prompt_text']
                    prompt_language = details['prompt_language']
                    break
            if ref_wav_path is None:
                print("找不到ref_wav_path！请删除infer_config.json文件，让系统自动生成")

        try:
            text_language = dict_language[text_language]
            prompt_language = dict_language[prompt_language]
        except:
            text_language = "auto"
            prompt_language = "auto"
        ref_free = False
        
        params = {
            "text": text,
            "text_lang": text_language,
            "ref_audio_path": ref_wav_path,
            "prompt_text": prompt_text,
            "prompt_lang": prompt_language,
            "top_k": top_k,
            "top_p": top_p,
            "temperature": temperature,
            "text_split_method": cut_method, 
            "batch_size": batch_size,
            "speed_factor": speed_factor,
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



