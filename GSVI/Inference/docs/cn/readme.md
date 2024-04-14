[**English**](../../readme.md) | [**简体中文**](./readme.md) 

---
## 项目介绍
欢迎您使用我们的项目！
这是一个基于GPT-SoVITS开发的，专门为推理任务设计的插件：GSV是一款优秀的人工智能语音合成引擎，我们在此基础上提供了一个更用户友好的api接口。
我们的插件以一种子模块的方式附着在原始GPT-SoVITS项目之上，为用户带来更加丰富和便捷的体验。
### 套件说明
我们提供了一个统一的API接口，让所有语音合成任务都能轻松地通过这个接口来完成。它具备了一个语音合成引擎后端的基本功能，例如您可以指定发音人、语速、与角色情绪，或者选择返回的音频格式、是否使用流式合成；也有许多与GSV项目相关的参数可选，例如文字的切分方法，batch size 与一些GPT的扩散参数。
此外，我们还额外提供了两个配套的gradio程序：一个是前端界面，便于用户进行语音合成操作；另一个是模型管理界面，用户可以在此自定义角色预设情感的参考音频，让语音合成更加个性化。

### 核心特点

- **高级抽象接口**：用户无需直接接触复杂的模型路径或技术参数，只需通过直观的“人物卡”导入与选择所需角色和情绪。
- **全面的TTS引擎支持**：我们的插件支持所有基本的文本到语音（TTS）引擎功能，包括但不限于发音人选择、语速调节、音量控制等，确保用户可以根据具体需要调整语音输出。
- **一键式操作**：简化的操作流程，让用户可以快速从角色导入到语音合成，实现一键运行。
- **便捷的模型共享**：只需要放入别人分享的角色模型文件夹，即可快速使用
- **用户友好设计**：旨在为所有用户提供清晰、简单、易用的体验，无论技术背景如何。
- **高度的兼容性和扩展性**：api接口的设计考虑到了与不同平台和应用的兼容性，无论是移动应用、桌面软件还是网络服务，都可以轻松集成和使用（需要您有一台正在运行后端服务的服务器/ 在您本地电脑上运行）。同时，我们也为开发者提供了丰富的API文档，支持自定义开发和扩展。
## 安装指南
安装我们的插件其实非常简单和直接，即使我们的方法相对来说更具创新性。下面是一个简化和明晰的步骤指南，旨在帮助您快速开始使用。
整体来说，您可以选择自行部署或者使用我们提供的Windows整合包
### 自行部署
使用我们的优化分支，[GSVI on GitHub](https://github.com/X-T-E-R/GPT-SoVITS-Inference)，以获得扩展功能和插件兼容性。按照提供的安装说明进行操作。

### 预打包版本（适用于Windows用户）

Windows用户可以使用我们的预打包版本，其中包括预训练的模型、Python环境和一个用易语言编写的启动器。下载预打包版本并按照我们的[Yuque文档页面](https://www.yuque.com/xter/zibxlp/kkicvpiogcou5lgp)上的安装指南操作。

## 使用说明
### TTS

#### 通过单一gradio文件开始

- Gradio应用程序：`../app.py`（位于GSVI的根目录）

#### 通过后端和前端模块开始

- Flask后端程序：`src/tts_backend.py`
- Gradio前端应用程序：`src/TTS_Webui.py`
- 使用我们的API的其他前端应用程序或服务

### 模型管理

- Gradio模型管理界面：`src/Character_Manager.py`

有关API文档，请访问我们的[Yuque文档页面](https://www.yuque.com/xter/zibxlp/knu8p82lb5ipufqy)。

## 后续步骤

- **探索文档**：我们强烈建议您在开始使用之前，仔细阅读我们的文档和使用说明。这将帮助您更好地了解所有功能和可用的定制选项。文档链接：[https://www.yuque.com/xter/zibxlp](https://www.yuque.com/xter/zibxlp)
- **社区支持**：如果在安装或使用过程中遇到任何问题，不要犹豫加入我们的社区或查阅FAQ。我们的社区非常活跃，很多经验丰富的用户和开发者都乐于帮助新手。QQ：`863760614`

## Credits

这是一个适用于 [GPT-soVITS](https://github.com/RVC-Boss/GPT-SoVITS) 的插件
部分代码（比如经典推理部分）沿用了原始项目。

特别感谢以下项目

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

通过遵循这些步骤，您应该能够轻松地开始使用我们的项目，无论是进行语音合成实验，还是开发自己的应用。我们期待看到您如何使用GSVI来实现您的创意和项目！

