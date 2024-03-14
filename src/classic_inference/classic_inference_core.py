import os, re, logging
import LangSegment
from classic_text_cleaner import *

logging.getLogger("markdown_it").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)
logging.getLogger("httpcore").setLevel(logging.ERROR)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)

logging.getLogger("charset_normalizer").setLevel(logging.ERROR)
logging.getLogger("torchaudio._extension").setLevel(logging.ERROR)
import json


cnhubert_base_path = os.environ.get(
    "cnhubert_base_path", "GPT_SoVITS/pretrained_models/chinese-hubert-base"
)
bert_path = os.environ.get(
    "bert_path", "GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large"
)


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
from time import time as ttime
from module.mel_processing import spectrogram_torch
from my_utils import load_audio
from tools.i18n.i18n import I18nAuto

i18n = I18nAuto()

os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'  # 确保直接启动推理UI时也能够设置。

if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"
    is_half = False

# 取得模型文件夹路径
config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        _config = json.load(f)
        if _config.get("device", "auto") != "auto":
            device = _config["device"]
            if device == "cpu":
                is_half = False
        if _config.get("half_precision", "auto") != "auto":
            is_half = _config["half_precision"]

        
print(f"device: {device}, is_half: {is_half}")

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
    "中文": "all_zh",#全部按中文识别
    "英文": "en",#全部按英文识别#######不变
    "日文": "all_ja",#全部按日文识别
    "中英混合": "zh",#按中英混合识别####不变
    "日英混合": "ja",#按日英混合识别####不变
    "多语种混合": "auto",#多语种启动切分识别语种
    "auto": "auto",
    "zh": "zh",
    "en": "en",
    "ja": "ja",
    "all_zh": "all_zh",
    "all_ja": "all_ja",
}





dtype=torch.float16 if is_half == True else torch.float32
def get_bert_inf(phones, word2ph, norm_text, language):
    language=language.replace("all_","")
    if language == "zh":
        bert = get_bert_feature(norm_text, word2ph).to(device)#.to(dtype)
    else:
        bert = torch.zeros(
            (1024, len(phones)),
            dtype=torch.float16 if is_half == True else torch.float32,
        ).to(device)

    return bert




splits = {"，", "。", "？", "！", ",", ".", "?", "!", "~", ":", "：", "—", "…", }


def get_tts_wav(ref_wav_path, prompt_text, prompt_language, text, text_language, how_to_cut=i18n("不切"), top_k=20, top_p=0.6, temperature=0.6, ref_free=False, stream=False):
    if prompt_text is None or len(prompt_text) == 0:
        ref_free = True
    t0 = ttime()
    prompt_language = dict_language[prompt_language]
    text_language = dict_language[text_language]
    if not ref_free:
        prompt_text = prompt_text.strip("\n")
        if (prompt_text[-1] not in splits): prompt_text += "。" if prompt_language != "en" else "."
        print(i18n("实际输入的参考文本:"), prompt_text)
    text = text.strip("\n")
    if (text[0] not in splits and len(get_first(text)) < 4): text = "。" + text if text_language != "en" else "." + text
    
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

    text = auto_cut(text)
    while "\n\n" in text:
        text = text.replace("\n\n", "\n")
    print(i18n("实际输入的目标文本(切句后):"), text)
    texts = text.split("\n")
    texts = merge_short_text_in_array(texts, 5)
    audio_opt = []
    if not ref_free:
        phones1, bert1, norm_text1 = get_phones_and_bert(prompt_text, prompt_language)
    else:
        phones1, bert1 = None, None

    for text in texts:
        # 解决输入目标文本的空行导致报错的问题
        if (len(text.strip()) == 0):
            continue
        audio = get_tts_chunk(ref_wav_path, text, text_language, bert1, phones1, prompt_semantic,
                              top_k, top_p, temperature, ref_free, t0, t1)
        audio_opt.append(audio)
        audio_opt.append(zero_wav)
        if (stream):
            # 流式模式下每句返回一次
            yield (np.concatenate([audio, zero_wav], 0) * 32768).astype(np.int16).tobytes()
    
    if (not stream):
        # 非流式最终合并后返回
        yield hps.data.sampling_rate, (np.concatenate(audio_opt, 0) * 32768).astype(
            np.int16
        )

