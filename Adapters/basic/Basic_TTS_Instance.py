from .Basic_TTS_Task import Basic_TTS_Task as TTS_Task

class Basic_Instance:
    def __init__(self, models_path=None, **kwargs):
        self.models_path = models_path
        print(f"模型文件夹: {models_path}")

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

    def generate_from_text(self, task: TTS_Task):
        print(f"文本: {task.text}")
        return "生成文本任务"
    
    def generate_from_ssml(self, task: TTS_Task):
        print(f"SSML: {task.ssml}")
        return "生成SSML任务"