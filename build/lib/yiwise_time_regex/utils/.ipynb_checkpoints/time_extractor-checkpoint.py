# coding=utf-8
import regex as re
import arrow
import copy
import json
import os
import codecs
import pickle
from itertools import groupby
import copy
import numpy as np
from cocoNLP.config.basic.time_nlp import TimeNormalizer
from cocoNLP.config.basic.time_nlp.RangeTimeEnum import RangeTimeEnum
from cocoNLP.config.basic.time_nlp.StringPreHandler import StringPreHandler
try:
    from cocoNLP.config.basic.time_nlp.LunarSolarConverter.LunarSolarConverter import *
except:
    from cocoNLP.config.basic.time_nlp.LunarSolarConverter import *

class TimePoint(object):
    def __init__(self,tunit=[-1, -1, -1, -1, -1, -1]):
        self.tunit = tunit

# 时间语句分析
class TimeUnit(object):
    def __init__(self, exp_time, normalizer, contextTp):
        self._noyear = False
        self.exp_time = exp_time
        self.normalizer = normalizer
        self.tp = TimePoint([-1,-1,-1,-1,-1,-1])
        self.tp_origin = contextTp
        self.tp_origin_copy = copy.deepcopy(contextTp)
        self.isFirstTimeSolveContext = True
        self.isAllDayTime = True
        self.time = arrow.now()
        self.time_normalization()
        
    def get_cur_time(self):
        return self.tp_origin_copy

    def time_normalization(self):
        self.tp_origin = self.get_cur_time()
        self.norm_setnow()
        self.norm_setyear()
        self.norm_setmonth()
        self.norm_setday()
        self.norm_setmonth_fuzzyday()
        self.norm_setBaseRelated()
        self.norm_setCurRelated()
        self.norm_sethour()
        self.norm_setminute()
        self.norm_setsecond()
        self.norm_setSpecial()
        #self.norm_setSpanRelated()
        self.norm_setHoliday()
        
#         # 判断是时间点还是时间区间
#         flag = True
#         print(self.tp.tunit)
#         for i in range(0, 4):
#             if self.tp.tunit[i] != -1:
#                 flag = False
#         if flag:
#             self.normalizer.isTimeSpan = True

#         if self.normalizer.isTimeSpan:
#             now = arrow.now()
#             days = 0
#             if self.tp.tunit[0] > 0:
#                 days += (365 * (self.tp.tunit[0] - now.year))
#             if self.tp.tunit[1] > 0:
#                 days += (30 * (self.tp.tunit[1] - now.month))
#             if self.tp.tunit[2] > 0:
#                 days += (self.tp.tunit[2] - now.day)
#             tunit = self.tp.tunit
#             for i in range(3, 6):
#                 if self.tp.tunit[i] < 0:
#                     tunit[i] = 0
#             seconds = (tunit[3]) * 3600 + (tunit[4]) * 60 + tunit[5]
            
