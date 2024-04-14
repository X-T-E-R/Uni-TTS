# 在开头加入路径
import os, sys

# 尝试清空含有GPT_SoVITS的路径
for path in sys.path:
    if path.find(r"GPT_SoVITS") != -1:
        sys.path.remove(path)

now_dir = os.getcwd()
sys.path.append(now_dir)
# sys.path.append(os.path.join(now_dir, "GPT_SoVITS"))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Inference.src.config_manager import __version__ as backend_version
print(f"Backend version: {backend_version}")

import soundfile as sf
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import uvicorn  
import json

# 将当前文件所在的目录添加到 sys.path

from Inference.src.TTS_Task import TTS_Task
from Inference.src.data_analyser import params_analyser, ms_like_analyser
from Inference.src.config_manager import update_character_info, inference_config

try:
    from GPT_SoVITS.TTS_infer_pack.text_segmentation_method import register_method
except ImportError:
    is_classic = True
    raise ImportError("GPT_SoVITS is not installed, please use GSVI")
    pass

from Inference.src.TTS_Instance import TTS_instance
tts_instance = TTS_instance()

# 存储临时文件的字典
temp_files = {}

app = FastAPI()

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/character_list')
async def character_list():
    res = JSONResponse(update_character_info()['characters_and_emotions'])
    return res

@app.get('/voice/speakers')
async def speakers():
    speaker_dict = update_character_info()['characters_and_emotions']
    name_list = list(speaker_dict.keys())
    speaker_list = [{"id": i, "name": name_list[i], "lang":["zh","en","ja"]} for i in range(len(name_list))]
    res = {
        "VITS": speaker_list,
        "GSVI": speaker_list,
        "GPT-SOVITS": speaker_list
    }
    return JSONResponse(res)     

def generate_task(task: TTS_Task, adapter: str="gsv_fast"):

    if task.task_type == "text" and task.text.strip() == "":
        return HTTPException(status_code=400, detail="Text is empty")
    elif task.task_type == "ssml" and task.ssml.strip() == "":
        return HTTPException(status_code=400, detail="SSML is empty")
    format = task.format
    save_temp = task.save_temp
    request_hash = None if not save_temp else task.md5()
    stream = task.stream
    
    if task.task_type == "text":
        gen = tts_instance.generate_from_text(task)
    elif task.task_type == "ssml":
        # 还不支持 stream
        audio_path = tts_instance.generate_from_ssml(task)
        if audio_path is None:
            return HTTPException(status_code=400, detail="SSML is invalid")
        return FileResponse(audio_path, media_type=f"audio/{format}", filename=f"audio.{format}")

    if stream == False:
        if save_temp and request_hash in temp_files:
            return FileResponse(path=temp_files[request_hash], media_type=f'audio/{format}')
        else:
            # 假设 gen 是你的音频生成器
            try:
                sampling_rate, audio_data = next(gen)
            except StopIteration:
                raise HTTPException(status_code=404, detail="Generator is empty or error occurred")
            # 创建一个临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}') as tmp_file:
                # 尝试写入用户指定的格式，如果失败则回退到 WAV 格式
                try:
                    sf.write(tmp_file, audio_data, sampling_rate, format=format)
                except Exception as e:
                    # 如果指定的格式无法写入，则回退到 WAV 格式
                    sf.write(tmp_file, audio_data, sampling_rate, format='wav')
                    format = 'wav'  # 更新格式为 wav
                
                tmp_file_path = tmp_file.name
                task.audio_path = tmp_file_path
                if save_temp:
                    temp_files[request_hash] = tmp_file_path
            # 返回文件响应，FileResponse 会负责将文件发送给客户端
            return FileResponse(tmp_file_path, media_type=f"audio/{format}", filename=f"audio.{format}")
    else:
        return StreamingResponse(gen,  media_type='audio/wav')


# route 由 json 文件配置
async def tts(request: Request, adapter: str = "gsv_fast"):
    # 尝试从JSON中获取数据，如果不是JSON，则从查询参数中获取
    if request.method == "GET":
        data = request.query_params
    else:
        data = await request.json()
    return_type = "audio"
    # 认定一个请求只有一个任务
    if data.get("textType", None) is not None:
        task : TTS_Task = ms_like_analyser(data)
        return_type = "json"
    else:
        task : TTS_Task = params_analyser(data)
        
    if return_type == "audio":
        return generate_task(task, adapter)
    else:
        # TODO: return json
        return generate_task(task, adapter)
        pass

routes = ['/tts']
try:
    with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), "params_config.json"), "r", encoding="utf-8") as f:
        config = json.load(f)
        routes = config.get("route", {}).get("alias", ['/tts'])
except:
    pass

# 注册路由
for path in routes:
    app.api_route(path, methods=['GET', 'POST'])(tts)

# 便于小白理解
def print_ipv4_ip(host = "127.0.0.1", port = 5000):
    import socket

    def get_internal_ip():
        """获取内部IP地址"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 这不会发送真正的数据包
            s.connect(('10.253.156.219', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    if host == "0.0.0.0":
        display_hostname = get_internal_ip()
        if display_hostname != "127.0.0.1":
            print(f"Please use http://{display_hostname}:{port} to access the service.")


workers = inference_config.workers
tts_host = inference_config.tts_host
tts_port = inference_config.tts_port

if __name__ == "__main__":
    print_ipv4_ip(tts_host, tts_port)
    uvicorn.run(app, host=tts_host, port=tts_port)

