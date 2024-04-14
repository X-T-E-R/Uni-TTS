# from text_utils.segmenter import SentenceSegmenter
# from text_utils.tokenizer import Tokenizer
#https://github.com/numb3r3/text_utils
# from polyglot.text import Text
import requests,re,jieba
import concurrent.futures
import os



def send(speaker,text,index):
    
    # print(f"speaker:{speaker},text:{text},index:{index}")
    from time import time
    start = time()
    response = requests.get(f'http://127.0.0.1:5000/tts?text={text}&cha={speaker}&top_k=5')
    end = time()
    print(f"speaker:{speaker},index:{index},time:{end-start}")
    os.makedirs('tmp_audio',exist_ok=True)
    with open(f'tmp_audio/{str(index)}.wav','ab') as f:
        f.write(response.content)



text = '''我是一个粉刷匠，粉刷本领强。我要把那新房子，刷得更漂亮。刷了房顶又刷墙，刷子像飞一样。哎呀我的小鼻子，变呀变了样。'''
speakers = ['银狼','HuTao']
count = 3



SK_TEXT_INDEX = [(speakers[index%len(speakers)], text, index+1) for index in range(count)]

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    tasks = [executor.submit(send, a[0],a[1], a[2]) for a in SK_TEXT_INDEX]
concurrent.futures.wait(tasks)