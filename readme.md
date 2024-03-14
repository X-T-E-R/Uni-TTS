
[**English**](./README.md) | [**中文简体**](./docs/cn/README.md) 

---

## Welcome
This is an inference-specialized plugin developed on top of GPT-SoVITS, designed to enhance your text-to-speech (TTS) experience by offering a user-friendly API interface over the original functionalities. Our plugin, acting as a submodule, enriches the original GPT-SoVITS project, making voice synthesis more accessible and versatile for all users.
### **Suite Overview**
We offer a unified API interface that simplifies the voice synthesis process. This includes basic backend functionalities of a voice synthesis engine such as selecting speakers, speed, and emotional tones, as well as advanced options like audio format selection, streaming synthesis, and additional GSV-specific parameters like text segmentation, batch size, and GPT diffusion parameters.
Additionally, we provide two accompanying Gradio applications: one for the frontend interface, facilitating voice synthesis operations, and another for model management, where users can customize character presets and emotional reference audios for a more personalized voice synthesis experience.
### **Core Features**

- **High-Level Abstract Interface**: Simplifies user interaction by abstracting away complex model paths and technical parameters, allowing easy import and selection of characters and emotions through intuitive "character cards."
- **Comprehensive TTS Engine Support**: Includes all essential text-to-speech engine capabilities such as speaker selection, speed adjustment, and volume control, ensuring users can tailor the voice output to their specific needs.
- **One-Click Operation**: Streamlines the process from character import to voice synthesis, facilitating a one-click operation experience.
- **User-Friendly Design**: Aimed at providing a clear, simple, and easy-to-use experience for users of all technical backgrounds.
- **High Compatibility and Extensibility**: The API is designed for compatibility with different platforms and applications, from mobile apps and desktop software to web services, requiring a server or local computer running the backend service. We also offer extensive API documentation for developers, supporting custom development and extension.
### **Installation Guide**
Installing our plugin is straightforward, even given its innovative approach. You have two main options: self-deployment or using our provided Windows integration package.
#### **1. Self-Deployment**
Given our aggressive development strategy and the extensive customization over the original project's experimental branch, "fast_inference_", it's recommended to use our specifically prepared fork version, GSVI (GPT-SoVITS-Inference), optimized for extended functionalities and plugin compatibility.

- **GSVI Source**: [GSVI on GitHub](https://github.com/X-T-E-R/GPT-SoVITS-Inference)

Follow the installation instructions provided on the page.
#### **2. Integration Package (For Windows Users)**
We highly recommend Windows users to opt for the integration package, streamlined for the Windows platform, which includes pre-trained models, a Python environment, and an Easy Language-written launcher.

- **Integration Package Download**: Access our documentation on [Yuque](https://www.yuque.com/xter/zibxlp/kkicvpiogcou5lgp) for the download link and detailed installation and usage guide.
### **Usage Instructions**

- **Flask Backend Program**: `src/tts_backend.py``
- **Gradio Frontend Application**: `src/TTS_Webui.py`
- **Gradio Model Management Interface**: `src/Character_Manager.py`

For API documentation, visit our Yuque documentation page: [API Documentation](https://www.yuque.com/xter/zibxlp/knu8p82lb5ipufqy). Note that the updates in the **doc** folder's markdown files might not be immediate.
### **Next Steps**

- **Explore Documentation**: We strongly recommend reading our documentation and usage instructions before starting, available at: [Documentation Link](https://www.yuque.com/xter/zibxlp).
- **Community Support**: If you encounter any issues during installation or use, don't hesitate to join our community or consult the FAQ. Our community is vibrant, with many experienced users and developers ready to assist newcomers. QQ Group: 863760614

By following these steps, you should be able to easily begin using our project, whether for voice synthesis experiments or developing your applications. We look forward to seeing how you utilize GSVI to bring your creative projects to life!