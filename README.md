文档待更新
请暂时不要用这个项目

如果想使用GPT-soVITS的推理特化版，请直接看：https://github.com/X-T-E-R/GPT-SoVITS-Inference

本项目意图在于让使用各类语音合成引擎的方式变得统一，支持多种语音合成引擎适配器，允许直接作为模组使用或启动后端服务。

目前已经实现的部分：
1. 框架
2. 解析器：参数解析器（可指定别名、已反向兼容很多其它项目）、类微软请求的解析器
3. Adapter：GPT-soVITS Adapter
4. fastAPI的返回：File、Stream

文档待更新
请暂时不要用这个项目

## Credits

### 整段使用的代码：
1. 内部的 `Adapters/gsv_fast` 文件夹主要来自[GPT-soVITS](https://github.com/RVC-Boss/GPT-SoVITS)项目的`fast_inference_`分支
2. `tools/i18n` 魔改自 [GSVI](https://github.com/X-T-E-R/GPT-SoVITS-Inference) ，基于 [i18n](https://github.com/RVC-Boss/GPT-SoVITS/tree/main/tools/i18n)

### 感谢所有有关项目与贡献者

#### Theoretical

- [ar-vits](https://github.com/innnky/ar-vits)
- [SoundStorm](https://github.com/yangdongchao/SoundStorm/tree/master/soundstorm/s1/AR)
- [vits](https://github.com/jaywalnut310/vits)
- [TransferTTS](https://github.com/hcy71o/TransferTTS/blob/master/models.py#L556)
- [contentvec](https://github.com/auspicious3000/contentvec/)
- [hifi-gan](https://github.com/jik876/hifi-gan)
- [fish-speech](https://github.com/fishaudio/fish-speech/blob/main/tools/llama/generate.py#L41)

#### Pretrained Models

- [Chinese Speech Pretrain](https://github.com/TencentGameMate/chinese_speech_pretrain)
- [Chinese-Roberta-WWM-Ext-Large](https://huggingface.co/hfl/chinese-roberta-wwm-ext-large)

#### Text Frontend for Inference

- [paddlespeech zh_normalization](https://github.com/PaddlePaddle/PaddleSpeech/tree/develop/paddlespeech/t2s/frontend/zh_normalization)
- [LangSegment](https://github.com/juntaosun/LangSegment)

#### WebUI Tools

- [ultimatevocalremovergui](https://github.com/Anjok07/ultimatevocalremovergui)
- [audio-slicer](https://github.com/openvpi/audio-slicer)
- [SubFix](https://github.com/cronrpc/SubFix)
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [gradio](https://github.com/gradio-app/gradio)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [FunASR](https://github.com/alibaba-damo-academy/FunASR)