import sys
sys.path.insert(0, "GPT_SoVITS")
from text import cleaned_text_to_sequence
from text.cleaner import clean_text
import LangSegment
import re

splits = {"，", "。", "？", "！", ",", ".", "?", "!", "~", ":", "：", "—", "…", }

def clean_text_inf(text, language):
    phones, word2ph, norm_text = clean_text(text, language)
    phones = cleaned_text_to_sequence(phones)
    return phones, word2ph, norm_text





def get_first(text):
    pattern = "[" + "".join(re.escape(sep) for sep in splits) + "]"
    text = re.split(pattern, text)[0].strip()
    return text

def splite_en_inf(sentence, language):
    """
    Split the input sentence into a list of text segments and language tags.

    Args:
        sentence (str): The input sentence to be split.
        language (str): The language tag of the input sentence.

    Returns:
        tuple: A tuple containing two lists - textlist and langlist.
            - textlist: A list of text segments extracted from the input sentence.
            - langlist: A list of language tags corresponding to each text segment.
    """
    pattern = re.compile(r'[a-zA-Z ]+')
    textlist = []
    langlist = []
    pos = 0
    for match in pattern.finditer(sentence):
        start, end = match.span()
        if start > pos:
            textlist.append(sentence[pos:start])
            langlist.append(language)
        textlist.append(sentence[start:end])
        langlist.append("en")
        pos = end
    if pos < len(sentence):
        textlist.append(sentence[pos:])
        langlist.append(language)
    # Merge punctuation into previous word
    for i in range(len(textlist)-1, 0, -1):
        if re.match(r'^[\W_]+$', textlist[i]):
            textlist[i-1] += textlist[i]
            del textlist[i]
            del langlist[i]
    # Merge consecutive words with the same language tag
    i = 0
    while i < len(langlist) - 1:
        if langlist[i] == langlist[i+1]:
            textlist[i] += textlist[i+1]
            del textlist[i+1]
            del langlist[i+1]
        else:
            i += 1

    return textlist, langlist


def merge_short_text_in_array(texts, threshold):
    if (len(texts)) < 2:
        return texts
    result = []
    text = ""
    for ele in texts:
        text += ele
        if len(text) >= threshold:
            result.append(text)
            text = ""
    if (len(text) > 0):
        if len(result) == 0:
            result.append(text)
        else:
            result[len(result) - 1] += text
    return result


def auto_cut(inp):
    # if not re.search(r'[^\w\s]', inp[-1]):
    # inp += '。'
    inp = inp.strip("\n")
    
    split_punds = r'[?!。？！~：]'
    if inp[-1] not in split_punds:
        inp+="。"
    items = re.split(f'({split_punds})', inp)
    items = ["".join(group) for group in zip(items[::2], items[1::2])]

    def process_commas(text):

        separators = ['，', ',', '、', '——', '…']
        count = 0
        processed_text = ""
        for char in text:
            processed_text += char
            if char in separators:
                if count > 12:
                    processed_text += '\n'
                    count = 0
            else:
                count += 1  # 对于非分隔符字符，增加计数
        return processed_text

    final_items=[process_commas(item) for item in items]


    return "\n".join(final_items)
