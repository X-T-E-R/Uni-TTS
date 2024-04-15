
import os, json, sys

from uuid import uuid4
from typing import Literal
import urllib.parse
import hashlib


class Base_TTS_Task:
    """
    Represents a basic Text-to-Speech (TTS) task.

    Attributes:
        uuid (str): The unique identifier for the task.
        task_type (Literal["audio", "ssml", "text"]): The type of the TTS task.
        audio_path (str): The path to the audio file.
        
        src (str): The source of the audio file.
        ssml (str): The SSML content.
        text (str): The text content.
        variation (str): The variation of the text content.
        
        params_config (dict): The parameter configuration.
        disabled_features (list): The list of disabled features.
        format (str): The audio format.
        stream (bool): Indicates if the audio should be streamed.
        loudness (float): The loudness of the audio.
        speed (float): The speed of the audio.
        
    Methods:
        get_param_value(param_name, data, return_default=True, special_dict={}): Returns the value of a parameter.
        update_from_param(param_name, data, special_dict={}): Updates a parameter value.
        
    Methods need to rewrite:
        load_from_dict(data: dict={}): Loads the task from a dictionary.
        md5(): Returns the MD5 hash of the task.
        to_dict(): Returns the task as a dictionary.
        __str__(): Returns a string representation of the task.
    """
    def __init__(self, other_task=None):
        self.uuid: str = str(uuid4())
        
        self.task_type: Literal["audio", "ssml", "text"] = "text"
        self.audio_path: str = ""
        
        # 任务类型为音频时的属性
        self.src: str = ""       

        # 任务类型为SSML时的属性
        self.ssml: str = ""

        # 任务类型为文本时的属性
        self.text: str = ""
        self.variation: str = None
        
        # 从文件可以读取参数配置与别名
        self.params_config: dict = None
        self.disabled_features: list = []
        
        # 通用属性
        self.format: str = "wav" if other_task is None else other_task.format
        self.stream: bool = False if other_task is None else other_task.stream
        self.loudness: float = None if other_task is None else other_task.loudness
        self.speed: float = 1.0 if other_task is None else other_task.speed
        self.save_temp: bool = False if other_task is None else other_task.save_temp
        self.sample_rate: int = 32000 if other_task is None else other_task.sample_rate
    
    def get_param_value(self, param_name, data, return_default=True, special_dict={}):
        # ban disabled features
        param_config = self.params_config[param_name]
        if param_name not in self.disabled_features:
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
        
        assert self.params_config is not None, "params_config.json not found."
        
        task_type = self.get_param_value('task_type', data)
        self.task_type = "ssml" if "ssml" in task_type.lower() else "text"
        if self.task_type == "text" and data.get("ssml") not in [None, ""]:
            self.task_type = "ssml"
        # 参数提取
        if self.task_type == "text":
            self.text = self.get_param_value('text', data).strip()
        else:
            self.ssml = self.get_param_value('ssml', data).strip()
            
        self.format = self.get_param_value('format', data)
        self.stream = self.get_param_value('stream', data)
        self.loudness = self.get_param_value('loudness', data)
        self.speed = self.get_param_value('speed', data)
        
        
    def md5(self):
        m = hashlib.md5()
        if self.task_type == "audio":
            m.update(self.src.encode())
        elif self.task_type == "ssml":
            m.update(self.ssml.encode())
        elif self.task_type == "text":
            m.update(self.text.encode())
            m.update(self.variation.encode())
        return m.hexdigest()
    
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
        json_content = json.dumps(self.to_dict(), ensure_ascii=False)  # ensure_ascii=False to properly display non-ASCII characters
        return f"----------------TTS Task--------------\n content: {json_content}\n--------------------------------------"


