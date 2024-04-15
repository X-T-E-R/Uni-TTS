
import os, json, sys
sys.path.append(".")

from uuid import uuid4
from typing import List, Dict, Literal
import urllib.parse
import hashlib


def get_params_config():
    try:
        with open(os.path.join("configs/gsv_fast", "params_config.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        raise FileNotFoundError("params_config.json not found.")
    
params_config = get_params_config()

from Adapters.base import Base_TTS_Task

class GSV_TTS_Task(Base_TTS_Task):
    
    def __init__(self, other_task=None):
        super().__init__(other_task)
        
        self.params_config:dict = params_config
        self.disabled_features: List[str] = []
        
        self.character: str = self.params_config["character"]["default"] if other_task is None else other_task.character
        self.emotion: str = self.params_config["emotion"]["default"] if other_task is None else other_task.emotion
        self.text_language: str = self.params_config["text_language"]["default"] if other_task is None else other_task.text_language
        self.speaker_id: int = self.params_config["speaker_id"]["default"] if other_task is None else other_task.speaker_id
        self.batch_size: int = self.params_config["batch_size"]["default"] if other_task is None else other_task.batch_size
        self.top_k: int = self.params_config["top_k"]["default"] if other_task is None else other_task.top_k
        self.top_p: float = self.params_config["top_p"]["default"] if other_task is None else other_task.top_p
        self.temperature: float = self.params_config["temperature"]["default"] if other_task is None else other_task.temperature
        self.cut_method: str = self.params_config["cut_method"]["default"] if other_task is None else other_task.cut_method
        self.seed: int = self.params_config["seed"]["default"] if other_task is None else other_task.seed
        
        # 通用属性
        self.sample_rate: int = 32000 # 采样率, gsv底模为32000, 因此只能是32000
        self.format: str = self.params_config["format"]["default"] if other_task is None else other_task.format
        self.stream: bool = self.params_config["stream"]["default"] if other_task is None else other_task.stream
        self.loudness: float = self.params_config["loudness"]["default"] if other_task is None else other_task.loudness
        self.speed: float = self.params_config["speed"]["default"] if other_task is None else other_task.speed
        self.save_temp: bool = self.params_config["save_temp"]["default"] if other_task is None else other_task.save_temp
    
    
    def load_from_dict(self, data: dict={}):
        
        assert self.params_config is not None, "params_config.json not found."
        
        super().load_from_dict(data)
        
        # 参数提取
        if self.task_type == "text":
            self.text = self.get_param_value('text', data).strip()
            
            self.character = self.get_param_value('character', data)
            self.speaker_id = self.get_param_value('speaker_id', data)

            self.text_language = self.get_param_value('text_language', data)
            self.batch_size = self.get_param_value('batch_size', data)
            self.speed = self.get_param_value('speed', data)
            self.top_k = self.get_param_value('top_k', data)
            self.top_p = self.get_param_value('top_p', data)
            self.temperature = self.get_param_value('temperature', data)
            self.seed = self.get_param_value('seed', data)

            self.emotion = self.get_param_value('emotion', data)
            self.cut_method = self.get_param_value('cut_method', data)
            if self.cut_method == "auto_cut":
                self.cut_method = f"auto_cut_100"
        else:
            self.ssml = self.get_param_value('ssml', data).strip()

        
    def md5(self):
        m = hashlib.md5()
        if self.task_type == "audio":
            m.update(self.src.encode())
        elif self.task_type == "ssml":
            m.update(self.ssml.encode())
        elif self.task_type == "text":
            m.update(self.variation.encode())
            m.update(self.text.encode())
            m.update(self.text_language.encode())
            m.update(self.character.encode())
            m.update(str(self.speaker_id).encode())
            m.update(str(self.speed).encode())
            m.update(str(self.top_k).encode())
            m.update(str(self.top_p).encode())
            m.update(str(self.temperature).encode())
            m.update(str(self.cut_method).encode())
            m.update(str(self.emotion).encode())
        return m.hexdigest()
    
    def updateVariation(self):
        self.variation = str(uuid4())
        
    def to_dict(self):
        return {
            "text": self.text,
            "text_language": self.text_language,
            "character_emotion": self.emotion,
            "batch_size": self.batch_size,
            "speed": self.speed,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "cut_method": self.cut_method,
            "format": self.format,
            "seed": self.seed,
            
            "stream": self.stream,
            "loudness": self.loudness,
            "save_temp": self.save_temp,
            
        }
        
    def __str__(self):
        character = self.character
        json_content = json.dumps(self.to_dict(), ensure_ascii=False)  # ensure_ascii=False to properly display non-ASCII characters
        return f"----------------TTS Task--------------\ncharacter: {character}, content: {json_content}\n--------------------------------------"


if __name__ == "__main__":
    sys.path.append(".")
    task = GSV_TTS_Task()
    print(task)