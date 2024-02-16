import os, re, logging

logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)

logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)
import json

global character_name

cnhubert_base_path = os.environ.get(
    "cnhubert_base_path", "./pretrained_models/chinese-hubert-base"
)
bert_path = os.environ.get(
    "bert_path", "./pretrained_models/chinese-roberta-wwm-ext-large"
)

infer_ttswebui = os.environ.get("infer_ttswebui", 9872)
infer_ttswebui = int(infer_ttswebui)
is_share = os.environ.get("is_share", "False")
is_share = eval(is_share)
if "_CUDA_VISIBLE_DEVICES" in os.environ:
    os.environ["CUDA_VISIBLE_DEVICES"] = os.environ["_CUDA_VISIBLE_DEVICES"]
is_half = eval(os.environ.get("is_half", "True"))
from transformers import AutoModelForMaskedLM, AutoTokenizer
import numpy as np
import librosa, torch
from feature_extractor import cnhubert

cnhubert.cnhubert_base_path = cnhubert_base_path

from module.models import SynthesizerTrn
from AR.models.t2s_lightning_module import Text2SemanticLightningModule
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
from time import time as ttime
from module.mel_processing import spectrogram_torch
from my_utils import load_audio
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto()

os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'  # 确保直接启动推理UI时也能够设置。

if torch.cuda.is_available():
    device = "cuda"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

tokenizer = AutoTokenizer.from_pretrained(bert_path)
bert_model = AutoModelForMaskedLM.from_pretrained(bert_path)
if is_half == True:
    bert_model = bert_model.half().to(device)
else:
    bert_model = bert_model.to(device)


def get_bert_feature(text, word2ph):
    with torch.no_grad():
        inputs = tokenizer(text, return_tensors="pt")
        for i in inputs:
            inputs[i] = inputs[i].to(device)
        res = bert_model(**inputs, output_hidden_states=True)
        res = torch.cat(res["hidden_states"][-3:-2], -1)[0].cpu()[1:-1]
    assert len(word2ph) == len(text)
    phone_level_feature = []
    for i in range(len(word2ph)):
        repeat_feature = res[i].repeat(word2ph[i], 1)
        phone_level_feature.append(repeat_feature)
    phone_level_feature = torch.cat(phone_level_feature, dim=0)
    return phone_level_feature.T


class DictToAttrRecursive(dict):
    def __init__(self, input_dict):
        super().__init__(input_dict)
        for key, value in input_dict.items():
            if isinstance(value, dict):
                value = DictToAttrRecursive(value)
            self[key] = value
            setattr(self, key, value)

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")

    def __setattr__(self, key, value):
        if isinstance(value, dict):
            value = DictToAttrRecursive(value)
        super(DictToAttrRecursive, self).__setitem__(key, value)
        super().__setattr__(key, value)

    def __delattr__(self, item):
        try:
            del self[item]
        except KeyError:
            raise AttributeError(f"Attribute {item} not found")


ssl_model = cnhubert.get_model()
if is_half == True:
    ssl_model = ssl_model.half().to(device)
else:
    ssl_model = ssl_model.to(device)


def change_sovits_weights(sovits_path):
    global vq_model, hps
    dict_s2 = torch.load(sovits_path, map_location="cpu")
    hps = dict_s2["config"]
    hps = DictToAttrRecursive(hps)
    hps.model.semantic_frame_rate = "25hz"
    vq_model = SynthesizerTrn(
        hps.data.filter_length // 2 + 1,
        hps.train.segment_size // hps.data.hop_length,
        n_speakers=hps.data.n_speakers,
        **hps.model
    )
    if ("pretrained" not in sovits_path):
        del vq_model.enc_q
    if is_half == True:
        vq_model = vq_model.half().to(device)
    else:
        vq_model = vq_model.to(device)
    vq_model.eval()
    print(vq_model.load_state_dict(dict_s2["weight"], strict=False))
   

def change_gpt_weights(gpt_path):
    global hz, max_sec, t2s_model, config
    hz = 50
    dict_s1 = torch.load(gpt_path, map_location="cpu")
    config = dict_s1["config"]
    max_sec = config["data"]["max_sec"]
    t2s_model = Text2SemanticLightningModule(config, "****", is_train=False)
    t2s_model.load_state_dict(dict_s1["weight"])
    if is_half == True:
        t2s_model = t2s_model.half()
    t2s_model = t2s_model.to(device)
    t2s_model.eval()
    total = sum([param.nelement() for param in t2s_model.parameters()])
    print("Number of parameter: %.2fM" % (total / 1e6))
    



