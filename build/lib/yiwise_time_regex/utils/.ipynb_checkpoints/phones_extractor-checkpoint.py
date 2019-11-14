# coding=utf-8
import re
from itertools import groupby
from phone import Phone
import phonenumbers

class PhonesExtractor(object):
    def __init__(self):
        pass

    def parse_location(self,phone_number,nation='CHN'):
        if nation == 'CHN':
            p = Phone()
            res = p.find(phone_number)
        else:
            x = phonenumbers.parse(phone_number,'GB')
            if phonenumbers.is_possible_number(x):
                res = x
        return res

    def parse(self,text,nation='CHN'):
        if text=='':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        if nation=='CHN':
            phone_pattern = r'^((\+86)?([- ])?)?(|(13[0-9])|(14[0-9])|(15[0-9])|(17[0-9])|(18[0-9])|(19[0-9]))([- ])?\d{3}([- ])?\d{4}([- ])?\d{4}$'
        phones = []
        for eng_text in eng_split_texts_clean:
            result = re.match(phone_pattern, eng_text, flags=0)
            if result:
                phones.append(result.string.replace('+86','').replace('-',''))
        return phones

    def replace_chinese(self,text):
        if text=='':
            return []
        filtrate = re.compile(u'[\u4E00-\u9FA5]')
        text_without_chinese = filtrate.sub(r' ', text)
        return text_without_chinese
