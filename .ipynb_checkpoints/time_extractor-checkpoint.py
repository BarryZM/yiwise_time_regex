# coding=utf-8
import os
import regex as re
import copy
import json
import arrow
import pickle
import codecs
from itertools import groupby
import numpy as np
from .utils.RangeTimeEnum import RangeTimeEnum
from .utils.StringPreHandler import StringPreHandler
from .utils.LunarSolarConverter import *


# 时间点对象
class TimePoint(object):
    
    def __init__(self, tunit=[-1, -1, -1, -1, -1, -1]):
        self.tunit = tunit


class TimeUnit(object):
    
    def __init__(self, exp_time, normalizer, context_tp):
        self._noyear = False
        self.exp_time = exp_time
        self.normalizer = normalizer
        self.tp = TimePoint([-1,-1,-1,-1,-1,-1])
        self.tp_origin = context_tp
        self.is_first_time_solve_context = True
        self.is_all_day_time = True
        self.time = arrow.now()
        self.assigned_period = False
        self.time_normalization()
    
    def get_cur_time(self):
        tunit = [int(item) for item in arrow.now().format("YYYY-M-D-H-m-s").split("-")]
        return tunit
    
    def time_normalization(self):
        self.tp_origin.tunit = self.get_cur_time()
        self.norm_set_now()
        self.norm_set_year()
        self.norm_set_month()
        self.norm_set_day()
        self.norm_set_month_fuzzyday()
        self.norm_set_base_related()
        self.norm_set_cur_related()
        self.norm_set_hour()
        self.norm_set_minute()
        self.norm_set_second()
        self.norm_set_special()
        self.norm_set_span_related()
        self.norm_set_holiday()
        
        # 判断是时间点还是时间区间
        flag = True
        for i in range(0, 4):
            if self.tp.tunit[i] != -1:
                flag = False
        if flag:
            self.normalizer.is_time_span = True
        if self.normalizer.is_time_span:
            now = arrow.now()
            days = 0
            if self.tp.tunit[0] > 0:
                days += (365 * (self.tp.tunit[0] - now.year))
            if self.tp.tunit[1] > 0:
                days += (30 * (self.tp.tunit[1] - now.month))
            if self.tp.tunit[2] > 0:
                days += (self.tp.tunit[2] - now.day)
            tunit = self.tp.tunit
            for i in range(3,6):
                if self.tp.tunit[i] < 0:
                    tunit[i] = 0
            seconds = tunit[3] * 3600 + tunit[4] * 60 + tunit[5]
            if seconds == 0 and days == 0:
                self.normalizer.invalid_time_span = True
            self.normalizer.time_span = self.gen_span(days, seconds)
            return
        
        time_grid = self.normalizer.time_base.split("-")
        tunit_pointer = 5
        while tunit_pointer >= 0 and self.tp.tunit[tunit_pointer] < 0:
            tunit_pointer -= 1
        for i in range(tunit_pointer):
            if self.tp.tunit[i] < 0:
                self.tp.tunit[i] = int(time_grid[i])
        self.time = self.gen_time(self.tp.tunit)
    
    def gen_span(self, days, seconds):
        day = int(seconds / (3600 * 24))
        h = int((seconds % (3600 * 24)) / 3600)
        m = int(((seconds % (3600 * 24)) % 3600) / 60)
        s = int(((seconds % (3600 * 24)) % 3600) % 60)
        return str(days + day) + ' days, ' + "%d:%02d:%02d" % (h, m, s)
    
    def gen_time(self, tunit):
        time = arrow.get('1970-01-01 00:00:00')
        if tunit[0] > 0:
            time = time.replace(year=int(tunit[0]))
        if tunit[1] > 0:
            time = time.replace(month=int(tunit[1]))
        if tunit[2] > 0:
            time = time.replace(day=int(tunit[2]))
        if tunit[3] > 0:
            time = time.replace(hour=int(tunit[3]))
        if tunit[4] > 0:
            time = time.replace(minute=int(tunit[4]))
        if tunit[5] > 0:
            time = time.replace(second=int(tunit[5]))
        return time
    
    def norm_set_now(self):
        """
        当前-规范化方法--该方法识别时间表达式单元的当前时刻所有字段
        """
        rule = re.compile(r"现在|这时候|这个时候|这个点|此时|当下|此刻")
        match = rule.search(self.exp_time)
        if match is not None:
            self.tp.tunit = [int(item) for item in arrow.now().format('YYYY-MM-DD-HH-mm-ss').split('-')]
            self.tp.tunit[-1] = -1
    
    def norm_set_year(self):
        """
        年-规范化方法--该方法识别时间表达式单元的年字段
        """
        # 一位数表示的年份
        rule = re.compile(r"(?<![0-9])[0-9]{1}(?=年)")
        match = rule.search(self.exp_time)
        if match is not None:
            self.normalizer.is_time_span = True
            year = int(match.group())
            self.tp.tunit[0] = year

        # 两位数表示的年份
        rule = re.compile(r"[0-9]{2}(?=年)")
        match = rule.search(self.exp_time)
        if match is not None:
            year = int(match.group())
            self.tp.tunit[0] = year

        # 三位数表示的年份
        rule = re.compile(r"(?<![0-9])[0-9]{3}(?=年)")
        match = rule.search(self.exp_time)
        if match is not None:
            self.normalizer.is_time_span = True
            year = int(match.group())
            self.tp.tunit[0] = year

        # 四位数表示的年份
        rule = re.compile(r"[0-9]{4}(?=年)")
        match = rule.search(self.exp_time)
        if match is not None:
            year = int(match.group())
            self.tp.tunit[0] = year
            
    def norm_set_month(self):
        """
        月-规范化方法--该方法识别时间表达式单元的月字段
        """
        rule = re.compile(r"((10)|(11)|(12)|([1-9]))(?=月)")
        match = rule.search(self.exp_time)
        if match is not None:
            month = int(match.group())
            self.tp.tunit[1] = month
            self.prefer_future(1)
            
    def norm_set_month_fuzzyday(self):
        """
        月-日 兼容模糊写法：该方法识别时间表达式单元的月、日字段
        """
        rule = re.compile(r"((10)|(11)|(12)|([1-9]))(月|\\.|\\-)([0-3][0-9]|[1-9])")
        match = rule.search(self.exp_time)
        if match is not None:
            match_res = match.group()
            rule_sub = re.compile(r"(月|\\.|\\-)")
            sub_match = rule_sub.search(match_res)
            if sub_match is not None:
                split_idx = sub_match.start()
                month = int(match_res[:split_idx])
                day = int(match_res[split_idx+1:])
                self.tp.tunit[1] = month
                self.tp.tunit[2] = day
                self.prefer_future(1)
            self._check_time(self.tp.tunit)
    
    def norm_set_day(self):
        """
        日-规范化方法：该方法识别时间表达式单元的日字段
        """
        rule = re.compile(r"((?<!\\d))([0-3][0-9]|[1-9])(?=(日|号))")
        match = rule.search(self.exp_time)
        if match is not None:
            day = int(match.group())
            self.tp.tunit[2] = day
            self.prefer_future(2)
            self._check_time(self.tp.tunit)
            
    def norm_set_hour(self):
        """
        时-规范化方法：该方法识别时间表达式单元的时字段
        """
        rule = re.compile(r"(?<!(周|星期))([0-2]?[0-9])(?=(点|时))")
        match = rule.search(self.exp_time)
        if match is not None:
            hour = int(match.group())
            self.tp.tunit[3] = hour
            self.prefer_future(3)
            self.is_all_day_time = False
        
        # * 对关键字：早（包含早上/早晨/早间），上午，中午,午间,下午,午后,晚上,傍晚,晚间,晚,pm,PM的正确时间计算
        # * 规约：
        # * 1.中午/午间0-10点视为12-22点
        # * 2.下午/午后0-11点视为12-23点
        # * 3.晚上/傍晚/晚间/晚1-11点视为13-23点，12点视为0点
        # * 4.0-11点pm/PM视为12-23点
        
        rule = re.compile(r"凌晨")
        match = rule.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“凌晨”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.day_break
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True

        rule = re.compile(r"早上|早晨|早间|晨间|今早|明早|早|清晨")
        match = rule.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“早上/早晨/早间”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.early_morning
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True

        rule = re.compile(r"上午")
        match = rule.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“上午”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.morning
            elif 12 <= self.tp.tunit[3] <= 23:
                self.tp.tunit[3] -= 12
            elif self.tp.tunit[3] == 0:
                self.tp.tunit[3] = 12
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True

        rule = re.compile(r"(中午)|(午间)|白天")
        match = rule.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 10:
                self.tp.tunit[3] += 12
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“中午/午间”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.noon
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True

        rule = re.compile(r"(下午)|(午后)|(pm)|(PM)")
        match = rule.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 11:
                self.tp.tunit[3] += 12
            if self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“下午|午后”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.afternoon
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True

        rule = re.compile(r"晚上|夜间|夜里|今晚|明晚|晚|夜里")
        match = rule.search(self.exp_time)
        if match is not None:
            if 0 <= self.tp.tunit[3] <= 11:
                self.tp.tunit[3] += 12
            elif self.tp.tunit[3] == 12:
                self.tp.tunit[3] = 0
            elif self.tp.tunit[3] == -1:  # 增加对没有明确时间点，只写了“下午|午后”这种情况的处理
                self.tp.tunit[3] = RangeTimeEnum.late_night
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True
        
    def norm_set_minute(self):
        """
        分-规范化方法：该方法识别时间表达式单元的分字段
        """
        rule = re.compile(r"([0-9]+(?=分(?!钟)))|((?<=((?<!小)[点时]))[0-5]?[0-9](?!刻))")
        match = rule.search(self.exp_time)
        if match is not None:
            if match.group() != '':
                minute = int(match.group())
                self.tp.tunit[4] = minute