#             if seconds == 0 and days == 0:
#                 self.normalizer.invalidSpan = True
#             self.normalizer.timeSpan = self.genSpan(days, seconds)
#             return

        time_grid = self.normalizer.timeBase.split('-')
        tunitpointer = 5
        while tunitpointer >= 0 and self.tp.tunit[tunitpointer] < 0:
            tunitpointer -= 1
        for i in range(0, tunitpointer):
            if self.tp.tunit[i] < 0:
                self.tp.tunit[i] = int(time_grid[i])

        self.time = self.genTime(self.tp.tunit)

    def genSpan(self, days, seconds):
        day = int(seconds / (3600 * 24))
        h = int((seconds % (3600 * 24)) / 3600)
        m = int(((seconds % (3600 * 24)) % 3600) / 60)
        s = int(((seconds % (3600 * 24)) % 3600) % 60)
        return str(days + day) + ' days, ' + "%d:%02d:%02d" % (h, m, s)

    def genTime(self, tunit):
        time = arrow.get('1970-01-01 00:00:00')
        if tunit[0] > 0:
            time = time.replace(year=int(tunit[0]))
        if tunit[1] > 0:
            time = time.replace(month=tunit[1])
        if tunit[2] > 0:
            time = time.replace(day=tunit[2])
        if tunit[3] > 0:
            time = time.replace(hour=tunit[3])
        if tunit[4] > 0:
            time = time.replace(minute=tunit[4])
        if tunit[5] > 0:
            time = time.replace(second=tunit[5])
        return time

    def norm_setnow(self):
        rule = u"现在|这时候|这个时候|这个点|此时|当下|此刻"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit = [int(item) for item in arrow.now().format('YYYY-MM-DD-HH-mm-ss').split('-')]
            self.tp.tunit[-1] = -1
    
    def norm_setyear(self):
        """
        年-规范化方法--该方法识别时间表达式单元的年字段
        :return:
        """
        # 一位数表示的年份
        rule = u"(?<![0-9])[0-9]{1}(?=年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            #self.normalizer.isTimeSpan = True
            year = int(match.group())
            self.tp.tunit[0] = year

        # 两位数表示的年份
        rule = u"[0-9]{2}(?=年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            year = int(match.group())
            self.tp.tunit[0] = year

        # 三位数表示的年份
        rule = u"(?<![0-9])[0-9]{3}(?=年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            #self.normalizer.isTimeSpan = True
            year = int(match.group())
            self.tp.tunit[0] = year

        # 四位数表示的年份
        rule = u"[0-9]{4}(?=年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            year = int(match.group())
            self.tp.tunit[0] = year

    def norm_setmonth(self):
        """
        月-规范化方法--该方法识别时间表达式单元的月字段
        :return:
        """
        rule = u"((10)|(11)|(12)|([1-9]))(?=月)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[1] = int(match.group())
            # 处理倾向于未来时间的情况
            self.preferFuture(1)

    def norm_setmonth_fuzzyday(self):
        """
        月-日 兼容模糊写法：该方法识别时间表达式单元的月、日字段
        :return:
        """
        rule = u"((10)|(11)|(12)|([1-9]))(月|\\.|\\-)([0-3][0-9]|[1-9])"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            matchStr = match.group()
            p = re.compile(u"(月|\\.|\\-)")
            m = p.search(matchStr)
            if match is not None:
                splitIndex = m.start()
                month = matchStr[0: splitIndex]
                day = matchStr[splitIndex + 1:]
                self.tp.tunit[1] = int(month)
                self.tp.tunit[2] = int(day)
                # 处理倾向于未来时间的情况
                self.preferFuture(1)
            self._check_time(self.tp.tunit)

    def norm_setday(self):
        """
        日-规范化方法：该方法识别时间表达式单元的日字段
        :return:
        """
        rule = u"((?<!\\d))([0-3][0-9]|[1-9])(?=(日|号))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[2] = int(match.group())
            # 处理倾向于未来时间的情况
            self.preferFuture(2)
            self._check_time(self.tp.tunit)

    def norm_sethour(self):
        """
        时-规范化方法：该方法识别时间表达式单元的时字段
        :return:
        """
        rule = u"(?<!(周|星期))([0-2]?[0-9])(?=(点|时))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[3] = int(match.group())
            # print('first', self.tp.tunit[3] )
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        # * 对关键字：早（包含早上/早晨/早间），上午，中午,午间,下午,午后,晚上,傍晚,晚间,晚,pm,PM的正确时间计算
        # * 规约：
        # * 1.中午/午间0-10点视为12-22点
        # * 2.下午/午后0-11点视为12-23点
        # * 3.晚上/傍晚/晚间/晚1-11点视为13-23点，12点视为0点
        # * 4.0-11点pm/PM视为12-23点
        rule = u"凌晨"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“凌晨”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.day_break
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = u"早上|早晨|早间|晨间|今早|明早|早|清晨"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“早上/早晨/早间”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.early_morning
                # 处理倾向于未来时间的情况
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = u"上午"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“上午”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.morning
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = u"(中午)|(午间)|白天"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 10:
                self.tp.tunit[3] += 12
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“中午/午间”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.noon
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = u"(下午)|(午后)|(pm)|(PM)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 11:
                self.tp.tunit[3] += 12
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“下午|午后”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.afternoon
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        rule = u"晚上|夜间|夜里|今晚|明晚|晚|夜里"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 11:
                self.tp.tunit[3] += 12
            elif self.tp.tunit[3] == 12:
                self.tp.tunit[3] = 0
            elif self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“下午|午后”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.lateNight
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

    def norm_setminute(self):
        """
        分-规范化方法：该方法识别时间表达式单元的分字段
        :return:
        """
        rule = u"([0-9]+(?=分(?!钟)))|((?<=((?<!小)[点时]))[0-5]?[0-9](?!刻))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if match.group() != '':
                self.tp.tunit[4] = int(match.group())
                # 处理倾向于未来时间的情况
                # self.preferFuture(4)
                self.isAllDayTime = False
        # 加对一刻，半，3刻的正确识别（1刻为15分，半为30分，3刻为45分）
        rule = u"(?<=[点时])[1一]刻(?!钟)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[4] = 15
            # 处理倾向于未来时间的情况
            # self.preferFuture(4)
            self.isAllDayTime = False

        rule = u"(?<=[点时])半"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if (match is not None) and ('小时' not in self.exp_time):
            ### 2019.07.21更新： 这个地方会和“一小时半后”起冲突
            self.tp.tunit[4] = 30
            # 处理倾向于未来时间的情况
            self.preferFuture(4)
            self.isAllDayTime = False

        rule = u"(?<=[点时])[3三]刻(?!钟)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[4] = 45
            # 处理倾向于未来时间的情况
            # self.preferFuture(4)
            self.isAllDayTime = False

    def norm_setsecond(self):
        """
        添加了省略“秒”说法的时间：如17点15分32
        :return:
        """
        rule = u"([0-9]+(?=秒))|((?<=分)[0-5]?[0-9])"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            self.tp.tunit[5] = int(match.group())
            self.isAllDayTime = False

    def norm_setSpecial(self):
        """
        特殊形式的规范化方法-该方法识别特殊形式的时间表达式单元的各个字段
        :return:
        """
        rule = u"(晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            rule = '([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]'
            pattern = re.compile(rule)
            match = pattern.search(self.exp_time)
            tmp_target = match.group()
            tmp_parser = tmp_target.split(":")
            if 0 <= int(tmp_parser[0]) <= 11:
                self.tp.tunit[3] = int(tmp_parser[0]) + 12
            else:
                self.tp.tunit[3] = int(tmp_parser[0])

            self.tp.tunit[4] = int(tmp_parser[1])
            self.tp.tunit[5] = int(tmp_parser[2])
            # 处理倾向于未来时间的情况
            self.preferFuture(3)
            self.isAllDayTime = False

        else:
            rule = u"(晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]"
            pattern = re.compile(rule)
            match = pattern.search(self.exp_time)
            if match is not None:
                rule = '([0-2]?[0-9]):[0-5]?[0-9]'
                pattern = re.compile(rule)
                match = pattern.search(self.exp_time)
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                if 0 <= int(tmp_parser[0]) <= 11:
                    self.tp.tunit[3] = int(tmp_parser[0]) + 12
                else:
                    self.tp.tunit[3] = int(tmp_parser[0])
                self.tp.tunit[4] = int(tmp_parser[1])
                # 处理倾向于未来时间的情况
                self.preferFuture(3)
                self.isAllDayTime = False

        if match is None:
            rule = u"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9](PM|pm|p\\.m)"
            pattern = re.compile(rule, re.I)
            match = pattern.search(self.exp_time)
            if match is not None:
                rule = '([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]'
                pattern = re.compile(rule)
                match = pattern.search(self.exp_time)
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                if 0 <= int(tmp_parser[0]) <= 11:
                    self.tp.tunit[3] = int(tmp_parser[0]) + 12
                else:
                    self.tp.tunit[3] = int(tmp_parser[0])

                self.tp.tunit[4] = int(tmp_parser[1])
                self.tp.tunit[5] = int(tmp_parser[2])
                # 处理倾向于未来时间的情况
                self.preferFuture(3)
                self.isAllDayTime = False

            else:
                rule = u"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9](PM|pm|p.m)"
                pattern = re.compile(rule, re.I)
                match = pattern.search(self.exp_time)
                if match is not None:
                    rule = '([0-2]?[0-9]):[0-5]?[0-9]'
                    pattern = re.compile(rule)
                    match = pattern.search(self.exp_time)
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    if 0 <= int(tmp_parser[0]) <= 11:
                        self.tp.tunit[3] = int(tmp_parser[0]) + 12
                    else:
                        self.tp.tunit[3] = int(tmp_parser[0])
                    self.tp.tunit[4] = int(tmp_parser[1])
                    # 处理倾向于未来时间的情况
                    self.preferFuture(3)
                    self.isAllDayTime = False

        if match is None:
            rule = u"(?<!(周|星期|晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]"
            pattern = re.compile(rule)
            match = pattern.search(self.exp_time)
            if match is not None:
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                self.tp.tunit[3] = int(tmp_parser[0])
                self.tp.tunit[4] = int(tmp_parser[1])
                self.tp.tunit[5] = int(tmp_parser[2])
                # 处理倾向于未来时间的情况
                self.preferFuture(3)
                self.isAllDayTime = False
            else:
                rule = u"(?<!(周|星期|晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后))([0-2]?[0-9]):[0-5]?[0-9]"
                pattern = re.compile(rule)
                match = pattern.search(self.exp_time)
                if match is not None:
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    self.tp.tunit[3] = int(tmp_parser[0])
                    self.tp.tunit[4] = int(tmp_parser[1])
                    # 处理倾向于未来时间的情况
                    self.preferFuture(3)
                    self.isAllDayTime = False
        # 这里是对年份表达的极好方式
        rule = u"[0-9]?[0-9]?[0-9]{2}-((10)|(11)|(12)|([1-9]))-((?<!\\d))([0-3][0-9]|[1-9])"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("-")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])

        rule = u"[0-9]?[0-9]?[0-9]{2}/((10)|(11)|(12)|([1-9]))/((?<!\\d))([0-3][0-9]|[1-9])"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])

        rule = u"((10)|(11)|(12)|([1-9]))/((?<!\\d))([0-3][0-9]|[1-9])/[0-9]?[0-9]?[0-9]{2}"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.tunit[1] = int(tmp_parser[0])
            self.tp.tunit[2] = int(tmp_parser[1])
            self.tp.tunit[0] = int(tmp_parser[2])

        rule = u"[0-9]?[0-9]?[0-9]{2}\\.((10)|(11)|(12)|([1-9]))\\.((?<!\\d))([0-3][0-9]|[1-9])"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split(".")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])

    def norm_setBaseRelated(self):
        """
        设置以上文时间为基准的时间偏移计算
        :return:
        """
        cur = arrow.get(self.normalizer.timeBase, "YYYY-M-D-H-m-s")
        flag = [False, False, False, False, False, False]
        ###2019.07.20更新：半xx前/后-->若没有[前后]，默认为后
        rule = u"\\S+(?=((半)(年|月|周|礼拜|星期天|日|天|小时|时|分钟|分)))|\\S+(?=((年|月|周|礼拜|星期天|日|天|小时|时|分钟|分)(半)))"
        pattern = re.compile(rule)
        match = pattern.search("<start>"+self.exp_time+"<end>")
        if match:
            num_match = re.compile(u"[0-9]").search(match.group().replace("<start>",'').replace("<end>",''))
            if '年' in self.exp_time:
                flag[0],flag[1] = True,True
                if num_match:
                    year = int(num_match.group())
                else:
                    year = 0
                month = 6
                if '前' in self.exp_time:
                    cur = cur.shift(years=-year)
                    cur = cur.shift(months=-month)
                else:
                    cur = cur.shift(years=year)
                    cur = cur.shift(months=month)
            if '月' in self.exp_time:
                flag[0],flag[1],flag[2] = True,True,True
                if num_match:
                    month = int(num_match.group())
                else:
                    month = 0
                day = 15
                if '前' in self.exp_time:
                    cur = cur.shift(months=-month)
                    cur = cur.shift(days=-day)
                else:
                    cur = cur.shift(months=month)
                    cur = cur.shift(days=day)
            if ('周' in self.exp_time) or ('星期' in self.exp_time) or ('礼拜' in self.exp_time):
                flag[0],flag[1],flag[2] = True,True,True
                if num_match:
                    week = int(num_match.group())
                else:
                    week = 0
                day = 4
                if '前' in self.exp_time:
                    cur = cur.shift(weeks=-week)
                    cur = cur.shift(days=-day)
                else:
                    cur = cur.shift(weeks=week)
                    cur = cur.shift(days=day)
            if ('天' in self.exp_time) or ('日' in self.exp_time):
                flag[0],flag[1],flag[2],flag[3] = True,True,True,True
                if num_match:
                    day = int(num_match.group())
                else:
                    day = 0
                hour = 12
                if '前' in self.exp_time:
                    cur = cur.shift(days=-day)
                    cur = cur.shift(hours=-hour)
                else:
                    cur = cur.shift(days=day)
                    cur = cur.shift(hours=hour)
            if '时' in self.exp_time:
                flag[0],flag[1],flag[2],flag[3],flag[4] = True,True,True,True,True
                if num_match:
                    hour = int(num_match.group())
                else:
                    hour = 0
                minute = 30
                if '前' in self.exp_time:
                    cur = cur.shift(hours=-hour)
                    cur = cur.shift(minutes=-minute)
                else:
                    cur = cur.shift(hours=hour)
                    cur = cur.shift(minutes=minute)
            if '分' in self.exp_time:
                flag[0],flag[1],flag[2],flag[3],flag[4],flag[5] = True,True,True,True,True,True
                if num_match:
                    minute = int(num_match.group())
                else:
                    minute = 0
                second = 30
                if '前' in self.exp_time:
                    cur = cur.shift(minutes=-minute)
                    cur = cur.shift(second=-second)
                else:
                    cur = cur.shift(minutes=minute)
                    cur = cur.shift(second=second)
        
        ###2019.07.20更新：原来只有天级别，扩展到分钟级别（秒级别也支持）
        
