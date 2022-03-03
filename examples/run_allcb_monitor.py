# coding: utf-8
"""
基于聚宽数据的实时日线因子监控
"""

# 首次使用需要设置聚宽账户
# from czsc.data.jq import set_token
# set_token("phone number", 'password') # 第一个参数是JQData的手机号，第二个参数是登录密码
import traceback
import time
import shutil
import os
from datetime import datetime, timedelta
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks, pro, format_kline, get_ths_members
# from czsc.data.jq import JqCzscTrader as CzscTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.utils.qywx import push_text, push_file
from czsc.utils.io import read_pkl, save_pkl
import requests
import json
from czsc.data.ts import get_kline, get_all_cb, get_all_cbDaily
import pandas as pd
from czsc.enum import Freq
from czsc.utils.bar_generator import BarGenerator
from czsc.cb.advanced_cb import CzscCBTrader
from czsc.signals.signals import get_default_signals
import akshare as ak

# =======================================================================================================
# 基础参数配置
ct_path = "/Volumes/OuGuMore/Stock/cb"
os.makedirs(ct_path, exist_ok=True)

allCBs = get_all_cb()
allcodes = allCBs['ts_code'].values.tolist()


events_monitor = [
    # 五笔aAb式
    Event(name="五笔aAb式买", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    ]),

    Event(name="五笔aAb式卖", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    ]),

    # 五笔类趋势
    Event(name="五笔类趋势买", operate=Operate.LO, factors=[
        Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
        Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
        Factor(name="15分钟_类趋势买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
        Factor(name="5分钟_类趋势买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
        Factor(name="60分钟_类趋势买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),

    ]),

    Event(name="五笔类趋势卖", operate=Operate.LO, factors=[
        Factor(name="日线_类趋势卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
        Factor(name="30分钟_类趋势卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
        Factor(name="15分钟_类趋势卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
        Factor(name="5分钟_类趋势卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
        Factor(name="60分钟_类趋势卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    ]),

    # 五笔三买
    Event(name="五笔三买", operate=Operate.LO, factors=[
        Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_五笔_任意_0")]),
        Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
        Factor(name="15分钟_三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
        Factor(name="5分钟_三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
        Factor(name="60分钟_三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    ]),

    Event(name="五笔三卖", operate=Operate.LO, factors=[
        Factor(name="30分钟_三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
        Factor(name="日线_三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_五笔_任意_0")]),
        Factor(name="15分钟_三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
        Factor(name="5分钟_三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
        Factor(name="60分钟_三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    ]),

    # 七笔aAbcd式
    Event(name="七笔aAbcd式买", operate=Operate.LO, factors=[
        Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
        Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
        Factor(name="15分钟_aAbcd式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
        Factor(name="5分钟_aAbcd式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
        Factor(name="60分钟_aAbcd式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    ]),

    Event(name="七笔aAbcd式卖", operate=Operate.LO, factors=[
        Factor(name="日线_aAbcd式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
        Factor(name="30分钟_aAbcd式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
        Factor(name="15分钟_aAbcd式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
        Factor(name="5分钟_aAbcd式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
        Factor(name="60分钟_aAbcd式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    ]),

    # 七笔abcAd式
    Event(name="七笔abcAd式买", operate=Operate.LO, factors=[
        Factor(name="日线_abcAd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
        Factor(name="30分钟_abcAd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
        Factor(name="15分钟_abcAd式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
        Factor(name="5分钟_abcAd式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
        Factor(name="60分钟_abcAd式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    ]),

    Event(name="七笔abcAd式卖", operate=Operate.LO, factors=[
        Factor(name="日线_abcAd式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
        Factor(name="30分钟_abcAd式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
        Factor(name="15分钟_abcAd式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
        Factor(name="5分钟_abcAd式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
        Factor(name="60分钟_abcAd式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    ]),

    # 七笔aAb式
    Event(name="七笔aAb式买", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    ]),

    Event(name="七笔aAb式卖", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    ]),

    # 七笔三买
    Event(name="七笔三买", operate=Operate.LO, factors=[
        Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_七笔_任意_0")]),
        Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
        Factor(name="15分钟_三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
        Factor(name="5分钟_三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
        Factor(name="60分钟_三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    ]),

    Event(name="七笔三卖", operate=Operate.LO, factors=[
        Factor(name="日线_三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_七笔_任意_0")]),
        Factor(name="30分钟_三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
        Factor(name="15分钟_三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
        Factor(name="5分钟_三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
        Factor(name="60分钟_三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    ]),

    # 七笔类趋势
    Event(name="七笔类趋势买", operate=Operate.LO, factors=[
        Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
        Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
        Factor(name="15分钟_类趋势买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
        Factor(name="5分钟_类趋势买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
        Factor(name="60分钟_类趋势买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    ]),

    Event(name="七笔类趋势卖", operate=Operate.LO, factors=[
        Factor(name="日线_类趋势卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
        Factor(name="30分钟_类趋势卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
        Factor(name="15分钟_类趋势卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
        Factor(name="5分钟_类趋势卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
        Factor(name="60分钟_类趋势卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    ]),

    # 九笔aAb式
    Event(name="九笔aAb式买", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    ]),

    Event(name="九笔aAb式卖", operate=Operate.LO, factors=[
        Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
        Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
        Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
        Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
        Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    ]),

    # 九笔aAbcd式
    Event(name="九笔aAbcd式买", operate=Operate.LO, factors=[
        Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0")]),
        Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0")]),
        Factor(name="15分钟_aAbcd式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0")]),
        Factor(name="5分钟_aAbcd式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0")]),
        Factor(name="60分钟_aAbcd式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0")]),
    ]),

    Event(name="九笔aAbcd式卖", operate=Operate.LO, factors=[
        Factor(name="日线_aAbcd式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
        Factor(name="30分钟_aAbcd式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
        Factor(name="15分钟_aAbcd式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
        Factor(name="5分钟_aAbcd式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
        Factor(name="60分钟_aAbcd式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    ]),

    # 九笔ABC式
    Event(name="九笔ABC式买", operate=Operate.LO, factors=[
        Factor(name="日线_ABC式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔ABC式_任意_0")]),
        Factor(name="30分钟_ABC式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0")]),
        Factor(name="15分钟_ABC式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0")]),
        Factor(name="5分钟_ABC式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0")]),
        Factor(name="60分钟_ABC式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0")]),
    ]),

    Event(name="九笔ABC式卖", operate=Operate.LO, factors=[
        Factor(name="日线_ABC式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
        Factor(name="30分钟_ABC式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
        Factor(name="15分钟_ABC式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
        Factor(name="5分钟_ABC式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
        Factor(name="60分钟_ABC式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    ]),

    # 九笔类一买 （2~4构成中枢A，6~8构成中枢B，9背驰）
    Event(name="九笔aAbBc式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0")]),
    ]),

    Event(name="九笔aAbBc式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    ]),

    # 九笔类三买 （1357构成中枢，最低点在3或5）（357构成中枢，8的力度小于2，9回调不跌破GG构成三买）
    Event(name="九笔GG三买", operate=Operate.LO, factors=[
        Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0")]),
        Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0")]),
        Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0")]),
        Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0")]),
        Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0")]),
    ]),

    # 九笔类三买 前五笔构成向下类趋势 567构成中枢，且8的高点大于GG
    Event(name="九笔ZG三买", operate=Operate.LO, factors=[
        Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
        Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
        Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
        Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
        Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    ]),

    # 九笔类二买
    Event(name="九笔二买", operate=Operate.LO, factors=[
        Factor(name="日线_类二买", signals_all=[Signal("日线_倒1笔_类买卖点_类二买_九笔_任意_0")]),
        Factor(name="30分钟_类二买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
        Factor(name="15分钟_类二买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
        Factor(name="5分钟_类二买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
        Factor(name="60分钟_类二买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    ]),

    Event(name="九笔类二卖", operate=Operate.LO, factors=[
        Factor(name="日线_类二卖", signals_all=[Signal("日线_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
        Factor(name="30分钟_类二卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
        Factor(name="15分钟_类二卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
        Factor(name="5分钟_类二卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
        Factor(name="60分钟_类二卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    ]),

    # 九笔类三卖
    Event(name="九笔类三卖", operate=Operate.LO, factors=[
        Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
        Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
        Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
        Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
        Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    ]),

    # 九笔类三卖 前五笔构成向下类趋势 567构成中枢，且8的高点大于GG
    Event(name="九笔ZD三卖", operate=Operate.LO, factors=[
        Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
        Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
        Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
        Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
        Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    ]),

    # 十一笔 11笔A5B3C3式
    Event(name="11笔A5B3C3式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    ]),

    Event(name="11笔A5B3C3式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    ]),

    # 十一笔 11笔A3B3C5式
    Event(name="11笔A3B3C5式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    ]),

    Event(name="11笔A3B3C5式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    ]),

    # 十一笔 11笔A3B5C3式
    Event(name="11笔A3B5C3式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    ]),

    Event(name="11笔A3B5C3式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    ]),

    # 十一笔 11笔a1Ab式
    Event(name="11笔a1Ab式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    ]),

    # 11笔类三买 （1~9构成大级别中枢，10离开，11回调不跌破GG）
    Event(name="11笔GG三买", operate=Operate.LO, factors=[
        Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0")]),
        Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0")]),
        Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0")]),
        Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0")]),
        Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0")]),
    ]),

    # 13笔 ABC式类一买，A5B3C5
    Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    ]),

    # 13笔 ABC式类一卖，A5B3C5
    Event(name="13笔ABC式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    ]),

    # 13笔 ABC式类一买，A3B5C5
    Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    ]),

    # 13笔 ABC式类一卖，A3B5C5
    Event(name="13笔ABC式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    ]),

    # 13笔 ABC式类一买，A5B5C3
    Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    ]),

    # 13笔 ABC式类一卖，A5B5C3
    Event(name="13笔ABC式类一卖", operate=Operate.LO, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_13笔A5B5C3式_任意_0")]),
        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_13笔A5B5C3式_任意_0")]),
        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_13笔A5B5C3式_任意_0")]),
        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_13笔A5B5C3式_任意_0")]),
        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_13笔A5B5C3式_任意_0")]),
    ]),

    # 潜在三买
    Event(name="潜在三买", operate=Operate.LO, factors=[
        Factor(name="日线_潜在三买", signals_all=[Signal("日线_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_近7K突破中枢GG_0")]),
        Factor(name="30分钟_潜在三买", signals_all=[Signal("30分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
        Factor(name="15分钟_潜在三买", signals_all=[Signal("15分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
        Factor(name="5分钟_潜在三买", signals_all=[Signal("5分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
        Factor(name="60分钟_潜在三买", signals_all=[Signal("60分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    ]),

    # 开多
    Event(name="一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_任意_任意_0")]),
        Factor(name="日线_形一买", signals_all=[Signal("日线_倒1笔_基础形态_类一买_任意_任意_0")]),

        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
        Factor(name="30分钟_形一买", signals_all=[Signal("30分钟_倒1笔_基础形态_类一买_任意_任意_0")]),

        Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
        Factor(name="15分钟_形一买", signals_all=[Signal("15分钟_倒1笔_基础形态_类一买_任意_任意_0")]),

        Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
        Factor(name="5分钟_形一买", signals_all=[Signal("5分钟_倒1笔_基础形态_类一买_任意_任意_0")]),

        Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
        Factor(name="60分钟_形一买", signals_all=[Signal("60分钟_倒1笔_基础形态_类一买_任意_任意_0")]),
    ]),

    Event(name="二买", operate=Operate.LO, factors=[
        Factor(name="日线_类二买", signals_all=[Signal("日线_倒1笔_类买卖点_类二买_任意_任意_0")]),
        Factor(name="日线_形二买", signals_all=[Signal("日线_倒1笔_基础形态_类二买_任意_任意_0")]),

        Factor(name="30分钟_类二买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
        Factor(name="30分钟_形二买", signals_all=[Signal("30分钟_倒1笔_基础形态_类二买_任意_任意_0")]),

        Factor(name="15分钟_类二买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
        Factor(name="15分钟_形二买", signals_all=[Signal("15分钟_倒1笔_基础形态_类二买_任意_任意_0")]),

        Factor(name="5分钟_类二买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
        Factor(name="5分钟_形二买", signals_all=[Signal("5分钟_倒1笔_基础形态_类二买_任意_任意_0")]),

        Factor(name="60分钟_类二买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
        Factor(name="60分钟_形二买", signals_all=[Signal("60分钟_倒1笔_基础形态_类二买_任意_任意_0")]),
    ]),
    Event(name="三买", operate=Operate.LO, factors=[
        Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_任意_任意_0")]),
        Factor(name="日线_形三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_任意_任意_0")]),

        Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
        Factor(name="30分钟_形三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_任意_任意_0")]),

        Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
        Factor(name="15分钟_形三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_任意_任意_0")]),

        Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
        Factor(name="5分钟_形三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_任意_任意_0")]),

        Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
        Factor(name="60分钟_形三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_任意_任意_0")]),
    ]),

    # 平多
    Event(name="一卖", operate=Operate.LE, factors=[
        Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_任意_任意_0")]),
        Factor(name="日线_形一卖", signals_all=[Signal("日线_倒1笔_基础形态_类一卖_任意_任意_0")]),

        Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
        Factor(name="30分钟_形一卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),

        Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
        Factor(name="15分钟_形一卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),

        Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
        Factor(name="5分钟_形一卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),

        Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
        Factor(name="60分钟_形一卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),
    ]),
    Event(name="二卖", operate=Operate.LE, factors=[
        Factor(name="日线_类二卖", signals_all=[Signal("日线_倒1笔_类买卖点_类二卖_任意_任意_0")]),
        Factor(name="日线_形二卖", signals_all=[Signal("日线_倒1笔_基础形态_类二卖_任意_任意_0")]),
        Factor(name="30分钟_类二卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
        Factor(name="30分钟_形二卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
        Factor(name="15分钟_类二卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
        Factor(name="15分钟_形二卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
        Factor(name="5分钟_类二卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
        Factor(name="5分钟_形二卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
        Factor(name="60分钟_类二卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
        Factor(name="60分钟_形二卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
    ]),
    Event(name="三卖", operate=Operate.LE, factors=[
        Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_任意_任意_0")]),
        Factor(name="日线_形三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_任意_任意_0")]),
        Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
        Factor(name="30分钟_形三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
        Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
        Factor(name="15分钟_形三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
        Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
        Factor(name="5分钟_形三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
        Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
        Factor(name="60分钟_形三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
    ]),
]

def monitor(use_cache=True):
    # dingmessage("自选股因子监控启动 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    moni_path = os.path.join(ct_path, "monitor")
    # 首先清空历史快照
    if os.path.exists(moni_path):
        shutil.rmtree(moni_path)
    os.makedirs(moni_path, exist_ok=True)

    # print(len(symbols))
    k = 1
    for s in allcodes:
        print(k)
        k += 1
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct) and use_cache:
                ct: CzscAdvancedTrader = read_pkl(file_ct)
                updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="日线", freqs=['日线', '周线', '月线'])
                ct = CzscAdvancedTrader(kg, get_default_signals)
            save_pkl(ct, file_ct)
            # continue
            # 每次执行，会在moni_path下面保存一份快照
            file_html = os.path.join(moni_path, f"{ct.symbol}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
            ct.take_snapshot(file_html, width="2000px", height="900px")

            # msg = f"标的代码：{s}\n同花顺F10：http://basic.10jqka.com.cn/{s.split('.')[0]}\n"
            msg = f"标的代码：{s}\n"
            msg += f"标的名称：{stockDf.loc[stockDf['ts_code'] == s]['name'].values[0]}\n"
            for event in events_monitor:
                m, f = event.is_match(ct.s)
                if m:
                    daoZeroKey = "{}_倒0笔_长度".format(f.split("_")[0])
                    msg += "监控提醒：{}@{} [{}]\n".format(event.name, f, ct.s[daoZeroKey])
            print(msg)
            # if "监控提醒" in msg:
            #     dingmessage(msg.strip("\n"))

        except Exception as e:
            traceback.print_exc()
            print("{} 执行失败 - {}".format(s, e))

    # dingmessage("自选股因子监控结束 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))


def compare_time(startTime,endTime):
    d_start = datetime.strptime(str(startTime), '%Y-%m-%d %H:%M:%S')
    d_end = datetime.strptime(str(endTime), '%Y-%m-%d %H:%M:%S')

    result = d_start < d_end

    return result

    # for oneDay in allTradingDates:
    #     stock_zt_pool_em_df = ak.stock_zt_pool_em(date=oneDay)
    #     pro.limit_list(trade_date='oneDay')
    #     for index, row in stock_zt_pool_em_df.iterrows():
    #         matchedCB = allCBs.loc[allCBs['stk_short_name'] == row['名称']]
    #         if matchedCB.empty == False:
    #             lastFeng = row['最后封板时间']
    #             if (int)(lastFeng) < 93000:
    #                 # if (int)(lastFeng) < 100000:
    #                 print(str(oneDay) + ' ' + row['名称'] + ' ' + matchedCB['ts_code'])
    #                 print('----------')

if __name__ == '__main__':
    # get_ths_members()
    conceptsDic = read_pkl(os.path.join(ct_path, "members"))
    concepts = pro.ths_index(exchange="A")
    for index, row in concepts.iterrows():
        thisTypeConcept = {}
        if row['type'] in conceptsDic.keys():
            thisTypeConcept = conceptsDic[row['type']]
        thisTypeConcept[row['ts_code']] = {"name" : row['name'], "count" : row['count'], 'list_date' : row['list_date']}
        time.sleep(0.3)
        thisTypeConceptDetailStock = {}
        detailDF = pro.ths_member(ts_code=row['ts_code'],
                            fields="ts_code,code,name,weight,in_date,out_date,is_new")
        for index2, row2 in detailDF.iterrows():
            #判断是不是中国的股票
            if row2['code'].endswith('.SH') or row2['code'].endswith('.SH'):
                thisTypeConceptDetailStock[row2['code']] = row2['name']
        if len(thisTypeConceptDetailStock.keys()) > 0:
            thisTypeConcept[row['ts_code']]['stocks'] = thisTypeConceptDetailStock
            conceptsDic[row['type']] = thisTypeConcept
    save_pkl(conceptsDic, os.path.join(ct_path, "members"))
    # df = pro.trade_cal(exchange='', start_date='20210215')
    # allTradingDates = df.loc[df['is_open'] == 1]['cal_date'].values.tolist()
    # moni_path = os.path.join(ct_path, "monitor")
    #
    # for oneDay in allTradingDates:
    #     stock_zt_pool_em_df = pro.limit_list(trade_date=oneDay)
    #     for index, row in stock_zt_pool_em_df.iterrows():
    #         matchedCB = allCBs.loc[allCBs['stk_short_name'] == row['name']]
    #         if matchedCB.empty == False:
    #             strong = row['strth']
    #             if strong > 99:
    #             # if (int)(lastFeng) < 100000:
    #                 print(str(oneDay) + ' ' + row['name'] + ' ' + matchedCB['ts_code'])
    #                 print('----------')


        # allCBDaily = get_all_cbDaily(start_date=oneDay, end_date=oneDay)
        # print(str(oneDay))
        # for index, row in allCBDaily.iterrows():
        #     thisCBInfo = allCBs.loc[allCBs['ts_code']==row['ts_code']]
        #
        #     # bg = BarGenerator("日线", ['日线', '周线', '月线'], 1000)
        #     df2 = row.to_frame().T
        #     bars = format_kline(df2, Freq.D)
        #     bgd = BarGenerator("日线", ['周线', '月线'])
        #     for b in bars:
        #         bgd.update(b)
        #
        #     file_ct = os.path.join(ct_path, "{}.ct".format(row['ts_code']))
        #     if os.path.exists(file_ct):
        #         ct: CzscCBTrader = read_pkl(file_ct)
        #         if compare_time(ct.end_dt, bgd.end_dt):
        #             ct.update(b)
        #             print(f"{thisCBInfo['bond_short_name']}: 更新 bar generator 至 {ct.end_dt.strftime(dt_fmt)}")
        #         else:
        #             print(f"{ct.end_dt.strftime(dt_fmt)}过")
        #         # file_html = os.path.join(moni_path, f"{ct.symbol}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
        #         # ct.take_snapshot(file_html, width="2000px", height="900px")
        #     else:
        #         ct = CzscCBTrader(bgd, get_default_signals, chineseName=thisCBInfo['bond_short_name'], stock=thisCBInfo['stk_code'])
        #         print(f"{thisCBInfo['bond_short_name']}: 新建 bar generator {ct.end_dt.strftime(dt_fmt)}")
        #     save_pkl(ct, file_ct)