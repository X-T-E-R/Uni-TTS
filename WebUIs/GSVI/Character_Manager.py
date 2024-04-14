import gradio as gr
import os, json

# 在开头加入路径
import os, sys
now_dir = os.getcwd()
sys.path.append(now_dir)
# sys.path.append(os.path.join(now_dir, "tools"))



global state

state = {   'models_path': r"trained",
            'character_list': [],
            

            'edited_character_path': '',
            'edited_character_name': '',
            'ckpt_file_found': [],
            'pth_file_found': [],
            'wav_file_found': [],

            
            }

global infer_config
infer_config = {
}

# 取得模型文件夹路径
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
        state["models_path"] = config.get("models_path", "trained")
        locale_language = str(config.get("locale", "auto"))
        locale_language = None if locale_language.lower() == "auto" else locale_language
        
from tools.i18n.i18n import I18nAuto
from Inference.src.config_manager import inference_config

i18n = I18nAuto(locale_language ,os.path.join(os.path.dirname(os.path.dirname(__file__)), "i18n/locale"))

# 微软提供的SSML情感表
emotional_styles = [
    "default",
    "advertisement_upbeat", "affectionate", "angry", "assistant", "calm", "chat", "cheerful", 
    "customerservice", "depressed", "disgruntled", "documentary-narration", "embarrassed", 
    "empathetic", "envious", "excited", "fearful", "friendly", "gentle", "hopeful", "lyrical", 
    "narration-professional", "narration-relaxed", "newscast", "newscast-casual", "newscast-formal", 
    "poetry-reading", "sad", "serious", "shouting", "sports_commentary", "sports_commentary_excited", 
    "whispering", "terrified", "unfriendly"
]

language_list = ["auto", "zh", "en", "ja", "all_zh", "all_ja"]
translated_language_list = [i18n(language) for language in language_list]
language_dict = dict(zip(translated_language_list, language_list))

translated_language_dict = dict(zip(language_list, translated_language_list))
translated_language_dict.update(dict(zip(translated_language_list, translated_language_list)))
translated_language_dict["多语种混合"] = i18n("auto")

# 预先建立相当数量的情感选择框
all_emotion_num=len(emotional_styles)

def generate_info_bar():
    current_character_textbox = gr.Textbox(value=state['edited_character_name'], label=i18n("当前人物"), interactive=False)
    version_textbox = gr.Textbox(value=infer_config['version'], label=i18n("版本"), interactive=True)
    gpt_model_dropdown = gr.Dropdown(choices=state['ckpt_file_found'], label=i18n("GPT模型路径"), interactive=True, value=infer_config['gpt_path'], allow_custom_value=True)
    sovits_model_dropdown = gr.Dropdown(choices=state['pth_file_found'], label=i18n("Sovits模型路径"), interactive=True, value=infer_config['sovits_path'], allow_custom_value=True)
    column_items = [current_character_textbox, version_textbox, gpt_model_dropdown, sovits_model_dropdown]
    index = 0
    for item in infer_config['emotion_list']:
        emotion, details = item
        index += 1
        column_items.append(gr.Number(index, visible=True, scale=1))
        column_items.append(gr.Dropdown(choices=translated_language_list, value=translated_language_dict[details['prompt_language']], visible=True, interactive=True, scale=3, label=i18n("提示语言")))
        column_items.append(gr.Dropdown(choices=emotional_styles, value=emotion, visible=True, interactive=True, scale=3, allow_custom_value=True, label=i18n("情感风格")))
        column_items.append(gr.Dropdown(choices=state["wav_file_found"], visible=True, value=details['ref_wav_path'], scale=8, allow_custom_value=True, label=i18n("参考音频路径")))
        column_items.append(gr.Textbox(value=details['prompt_text'], visible=True, scale=8, interactive=True, label=i18n("提示文本")))
        column_items.append(gr.Audio(os.path.join(state["edited_character_path"], details['ref_wav_path']), visible=True, scale=8, label=i18n("音频预览")))

    for i in range(all_emotion_num - index):
        column_items.append(gr.Number(i, visible=False))
        column_items.append(gr.Dropdown(visible=False))
        column_items.append(gr.Dropdown(visible=False))
        column_items.append(gr.Dropdown(visible=False))
        column_items.append(gr.Textbox(visible=False))
        column_items.append(gr.Audio(None, visible=False))

    return column_items

