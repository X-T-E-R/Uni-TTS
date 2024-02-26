CHCP 65001
@echo off 
cd ../
echo 尝试启动后端程序
runtime\python.exe ./TTS-for-GPT-soVITS/src/tts_backend.py

pause