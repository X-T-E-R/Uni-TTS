# from text_utils.segmenter import SentenceSegmenter
# from text_utils.tokenizer import Tokenizer
#https://github.com/numb3r3/text_utils
# from polyglot.text import Text
import requests,re,jieba
import concurrent.futures

text = '''皆さん、我在インターネット上看到someone把几国language混在一起speak。我看到之后be like：それは我じゃないか！私もtry一tryです。虽然是混乱している句子ですけど、中文日本語プラスEnglish、挑戦スタート！我study日本語的时候，もし有汉字，我会很happy。Bueause中国人として、when I see汉字，すぐに那个汉字がわかります。But 我hate外来語、什么マクドナルド、スターバックス、グーグル、ディズニーランド、根本记不住カタカナhow to写、太難しい。以上です，byebye！'''
text = '''皆さん我在インターネット上看到someone把几国!language混在一起speak我看到之后be like それは我じゃないか私もtry一tryです虽然是混乱している句子ですけど中文日本語プラスEnglish挑戦スタート我study日本語的时候もし有汉字我会很happyBueause中国人としてwhen I see汉字すぐに那个汉字がわかりますBut 我hate外来語什么マクドナルドスターバックスグーグルディズニーランド根本记不住カタカナhow to写太難しい以上ですbyebye！'''

# textlist = SentenceSegmenter(token_limits=10).segment(text)
# text_mixed = Text('\n'.join(textlist)).sentences
#
# for text in text_mixed:
#     print(text)
#     print('\n')

def split_text(text, max_length):
    text = text.lower()

    text = re.sub(r'[\,\，\；\;\、]+', ',', text)  # 制表符替换成空格
    text = re.sub(r'[\？\?]+', '?', text)  # 制表符替换成空格
    text = re.sub(r'[\！\!]+', '!', text)  # 制表符替换成空格
    text = re.sub(r'[\。\.]+', '.', text)  # 制表符替换成空格
    text = re.sub(r'[\"\'\’]+', "'", text)  # 制表符替换成空格
    text = re.sub(r'[\(\（\{\[\)\）\]\}\|\:\：\/\_]', ' ', text)  # 左括号替换成中文括号
    text = re.sub('[\n\r]+', ',', text)  # 换行符替换成逗号
    text = re.sub('[\s]+', ' ', text)  # 换行符替换成逗号

    symbols = {
        "&": "和",
        "\\": "斜杠",
        "/": "反斜杠",
        "+": "加",
        "-": "杠",
        "_": "杠",
        "*": "星",
        "%": "百分比",
        "=": "等"
    }
    # 遍历字典中的每一对键值
    for symbol, word in symbols.items():
        # 构造一个正则表达式，匹配中文旁边的特殊符号
        pattern = f"(?<=\u4e00-\u9fa5){re.escape(symbol)}(?=\u4e00-\u9fa5)"
        # 用对应的文字替换匹配到的特殊符号
        text = re.sub(pattern, word, text)

    symbols2 = {
        "a": "唉",
        "b": "比",
        "c": "西",
        "d": "第",
        "e": "衣",
        "f": "爱抚",
        "g": "记",
        "h": "唉取",
        "i": "爱",
        "j": "姐",
        "k": "克唉",
        "l": "唉欧",
        "m": "唉母",
        "n": "恩",
        "o": "欧",
        "p": "屁",
        "q": "口",
        "r": "阿",
        "s": "唉撕",
        "t": "体",
        "u": "油",
        "v": "喂",
        "w": "打不留",
        "x": "唉克撕",
        "y": "外",
        "z": "热",
    }

    # 遍历字典中的每一对键值
    for symbol, word in symbols2.items():
        # 构造一个正则表达式，匹配中文旁边的特殊符号
        pattern = f"(?<=[^a-zA-Z0-9\s]){re.escape(symbol)}(?=[^a-zA-Z0-9\s])"
        # 用对应的文字替换匹配到的特殊符号
        text = re.sub(pattern, word, text)

    text = re.sub(r'[\\\_\-\&\+\-\*\%\=]+(?![a-zA-Z\d])', '', text)  # 引号旁边没有英文则去掉



    '''
    最小值 = max_length*0.5
    最大值 = max_length*1.5
    对于result中的key是'zh'的项目的值 传入 concurrent.futures多线程  用jieba分词 ，分好的词进行累加，叠加词的长度进行范围判断，
    大于最小值后遇到[^\u4e00-\u9fa5\d]的元素叠加上后结束累加作为一个片段。如果没有遇到就继续累加，直到不超过最大值时停止，作为一个片段。
    如果一开始就大于max_length，也作为一个片段。片段按顺序组合成列表，重构对应result中的相应字典元素的值
    对于result中的key是'en'的项目的值,按字数累加，叠加字数长度进行范围判断，
    大于最小值后遇到[^a-zA-Z\d\s]的字叠加上后结束累加作为一个片段。如果没有遇到就继续累加，直到不超过最大值时，后面如果不是[^a-zA-Z],就以到最大值的相对值最小的符合[^a-zA-Z]的位置，作为一个片段。
    片段按顺序组合成列表，重构对应result中的相应字典元素的值
    无论 en 还是 zh 如果出现单独一段全是特殊符号空格的，就把这一段从元素值的列表中丢弃
    '''
    # 提示如下
    min_length = max_length * 0.5
    max_length = max_length * 1.8

    def split_words(text):
        words = jieba.cut(text)
        segments = []
        segment = ""
        length = 0
        for word in words:
            segment += word
            length += len(word)
            print(word)
            if length > min_length and (
                    re.search(r'[^\u4e00-\u9fa5\d]', word) or re.search(r'[^a-zA-Z\d\s\']', word)):
                segments.append(segment)
                segment = ""
                length = 0
            elif length > max_length:
                segments.append(segment)
                segment = ""
                length = 0

        if segment:
            segments.append(segment)
        return segments

    result = split_words(text)

    return result

def send(speaker,text,index):
    
    print(f"speaker:{speaker},text:{text},index:{index}")
    response = requests.get(f'http://127.0.0.1:5000/tts?text={text}&cha={speaker}')
    with open(f'tmp_audio/{str(index)}.wav','ab') as f:
        f.write(response.content)

index = 0

speakers = ['银狼','HuTao']
# speakers = ['1980US']

textlist = split_text(text, 20)

SK_TEXT_INDEX = [(speakers[index%len(speakers)], text, index+1) for index in range(10)]

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    tasks = [executor.submit(send, a[0],a[1], a[2]) for a in SK_TEXT_INDEX]
concurrent.futures.wait(tasks)