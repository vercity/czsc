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
from czsc.traders import CzscAdvancedTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.utils.qywx import push_text, push_file
from czsc.utils.io import read_pkl, save_pkl
from czsc.signals import signals
import requests
import json
import pandas as pd
from czsc.data.jq import get_concepts, get_concept_stocks, get_kline, freq_convert, freq_map_new, get_all_securities
from czsc.utils.bar_generator import BarGenerator
from czsc.traders import CzscAdvancedTrader
from czsc.signals.signals import get_default_signals
from czsc.enum import Freq

dt_fmt = "%Y-%m-%d %H:%M:%S"
date_fmt = "%Y%m%d"

# =======================================================================================================
# 基础参数配置
ct_path = "/Volumes/OuGuMore/Stock/realtimeData"
os.makedirs(ct_path, exist_ok=True)

# 关于企业微信群聊机器人的使用文档，参考：https://work.weixin.qq.com/api/doc/90000/90136/91770
# 企业微信群聊机器人的key
qywx_key = "4ad2e226-2519-4893-8670-*****"

# 定义需要监控的股票列表
symbols = ["002340.XSHE", "002062.XSHE", "002116.XSHE", '603316.XSHG', "000856.XSHE",
           # "159915.XSHE",
           ]

from jqdatasdk import *
# auth("18621819557", "8Ee*81120")
auth("18916752674", "8Ee*81120")
# symbols = get_index_stocks('000300.XSHG')

# all_securities_pd = get_all_securities()
# all_securities_pd.to_csv('/Volumes/OuGuMore/Stock/allSecurity')
all_securities_pd = pd.read_csv('/Volumes/OuGuMore/Stock/allSecurity', index_col=0)

def allSecurity():
    today = pd.Timestamp.today().strftime("%Y-%m-%d")
    # all_securities_pd = get_all_securities()
    # 过滤掉退市股
    filtered_securities_pd = all_securities_pd[all_securities_pd.end_date > pd.Timestamp.today()]
    # 过滤掉最近 150 天上市的新股
    last_150_days = pd.Timestamp.today() - timedelta(150)
    filtered_securities_pd = filtered_securities_pd[filtered_securities_pd.start_date < last_150_days]

    # 过滤掉 st 股
    security_is_st_pd = get_extras('is_st', filtered_securities_pd.index.tolist(), end_date=today, count=1).T
    security_is_st_pd.columns = ['is_st']
    filtered_securities_pd = filtered_securities_pd.join(security_is_st_pd)
    filtered_securities_pd = filtered_securities_pd[filtered_securities_pd.is_st == False]

    security_code_list = filtered_securities_pd.index.tolist()
    # security_code_list.reverse()
    return security_code_list

