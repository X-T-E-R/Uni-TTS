import re

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
