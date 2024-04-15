import sys
sys.path.append(".")

from Adapters.gsv_fast import GSV_Instance 
from Adapters.gsv_fast.gsv_task import GSV_TTS_Task as TTS_Task

gsv_instance = GSV_Instance()
task:TTS_Task = TTS_Task()

task.character = "Hutao"
task.text = "你好，我是一个测试文本。"


gen = gsv_instance.generate(task)
sr, audio = next(gen)

gen = gsv_instance.generate(task)
sr, audio = next(gen)

import tempfile
import soundfile as sf
with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
    sf.write(f.name, audio, sr)
    print(f"Audio saved to {f.name}")