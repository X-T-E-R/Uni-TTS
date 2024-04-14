
import os, json, sys

from uuid import uuid4
from typing import List, Dict, Literal
import urllib.parse
import hashlib

from Inference.src.config_manager import inference_config,  params_config
disabled_features = inference_config.disabled_features




class TTS_Task:
    # 一个TTS任务可以是三种类型：静态音频、SSML、纯文本
    def __init__(self, other_task=None):
        self.task_type: Literal["audio", "ssml", "text"] = "text"
        self.audio_path: str = ""
        self.uuid: str = str(uuid4())
        
        self.src: str = ""       

        self.ssml: str = ""

        self.text: str = ""
        self.variation: str = None
        
        self.emotion: str = params_config["emotion"]["default"] if other_task is None else other_task.emotion
        self.text_language: str = params_config["text_language"]["default"] if other_task is None else other_task.text_language
        self.character: str = params_config["character"]["default"] if other_task is None else other_task.character
        self.speaker_id: int = params_config["speaker_id"]["default"] if other_task is None else other_task.speaker_id
        self.batch_size: int = params_config["batch_size"]["default"] if other_task is None else other_task.batch_size
        self.top_k: int = params_config["top_k"]["default"] if other_task is None else other_task.top_k
        self.top_p: float = params_config["top_p"]["default"] if other_task is None else other_task.top_p
        self.temperature: float = params_config["temperature"]["default"] if other_task is None else other_task.temperature
        self.cut_method: str = params_config["cut_method"]["default"] if other_task is None else other_task.cut_method
        self.seed: int = params_config["seed"]["default"] if other_task is None else other_task.seed
        
        # 通用属性
        self.format: str = params_config["format"]["default"] if other_task is None else other_task.format
        self.stream: bool = params_config["stream"]["default"] if other_task is None else other_task.stream
        self.save_temp: bool = params_config["save_temp"]["default"] if other_task is None else other_task.save_temp
        self.loudness: float = params_config["loudness"]["default"] if other_task is None else other_task.loudness
        self.speed: float = params_config["speed"]["default"] if other_task is None else other_task.speed
    
    def get_param_value(self, param_name, data, return_default=True, special_dict={}):
        # ban disabled features
        param_config = params_config[param_name]
        if param_name not in disabled_features:
            for alias in param_config['alias']:
                if data.get(alias) is not None:
                    if special_dict.get(data.get(alias)) is not None:
                        return special_dict[data.get(alias)]
                    elif param_config['type'] == 'int':
                        return int(data.get(alias))
                    elif param_config['type'] == 'float':
                        x = data.get(alias)
                        if isinstance(x, str) and x[-1] == "%":
                            return float(x[:-1]) / 100
                        return float(x)
                    elif param_config['type'] == 'bool':
                        return str(data.get(alias)).lower() in ('true', '1', 't', 'y', 'yes', "allow", "allowed")
                    else:  # 默认为字符串
                        return urllib.parse.unquote(data.get(alias))
        if return_default:
            return param_config['default']
        else:
            return None
        
    def update_from_param(self, param_name, data, special_dict={}):
        value = self.get_param_value(param_name, data, return_default=False, special_dict=special_dict)
        if value is not None:
            setattr(self, param_name, value)
    
    def load_from_dict(self, data: dict={}):
        
        assert params_config is not None, "params_config.json not found."
        
        task_type = self.get_param_value('task_type', data)
        self.task_type = "ssml" if "ssml" in task_type.lower() else "text"
        if self.task_type == "text" and data.get("ssml") not in [None, ""]:
            self.task_type = "ssml"
        
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
        self.format = self.get_param_value('format', data)
        self.stream = self.get_param_value('stream', data)
        
        
    def md5(self):
        m = hashlib.md5()
        if self.task_type == "audio":
            m.update(self.src.encode())
        elif self.task_type == "ssml":
            m.update(self.ssml.encode())
        else:
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