def load_json_to_state(data):
    infer_config['version'] = data.get('version','')
    emotional_list = data.get('emotion_list',{})
    for emotion, details in emotional_list.items():
        infer_config['emotion_list'].append([emotion,details])
    infer_config['gpt_path'] = data['gpt_path']
    infer_config['sovits_path'] = data['sovits_path']
    return generate_info_bar()


def split_file_name(file_name):
    try :
        base_name=os.path.basename(file_name)
    except:
        base_name=file_name
  
    final_name = os.path.splitext(base_name)[0]
    return final_name


def clear_infer_config():
    global infer_config
    infer_config = {
        'version': '1.0.1',
        'gpt_path': '',
        'sovits_path': '',
        'emotion_list': [],
    }

clear_infer_config()

def read_json_from_file(character_dropdown,models_path  ):
    state['edited_character_name'] = character_dropdown  
    state['models_path']=models_path 
    state['edited_character_path'] = os.path.join(state['models_path'], state['edited_character_name'])
    state['ckpt_file_found'], state['pth_file_found'], state['wav_file_found'] = scan_files(state['edited_character_path'])
    print(i18n("当前人物变更为: ")+state['edited_character_name'])
    clear_infer_config()
    json_path = os.path.join(state['edited_character_path'], "infer_config.json")
    # 从json文件中读取数据
    with open(json_path, "r", encoding='utf-8') as f:
        data = json.load(f)
        return load_json_to_state(data)