#                 self.prefer_future(4)
                self.is_all_day_time = False
        
        # 加对一刻，半，3刻的正确识别（1刻为15分，半为30分，3刻为45分）
        rule = re.compile(r"(?<=[点时])[1一]刻(?!钟)")
        match = rule.search(self.exp_time)
        if match is not None:
            self.tp.tunit[4] = 15
            self.prefer_future(4)
            self.is_all_day_time = False

        rule = re.compile(r"(?<=[点时])半")
        match = rule.search(self.exp_time)
        if match is not None:
            self.tp.tunit[4] = 30
#             self.prefer_future(4)
            self.is_all_day_time = False

        rule = re.compile(r"(?<=[点时])[3三]刻(?!钟)")
        match = rule.search(self.exp_time)
        if match is not None:
            self.tp.tunit[4] = 45
#             self.prefer_future(4)
            self.is_all_day_time = False

    def norm_set_second(self):
        """
        添加了省略“秒”说法的时间：如17点15分32
        """
        rule = re.compile(r"([0-9]+(?=秒))|((?<=分)[0-5]?[0-9])")
        match = rule.search(self.exp_time)
        if match is not None:
            second = int(match.group())
            self.tp.tunit[5] = second
            self.prefer_future(5)
            self.is_all_day_time = False
            
    def norm_set_special(self):
        """
        特殊形式的规范化方法-该方法识别特殊形式的时间表达式单元的各个字段
        """
        rule = re.compile(r"(晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]")
        match = rule.search(self.exp_time)
        if match is not None:
            rule = re.compile(r"([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]")
            match = rule.search(self.exp_time)
            tmp_target = match.group()
            tmp_parser = tmp_target.split(":")
            if 0 <= int(tmp_parser[0]) <= 11:
                self.tp.tunit[3] = int(tmp_parser[0]) + 12
            else:
                self.tp.tunit[3] = int(tmp_parser[0])
            self.tp.tunit[4] = int(tmp_parser[1])
            self.tp.tunit[5] = int(tmp_parser[2])
            self.prefer_future(3)
            self.is_all_day_time = False
            self.assigned_period = True
        else:
            rule = re.compile(r"(晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后)(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]")
            match = rule.search(self.exp_time)
            if match is not None:
                rule = re.compile(r"([0-2]?[0-9]):[0-5]?[0-9]")
                match = rule.search(self.exp_time)
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                if 0 <= int(tmp_parser[0]) <= 11:
                    self.tp.tunit[3] = int(tmp_parser[0]) + 12
                else:
                    self.tp.tunit[3] = int(tmp_parser[0])
                self.tp.tunit[4] = int(tmp_parser[1])
                self.prefer_future(3)
                self.is_all_day_time = False
                self.assigned_period = True

        if match is None:
            rule = re.compile(r"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9](PM|pm|p\\.m)", re.I)
            match = rule.search(self.exp_time)
            if match is not None:
                rule = re.compile(r"([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]")
                match = rule.search(self.exp_time)
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                if 0 <= int(tmp_parser[0]) <= 11:
                    self.tp.tunit[3] = int(tmp_parser[0]) + 12
                else:
                    self.tp.tunit[3] = int(tmp_parser[0])

                self.tp.tunit[4] = int(tmp_parser[1])
                self.tp.tunit[5] = int(tmp_parser[2])
                self.prefer_future(3)
                self.is_all_day_time = False
                self.assigned_period = True

            else:
                rule = re.compile(r"(?<!(周|星期))([0-2]?[0-9]):[0-5]?[0-9](PM|pm|p.m)", re.I)
                match = rule.search(self.exp_time)
                if match is not None:
                    rule = re.compile(r"([0-2]?[0-9]):[0-5]?[0-9]")
                    match = rule.search(self.exp_time)
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    if 0 <= int(tmp_parser[0]) <= 11:
                        self.tp.tunit[3] = int(tmp_parser[0]) + 12
                    else:
                        self.tp.tunit[3] = int(tmp_parser[0])
                    self.tp.tunit[4] = int(tmp_parser[1])
                    self.prefer_future(3)
                    self.is_all_day_time = False
                    self.assigned_period = True

        if match is None:
            rule = re.compile(r"(?<!(周|星期|晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后))([0-2]?[0-9]):[0-5]?[0-9]:[0-5]?[0-9]")
            match = rule.search(self.exp_time)
            if match is not None:
                tmp_target = match.group()
                tmp_parser = tmp_target.split(":")
                self.tp.tunit[3] = int(tmp_parser[0])
                self.tp.tunit[4] = int(tmp_parser[1])
                self.tp.tunit[5] = int(tmp_parser[2])
                self.prefer_future(3)
                self.is_all_day_time = False
            else:
                rule = re.compile(r"(?<!(周|星期|晚上|夜间|夜里|今晚|明晚|晚|夜里|下午|午后))([0-2]?[0-9]):[0-5]?[0-9]")
                match = rule.search(self.exp_time)
                if match is not None:
                    tmp_target = match.group()
                    tmp_parser = tmp_target.split(":")
                    self.tp.tunit[3] = int(tmp_parser[0])
                    self.tp.tunit[4] = int(tmp_parser[1])
                    self.prefer_future(3)
                    self.is_all_day_time = False

        # 这里是对年份表达的极好方式
        rule = re.compile(r"[0-9]?[0-9]?[0-9]{2}-((10)|(11)|(12)|([1-9]))-((?<!\\d))([0-3][0-9]|[1-9])")
        match = rule.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("-")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])

        rule = re.compile(r"[0-9]?[0-9]?[0-9]{2}/((10)|(11)|(12)|([1-9]))/((?<!\\d))([0-3][0-9]|[1-9])")
        match = rule.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])

        rule = re.compile(r"((10)|(11)|(12)|([1-9]))/((?<!\\d))([0-3][0-9]|[1-9])/[0-9]?[0-9]?[0-9]{2}")
        match = rule.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split("/")
            self.tp.tunit[1] = int(tmp_parser[0])
            self.tp.tunit[2] = int(tmp_parser[1])
            self.tp.tunit[0] = int(tmp_parser[2])

        rule = re.compile(r"[0-9]?[0-9]?[0-9]{2}\\.((10)|(11)|(12)|([1-9]))\\.((?<!\\d))([0-3][0-9]|[1-9])")
        match = rule.search(self.exp_time)
        if match is not None:
            tmp_target = match.group()
            tmp_parser = tmp_target.split(".")
            self.tp.tunit[0] = int(tmp_parser[0])
            self.tp.tunit[1] = int(tmp_parser[1])
            self.tp.tunit[2] = int(tmp_parser[2])
            
    # 节假日相关
    def norm_set_holiday(self):
        rule = u"(情人节)|(母亲节)|(青年节)|(教师节)|(中元节)|(端午)|(劳动节)|(7夕)|(建党节)|(建军节)|(初13)|(初14)|(初15)|" \
               u"(初12)|(初11)|(初9)|(初8)|(初7)|(初6)|(初5)|(初4)|(初3)|(初2)|(初1)|(中和节)|(圣诞)|(中秋)|(春节)|(元宵)|" \
               u"(航海日)|(儿童节)|(国庆)|(植树节)|(元旦)|(重阳节)|(妇女节)|(记者节)|(立春)|(雨水)|(惊蛰)|(春分)|(清明)|(谷雨)|" \
               u"(立夏)|(小满 )|(芒种)|(夏至)|(小暑)|(大暑)|(立秋)|(处暑)|(白露)|(秋分)|(寒露)|(霜降)|(立冬)|(小雪)|(大雪)|" \
               u"(冬至)|(小寒)|(大寒)"
        pattern = re.compile(rule)
        match = pattern.search(self.exp_time)
        if match is not None:
            if self.tp.tunit[0] == -1:
                self.tp.tunit[0] = int(self.normalizer.time_base.split('-')[0])
            holi = match.group()
            if u"节" not in holi:
                holi += u"节"
            if holi in self.normalizer.holi_solar:
                date = self.normalizer.holi_solar[holi].split('-')
            elif holi in self.normalizer.holi_lunar:
                date = self.normalizer.holi_lunar[holi].split('-')
                lsc = LunarSolarConverter()
                lunar = Lunar(self.tp.tunit[0], int(date[0]), int(date[1]), False)
                solar = lsc.LunarToSolar(lunar)
                self.tp.tunit[0] = solar.solar_year
                date[0] = solar.solar_month
                date[1] = solar.solar_day
            else:
                holi = holi.strip(u"节")
                if holi in ["小寒", "大寒"]:
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
    
    def norm_set_base_related(self):
        """
        设置以上文时间为基准的时间偏移计算
        """
        cur = arrow.get(self.normalizer.time_base, "YYYY-M-D-H-m-s")
        flag = [False, False, False, False, False, False]
        rule_numb = re.compile(r"[0-9]+")
        
        # 规则一、半XX前/后，XX半前/后
        # 年前（半）
        rule = re.compile(r"(半年.*前)|(\d+年半.*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1] = True, True
            year = 0
            month = 6
            if numb_match:
                year = int(numb_match.group())
            cur = cur.shift(years=-year,months=-month)
        # 年后（半）
        rule = re.compile(r"(半年.*后)|(\d+年半.*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1] = True, True
            year = 0
            month = 6
            if numb_match:
                year = int(numb_match.group())
            cur = cur.shift(years=year,months=month)
        # 月前（半）
        rule = re.compile(r"(半(个)?月.*前)|(\d+(个)?月半.*前)|(\d+(个)?半月.*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            month = 0
            day = 15
            if numb_match:
                month = int(numb_match.group())
            cur = cur.shift(months=-month,days=-day)
        # 月后（半）
        rule = re.compile(r"(半(个)?月.*后)|(\d+(个)?月半.*后)|(\d+(个)?半月.*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            month = 0
            day = 15
            if numb_match:
                month = int(numb_match.group())
            cur = cur.shift(months=month,days=day)
        # 周前（半）
        rule = re.compile(r"(半(个)?(周|星期|礼拜).*前)|(\d+(个)?(周|星期|礼拜)半.*前)|(\d+(个)?半(周|星期|礼拜).*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            week = 0
            day = 4
            if numb_match:
                week = int(numb_match.group())
            cur = cur.shift(weeks=-week,days=-day)
        # 周后（半）
        rule = re.compile(r"(半(个)?(周|星期|礼拜).*后)|(\d+(个)?(周|星期|礼拜)半.*后)|(\d+(个)?半(周|星期|礼拜).*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            week = 0
            day = 4
            if numb_match:
                week = int(numb_match.group())
            cur = cur.shift(weeks=week,days=day)        
        # 天前（半）
        rule = re.compile(r"(半(个)?(日|天).*前)|(\d+(个)?(日|天)半.*前)|(\d+(个)?半(日|天).*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3] = True, True, True, True
            day = 0
            hour = 12
            if numb_match:
                day = int(numb_match.group())
            cur = cur.shift(days=-day,hours=-hour)
        # 天后（半）
        rule = re.compile(r"(半(个)?(日|天).*后)|(\d+(个)?(日|天)半.*后)|(\d+(个)?半(日|天).*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3] = True, True, True, True
            day = 0
            hour = 12
            if numb_match:
                day = int(numb_match.group())
            cur = cur.shift(days=day,hours=hour)
        # 小时前（半）
        rule = re.compile(r"(半(个)?(钟头|小时).*前)|(\d+(个)?(钟头|小时)半.*前)|(\d+(个)?半(钟头|小时).*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4] = True, True, True, True, True
            hour = 0
            minute = 30
            if numb_match:
                hour = int(numb_match.group())
            cur = cur.shift(hours=-hour,minutes=-minute)
        # 小时后（半）
        rule = re.compile(r"(半(个)?(钟头|小时).*后)|(\d+(个)?(钟头|小时)半.*后)|(\d+(个)?半(钟头|小时).*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4] = True, True, True, True, True
            hour = 0
            minute = 30
            if numb_match:
                hour = int(numb_match.group())
            cur = cur.shift(hours=hour,minutes=minute)
        # 分钟前（半）
        rule = re.compile(r"(半(个)?(分|分钟).*前)|(\d+(个)?(分|分钟)半.*前)|(\d+(个)?半(分|分钟).*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4], flag[5] = True, True, True, True, True, True
            minute = 0
            second = 30
            if numb_match:
                minute = int(numb_match.group())
            cur = cur.shift(minutes=-minute,seconds=-second)
        # 分钟后（半）
        rule = re.compile(r"(半(个)?(分|分钟).*后)|(\d+(个)?(分|分钟)半.*后)|(\d+(个)?半(分|分钟).*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4], flag[5] = True, True, True, True, True, True
            minute = 0
            second = 30
            if numb_match:
                minute = int(numb_match.group())
            cur = cur.shift(minutes=minute,seconds=second)
        
        # 规则二、XX前/后
        # 年前
        rule = re.compile(r"(\d+年[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1] = True, True
            year = 0
            if numb_match:
                year = int(numb_match.group())
            cur = cur.shift(years=-year)
        # 年后
        rule = re.compile(r"(\d+年[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1] = True, True
            year = 0
            if numb_match:
                year = int(numb_match.group())
            cur = cur.shift(years=year)
        # 月前
        rule = re.compile(r"(\d+(个)?月[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            month = 0
            if numb_match:
                month = int(numb_match.group())
            cur = cur.shift(months=-month)
        # 月后
        rule = re.compile(r"(\d+(个)?月[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            month = 0
            if numb_match:
                month = int(numb_match.group())
            cur = cur.shift(months=month)
        # 周前
        rule = re.compile(r"(\d+(个)?(周|星期|礼拜)[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            week = 0
            if numb_match:
                week = int(numb_match.group())
            cur = cur.shift(weeks=-week)
        # 周后
        rule = re.compile(r"(\d+(个)?(周|星期|礼拜)[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2] = True, True, True
            week = 0
            if numb_match:
                week = int(numb_match.group())
            cur = cur.shift(weeks=week)        
        # 天前
        rule = re.compile(r"(\d+(个)?(日|天)[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3] = True, True, True, True
            day = 0
            if numb_match:
                day = int(numb_match.group())
            cur = cur.shift(days=-day)
        # 天后
        rule = re.compile(r"(\d+(个)?(日|天)[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3] = True, True, True, True
            day = 0
            if numb_match:
                day = int(numb_match.group())
            cur = cur.shift(days=day)
        # 小时前
        rule = re.compile(r"(\d+(个)?(钟头|小时)[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4] = True, True, True, True, True
            hour = 0
            if numb_match:
                hour = int(numb_match.group())
            cur = cur.shift(hours=-hour)
        # 小时后
        rule = re.compile(r"(\d+(个)?(钟头|小时)[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4] = True, True, True, True, True
            hour = 0
            if numb_match:
                hour = int(numb_match.group())
            cur = cur.shift(hours=hour)
        # 分钟前
        rule = re.compile(r"(\d+(个)?(分|分钟)[^半]*前)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4], flag[5] = True, True, True, True, True, True
            minute = 0
            if numb_match:
                minute = int(numb_match.group())
            cur = cur.shift(minutes=-minute)
        # 分钟后
        rule = re.compile(r"(\d+(个)?(分|分钟)[^半]*后)")
        match = rule.search(self.exp_time)
        if match:
            match_res = match.group()
            numb_match = rule_numb.search(match_res)
            flag[0], flag[1], flag[2], flag[3], flag[4], flag[5] = True, True, True, True, True, True
            minute = 0
            if numb_match:
                minute = int(numb_match.group())
            cur = cur.shift(minutes=minute)
        
        if any(flag):
            repl_tunit = [int(item) for item in [cur.year,cur.month,cur.day,cur.hour,cur.minute,cur.second]]
            for i in range(len(repl_tunit)):
                if self.tp.tunit[i] == -1 and flag[i] == True:
                    self.tp.tunit[i] = repl_tunit[i]
        
    def norm_set_cur_related(self):
        """
        设置当前时间相关的时间表达式
        """
        cur = arrow.get(self.normalizer.time_base, "YYYY-M-D-H-m-s")
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

        # 星期相关的预测
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
            cur = self.prefer_future_week(week, cur)

        if flag[0] or flag[1] or flag[2]:
            self.tp.tunit[0] = int(cur.year)
        if flag[1] or flag[2]:
            self.tp.tunit[1] = int(cur.month)
        if flag[2]:
            self.tp.tunit[2] = int(cur.day)
            
    def norm_set_span_related(self):
        """
        设置时间长度相关的时间表达式
        """
        
        # 年（整）
        rule = re.compile(r"\d+(?=(个)?年(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            year = int(match.group())
            self.tp.tunit[0] = year
            
        # 年（半）
        rule = re.compile(r"(\d+(?=(个)?年半(?!.*前|.*后)))|(\d+(?=(个)?半年(?!.*前|.*后)))|(?=半年(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                year = 0
            else:
                year = int(match.group())
            self.tp.tunit[0] = year
            self.tp.tunit[1] = 6
        
        # 月（整）
        rule = re.compile(r"\d+(?=个月(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            month = int(match.group())
            self.tp.tunit[1] = month
            
        # 月（半）
        rule = re.compile(r"(\d+(?=个月半(?!.*前|.*后)))|(\d+(?=个半月(?!.*前|.*后)))|(?=半个月(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                month = 0
            else:
                month = int(match.group())
            self.tp.tunit[1] = month
            self.tp.tunit[2] = 15
        
        # 周（整）
        rule = re.compile(r"\d+(?=(个)?(周|礼拜|星期)(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            week = int(match.group())
            self.tp.tunit[2] = week * 7
            
        # 周（半）
        rule = re.compile(r"(\d+(?=(个)?(周|星期|礼拜)半(?!.*前|.*后)))|(\d+(?=(个)?半(周|礼拜|星期)(?!.*前|.*后)))|(?=半(个)?(周|礼拜|星期)(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                week = 0
            else:
                week = int(match.group())
            self.tp.tunit[2] = week * 7 + 4
        
        # 天（整）
        rule = re.compile(r"\d+(?=(个)?天(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            day = int(match.group())
            self.tp.tunit[2] = day
            
        # 天（半）
        rule = re.compile(r"(\d+(?=(个)?(日|天)半(?!.*前|.*后)))|(\d+(?=(个)?半(日|天)(?!.*前|.*后)))|(?=半(个)?(日|天)(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                day = 0
            else:
                day = int(match.group())
            self.tp.tunit[2] = day
            self.tp.tunit[3] = 12

        # 小时（整）
        rule = re.compile(r"\d+(?=(个)?(小时|钟头)(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            hour = int(match.group())
            self.tp.tunit[3] = hour
            
        # 小时（半）
        rule = re.compile(r"(\d+(?=(个)?(钟头|小时)半(?!.*前|.*后)))|(\d+(?=(个)?半(钟头|小时)(?!.*前|.*后)))|(?=半(个)?(钟头|小时)(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                hour = 0
            else:
                hour = int(match.group())
            self.tp.tunit[3] = hour
            self.tp.tunit[4] = 30
        
        # 分钟（整）
        rule = re.compile(r"\d+(?=(个)?(分钟)(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            minute = int(match.group())
            self.tp.tunit[4] = minute
            
        # 分钟（半）
        rule = re.compile(r"(\d+(?=(个)?(分钟)半(?!.*前|.*后)))|(\d+(?=(个)?半(分钟)(?!.*前|.*后)))|(?=半(个)?(分钟)(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                minute = 0
            else:
                minute = int(match.group())
            self.tp.tunit[4] = minute
            self.tp.tunit[5] = 30

        # 秒钟（整）
        rule = re.compile(r"\d+(?=(个)?(秒钟)(?!半.*|.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            second = int(match.group())
            self.tp.tunit[5] = second
            
        # 秒钟（半）-没有半秒的说法，所以默认改为秒钟（整）
        rule = re.compile(r"(\d+(?=(个)?(秒钟)半(?!.*前|.*后)))|(\d+(?=(个)?半(秒钟)(?!.*前|.*后)))|(?=半(个)?(秒钟)(?!.*前|.*后))")
        match = rule.search(self.exp_time)
        if match:
            self.normalizer.is_time_span = True
            if match.group() == "":
                second = 0
            else:
                second = int(match.group())
            self.tp.tunit[5] = second
            
    def prefer_future_week(self, weekday, cur):
        # 1. 确认用户选项
        if not self.normalizer.is_prefer_future:
            return cur
        # 2. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, 2):
            if self.tp.tunit[i] != -1:
                return cur
        # 获取当前是在周几，如果识别到的时间小于当前时间，则识别时间为下一周
        tmp = arrow.get(self.normalizer.time_base, "YYYY-M-D-H-m-s")
        cur_weekday = tmp.weekday()
        if cur_weekday > weekday:
            cur = cur.shift(days=7)
        return cur

    def prefer_future(self, check_time_idx):
        """
        如果用户选项是倾向于未来时间，检查check_time_index所指的时间是否是过去的时间，如果是的话，将大一级的时间设为当前时间的+1。
        如在晚上说“早上8点看书”，则识别为明天早上;
        12月31日说“3号买菜”，则识别为明年1月的3号。
        :param check_time_idx: tp.tunit时间数组的下标
        """
        # 1. 检查被检查的时间级别之前，是否没有更高级的已经确定的时间，如果有，则不进行处理.
        for i in range(0, check_time_idx):
            if self.tp.tunit[i] != -1:
                return
        # 2. 补全上下文时间
        for i in range(0, check_time_idx):
            if self.tp.tunit[i] == -1 and self.tp_origin.tunit[i] != -1:
                self.tp.tunit[i] = self.tp_origin.tunit[i]
        # 3. 检查是否指定了时间段（早上/中午等），如果有，则不进行处理。
        if self.assigned_period:
            return
        # 4. 确认用户选项
        time_arr = self.normalizer.time_base.split("-")
        cur_unit = int(time_arr[check_time_idx])
        cur = arrow.get(self.normalizer.time_base, "YYYY-M-D-H-m-s")
        if self.normalizer.is_prefer_future:
            if check_time_idx == 3:
                if self.tp.tunit[3] < 12 and cur.hour < 12:
                    if self.tp.tunit[3] < cur.hour:
                        self.tp.tunit[3] += 12
                elif self.tp.tunit[3] < 12 and cur.hour >= 12:
                    if self.tp.tunit[3] + 12 >= cur.hour:
                        self.tp.tunit[3] += 12
                    else:
                        cur = cur.shift(days=1)
                        self.tp.tunit[0], self.tp.tunit[1], self.tp.tunit[2] = cur.year, cur.month, cur.day
                elif self.tp.tunit[3] >= 12 and cur.hour < 12:
                    if self.tp.tunit[3] - 12 >= cur.hour:
                        self.tp.tunit[3] -= 12
                else:
                    if self.tp.tunit[3] < cur.hour:
                        cur = cur.shift(hours=12)
                        self.tp.tunit[0], self.tp.tunit[1], self.tp.tunit[2] = cur.year, cur.month, cur.day
                        self.tp.tunit[3] -= 12
            else:
                cur = self.shift_time(cur, check_time_idx - 1, 1)
                time_arr = cur.format("YYYY-M-D-H-m-s").split("-")
                for i in range(0, check_time_idx):
                    self.tp.tunit[i] = int(time_arr[i])
        else:
            if check_time_idx == 3:
                if self.tp.tunit[3] < 12 and cur.hour < 12:
                    if self.tp.tunit[3] >= cur.hour:
                        cur = cur.shift(hours=-12)
                        self.tp.tunit[0], self.tp.tunit[1], self.tp.tunit[2] = cur.year, cur.month, cur.day
                        self.tp.tunit[3] += 12
                elif self.tp.tunit[3] < 12 and cur.hour >= 12:
                    if self.tp.tunit[3] + 12 < cur.hour:
                        self.tp.tunit[3] += 12
                elif self.tp.tunit[3] >= 12 and cur.hour < 12:
                    if self.tp.tunit - 12 >= cur.hour:
                        cur = cur.shift(days=-1)
                        self.tp.tunit[0], self.tp.tunit[1], self.tp.tunit[2] = cur.year, cur.month, cur.day
                    else:
                        self.tp.tunit -= 12
                else:
                    if self.tp.tunit[3] >= cur.hour:
                        self.tp.tunit -= 12
            else:
                cur = self.shift_time(cur, check_time_idx - 1, -1)
                time_arr = cur.format("YYYY-M-D-H-m-s").split("-")
                for i in range(0, check_time_idx):
                    self.tp.tunit[i] = int(time_arr[i])
            
    def _check_time(self, parse):
        """
        检查未来时间点
        :param parse: 解析出来的list
        """
        time_arr = self.normalizer.time_base.split('-')
        if self._noyear:
            if parse[1] == int(time_arr[1]):
                if parse[2] > int(time_arr[2]):
                    parse[0] = parse[0] - 1
            self._noyear = False
        
    def shift_time(self, cur, fore_unit, move):
        if fore_unit == 0:
            cur = cur.shift(years=move)
        elif fore_unit == 1:
            cur = cur.shift(months=move)
        elif fore_unit == 2:
            cur = cur.shift(days=move)
        elif fore_unit == 3:
            cur = cur.shift(hours=move)
        elif fore_unit == 4:
            cur = cur.shift(minutes=move)
        elif fore_unit == 5:
            cur = cur.shift(seconds=move)
        return cur
        
        
# 时间表达式识别的主要工作类
class TimeExtractor(object):
    
    def __init__(self, is_prefer_future=False):
        self.is_prefer_future = is_prefer_future
        self.pattern, self.holi_solar, self.holi_lunar = self._load_regex()
        
    def _load_regex(self):
        basic_path = os.path.dirname(__file__)
        pkl_path = os.path.join(basic_path, "utils/resource/reg.pkl")
        reg_path = os.path.join(basic_path, "utils/resource/regex.txt")
        if not os.path.exists(pkl_path):
            with codecs.open(reg_path, "r", "utf-8-sig") as f:
                content = f.read()
            pkl = re.compile(content)
            with open(pkl_path, "wb") as f:
                pickle.dump(pkl, f)
        with open(pkl_path, "rb") as f:
            pattern = pickle.load(f)
        with codecs.open(os.path.join(basic_path, "utils/resource/holi_solar.json"), "r", "utf-8-sig") as f:
            holi_solar = json.load(f)
        with codecs.open(os.path.join(basic_path, "utils/resource/holi_lunar.json"), "r", "utf-8-sig") as f:
            holi_lunar = json.load(f)
        return pattern, holi_solar, holi_lunar
    
    def __pre_handling(self):
        """
        待匹配字符串的清理空白符和语气助词以及大写数字转化的预处理
        """
        self.target = StringPreHandler.delKeyword(
            self.target, u"\\s+")  # 清理空白符
        self.target = StringPreHandler.delKeyword(
            self.target, u"[的]+")  # 清理语气助词
        self.target = StringPreHandler.numberTranslator(self.target)  # 大写数字转化
    
    def _fix_fuzzy_weekdays(self, s):
        """
        模糊匹配：包含周模糊和时刻模糊中至少一个，将二者拆分出来。
        """
        # rule: 判断是否同时包含周和时刻的信息
        rule = re.compile(r"(礼拜|周|星期)(一二|二三|三四|四五|五六|六七|六日)(早上|上午|中午|下午|晚上|早|中|晚)?(一|二|三|四|五|六|七|八|九|十|两)*?(点|时)")
        if rule.search(s) == None:
            # rule_week: 简单提取周信息即可
            rule_week = re.compile(r"(礼拜|周|星期)(一二|二三|三四|四五|五六|六七|六日)")
            rule_week_res = [
                {
                    "text": i.group(),
                    "start": i.start(),
                    "end": i.end()
                } for i in rule_week.finditer(s)
            ]
            if rule_week_res == []:
                fixed_s = s
            else:
                fixed_s = ""
                c_end = 0
                for term in rule_week_res:
                    n_start = term["start"]
                    n_end = term["end"]
                    fixed_s += s[c_end:n_start+2] + s[n_start+3:n_end]
                    c_end = n_end
                fixed_s += s[c_end:]
        else:
            # rule_week: 同时包含周信息和时刻信息，仅对周信息进行处理
            rule_seg = re.compile(r"(早上|上午|中午|下午|晚上|早|中|晚)")
            if rule_seg.search(s) != None:
                rule_week = re.compile(r"(礼拜|周|星期)(一二|二三|三四|四五|五六|六七|六日)")
                rule_week_res = [
                    {
                        "text": i.group(),
                        "start": i.start(),
                        "end": i.end()
                    } for i in rule_week.finditer(s)
                ]
                if rule_week_res == []:
                    fixed_s = s
                else:
                    fixed_s = ""
                    c_end = 0
                    for term in rule_week_res:
                        n_start = term["start"]
                        n_end = term["end"]
                        fixed_s += s[c_end:n_start+2] + s[n_start+3:n_end]
                        c_end = n_end
                    fixed_s += s[c_end:]
            else:
                rule_week = re.compile(r"(礼拜|周|星期)(一二|二三|三四|四五|五六|六七|六日)(一|二|三|四|五|六|七|八|九|十|两)*?(点|时)")
                if rule_week.search(s) == None:
                    fixed_s = s
                else:
                    rule_week_res = [
                        {
                            "text": i.group(),
                            "start": i.start(),
                            "end": i.end()
                        } for i in rule_week.finditer(s)
                    ]
                    rule_digit = re.compile(r"(一|二|三|四|五|六|七|八|九|十|日|两)+")
                    rule_digit_res = [
                        rule_digit.search(item["text"]) for item in rule_week_res
                    ]
                    fixed_s = ""
                    c_end = 0
                    for week_term, digit_term in zip(rule_week_res, rule_digit_res):
                        n_start = week_term["start"] + digit_term.start()
                        n_end = week_term["start"] + digit_term.end()
                        fixed_s += s[c_end:n_start]
                        if (digit_term.group()[1]=="两") or (digit_term.group()[1]=="十") or (digit_term.group()[1]=="二" and digit_term.group()[2]=="十"):
                            fixed_s += (s[n_start] + s[n_start+1:n_end])
                        else:
                            fixed_s += (s[week_term["start"]+1] + s[n_start+2:n_end])
                        c_end = n_end
                    fixed_s += s[c_end:]
        return fixed_s
    
    def _fix_fuzzy_times(self, s):
        """
        模糊匹配：包含日期模糊。
        """
        # rule: 判断是否包含连续的数字
        rule = re.compile(r"(一|二|两|三|四|五|六|七|八|九|十){2}(个)?(年|月|周|天|日|号|小时|时|点|钟|分|分钟|秒|秒钟)")
        if rule.search(s) == None:
            fixed_s = s
        else:
            rule_res = [
                {
                    "text": i.group(),
                    "start": i.start(),
                    "end": i.end()
                } for i in rule.finditer(s)
            ]
            fixed_s = ""
            c_end = 0
            for term in rule_res:
                n_start = term["start"]
                n_end = term["end"]
                fixed_s += s[c_end:n_start]
                if (term["text"][0]=="十") or (term["text"][0]=="二" and term["text"][1]=="十"):
                    fixed_s += (s[n_start] + s[n_start+1:n_end])
                else:
                    fixed_s += (s[n_start] + s[n_start+2:n_end])
                c_end = n_end
            fixed_s += s[c_end:]
        return fixed_s
    
    def _filter(self, s):
        # 模糊时间的处理
        s = self._fix_fuzzy_weekdays(s)
        s = self._fix_fuzzy_times(s)
        
        # 这里对于下个周末这种做转化 把个给移除掉
        s = StringPreHandler.numberTranslator(s)
        rule = u"[0-9]月[0-9]"
        pattern = re.compile(rule)
        match = pattern.search(s)
        if match != None:
            index = s.find('月')
            rule = u"日|号"
            pattern = re.compile(rule)
            match = pattern.search(s[index:])
            if match == None:
                rule = u"[0-9]月[0-9]+"
                pattern = re.compile(rule)
                match = pattern.search(s)
                if match != None:
                    end = match.end()
                    s = s[:end] + '号' + s[end:]
        rule = u"月"
        pattern = re.compile(rule)
        match = pattern.search(s)
        if match == None:
            s = s.replace('个', '')
        s = s.replace('中旬', '15号')
        s = s.replace('傍晚', '午后')
        s = s.replace('大年', '')
        s = s.replace('五一', '劳动节')
        s = s.replace('白天', '早上')
        s = s.replace('：', ':')
        return s
    
    def parse(self, target):
        """
        time_base取默认的系统当前时间
        """
        self.is_time_span = False
        self.invalid_time_span = False
        self.time_span = ""
        self.target = self._filter(target)
        self.__pre_handling()
        self.time_base = arrow.now().format("YYYY-M-D-H-m-s")
        self.str_time, self.norm_time = self.__time_ex()
        dic = {}
        res = self.norm_time
        
        if self.is_time_span:
            if self.invalid_time_span:
                dic["error"] = "no timedelta could be extracted."
            else:
                result = {}
                dic["type"] = "timedelta"
                dic["timedelta"] = self.time_span
                idx = dic["timedelta"].find("days")
                
                days = int(dic["timedelta"][:idx-1])
                result["year"] = int(days/365)
                result["month"] = int(days/30 - result["year"]*12)
                result["day"] = int(days - result["year"]*365 - result["month"]*30)
                idx = dic["timedelta"].find(",")
                time = dic["timedelta"][idx+1:]
                time = time.split(":")
                result["hour"] = int(time[0])
                result["minute"] = int(time[1])
                result["minute"] = int(time[2])
                dic["timedelta"] = result
        else:
            if len(res) == 0:
                dic["error"] = "no timestamp or timespan could be extracted."
            elif len(res) == 1:
                dic["type"] = "timestamp"
                dic["timestamp"] = res[0].time.format("YYYY-MM-DD HH:mm:ss")
            else:
                dic["type"] = "timespan"
                dic["timespan"] = [res[0].time.format("YYYY-MM-DD HH:mm:ss"),
                                   res[1].time.format("YYYY-MM-DD HH:mm:ss")]
            return json.dumps(dic,ensure_ascii=False)      
        
    def __time_ex(self):
        """
        文本字符串时间转TimeUnit时间数组
        """
        start, end, r_pointer = -1, -1, 0
        str_time, norm_time = [], []
        
        rule_res = self.pattern.finditer(self.target)
        for item in rule_res:
            start = item.start()
            if start == end:
                r_pointer -= 1
                str_time[r_pointer] = str_time[r_pointer] + item.group()
            else:
                str_time.append(item.group())
            end = item.end()
            r_pointer += 1
        str_time = [item for item in str_time if item != ""]
        r_pointer = len(str_time)
        now_time = [int(item) for item in self.time_base.format("YYYY-MM-DD-HH-mm-ss").split("-")]
        tp = TimePoint(now_time)
        if r_pointer != 0:
            for i in range(r_pointer):
                norm_time.append(TimeUnit(str_time[i],self,TimePoint(now_time)))
            norm_time = self.__filter_time_unit(norm_time)
        return str_time, norm_time
    
    def __filter_time_unit(self, tu_arr):
        """
        过滤识别结果中的无用识别词，其返回的时间为1970.01.01 00:00:00(fastTime=0)
        """
        if (tu_arr is None) or (len(tu_arr) < 1):
            return tu_arr
        res = []
        for tu in tu_arr:
            if tu.time.timestamp != 0:
                res.append(tu)
        return res