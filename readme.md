[**English**](./readme.md) | [**简体中文**](./docs/cn/readme.md) 

---
# TTS-for-GPT-SoVITS: GPT-SoVITS Inference Plugin

Welcome to GSVI, an inference-specialized plugin built on top of GPT-SoVITS to enhance your text-to-speech (TTS) experience with a user-friendly API interface. This plugin enriches the [original GPT-SoVITS project](https://github.com/RVC-Boss/GPT-SoVITS), making voice synthesis more accessible and versatile.

## Features

- High-level abstract interface for easy character and emotion selection
- Comprehensive TTS engine support (speaker selection, speed adjustment, volume control)
- User-friendly design for everyone
- Simply place the shared character model folder, and you can quickly use it.
- High compatibility and extensibility for various platforms and applications (for example: SillyTavern)

## Installation

### Self-Deployment
Use our optimized fork, [GSVI on GitHub](https://github.com/X-T-E-R/GPT-SoVITS-Inference), for extended functionalities and plugin compatibility. Follow the installation instructions provided.

### Prezip (For Windows)
Windows users can use our prezip, which includes pre-trained models, a Python environment, and a launcher written in Easy-Programming-Language. Download the prezip and follow the installation guide on our [Yuque documentation page](https://www.yuque.com/xter/zibxlp/kkicvpiogcou5lgp).

## Usage

### TTS
#### Start with a single gradio file
- Gradio Application: `../app.py`  (In the root of GSVI)
#### Start with backend and frontend mod
- Flask Backend Program: `src/tts_backend.py`
- Gradio Frontend Application: `src/TTS_Webui.py`
- Other Frontend Applications or Services Using Our API 
### Model Management
- Gradio Model Management Interface: `src/Character_Manager.py`

For API documentation, visit our [Yuque documentation page](https://www.yuque.com/xter/zibxlp/knu8p82lb5ipufqy).

## Getting Started

1. Read our [documentation and usage instructions](https://www.yuque.com/xter/zibxlp) before starting.
2. Go and see our [huggingface demo](https://huggingface.co/spaces/XTer123/GSVI_ShowPage)
3. If you encounter issues, join our community or consult the FAQ. QQ Group: 863760614

We look forward to seeing how you use GSVI to bring your creative projects to life!

## Credits

This fork is a plugin for [GPT-soVITS](https://github.com/RVC-Boss/GPT-SoVITS) project. 
Some of the codes (e.g. the classic inference part) are using its original code.

Special thanks to the following projects and contributors:

### Theoretical
- [ar-vits](https://github.com/innnky/ar-vits)
- [SoundStorm](https://github.com/yangdongchao/SoundStorm/tree/master/soundstorm/s1/AR)
- [vits](https://github.com/jaywalnut310/vits)
- [TransferTTS](https://github.com/hcy71o/TransferTTS/blob/master/models.py#L556)
- [contentvec](https://github.com/auspicious3000/contentvec/)
- [hifi-gan](https://github.com/jik876/hifi-gan)
- [fish-speech](https://github.com/fishaudio/fish-speech/blob/main/tools/llama/generate.py#L41)
### Pretrained Models
- [Chinese Speech Pretrain](https://github.com/TencentGameMate/chinese_speech_pretrain)
- [Chinese-Roberta-WWM-Ext-Large](https://huggingface.co/hfl/chinese-roberta-wwm-ext-large)
### Text Frontend for Inference
- [paddlespeech zh_normalization](https://github.com/PaddlePaddle/PaddleSpeech/tree/develop/paddlespeech/t2s/frontend/zh_normalization)
- [LangSegment](https://github.com/juntaosun/LangSegment)
### WebUI Tools
- [FFmpeg](https://github.com/FFmpeg/FFmpeg)
- [gradio](https://github.com/gradio-app/gradio))
  
## Thanks to all contributors for their efforts


---
## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=X-T-E-R/TTS-for-GPT-soVITS&type=Date)](https://star-history.com/#X-T-E-R/TTS-for-GPT-soVITS&Date)
