global character_name

import os, json
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from classic_inference_core import get_tts_wav, get_streaming_tts_wav, change_sovits_weights, change_gpt_weights

print("您正在使用经典推理模式，不支持并行推理。\n如果您不希望使用，请去调节config.json文件中的classic_inference参数为false。")

def load_infer_config(character_path):
    config_path = os.path.join(character_path, "infer_config.json")
    """加载环境配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    if config.get("ref_wav_path") is not None:
        return update_config_version(character_path)
    return config

import os
import json

# 取得模型文件夹路径
global models_path
models_path = "trained"
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        models_path = config.get("models_path", "trained")

def remove_character_path(full_path,character_path):
    # 从full_path中移除character_path部分
    relative_path = full_path.replace(character_path, '')
    # 如果relative_path以路径分隔符开头，去除它
    if relative_path.startswith(os.path.sep):
        relative_path = relative_path[len(os.path.sep):]
    return relative_path


def update_config_version(character_path):
    
    config_path = os.path.join(character_path, "infer_config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("正在更新文件")
        if config.get("ref_wav_path") is not None:
            config["emotion_list"] = {
                "default": {
                    "ref_wav_path": remove_character_path(config["ref_wav_path"],character_path),
                    "prompt_text": config["prompt_text"],
                    "prompt_language": config["prompt_language"]
                }
            }
            config.pop("ref_wav_path", None)
            config.pop("prompt_text", None)
            config.pop("prompt_language", None)
            config["sovits_path"] = remove_character_path(config["sovits_path"],character_path)
            config["gpt_path"] = remove_character_path(config["gpt_path"],character_path)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        return config
    except:
        raise Exception("更新失败！请手动删除infer_config.json文件，让系统自动生成")
             

def auto_generate_infer_config(character_path):
    ## TODO: Auto-generate wav-list and prompt-list from character_path
    ##     
    # Initialize variables for file detection

    print(f"正在自动生成配置文件: {character_path}")
    ckpt_file_found = None
    pth_file_found = None
    wav_file_found = None

    # Iterate through files in character_path to find matching file types
    for dirpath, dirnames, filenames in os.walk(character_path):
        for file in filenames:
            # 构建文件的完整路径
            full_path = os.path.join(dirpath, file)
            # 从full_path中移除character_path部分
            relative_path = remove_character_path(full_path,character_path)
            # 根据文件扩展名和变量是否已赋值来更新变量
            if file.lower().endswith(".ckpt") and ckpt_file_found is None:
                ckpt_file_found = relative_path
            elif file.lower().endswith(".pth") and pth_file_found is None:
                pth_file_found = relative_path
            elif file.lower().endswith(".wav") and wav_file_found is None:
                wav_file_found = relative_path
            elif file.lower().endswith(".mp3"):
                import pydub
                # Convert mp3 to wav
                wav_file_path = os.path.join(dirpath,os.path.splitext(file)[0] + ".wav")


                pydub.AudioSegment.from_mp3(full_path).export(wav_file_path, format="wav")
                if wav_file_found is None:
                    wav_file_found = remove_character_path(os.path.join(dirpath,os.path.splitext(file)[0] + ".wav"),character_path)
                    

    # Initialize infer_config with gpt_path and sovits_path regardless of wav_file_found
    infer_config = {
        "gpt_path": ckpt_file_found,
        "sovits_path": pth_file_found,
        "software_version": "1.1",
        r"简介": r"这是一个配置文件适用于https://github.com/X-T-E-R/TTS-for-GPT-soVITS，是一个简单好用的前后端项目"
    }

    # If wav file is also found, update infer_config to include ref_wav_path, prompt_text, and prompt_language
    if wav_file_found:
        wav_file_name = os.path.splitext(os.path.basename(wav_file_found))[0]  # Extract the filename without extension
        infer_config["emotion_list"] = {
            "default": {
                "ref_wav_path": wav_file_found,
                "prompt_text": wav_file_name,
                "prompt_language": "多语种混合"
            }
        }
    else:
        raise Exception("找不到wav参考文件！请把有效wav文件放置在模型文件夹下。否则效果可能会非常怪")
        pass
    # Check if the essential model files were found
    if ckpt_file_found and pth_file_found:
        infer_config_path = os.path.join(character_path, "infer_config.json")
        try:
            with open(infer_config_path , 'w', encoding='utf-8') as f:
                json.dump(infer_config, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"无法写入文件: {infer_config_path}. 错误: {e}")

        return infer_config_path
    else:
        return "Required model files (.ckpt or .pth) not found in character_path directory."


def load_character(cha_name):
    global character_name
    
    character_path=os.path.join(models_path,cha_name)
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
            load_character(cha_name)
            return 
        except:
            # 报错
            raise Exception("找不到模型文件！请把有效模型放置在模型文件夹下，确保其中至少有pth、ckpt和wav三种文件。")
    # 修改权重
    character_name = cha_name
    change_sovits_weights(sovits_path)
    change_gpt_weights(gpt_path)
    print(f"加载角色成功: {cha_name}")

def get_deflaut_character_name():
    import os
    import json

    # character_info_path = os.path.join(models_path, "character_info.json")
    default_character = None

    # if os.path.exists(character_info_path):
    #     with open(character_info_path, "r", encoding='utf-8') as f:
    #         try:
    #             character_info = json.load(f)
    #             default_character = character_info.get("deflaut_character")
    #         except:
    #             pass

    if default_character is None or not os.path.exists(os.path.join(models_path, default_character)):
        # List all items in models_path
        all_items = os.listdir(models_path)
        
        # Filter out only directories (folders) from all_items
        trained_folders = [item for item in all_items if os.path.isdir(os.path.join(models_path, item))]
        
        # If there are any directories found, set the first one as the default character
        if trained_folders:
            default_character = trained_folders[0]

    return default_character

character_name = get_deflaut_character_name()
load_character(character_name)

def match_character_emotion(character_path):
    if not os.path.exists(os.path.join(character_path, "reference_audio")):
        # 如果没有reference_audio文件夹，就返回None
        return None, None, None
    

def get_wav_from_text_api(text, text_language, top_k=12, top_p=0.6, temperature=0.6, character_emotion="default", cut_method="auto_cut", stream=False, **kwargs):
    # 加载环境配置
    config = load_infer_config(os.path.join(models_path, character_name))
    
   
    
    # 尝试从配置中提取参数，如果找不到则设置为None
    ref_wav_path =  None
    prompt_text = None
    prompt_language = None
    if character_emotion == "auto":
        # 如果是auto模式，那么就自动决定情感
        ref_wav_path, prompt_text, prompt_language = match_character_emotion(os.path.join(models_path, character_name))
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
                ref_wav_path = os.path.join(os.path.join(models_path,character_name), details['ref_wav_path'])
                prompt_text = details['prompt_text']
                prompt_language = details['prompt_language']
                break
        if ref_wav_path is None:
            print("找不到ref_wav_path！请删除infer_config.json文件，让系统自动生成")
            
    print(prompt_text)
    
    # 根据是否找到ref_wav_path和prompt_text、prompt_language来决定ref_free的值
    if ref_wav_path is not None and prompt_text is not None and prompt_language is not None:
        ref_free = False
    else:
        ref_free = True
        top_k = 3
        top_p = 0.3
        temperature = 0.3
       

    # 调用原始的get_tts_wav函数
    # 注意：这里假设get_tts_wav函数及其所需的其它依赖已经定义并可用
    if stream == False:
        return get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language, top_k=top_k, top_p=top_p, temperature=temperature, ref_free=ref_free, stream=stream)
    else:
        return get_streaming_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language, top_k=top_k, top_p=top_p, temperature=temperature, ref_free=ref_free, byte_stream=True)




def update_character_info():
    # with open(os.path.join(models_path, "character_info.json"), "r", encoding='utf-8') as f:
    #     default_character = json.load(f).get("deflaut_character", None)
    default_character = None
    characters_and_emotions = {}
    for character_subdir in [f for f in os.listdir(models_path) if os.path.isdir(os.path.join(models_path, f))]:
        if os.path.exists(os.path.join(models_path, character_subdir, "infer_config.json")):
            try:
                with open(os.path.join(models_path, character_subdir, "infer_config.json"), "r", encoding='utf-8') as f:
                    config = json.load(f)
                    emotion_list=[emotion for emotion in config.get('emotion_list', None)]
                    if emotion_list is not None:
                        characters_and_emotions[character_subdir] = emotion_list
                    else:
                        characters_and_emotions[character_subdir] = ["default"]
            except:
                characters_and_emotions[character_subdir] = ["default"]
        else:
            characters_and_emotions[character_subdir] = ["default"]
                    
    # with open(os.path.join(models_path, "character_info.json"), "w", encoding='utf-8') as f:
    #     json.dump({"deflaut_character": default_character, "characters_and_emotions": characters_and_emotions}, f, ensure_ascii=False, indent=4)

    return {"deflaut_character": default_character, "characters_and_emotions": characters_and_emotions}
        

# def test_audio_save():
#     fs, audio_to_save=get_wav_from_text_api("""这是一段音频测试""",'多语种混合')
#     file_path = "example_audio.wav"
#     from scipy.io.wavfile import write
#     write(file_path, fs, audio_to_save)


# test_audio_save()
update_character_info()