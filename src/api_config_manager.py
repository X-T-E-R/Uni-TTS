import os, sys, json


class API_Config():
    def __init__(self, config_path = None):
        self.config_path = config_path
        assert os.path.exists(self.config_path), f"配置文件不存在: {self.config_path}"
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config:dict = json.load(f)
                
                self.tts_host = config.get("tts_host", "0.0.0.0")
                self.tts_port = config.get("tts_port", 5000)
                
                locale_language = str(config.get("locale", "auto"))
                self.locale_language = None if locale_language.lower() == "auto" else locale_language
                
                self.enabled_adapters = config.get("enabled_adapters", ["gsv_fast"])
                self.default_adapter = self.enabled_adapters[0]

api_config = API_Config(os.path.join("configs", "api_config.json"))