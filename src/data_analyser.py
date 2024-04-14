import json

from Inference.src.TTS_Task import TTS_Task


def params_analyser(data) -> TTS_Task:
    task = TTS_Task()
    task.load_from_dict(data)
    return task

def ms_like_analyser(data) -> TTS_Task:
    task = TTS_Task()
    inputs = data.get("inputs", [])
    try :
        data["text"] = inputs[0]["text"]
    except:
        return task
    task.load_from_dict(data)
    return task