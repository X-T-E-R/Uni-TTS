from abc import ABC, abstractmethod

from .Base_TTS_Task import Base_TTS_Task as TTS_Task

class Base_TTS_Instance(ABC):
    @abstractmethod
    def __init__(self, models_path=None, **kwargs):
        pass
    
    @abstractmethod
    def generate(self, task: TTS_Task):
        if task.task_type == "text":
            print("生成文本任务")
            return self.generate_from_text(task)
        elif task.task_type == "ssml":
            print("生成SSML任务")
            return self.generate_from_ssml(task)
        else:
            print("未知任务类型")
            return None

    @abstractmethod
    def generate_from_text(self, task: TTS_Task):
        print(f"文本: {task.text}")
        return "生成文本任务"
    
    @abstractmethod
    def generate_from_ssml(self, task: TTS_Task):
        print(f"SSML: {task.ssml}")
        return "生成SSML任务"
    
    @abstractmethod
    def get_characters(self):
        return {"character": ["emotion1", "emotion2", "emotion3"]}
    
    @abstractmethod
    def params_analyser(self, data)->TTS_Task:
        pass
    
    @abstractmethod
    def ms_like_analyser(self, data)->TTS_Task:
        pass
    