#         rule = u"\\d+(?=(秒钟|秒))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             flag[5] = True
#             second = int(match.group())
#             if '前' in self.exp_time:
#                 cur = cur.shift(seconds=-second)
#             else:
#                 cur = cur.shift(seconds=second)
        
        rule = u"\\d+(?=(分钟|分))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[4] = True
            minute = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(minutes=-minute)
            else:
                cur = cur.shift(minutes=minute)

        rule = u"\\d+(?=(小时|时))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[3] = True
            hour = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(hours=-hour)
            else:
                cur = cur.shift(hours=hour)
        
        rule = u"\\d+(?=(天|日))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[2] = True
            day = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(days=-day)
            else:
                cur = cur.shift(days=day)
                
        rule = u"\\d+(?=(周|星期|礼拜))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[2] = True
            week = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(weeks=-week)
            else:
                cur = cur.shift(weeks=week)

        rule = u"\\d+(?=(月))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[1] = True
            month = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(months=-month)
            else:
                cur = cur.shift(months=month)
        
        rule = u"\\d+(?=(年))"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None and '半' not in self.exp_time:
            flag[0] = True
            year = int(match.group())
            if '前' in self.exp_time:
                cur = cur.shift(years=-year)
            else:
                cur = cur.shift(years=year)
        
        if any(flag):
            self.tp.tunit[0] = int(cur.year)
            self.tp.tunit[1] = int(cur.month)
            self.tp.tunit[2] = int(cur.day)
            self.tp.tunit[3] = int(cur.hour)
            self.tp.tunit[4] = int(cur.minute)
            #self.tp.tunit[5] = int(cur.second)