def save_json():
    if infer_config['gpt_path'] == '' or infer_config['gpt_path'] is None:
        gr.Error(i18n("缺失某些项，保存失败！"))
        raise Exception(i18n("缺失某些项，保存失败！"))
    json_path = os.path.join(state['edited_character_path'], "infer_config.json")
    data = {
        'version': infer_config['version'],
        'gpt_path': infer_config['gpt_path'],
        'sovits_path': infer_config['sovits_path'],
        i18n("简介"): i18n(r"这是一个配置文件适用于https://github.com/X-T-E-R/TTS-for-GPT-soVITS，是一个简单好用的前后端项目"),
        'emotion_list': {}
    }
    for item in infer_config['emotion_list']:
        data['emotion_list'][item[0]] = item[1]
    try:
        # 将state中的数据保存到json文件中
        with open(json_path, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        gr.Info(i18n("保存成功！"))
        
    except:
        gr.Error(i18n("文件打开失败，保存失败！"))
        raise Exception(i18n("保存失败！"))



def scan_files(character_path):
    ckpt_file_found = []
    pth_file_found = []
    wav_file_found = []

    # 扫描3种文件
    for dirpath, dirnames, filenames in os.walk(character_path):
        for file in filenames:
            # 构建文件的完整路径
            full_path = os.path.join(dirpath, file)
            rev_path = os.path.relpath(full_path, character_path)
            print(full_path)
            # 根据文件扩展名和变量是否已赋值来更新变量
            if file.lower().endswith(".ckpt"):
                ckpt_file_found.append(rev_path)
            elif file.lower().endswith(".pth"):
                pth_file_found.append(rev_path)
            elif file.lower().endswith(".wav"):
                wav_file_found.append(rev_path)
            
    return ckpt_file_found, pth_file_found, wav_file_found

def auto_generate_json(character_dropdown, models_path):
    # 将选中人物设定为当前人物
    state['edited_character_name'] = character_dropdown  
    state['models_path'] = models_path 
    state['edited_character_path'] = os.path.join(state['models_path'], state['edited_character_name'])
    print(i18n(f"当前人物变更为: {state['edited_character_name']}"))
    clear_infer_config()
    character_path = state['edited_character_path']
    
    ckpt_file_found, pth_file_found, wav_file_found = scan_files(character_path)
   
    if len(ckpt_file_found) == 0 or len(pth_file_found) == 0:
        gr.Error(i18n("找不到模型文件！请把有效文件放置在文件夹下！！！"))
        raise Exception(i18n("找不到模型文件！请把有效文件放置在文件夹下！！！"))
    else:
        state['ckpt_file_found'] = ckpt_file_found
        state['pth_file_found'] = pth_file_found
        state['wav_file_found'] = wav_file_found
        gpt_path = ckpt_file_found[0]
        sovits_path = pth_file_found[0]

        infer_config['gpt_path'] = gpt_path
        infer_config['sovits_path'] = sovits_path
    
    if len(wav_file_found) == 0:
        return generate_info_bar()
    else:
        return add_emotion()


def scan_subfolder(models_path):
    subfolders = [os.path.basename(f.path) for f in os.scandir(models_path) if f.is_dir()]
    state['models_path'] = models_path
    state['character_list'] = subfolders
    print(i18n("扫描模型文件夹:")+models_path)
    print(i18n(f"找到的角色列表:") + str(subfolders))
    gr.Info(i18n(f"找到的角色列表:") + str(subfolders))
    d2 = gr.Dropdown(subfolders)
    return d2



def add_emotion():
    
    unused_emotional_style = ''
    for style in emotional_styles:
        style_in_list = False
        for item in infer_config['emotion_list']:
            if style == item[0]:
                style_in_list = True
                break
        if not style_in_list:
            unused_emotional_style = style
            break
    
    ref_wav_path = state['wav_file_found'][0]
    infer_config['emotion_list'].append([f'{unused_emotional_style}',    {
        'ref_wav_path':ref_wav_path,'prompt_text':split_file_name(ref_wav_path),'prompt_language':translated_language_dict['auto']}])
    return generate_info_bar()


def change_pt_files(version_textbox, sovits_model_dropdown, gpt_model_dropdown):
    infer_config['version'] = version_textbox
    infer_config['sovits_path'] = sovits_model_dropdown
    infer_config['gpt_path'] = gpt_model_dropdown
    pass

def change_parameters(index, wav_path, emotion_list, prompt_language, prompt_text = ""):
    
    # Convert index to integer in case it's passed as a string
    index = int(index)
    
    if prompt_text=="" or prompt_text is None:
        prompt_text = split_file_name(wav_path)
    
    infer_config['emotion_list'][index-1][0]=emotion_list
    infer_config['emotion_list'][index-1][1]['ref_wav_path'] = wav_path
    infer_config['emotion_list'][index-1][1]['prompt_text'] = prompt_text
    infer_config['emotion_list'][index-1][1]['prompt_language'] = language_dict[prompt_language]

    return gr.Dropdown(value=wav_path), gr.Dropdown(value=emotion_list), gr.Dropdown(value=prompt_language), gr.Textbox(value=prompt_text), gr.Audio(os.path.join(state["edited_character_path"],wav_path))


def run_as_tab(app: gr.Blocks):
    with gr.Row() as status_bar:       
        # 创建模型文件夹路径的输入框
        models_path = gr.Textbox(value=state["models_path"], label=i18n("模型文件夹路径"), scale=3)

        # 创建扫描按钮并设置点击事件
        scan_button = gr.Button(i18n("扫描"), scale=1, variant="primary")
        # 创建角色列表的下拉菜单，初始为空
        character_dropdown = gr.Dropdown([], label=i18n("选择角色"), scale=3)
        # 创建从json中读取按钮并设置点击事件
        read_info_from_json_button = gr.Button(i18n("从json中读取"), size="lg", scale=2, variant="secondary")
        # 创建自动生成json的按钮并设置点击事件
        auto_generate_info_button = gr.Button(i18n("自动生成info"), size="lg", scale=2, variant="primary")
        
        scan_button.click(scan_subfolder, inputs=[models_path], outputs=[character_dropdown])
    
    gr.HTML(i18n("""<p>这是模型管理界面，为了实现对多段参考音频分配情感设计，如果您只有一段可不使用这个界面</p><p>若有疑问或需要进一步了解，可参考文档：<a href="https://www.yuque.com/xter/zibxlp/hme8bw2r28vad3le">点击查看详细文档</a>。</p>"""))
    gr.Markdown(i18n("请修改后点击下方按钮进行保存"))

    # 创建保存json的按钮并设置点击事件
    with gr.Row() as submit_bar:
        save_json_button = gr.Button(i18n("保存json\n（可能不会有完成提示，没报错就是成功）"), scale=2, variant="primary")
        save_json_button.click(save_json)
    
    # 模型信息
    with gr.Row():
        with gr.Column(scale=1):
            current_character_textbox = gr.Textbox(value=state['edited_character_name'], label=i18n("当前人物"), interactive=False)
            version_textbox = gr.Textbox(value=infer_config['version'], label=i18n("版本"))
            gpt_model_dropdown = gr.Dropdown(choices=state['ckpt_file_found'], label=i18n("GPT模型路径"))
            sovits_model_dropdown = gr.Dropdown(choices=state['pth_file_found'], label=i18n("Sovits模型路径"))
            version_textbox.blur(change_pt_files, inputs=[version_textbox, sovits_model_dropdown, gpt_model_dropdown], outputs=None)
            gpt_model_dropdown.input(change_pt_files, inputs=[version_textbox, sovits_model_dropdown, gpt_model_dropdown], outputs=None)
            sovits_model_dropdown.input(change_pt_files, inputs=[version_textbox, sovits_model_dropdown, gpt_model_dropdown], outputs=None)
            column_items = [current_character_textbox, version_textbox, gpt_model_dropdown, sovits_model_dropdown]
        
        with gr.Column(scale=3):
            add_emotion_button = gr.Button(i18n("添加情感"), size="lg", scale=2, variant="primary")

            for index in range(all_emotion_num):

                with gr.Row() as emotion_row:
                    row_index = gr.Number(visible=False)
                    emotional_list = gr.Dropdown(visible=False)
                    prompt_language = gr.Dropdown(visible=False)
                    wav_path =  gr.Dropdown(visible=False)
                    prompt_text = gr.Textbox(visible=False)
                    audio_preview = gr.Audio(visible=False, type="filepath")

                    emotional_list.input(change_parameters, inputs=[row_index, wav_path, emotional_list, prompt_language, prompt_text], outputs=[wav_path, emotional_list, prompt_language, prompt_text, audio_preview])
                    prompt_language.input(change_parameters, inputs=[row_index, wav_path, emotional_list, prompt_language, prompt_text], outputs=[wav_path, emotional_list, prompt_language, prompt_text, audio_preview])
                    wav_path.input(change_parameters, inputs=[row_index, wav_path, emotional_list, prompt_language], outputs=[wav_path, emotional_list, prompt_language, prompt_text, audio_preview])
                    prompt_text.input(change_parameters, inputs=[row_index, wav_path, emotional_list, prompt_language, prompt_text], outputs=[wav_path, emotional_list, prompt_language, prompt_text, audio_preview])
                    
                    column_items.append(row_index)
                    column_items.append(prompt_language)
                    column_items.append(emotional_list)
                    column_items.append(wav_path)
                    column_items.append(prompt_text)
                    column_items.append(audio_preview)

    add_emotion_button.click(add_emotion, outputs=column_items)
    read_info_from_json_button.click(read_json_from_file, inputs=[character_dropdown,models_path] , outputs=column_items)
    auto_generate_info_button.click(auto_generate_json, inputs=[character_dropdown,models_path], outputs=column_items)
    
if __name__ == '__main__':
    with gr.Blocks() as app:
        run_as_tab(app)
    app.launch(server_port=9868, show_error=True,debug=True, inbrowser=True, share=inference_config.is_share)