def get_tts_chunk(ref_wav_path, text, text_language, bert1, phones1, prompt_semantic, top_k, top_p, temperature, ref_free, t0, t1):
    if (text[-1] not in splits): text += "。" if text_language != "en" else "."
    print(i18n("实际输入的目标文本(每句):"), text)
    phones2, bert2, norm_text2 = get_phones_and_bert(text, text_language)
    print(i18n("前端处理后的文本(每句):"), norm_text2)
    if not ref_free:
        bert = torch.cat([bert1, bert2], 1)
        all_phoneme_ids = torch.LongTensor(phones1+phones2).to(device).unsqueeze(0)
    else:
        bert = bert2
        all_phoneme_ids = torch.LongTensor(phones2).to(device).unsqueeze(0)

    bert = bert.to(device).unsqueeze(0)
    all_phoneme_len = torch.tensor([all_phoneme_ids.shape[-1]]).to(device)
    prompt = prompt_semantic.unsqueeze(0).to(device)
    t2 = ttime()
    with torch.no_grad():
        # pred_semantic = t2s_model.model.infer(
        pred_semantic, idx = t2s_model.model.infer_panel(
            all_phoneme_ids,
            all_phoneme_len,
            None if ref_free else prompt,
            bert,
            # prompt_phone_len=ph_offset,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            early_stop_num=hz * max_sec,
        )
    t3 = ttime()
    # print(pred_semantic.shape,idx)
    if type(idx) == list:
        idx = idx[0]
        pred_semantic = pred_semantic[0][-idx:].unsqueeze(0).unsqueeze(0)
        print(f"pred_type:{type(pred_semantic)}")
    else:
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
    max_audio=np.abs(audio).max()#简单防止16bit爆音
    if max_audio>1:audio/=max_audio
    t4 = ttime()
    print("%.3f\t%.3f\t%.3f\t%.3f" % (t1 - t0, t2 - t1, t3 - t2, t4 - t3))
    return audio

def get_phones_and_bert(text,language):
    if language in {"en","all_zh","all_ja"}:
        language = language.replace("all_","")
        if language == "en":
            LangSegment.setfilters(["en"])
            formattext = " ".join(tmp["text"] for tmp in LangSegment.getTexts(text))
        else:
            # 因无法区别中日文汉字,以用户输入为准
            formattext = text
        while "  " in formattext:
            formattext = formattext.replace("  ", " ")
        phones, word2ph, norm_text = clean_text_inf(formattext, language)
        if language == "zh":
            bert = get_bert_feature(norm_text, word2ph).to(device)
        else:
            bert = torch.zeros(
                (1024, len(phones)),
                dtype=torch.float16 if is_half == True else torch.float32,
            ).to(device)
    elif language in {"zh", "ja","auto"}:
        textlist=[]
        langlist=[]
        LangSegment.setfilters(["zh","ja","en","ko"])
        if language == "auto":
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "ko":
                    langlist.append("zh")
                    textlist.append(tmp["text"])
                else:
                    langlist.append(tmp["lang"])
                    textlist.append(tmp["text"])
        else:
            for tmp in LangSegment.getTexts(text):
                if tmp["lang"] == "en":
                    langlist.append(tmp["lang"])
                else:
                    # 因无法区别中日文汉字,以用户输入为准
                    langlist.append(language)
                textlist.append(tmp["text"])
        print(textlist)
        print(langlist)
        phones_list = []
        bert_list = []
        norm_text_list = []
        for i in range(len(textlist)):
            lang = langlist[i]
            phones, word2ph, norm_text = clean_text_inf(textlist[i], lang)
            bert = get_bert_inf(phones, word2ph, norm_text, lang)
            phones_list.append(phones)
            norm_text_list.append(norm_text)
            bert_list.append(bert)
        bert = torch.cat(bert_list, dim=1)
        phones = sum(phones_list, [])
        norm_text = ''.join(norm_text_list)

    return phones,bert.to(dtype),norm_text

# from https://github.com/RVC-Boss/GPT-SoVITS/pull/448

import tempfile, io, wave
from pydub import AudioSegment

# from https://huggingface.co/spaces/coqui/voice-chat-with-mistral/blob/main/app.py
def wave_header_chunk(frame_input=b"", channels=1, sample_width=2, sample_rate=32000):
    # This will create a wave header then append the frame input
    # It should be first on a streaming wav file
    # Other frames better should not have it (else you will hear some artifacts each chunk start)
    wav_buf = io.BytesIO()
    with wave.open(wav_buf, "wb") as vfout:
        vfout.setnchannels(channels)
        vfout.setsampwidth(sample_width)
        vfout.setframerate(sample_rate)
        vfout.writeframes(frame_input)

    wav_buf.seek(0)
    return wav_buf.read()


def get_streaming_tts_wav(
    ref_wav_path,
    prompt_text,
    prompt_language,
    text,
    text_language,
    how_to_cut=i18n("不切"), 
    top_k=20,
    top_p=0.6,
    temperature=0.6,
    ref_free=False,
    byte_stream=True,
):
    chunks = get_tts_wav(
        ref_wav_path=ref_wav_path,
        prompt_text=prompt_text,
        prompt_language=prompt_language,
        text=text,
        text_language=text_language,
        how_to_cut=how_to_cut,
        top_k=top_k,
        top_p=top_p,
        temperature=temperature,
        ref_free=ref_free,
        stream=True,
    )

    if byte_stream:
        yield wave_header_chunk()
        for chunk in chunks:
            assert isinstance(chunk, bytes), "Chunk must be bytes"
            yield chunk
    else:
        # Send chunk files
        i = 0
        format = "wav"
        for chunk in chunks:
            i += 1
            file = f"{tempfile.gettempdir()}/{i}.{format}"
            segment = AudioSegment(chunk, frame_rate=32000, sample_width=2, channels=1)
            segment.export(file, format=format)
            yield file
