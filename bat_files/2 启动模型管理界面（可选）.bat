CHCP 65001
@echo off 
cd ../
echo 尝试启动程序
start  http://127.0.0.1:9868
runtime\python.exe ./TTS-for-GPT-soVITS/src/Character_Manager.py

pause