def monitor(use_cache=True):
    print("聚宽剩余调用次数：{}".format(get_query_count()))
    dingmessage("自选股因子监控启动 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    moni_path = os.path.join(ct_path, "monitor")
    # 首先清空历史快照
    if os.path.exists(moni_path):
        shutil.rmtree(moni_path)
    os.makedirs(moni_path, exist_ok=True)
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
    # print(len(symbols))
    k = 1
    for s in symbols:
        print(k)
        k += 1
        print(s)
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct) and use_cache:
                ct: CzscAdvancedTrader = read_pkl(file_ct)
                updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
                                 freqs=['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线'])
                ct = CzscAdvancedTrader(kg, get_default_signals)
            save_pkl(ct, file_ct)
            # continue
            # 每次执行，会在moni_path下面保存一份快照
            file_html = os.path.join(moni_path, f"{ct.symbol}_{all_securities_pd.loc[s]['display_name']}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
            ct.take_snapshot(file_html, width="2000px", height="900px")

            # msg = f"标的代码：{s}\n同花顺F10：http://basic.10jqka.com.cn/{s.split('.')[0]}\n"
            msg = f"标的代码：{s}\n"
            msg += f"标的名称：{all_securities_pd.loc[s]['display_name']}\n"
            for event in events_monitor:
                m, f = event.is_match(ct.s)
                if m:
                    daoZeroKey = "{}_倒0笔_长度".format(f.split("_")[0])
                    msg += "监控提醒：{}@{} [{}]\n".format(event.name, f, ct.s[daoZeroKey])
            print(msg)
            if "监控提醒" in msg:
                dingmessage(msg.strip("\n"))

        except Exception as e:
            traceback.print_exc()
            print("{} 执行失败 - {}".format(s, e))

    dingmessage("自选股因子监控结束 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))



def run_monitor():
    mdt = ["09:30", "09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", "11:30", "13:00", "13:15", "13:30",
           "13:45", "14:00", "14:15", "14:30", "14:45", "15:00"]
    monitor()
    while 1:
        print(datetime.now().strftime("%H:%M"))
        if datetime.now().strftime("%H:%M") in mdt:
            monitor()
        time.sleep(60)


def dingmessage(dingMessage):
    # 请求的URL，WebHook地址
    webhook = "https://oapi.dingtalk.com/robot/send?access_token" \
              "=bf6bd4ce69ef8c69dd394331dff77bd351b30070728f98f9130ad92caa5aa287 "
    # 构建请求头部
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    # 构建请求数据
    tex = "【有点东西】: {}".format(dingMessage)
    # print(tex)
    message = {

        "msgtype": "text",
        "text": {
            "content": tex
        },
        # "at": {
        #     "isAtAll": True
        # }
    }
    # 对请求的数据进行json封装
    message_json = json.dumps(message)
    # 发送请求
    info = requests.post(url=webhook, data=message_json, headers=header)
    # 打印返回的结果
    # print(info.text)

def get_init_bg(symbol: str,
                end_dt: [str, datetime],
                base_freq: str,
                freqs=('1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线'),
                max_count=5000,
                adjust='qfq'):
    """获取 symbol 的初始化 bar generator"""
    # if isinstance(end_dt, str):
    #     end_dt = pd.to_datetime(end_dt, utc=True)
    #     end_dt = end_dt.tz_convert('dateutil/PRC')
    #     # 时区转换之后，要减去8个小时才是设置的时间
    #     end_dt = end_dt - timedelta(hours=8)
    # else:
    #     assert end_dt.tzinfo._filename == 'PRC'
    last_day = (end_dt - timedelta(days=1)).replace(hour=16, minute=0)

    bg = BarGenerator(base_freq, freqs, max_count)
    if "周线" in freqs or "月线" in freqs:
        d_bars = get_kline(symbol=symbol, start_date=last_day - timedelta(days=2500), end_date=last_day,
                           freq='D')
        bgd = BarGenerator("日线", ['周线', '月线'])
        for b in d_bars:
            bgd.update(b)
    else:
        bgd = None

    for freq in bg.bars.keys():
        if freq in ['周线', '月线', '季线', '年线']:
            bars_ = bgd.bars[freq]
        else:
            if freq == Freq.F1.value:
                start_dt = end_dt - timedelta(days=21)
                fq = None
            elif freq == Freq.F5.value:
                start_dt = end_dt - timedelta(days=21 * 5)
                fq = None
            elif freq == Freq.F15.value:
                start_dt = end_dt - timedelta(days=21 * 15)
                fq = None
            elif freq == Freq.F30.value:
                start_dt = end_dt - timedelta(days=500)
                fq = None
            elif freq == Freq.F60.value:
                start_dt = end_dt - timedelta(days=1000)
                fq = None
            elif freq == Freq.D.value:
                start_dt = end_dt - timedelta(days=1500)
                fq = "qfq"
            else:
                raise ValueError(freq.value)

            bars_ = get_kline(symbol=symbol, start_date=start_dt, end_date=last_day, freq=freq_map_new[freq])
        bg.bars[freq] = bars_
        print(f"{symbol} - {freq} - {len(bg.bars[freq])} - last_dt: {bg.bars[freq][-1].dt} - last_day: {last_day}")

    bars2 = get_kline(symbol=symbol, start_date=last_day, end_date=end_dt, freq='1min')
    data = [x for x in bars2 if x.dt > last_day]

    if data:
        print(f"{symbol}: 更新 bar generator 至 {end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            bg.update(row)
    return bg

def updateKline(trader: CzscAdvancedTrader):
    bars = get_kline(symbol=trader.symbol, start_date=trader.end_dt, end_date=datetime.now(), freq='1min')
    data = [x for x in bars if x.dt > trader.end_dt]

    if data:
        print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            trader.update(row)

if __name__ == '__main__':
    # symbols = allSecurity()
    # type: 类型: stock(股票)，index(指数)，etf(
    #     ETF基金)，fja（分级A），fjb（分级B），fjm（分级母基金），mmf（场内交易的货币基金）open_fund（开放式基金）, bond_fund（债券基金）, stock_fund（股票型基金）, QDII_fund（QDII
    # 基金）, money_market_fund（场外交易的货币基金）, mixture_fund（混合型基金）, options（期权）
    # ss = get_all_securities(['etf'])
    run_monitor()

    # jqconcepts = get_concepts()
    #
    # for oneCode in jqconcepts.index:
    #     print(jqconcepts.loc[oneCode]['name'])
    #     print(get_concept_stocks(oneCode))