#     # todo 时间长度相关
#     def norm_setSpanRelated(self):
#         """
#         设置时间长度相关的时间表达式
#         :return:
#         """
#         rule = u"\\d+(?=个月(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             month = int(match.group())
#             self.tp.tunit[1] = int(month)

#         rule = u"\\d+(?=天(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             day = int(match.group())
#             self.tp.tunit[2] = int(day)

#         rule = u"\\d+(?=(个)?小时(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             hour = int(match.group())
#             self.tp.tunit[3] = int(hour)

#         rule = u"\\d+(?=分钟(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             minute = int(match.group())
#             self.tp.tunit[4] = int(minute)

#         rule = u"\\d+(?=秒钟(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             second = int(match.group())
#             self.tp.tunit[5] = int(second)

#         rule = u"\\d+(?=(个)?(周|星期|礼拜)(?![以之]?[前后]))"
#         pattern = re.compile(rule)
#         match = pattern.search(self.exp_time)
#         if match is not None:
#             self.normalizer.isTimeSpan = True
#             week = int(match.group())
#             if self.tp.tunit[2] == -1:
#                 self.tp.tunit[2] = 0
#             self.tp.tunit[2] += int(week * 7)

    # 节假日相关
    def norm_setHoliday(self):
        rule = u"(情人节)|(母亲节)|(青年节)|(教师节)|(中元节)|(端午)|(劳动节)|(7夕)|(建党节)|(建军节)|(初13)|(初14)|(初15)|" \
               u"(初12)|(初11)|(初9)|(初8)|(初7)|(初6)|(初5)|(初4)|(初3)|(初2)|(初1)|(中和节)|(圣诞)|(中秋)|(春节)|(元宵)|" \
               u"(航海日)|(儿童节)|(国庆)|(植树节)|(元旦)|(重阳节)|(妇女节)|(记者节)|(立春)|(雨水)|(惊蛰)|(春分)|(清明)|(谷雨)|" \
               u"(立夏)|(小满 )|(芒种)|(夏至)|(小暑)|(大暑)|(立秋)|(处暑)|(白露)|(秋分)|(寒露)|(霜降)|(立冬)|(小雪)|(大雪)|" \
               u"(冬至)|(小寒)|(大寒)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[0] == -1:
                self.tp.tunit[0] = int(self.normalizer.timeBase.split('-')[0])
            holi = match.group()
            if u'节' not in holi:
                holi += u'节'
            if holi in self.normalizer.holi_solar:
                date = self.normalizer.holi_solar[holi].split('-')
            elif holi in self.normalizer.holi_lunar:
                date = self.normalizer.holi_lunar[holi].split('-')
                lsConverter = LunarSolarConverter()
                lunar = Lunar(self.tp.tunit[0], int(date[0]), int(date[1]), False)
                solar = lsConverter.LunarToSolar(lunar)
                self.tp.tunit[0] = solar.solarYear
                date[0] = solar.solarMonth
                date[1] = solar.solarDay
            else:
                holi = holi.strip(u'节')
                if holi in ['小寒', '大寒']:
                    self.tp.tunit[0] += 1
                date = self.china_24_st(self.tp.tunit[0], holi)
            self.tp.tunit[1] = int(date[0])
            self.tp.tunit[2] = int(date[1])

    def china_24_st(self, year: int, china_st: str):
        """
        二十世纪和二十一世纪，24节气计算
        :param year: 年份
        :param china_st: 节气
        :return: 节气日期（月, 日）
        """
        if (19 == year // 100) or (2000 == year):
            # 20世纪 key值
            st_key = [6.11, 20.84, 4.6295, 19.4599, 6.3826, 21.4155, 5.59, 20.888, 6.318, 21.86, 6.5, 22.2, 7.928,
                      23.65, 8.35, 23.95, 8.44, 23.822, 9.098, 24.218, 8.218, 23.08, 7.9, 22.6]
        else:
            # 21世纪 key值
            st_key = [5.4055, 20.12, 3.87, 18.73, 5.63, 20.646, 4.81, 20.1, 5.52, 21.04, 5.678, 21.37, 7.108, 22.83,
                      7.5, 23.13, 7.646, 23.042, 8.318, 23.438, 7.438, 22.36, 7.18, 21.94]
        # 二十四节气字典-- key值, 月份，(特殊年份，相差天数)...
        solar_terms = {
            '小寒': [st_key[0], '1', (2019, -1), (1982, 1)],
            '大寒': [st_key[1], '1', (2082, 1)],
            '立春': [st_key[2], '2', (None, 0)],
            '雨水': [st_key[3], '2', (2026, -1)],
            '惊蛰': [st_key[4], '3', (None, 0)],
            '春分': [st_key[5], '3', (2084, 1)],
            '清明': [st_key[6], '4', (None, 0)],
            '谷雨': [st_key[7], '4', (None, 0)],
            '立夏': [st_key[8], '5', (1911, 1)],
            '小满': [st_key[9], '5', (2008, 1)],
            '芒种': [st_key[10], '6', (1902, 1)],
            '夏至': [st_key[11], '6', (None, 0)],
            '小暑': [st_key[12], '7', (2016, 1), (1925, 1)],
            '大暑': [st_key[13], '7', (1922, 1)],
            '立秋': [st_key[14], '8', (2002, 1)],
            '处暑': [st_key[15], '8', (None, 0)],
            '白露': [st_key[16], '9', (1927, 1)],
            '秋分': [st_key[17], '9', (None, 0)],
            '寒露': [st_key[18], '10', (2088, 0)],
            '霜降': [st_key[19], '10', (2089, 1)],
            '立冬': [st_key[20], '11', (2089, 1)],
            '小雪': [st_key[21], '11', (1978, 0)],
            '大雪': [st_key[22], '12', (1954, 1)],
            '冬至': [st_key[23], '12', (2021, -1), (1918, -1)]
        }
        if china_st in ['小寒', '大寒', '立春', '雨水']:
            flag_day = int((year % 100) * 0.2422 + solar_terms[china_st][0]) - int((year % 100 - 1) / 4)
        else:
            flag_day = int((year % 100) * 0.2422 + solar_terms[china_st][0]) - int((year % 100) / 4)
        # 特殊年份处理
        for special in solar_terms[china_st][2:]:
            if year == special[0]:
                flag_day += special[1]
                break
        return (solar_terms[china_st][1]), str(flag_day)

    def norm_setCurRelated(self):
        """
        设置当前时间相关的时间表达式
        :return:
        """
        # 这一块还是用了断言表达式
        cur = arrow.get(self.normalizer.timeBase, "YYYY-M-D-H-m-s")
        flag = [False, False, False]

        rule = u"前年"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[0] = True
            cur = cur.shift(years=-2)

        rule = u"去年"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[0] = True
            cur = cur.shift(years=-1)

        rule = u"今年"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[0] = True
            cur = cur.shift(years=0)

        rule = u"明年"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[0] = True
            cur = cur.shift(years=1)

        rule = u"后年"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[0] = True
            cur = cur.shift(years=2)

        rule = u"上*上(个)?月"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[1] = True
            rule = u"上"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            cur = cur.shift(months=-len(match))

        rule = u"(本|这个)月"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[1] = True
            cur = cur.shift(months=0)

        rule = u"下*下(个)?月"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[1] = True
            rule = u"下"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            cur = cur.shift(months=len(match))

        rule = u"大*大前天"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            rule = u"大"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            cur = cur.shift(days=-(2 + len(match)))

        rule = u"(?<!大)前天"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            cur = cur.shift(days=-2)

        rule = u"昨"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            cur = cur.shift(days=-1)

        rule = u"今(?!年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            cur = cur.shift(days=0)

        rule = u"明(?!年)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            cur = cur.shift(days=1)

        rule = u"(?<!大)后天"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            cur = cur.shift(days=2)

        rule = u"大*大后天"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            rule = u"大"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            flag[2] = True

            cur = cur.shift(days=(2 + len(match)))

        # todo 补充星期相关的预测 done
        rule = u"(?<=(上*上上(周|星期)))[1-7]?"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            try:
                week = int(match.group())
            except:
                week = 1
            week -= 1
            span = week - cur.weekday()
            rule = u"上"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            cur = cur.replace(weeks=-len(match), days=span)

        rule = u"(?<=((?<!上)上(周|星期)))[1-7]?"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            try:
                week = int(match.group())
            except:
                week = 1
            week -= 1
            span = week - cur.weekday()
            cur = cur.replace(weeks=-1, days=span)

        rule = u"(?<=((?<!下)下(周|星期)))[1-7]?"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            try:
                week = int(match.group())
            except:
                week = 1
            week -= 1
            span = week - cur.weekday()
            cur = cur.replace(weeks=1, days=span)

        # 这里对下下下周的时间转换做出了改善
        rule = u"(?<=(下*下下(周|星期)))[1-7]?"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            try:
                week = int(match.group())
            except:
                week = 1
            week -= 1
            span = week - cur.weekday()
            rule = u"下"
            pattern = re.compile(rule)
            match = pattern.findall(self.exp_time)
            cur = cur.replace(weeks=len(match), days=span)

        rule = u"(?<=((?<!(上|下|个|[0-9]))(周|星期)))[1-7]"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            flag[2] = True
            try:
                week = int(match.group())
            except:
                week = 1
            week -= 1
            span = week - cur.weekday()
            cur = cur.replace(days=span)
            # 处理未来时间
            cur = self.preferFutureWeek(week, cur)

        if flag[0] or flag[1] or flag[2]:
            self.tp.tunit[0] = int(cur.year)
        if flag[1] or flag[2]:
            self.tp.tunit[1] = int(cur.month)
        if flag[2]:
            self.tp.tunit[2] = int(cur.day)

    def preferFutureWeek(self, weekday, cur):
        # 1. 确认用户选项
        if not self.normalizer.isPreferFuture:
            return cur
        # 2. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, 2):
            if self.tp.tunit[i] != -1:
                return cur
        # 获取当前是在周几，如果识别到的时间小于当前时间，则识别时间为下一周
        tmp = arrow.get(self.normalizer.timeBase, "YYYY-M-D-H-m-s")
        curWeekday = tmp.weekday()
        if curWeekday > weekday:
            cur = cur.shift(days=7)
        return cur

    def preferFuture(self, checkTimeIndex):
        """
        如果用户选项是倾向于未来时间，检查checkTimeIndex所指的时间是否是过去的时间，如果是的话，将大一级的时间设为当前时间的+1。
        如在晚上说“早上8点看书”，则识别为明天早上;
        12月31日说“3号买菜”，则识别为明年1月的3号。
        :param checkTimeIndex: _tp.tunit时间数组的下标
        :return:
        """
        # 1. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, checkTimeIndex):
            if self.tp.tunit[i] != -1:
                return
        # 2. 根据上下文补充时间
        self.checkContextTime(checkTimeIndex)
        # 3. 根据上下文补充时间后再次检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行倾向处理.\
        for i in range(0, checkTimeIndex):
            if self.tp.tunit[i] != -1:
                return
        # 4. 确认用户选项
        if not self.normalizer.isPreferFuture:
            return
        # 5. 获取当前时间，如果识别到的时间小于当前时间，则将其上的所有级别时间设置为当前时间，并且其上一级的时间步长+1
        time_arr = self.normalizer.timeBase.split('-')
        cur = arrow.get(self.normalizer.timeBase, "YYYY-M-D-H-m-s")
        cur_unit = int(time_arr[checkTimeIndex])
        # print(time_arr)
        # print(self.tp.tunit)
        if self.tp.tunit[0] == -1:
            self._noyear = True
        else:
            self._noyear = False
        if cur_unit < self.tp.tunit[checkTimeIndex]:
            return
        # if cur_unit == self.tp.tunit[checkTimeIndex]:
        #     down_unit = int(time_arr[checkTimeIndex + 1])
        #     if down_unit
        # 准备增加的时间单位是被检查的时间的上一级，将上一级时间+1
        cur = self.addTime(cur, checkTimeIndex - 1)
        time_arr = cur.format("YYYY-M-D-H-m-s").split('-')
        for i in range(0, checkTimeIndex):
            self.tp.tunit[i] = int(time_arr[i])
            # if i == 1:
            #     self.tp.tunit[i] += 1

    def _check_time(self, parse):
        '''
        检查未来时间点
        :param parse: 解析出来的list
        :return:
        '''
        time_arr = self.normalizer.timeBase.split('-')
        if self._noyear:
            # check the month
            # print(parse)
            # print(time_arr)
            if parse[1] == int(time_arr[1]):
                if parse[2] > int(time_arr[2]):
                    parse[0] = parse[0] - 1
            self._noyear = False

    def checkContextTime(self, checkTimeIndex):
        """
        根据上下文时间补充时间信息
        :param checkTimeIndex:
        :return:
        """
        for i in range(0, checkTimeIndex):
            if self.tp.tunit[i] == -1 and self.tp_origin.tunit[i] != -1:
                self.tp.tunit[i] = self.tp_origin.tunit[i]
        # 在处理小时这个级别时，如果上文时间是下午的且下文没有主动声明小时级别以上的时间，则也把下文时间设为下午
        # print('comparision time is ',self.tp_origin.tunit[checkTimeIndex])
        if self.isFirstTimeSolveContext is True and checkTimeIndex == 3 and self.tp_origin.tunit[
            checkTimeIndex] >= 12 and self.tp.tunit[checkTimeIndex] < 12:
            self.tp.tunit[checkTimeIndex] += 12
        self.isFirstTimeSolveContext = False

    def addTime(self, cur, fore_unit):
        if fore_unit == 0:
            cur = cur.shift(years=1)
        elif fore_unit == 1:
            cur = cur.shift(months=1)
        elif fore_unit == 2:
            cur = cur.shift(days=1)
        elif fore_unit == 3:
            cur = cur.shift(hours=1)
        elif fore_unit == 4:
            cur = cur.shift(minutes=1)
        elif fore_unit == 5:
            cur = cur.shift(seconds=1)
        return cur

# 时间表达式识别的主要工作类
class TimeHandler(object):
    def __init__(self, isPreferFuture=True):
        self.isPreferFuture = isPreferFuture
        self.pattern, self.holi_solar, self.holi_lunar = self.init()
        
    def _repl_tight_weekdays(self,s):
        s = '<start>' + s + '<end>'
        rule = re.compile(r"(礼拜|周|星期)(一二|二三|三四|四五|五六|六七|六日)[^点时]")
        finds = rule.findall(s)
        finds_res = []
        for item in finds:
            res = ''
            for i in range(len(item)):
                if i == 1:
                    res += item[i][:-1]
                else:
                    res += item[i]
            finds_res.append(res)
        finds = [''.join(item) for item in finds]
        for item,item_res in zip(finds,finds_res):
            s = s.replace(item,item_res)
        s = s.replace('<start>','').replace('<end>','')
        return s
    
    def _repl_tight_times(self,s):
        s = '<start>' + s + '<end>'
        rule = re.compile(r"([^(礼拜)周(星期)])(一二|一两|二三|两三|三四|四五|五六|六七|七八|八九|九十)(年|月|日|天|周|星期|礼拜|小时|时|点|分|秒)")
        finds = rule.findall(s)
        finds_res = []
        for item in finds:
            res = ''
            for i in range(len(item)):
                if i == 1:
                    res += item[i][:-1]
                else:
                    res += item[i]
            finds_res.append(res)
        finds = [''.join(item) for item in finds]
        for item,item_res in zip(finds,finds_res):
            s = s.replace(item,item_res)
        s = s.replace('<start>','').replace('<end>','')
        return s
    
    def _repl_tight_times_complex(self,s):
        s = '<start>' + s + '<end>'
        rule = re.compile(r"(一|二|三|四|五|六|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九|二十|二十一|二十二|二十三|二十四|二十五|二十六|二十七|二十八|二十九|三十|三十一)(年|月|日|天|周|星期|礼拜|小时|时|点|分|秒)")
        finds = rule.findall(s)
        finds_source = []
        finds_replace = []
        for item_i in finds:
            for item_j in finds:
                res_source = ''
                res_replace = ''
                if item_i[1] == item_j[1]:
                    res_source += (''.join(item_i) + ''.join(item_j))
                    res_replace += (''.join(item_i))
                finds_source.append(res_source)
                finds_replace.append(res_replace)
        for item_source,item_replace in zip(finds_source,finds_replace):
            s = s.replace(item_source,item_replace)
        s = s.replace('<start>','').replace('<end>','')
        return s
    
    def _repl_tights(self,s):
        s = self._repl_tight_times(s)
        s = self._repl_tight_times_complex(s)
        s = self._repl_tight_weekdays(s)
        return s

    # 这里对一些不规范的表达做转换
    def _filter(self, input_query):
        
        ### 2019.07.20更新：增加紧凑时间的拆分，并取最早的时间：如周五六三点->周五三点；十一点十二点->十一点；两三点->两点
        input_query = self._repl_tights(input_query)
        
        # 这里对于下个周末这种做转化 把个给移除掉
        input_query = StringPreHandler.numberTranslator(input_query)
        rule = u"[0-9]月[0-9]"
        pattern = re.compile(rule)
        match = pattern.search(input_query)
        if match != None:
            index = input_query.find('月')
            rule = u"日|号"
            pattern = re.compile(rule)
            match = pattern.search(input_query[index:])
            if match == None:
                rule = u"[0-9]月[0-9]+"
                pattern = re.compile(rule)
                match = pattern.search(input_query)
                if match != None:
                    end = match.span()[1]
                    input_query = input_query[:end] + '号' + input_query[end:]

        rule = u"月"
        pattern = re.compile(rule)
        match = pattern.search(input_query)
        if match == None:
            input_query = input_query.replace('个', '')

        input_query = input_query.replace('中旬', '15号')
        input_query = input_query.replace('傍晚', '午后')
        input_query = input_query.replace('大年', '')
        input_query = input_query.replace('五一', '劳动节')
        input_query = input_query.replace('白天', '早上')
        input_query = input_query.replace('：', ':')
        
        return input_query

    def init(self):
        fpath = os.path.dirname(TimeNormalizer.__file__) + '/resource/reg.pkl'
        #fpath = os.path.dirname(TimeNormalizer.__file__) + '/resource/reg.pkl'
        try:
            with open(fpath, 'rb') as f:
                pattern = pickle.load(f)
        except:
            with codecs.open(os.path.dirname(TimeNormalizer.__file__) + '/resource/regex.txt', 'r', 'utf-8-sig') as f:
                content = f.read()
            p = re.compile(content)
            with open(fpath, 'wb') as f:
                pickle.dump(p, f)
            with open(fpath, 'rb') as f:
                pattern = pickle.load(f)
        with codecs.open(os.path.dirname(TimeNormalizer.__file__) + '/resource/holi_solar.json', 'r', 'utf-8-sig') as f:
            holi_solar = json.load(f)
        with codecs.open(os.path.dirname(TimeNormalizer.__file__) + '/resource/holi_lunar.json', 'r', 'utf-8-sig') as f:
            holi_lunar = json.load(f)
        return pattern, holi_solar, holi_lunar

    def parse(self, target):
        """
        TimeNormalizer的构造方法，timeBase取默认的系统当前时间
        :param timeBase: 基准时间点
        :param target: 待分析字符串
        :return: 时间单元数组
        """
        #self.isTimeSpan = False
        self.invalidSpan = False
        self.timeSpan = ''
        self.target = self._filter(target)
        self.timeBase = arrow.now().format('YYYY-M-D-H-m-s')
        self.nowTime = arrow.now().format('YYYY-M-D-H-m-s')
        self.__preHandling()
        self.oriTimeToken,self.timeToken = self.__timeEx()
        dic = {}
        res = self.timeToken
        month_day_dict = {'1':31,'2-common':28,'2-special':29,'3':31,'4':30,'5':31,'6':30,'7':31,'8':31,'9':30,'10':31,'11':30,'12':31}
        
        if len(res) == 0:
            dic['error'] = 'no timestamp pattern could be extracted.'
        elif len(res) == 1:
            dic['type'] = 'timestamp'
            ###2019.07.20更新：比如现在是下午三点，“八点”应该显示的是20:00:00，而不是08:00:00。
            ###               容易混淆的地方在于：“今天八点联系我”，要表达的是“今天晚上八点联系我”；“今天八点联系过了”，要表达的是“今天早上八点联系过了”；目前规则是含有今天的，无论如何日期不能增加一天。
            ###               目前这一版的时间实体挖掘完全是根据大量的规则提取的，暂时没有语义理解功能，后续需要提升。
            now = arrow.now()
            res = res[-1].time
            now_date,res_date = now.format("YYYY-MM-DD"),res.format("YYYY-MM-DD")
            now_time,res_time = now.format("HH:mm:ss"),res.format("HH:mm:ss")
            oriTimeToken = ''.join(self.oriTimeToken)
            unchange_rule_base = re.compile(u"(凌晨|早上|早晨|早间|晨间|今早|明早|早|清晨|上午|am|AM|中午|午间|白天|下午|午后|pm|PM|晚上|夜间|夜里|今晚|明晚|晚|夜里)")
            if not unchange_rule_base.search(oriTimeToken):
                num_rule = re.compile(u'[0-9]')
                today_rule = re.compile(u'(今|现)')
                if num_rule.match(oriTimeToken) and now_date == res_date and now_time > res_time:
                    if now_time <= res.shift(hours=12).format("HH:mm:ss"):
                        dic['timestamp'] = res.shift(hours=12).format("YYYY-MM-DD HH:mm:ss")
                    else:
                        dic['timestamp'] = res.shift(days=1).format("YYYY-MM-DD HH:mm:ss")
                elif today_rule.search(oriTimeToken) and now_date == res_date and now_time > res_time:
                    if now_time <= res.shift(hours=12).format("HH:mm:ss"):
                        dic['timestamp'] = res.shift(hours=12).format("YYYY-MM-DD HH:mm:ss")
                    else:
                        dic['timestamp'] = res.format("YYYY-MM-DD HH:mm:ss")
                else:
                    dic['timestamp'] = res.format("YYYY-MM-DD HH:mm:ss")
            else:
                dic['timestamp'] = res.format("YYYY-MM-DD HH:mm:ss")
            dic['timetoken'] = oriTimeToken
        else:
            dic['type'] = 'timespan'
            res_0 = res[0].time
            res_1 = res[1].time
            res_0_date,res_1_date = res_0.format("YYYY-MM-DD"),res_1.format("YYYY-MM-DD")
            res_0_time,res_1_time = res_0.format("HH:mm:ss"),res_1.format("HH:mm:ss")
            if res_0_date >= res_1_date:
                res_1 = res_1.shift(days=(res_0.day-res_1.day))
                if res_0_time > res_1_time:
                    if int(res_0.format("HH")) <= 12 and int(res_1.format("HH")) <= 12:
                        res_1 = res_1.shift(hours=12)
                    elif int(res_0.format("HH")) > 12 and int(res_1.format("HH")) > 12:
                        res_1 = res_1.shift(days=1)
                    else:
                        if int(res_0.format("HH")) > int(res_1.shift(hours=12).format("HH")):
                            res_1 = res_1.shift(days=1)
                        else:
                            res_1 = res_1.shift(hours=12)
            ###2019.07.20更新：参照timestamp，对timespan也新增与当前时间比较的方法
            now = arrow.now()
            now_date,now_time = now.format("YYYY-MM-DD"),now.format("HH:mm:ss")
            oriTimeToken = [''.join(item) for item in self.oriTimeToken]
            unchange_rule_base = re.compile(u"(凌晨|早上|早晨|早间|晨间|今早|明早|早|清晨|上午|am|AM|中午|午间|白天|下午|午后|pm|PM|晚上|夜间|夜里|今晚|明晚|晚|夜里)")
            if not any([unchange_rule_base.search(item) for item in oriTimeToken]):
                num_rule = re.compile(u'[0-9]')
                today_rule = re.compile(u'(今|现)')
                if any([num_rule.match(item) for item in oriTimeToken]) and now_date == res_1_date and now_time > res_1_time:
                    if now_time <= res_1.shift(hours=12).format("HH:mm:ss"):
                        dic['timespan'] = [res_0.shift(hours=12).format("YYYY-MM-DD HH:mm:ss"),res_1.shift(hours=12).format("YYYY-MM-DD HH:mm:ss")]
                    else:
                        dic['timespan'] = [res_0.shift(days=1).format("YYYY-MM-DD HH:mm:ss"),res_1.shift(days=1).format("YYYY-MM-DD HH:mm:ss")]
                elif any([today_rule.search(item) for item in oriTimeToken]) and now_date == res_1_date and now_time > res_1_time:
                    if now_time <= res_1.shift(hours=12).format("HH:mm:ss"):
                        dic['timespan'] = [res_0.shift(hours=12).format("YYYY-MM-DD HH:mm:ss"),res_1.shift(hours=12).format("YYYY-MM-DD HH:mm:ss")]
                    else:
                        dic['timespan'] = [res_0.format("YYYY-MM-DD HH:mm:ss"),res_1.format("YYYY-MM-DD HH:mm:ss")]
                else:
                    dic['timespan'] = [res_0.format("YYYY-MM-DD HH:mm:ss"),res_1.format("YYYY-MM-DD HH:mm:ss")]
            else:
                dic['timespan'] = [res_0.format("YYYY-MM-DD HH:mm:ss"),res_1.format("YYYY-MM-DD HH:mm:ss")]
            dic['timetoken'] = self.oriTimeToken
        return json.dumps(dic,ensure_ascii=False)

    def __preHandling(self):
        """
        待匹配字符串的清理空白符和语气助词以及大写数字转化的预处理
        :return:
        """
        self.target = StringPreHandler.delKeyword(
            self.target, u"\\s+")  # 清理空白符
        self.target = StringPreHandler.delKeyword(
            self.target, u"[的]+")  # 清理语气助词
        self.target = StringPreHandler.numberTranslator(self.target)  # 大写数字转化

    def __timeEx(self):
        """
        :param target: 输入文本字符串
        :param timeBase: 输入基准时间
        :return: TimeUnit[]时间表达式类型数组
        """
        startline = -1
        endline = -1
        rpointer = 0
        temp = []

        match = self.pattern.finditer(self.target)
        for m in match:
            startline = m.start()
            if startline == endline:
                rpointer -= 1
                temp[rpointer] = temp[rpointer] + m.group()
            else:
                temp.append(m.group())
            endline = m.end()
            rpointer += 1
        temp = [item for item in temp if item != '']
        rpointer = len(temp)
        res = []
        nowTime = [int(item) for item in self.nowTime.format("YYYY-MM-DD-HH-mm-ss").split('-')]
        contextTp = TimePoint(nowTime)
        if any([item in self.target for item in ['现在','这时候','这个时候','这个点','此时','当下','此刻']]):
            contextTp.tunit[-1], contextTp.tunit[-2] = -1, -1
        else:
            contextTp.tunit[-1], contextTp.tunit[-2], contextTp.tunit[-3] = -1, -1, -1
        if rpointer == 0:
            res = []
        else:
            for i in range(0, rpointer):
                # 这里是一个类嵌套了一个类
                res.append(TimeUnit(temp[i], self, TimePoint(nowTime)))
            res = self.__filterTimeUnit(res)
        return temp,res
        
    def __filterTimeUnit(self, tu_arr):
        """
        过滤timeUnit中无用的识别词。无用识别词识别出的时间是1970.01.01 00:00:00(fastTime=0)
        :param tu_arr:
        :return:
        """
        if (tu_arr is None) or (len(tu_arr) < 1):
            return tu_arr
        res = []
        for tu in tu_arr:
            if tu.time.timestamp != 0:
                res.append(tu)
        return res

class TimeExtractor(object):
    def __init__(self):
        pass
    
    def replace_phones(self,text):
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        for phone_num in eng_split_texts_clean:
            text = text.replace(phone_num,'')
        return text
 
    def replace_ids(self,text):
        if text == '':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele) == 18]

        id_pattern = r'^[1-9][0-7]\d{4}((19\d{2}(0[1-9]|1[012])(0[1-9]|[12]\d|30))|(19\d{2}(0[13578]|1[02])31)|(19\d{2}02(0[1-9]|1\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\d{3}(\d|X|x)?$'
        ids = []
        for eng_text in eng_split_texts_clean:
            result = re.match(id_pattern, eng_text, flags=0)
            if result:
                ids.append(result.string)

        for phone_num in ids:
            text = text.replace(phone_num,'')
        return text   
 
    def replace_chinese(self,text):
        if text=='':
            return []
        filtrate = re.compile(u'[\u4E00-\u9FA5]')
        text_without_chinese = filtrate.sub(r' ', text)
        return text_without_chinese

    def parse(self,text):
        if text == '':
            return []
        text = self.replace_phones(text)
        text = self.replace_ids(text)
        time_handler = TimeHandler()
        res = time_handler.parse(target=text)
        return res