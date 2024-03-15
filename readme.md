
[**English**](./readme.md) | [**简体中文**](./docs/cn/readme.md) 

---
# TTS-for-GPT-SoVITS: GPT-SoVITS Inference Plugin

Welcome to GSVI, an inference-specialized plugin built on top of GPT-SoVITS to enhance your text-to-speech (TTS) experience with a user-friendly API interface. This plugin enriches the [original GPT-SoVITS project](https://github.com/RVC-Boss/GPT-SoVITS), making voice synthesis more accessible and versatile.

## Features

- High-level abstract interface for easy character and emotion selection
- Comprehensive TTS engine support (speaker selection, speed adjustment, volume control)
- User-friendly design for everyone
- High compatibility and extensibility for various platforms and applications (for example: SillyTavern)

## Installation

### Self-Deployment
Use our optimized fork, [GSVI on GitHub](https://github.com/X-T-E-R/GPT-SoVITS-Inference), for extended functionalities and plugin compatibility. Follow the installation instructions provided.

### Prezip (For Windows)
Windows users can use our prezip, which includes pre-trained models, a Python environment, and a launcher written in Easy-Programming-Language. Download the prezip and follow the installation guide on our [Yuque documentation page](https://www.yuque.com/xter/zibxlp/kkicvpiogcou5lgp).

## Usage

### TTS
#### Start with a single gradio file
- Gradio Application: `src/Exhibition_Webui.py`
#### Start with backend and frontend mod
- Flask Backend Program: `src/tts_backend.py`
- Gradio Frontend Application: `src/TTS_Webui.py`
- Other Frontend Applications or Services Using Our API 
### Manage Tools
- Gradio Model Management Interface: `src/Character_Manager.py`

For API documentation, visit our [Yuque documentation page](https://www.yuque.com/xter/zibxlp/knu8p82lb5ipufqy).

## Getting Started

1. Read our [documentation and usage instructions](https://www.yuque.com/xter/zibxlp) before starting.
2. Go and see our [huggingface demo](https://huggingface.co/spaces/XTer123/GSVI_ShowPage)
3. If you encounter issues, join our community or consult the FAQ. QQ Group: 863760614

We look forward to seeing how you use GSVI to bring your creative projects to life!