def load_infer_config(config_path='infer_config.json'):
    """加载环境配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def auto_get_infer_config(character_path):
    # Initialize variables for file detection
    ckpt_file_found = None
    pth_file_found = None
    wav_file_found = None

    # Iterate through files in character_path to find matching file types
    for file in os.listdir(character_path):
        if file.endswith(".ckpt"):
            ckpt_file_found = os.path.join(character_path, file)
        elif file.endswith(".pth"):
            pth_file_found = os.path.join(character_path, file)
        elif file.endswith(".wav"):
            wav_file_found = os.path.join(character_path, file)

    # If all required files are found, create the infer_config
    if ckpt_file_found and pth_file_found and wav_file_found:
        wav_file_name = os.path.splitext(os.path.basename(wav_file_found))[0]  # Extract the filename without extension

        infer_config = {
            "ref_wav_path": wav_file_found,
            "prompt_text": wav_file_name,  # Use the extracted wav file name
            "prompt_language": "中文",
            "text_language": "中文",
            "gpt_path": ckpt_file_found,
            "sovits_path": pth_file_found
        }

        infer_config_path = os.path.join(character_path, "infer_config.json")
        with open(infer_config_path, "w") as f:
            json.dump(infer_config, f)

        return infer_config_path
    else:
        return "Required files not found in character_path directory."

def load_character(character_name):
    try:
        # 加载配置
        config = load_infer_config(f"./trained/{character_name}/infer_config.json")
        # 尝试从环境变量获取gpt_path，如果未设置，则从配置文件读取
        gpt_path = config.get("gpt_path")
        # 尝试从环境变量获取sovits_path，如果未设置，则从配置文件读取
        sovits_path = config.get("sovits_path")
    except:
        try:
            # 尝试调用auto_get_infer_config
            auto_get_infer_config(f"./trained/{character_name}/")
            load_character(character_name)
            return 
        except:
            # 报错
            raise Exception("找不到模型文件！请把有效模型放置在trained文件夹下。")
    # 修改权重
    change_sovits_weights(sovits_path)
    change_gpt_weights(gpt_path)

def get_deflaut_character_name():
    import os
    import json

    character_info_path = "./trained/character_info.json"
    default_character = None

    if os.path.exists(character_info_path):
        with open(character_info_path, "r") as f:
            character_info = json.load(f)
            default_character = character_info.get("deflaut_character")

    if default_character is None:
        # List all items in "./trained"
        all_items = os.listdir("./trained")
        
        # Filter out only directories (folders) from all_items
        trained_folders = [item for item in all_items if os.path.isdir(os.path.join("./trained", item))]
        
        # If there are any directories found, set the first one as the default character
        if trained_folders:
            default_character = trained_folders[0]

    return default_character


character_name = get_deflaut_character_name()

load_character(character_name)

def get_spepc(hps, filename):
    audio = load_audio(filename, int(hps.data.sampling_rate))
    audio = torch.FloatTensor(audio)
    audio_norm = audio
    audio_norm = audio_norm.unsqueeze(0)
    spec = spectrogram_torch(
        audio_norm,
        hps.data.filter_length,
        hps.data.sampling_rate,
        hps.data.hop_length,
        hps.data.win_length,
        center=False,
    )
    return spec


dict_language = {
    i18n("中文"): "zh",
    i18n("英文"): "en",
    i18n("日文"): "ja"
}


def splite_en_inf(sentence, language):
    pattern = re.compile(r'[a-zA-Z ]+')
    textlist = []
    langlist = []
    pos = 0
    for match in pattern.finditer(sentence):
        start, end = match.span()
        if start > pos:
            textlist.append(sentence[pos:start])
            langlist.append(language)
        textlist.append(sentence[start:end])
        langlist.append("en")
        pos = end
    if pos < len(sentence):
        textlist.append(sentence[pos:])
        langlist.append(language)
    # Merge punctuation into previous word
    for i in range(len(textlist)-1, 0, -1):
        if re.match(r'^[\W_]+$', textlist[i]):
            textlist[i-1] += textlist[i]
            del textlist[i]
            del langlist[i]
    # Merge consecutive words with the same language tag
    i = 0
    while i < len(langlist) - 1:
        if langlist[i] == langlist[i+1]:
            textlist[i] += textlist[i+1]
            del textlist[i+1]
            del langlist[i+1]
        else:
            i += 1

    return textlist, langlist


def clean_text_inf(text, language):
    phones, word2ph, norm_text = clean_text(text, language)
    phones = cleaned_text_to_sequence(phones)

    return phones, word2ph, norm_text


def get_bert_inf(phones, word2ph, norm_text, language):
    if language == "zh":
        bert = get_bert_feature(norm_text, word2ph).to(device)
    else:
        bert = torch.zeros(
            (1024, len(phones)),
            dtype=torch.float16 if is_half == True else torch.float32,
        ).to(device)

    return bert


def nonen_clean_text_inf(text, language):
    textlist, langlist = splite_en_inf(text, language)
    phones_list = []
    word2ph_list = []
    norm_text_list = []
    for i in range(len(textlist)):
        lang = langlist[i]
        phones, word2ph, norm_text = clean_text_inf(textlist[i], lang)
        phones_list.append(phones)
        if lang == "en" or "ja":
            pass
        else:
            word2ph_list.append(word2ph)
        norm_text_list.append(norm_text)
    print(word2ph_list)
    phones = sum(phones_list, [])
    word2ph = sum(word2ph_list, [])
    norm_text = ' '.join(norm_text_list)

    return phones, word2ph, norm_text


def nonen_get_bert_inf(text, language):
    textlist, langlist = splite_en_inf(text, language)
    print(textlist)
    print(langlist)
    bert_list = []
    for i in range(len(textlist)):
        text = textlist[i]
        lang = langlist[i]
        phones, word2ph, norm_text = clean_text_inf(text, lang)
        bert = get_bert_inf(phones, word2ph, norm_text, lang)
        bert_list.append(bert)
    bert = torch.cat(bert_list, dim=1)

    return bert


splits = {"，", "。", "？", "！", ",", ".", "?", "!", "~", ":", "：", "—", "…", }


def get_first(text):
    pattern = "[" + "".join(re.escape(sep) for sep in splits) + "]"
    text = re.split(pattern, text)[0].strip()
    return text


def get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language):
    t0 = ttime()
    prompt_text = prompt_text.strip("\n")
    if (prompt_text[-1] not in splits): prompt_text += "。" if prompt_language != "en" else "."
    text = text.strip("\n")
    if (text[0] not in splits and len(get_first(text)) < 4): text = "。" + text if text_language != "en" else "." + text
    print(i18n("实际输入的参考文本:"), prompt_text)
    print(i18n("实际输入的目标文本:"), text)
    zero_wav = np.zeros(
        int(hps.data.sampling_rate * 0.3),
        dtype=np.float16 if is_half == True else np.float32,
    )
    with torch.no_grad():
        wav16k, sr = librosa.load(ref_wav_path, sr=16000)
        if (wav16k.shape[0] > 160000 or wav16k.shape[0] < 48000):
            raise OSError(i18n("参考音频在3~10秒范围外，请更换！"))
        wav16k = torch.from_numpy(wav16k)
        zero_wav_torch = torch.from_numpy(zero_wav)
        if is_half == True:
            wav16k = wav16k.half().to(device)
            zero_wav_torch = zero_wav_torch.half().to(device)
        else:
            wav16k = wav16k.to(device)
            zero_wav_torch = zero_wav_torch.to(device)
        wav16k = torch.cat([wav16k, zero_wav_torch])
        ssl_content = ssl_model.model(wav16k.unsqueeze(0))[
            "last_hidden_state"
        ].transpose(
            1, 2
        )  # .float()
        codes = vq_model.extract_latent(ssl_content)
        prompt_semantic = codes[0, 0]
    t1 = ttime()
    prompt_language = dict_language[prompt_language]
    text_language = dict_language[text_language]
    if prompt_language == "en":
        phones1, word2ph1, norm_text1 = clean_text_inf(prompt_text, prompt_language)
    else:
        phones1, word2ph1, norm_text1 = nonen_clean_text_inf(prompt_text, prompt_language)

    text = auto_cut(text)
    text = text.replace("\n\n", "\n").replace("\n\n", "\n").replace("\n\n", "\n")
    print(i18n("实际输入的目标文本(切句后):"), text)
    texts = text.split("\n")
    audio_opt = []
    if prompt_language == "en":
        bert1 = get_bert_inf(phones1, word2ph1, norm_text1, prompt_language)
    else:
        bert1 = nonen_get_bert_inf(prompt_text, prompt_language)
    for text in texts:
        # 解决输入目标文本的空行导致报错的问题
        if (len(text.strip()) == 0):
            continue
        if (text[-1] not in splits): text += "。" if text_language != "en" else "."
        print(i18n("实际输入的目标文本(每句):"), text)
        if text_language == "en":
            phones2, word2ph2, norm_text2 = clean_text_inf(text, text_language)
        else:
            phones2, word2ph2, norm_text2 = nonen_clean_text_inf(text, text_language)

        if text_language == "en":
            bert2 = get_bert_inf(phones2, word2ph2, norm_text2, text_language)
        else:
            bert2 = nonen_get_bert_inf(text, text_language)

        bert = torch.cat([bert1, bert2], 1)

        all_phoneme_ids = torch.LongTensor(phones1 + phones2).to(device).unsqueeze(0)
        bert = bert.to(device).unsqueeze(0)
        all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
        prompt = prompt_semantic.unsqueeze(0).to(device)
        t2 = ttime()
        with torch.no_grad():
            # pred_semantic = t2s_model.model.infer(
            pred_semantic, idx = t2s_model.model.infer_panel(
                all_phoneme_ids,
                all_phoneme_len,
                prompt,
                bert,
                # prompt_phone_len=ph_offset,
                top_k=config["inference"]["top_k"],
                early_stop_num=hz * max_sec,
            )
        t3 = ttime()
        # print(pred_semantic.shape,idx)
        pred_semantic = pred_semantic[:, -idx:].unsqueeze(
            0
        )  # .unsqueeze(0)#mq要多unsqueeze一次
        refer = get_spepc(hps, ref_wav_path)  # .to(device)
        if is_half == True:
            refer = refer.half().to(device)
        else:
            refer = refer.to(device)
        # audio = vq_model.decode(pred_semantic, all_phoneme_ids, refer).detach().cpu().numpy()[0, 0]
        audio = (
            vq_model.decode(
                pred_semantic, torch.LongTensor(phones2).to(device).unsqueeze(0), refer
            )
                .detach()
                .cpu()
                .numpy()[0, 0]
        )  ###试试重建不带上prompt部分
        audio_opt.append(audio)
        audio_opt.append(zero_wav)
        t4 = ttime()
    print("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t3 - t2, t4 - t3))
    return hps.data.sampling_rate, (np.concatenate(audio_opt, 0) * 32768).astype(
        np.int16
    )



def split(todo_text):
    todo_text = todo_text.replace("……", "。").replace("——", "，")
    if todo_text[-1] not in splits:
        todo_text += "。"
    i_split_head = i_split_tail = 0
    len_text = len(todo_text)
    todo_texts = []
    while 1:
        if i_split_head >= len_text:
            break  # 结尾一定有标点，所以直接跳出即可，最后一段在上次已加入
        if todo_text[i_split_head] in splits:
            i_split_head += 1
            todo_texts.append(todo_text[i_split_tail:i_split_head])
            i_split_tail = i_split_head
        else:
            i_split_head += 1
    return todo_texts




def auto_cut(inp):
    # if not re.search(r'[^\w\s]', inp[-1]):
    # inp += '。'
    inp = inp.strip("\n")
    
    split_punds = r'[?!。？！~：]'
    if inp[-1] not in split_punds:
        inp+="。"
    items = re.split(f'({split_punds})', inp)
    items = ["".join(group) for group in zip(items[::2], items[1::2])]

    def process_commas(text):
        separators = ['，', ',', '、', '——', '…']
        count = 0
        processed_text = ""
        for char in text:
            processed_text += char
            if char in separators:
                if count > 12:
                    processed_text += '\n'
                    count = 0
            else:
                count += 1  # 对于非分隔符字符，增加计数
        return processed_text

    final_items=[process_commas(item) for item in items]


    return "\n".join(final_items)


def custom_sort_key(s):
    # 使用正则表达式提取字符串中的数字部分和非数字部分
    parts = re.split('(\d+)', s)
    # 将数字部分转换为整数，非数字部分保持不变
    parts = [int(part) if part.isdigit() else part for part in parts]
    return parts

def get_tts_wav_api(text):
    
    # 加载环境配置
    config = load_infer_config(f"./trained/{character_name}/infer_config.json")
    
    # 从配置中提取参数
    ref_wav_path = config['ref_wav_path']
    prompt_text = config['prompt_text']
    prompt_language = config['prompt_language']
    text_language = config['text_language']

    # 调用原始的get_tts_wav函数
    # 注意：这里假设get_tts_wav函数及其所需的其它依赖已经定义并可用
    return get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language)

import soundfile as sf
from flask import Flask, request, Response, jsonify
import io
import urllib.parse

app = Flask(__name__)


@app.route('/tts', methods=['POST'])
def tts():
    global character_name
    if request.is_json:
        # 使用 request.json 来访问 JSON 数据
        data = request.json

        text = urllib.parse.unquote(data.get('text', ''))
        cha_name = data.get('cha_name', None)

        # 构建期望的目录路径
        expected_path = f"./trained/{cha_name}/" if cha_name else None

        # 检查是否提供了cha_name，且与当前全局变量不同，以及路径是否存在
        if cha_name and cha_name != character_name and expected_path and os.path.exists(expected_path):
            character_name = cha_name  # 更新全局变量
            load_character(character_name)  # 加载新角色
        elif expected_path and not os.path.exists(expected_path):
            return jsonify({"error": f"Directory {expected_path} does not exist. Using the current character."}), 400

        sample_rate, audio_data = get_tts_wav_api(text)
        
        # 将音频数据转换为二进制流
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format='WAV')
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype='audio/wav')
    else:
        return jsonify({"error": "Request must be JSON"}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

