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
from czsc.data.ts import freq_cn_map, dt_fmt, get_all_stocks
# from czsc.data.jq import JqCzscTrader as CzscTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.utils.qywx import push_text, push_file
from czsc.utils.io import read_pkl, save_pkl
import requests
import json
from czsc.data.ts import get_kline
import pandas as pd
from czsc.enum import Freq
from czsc.utils.bar_generator import BarGenerator
from czsc.traders import CzscAdvancedTrader
from czsc.traders import create_advanced_trader
from czsc.strategies import trader_strategy_custom
import dill
from czsc.utils.dingding import dingmessage
import numpy as np

# =======================================================================================================
# 基础参数配置
# ct_path = "/Volumes/OuGuMore/Stock/data"
ct_path = "/Users/guyeqi/Documents/Python/data/realtime/data"
os.makedirs(ct_path, exist_ok=True)
# allName = os.listdir("/Volumes/OuGuMore/Stock/data/")
# for oneName in allName:
#     try:
#         os.rename("/Volumes/OuGuMore/Stock/data/"+oneName, "/Volumes/OuGuMore/Stock/data/"+oneName.split('.')[0]+'.ct')
#     except:
#         print()
allStocks = get_all_stocks()
stockDf = pd.DataFrame(allStocks, columns=['ts_code', 'name'])

allcodes = stockDf['ts_code'].values.tolist()
# allStocksAfter = []
# for oneCode in allcodes:
#     allStocksAfter.append()
# print(stockDf)

events_monitor = [
    # # 五笔aAb式
    # Event(name="五笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    # ]),
    #
    # Event(name="五笔aAb式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_五笔aAb式_任意_0")]),
    # ]),
    #
    # # 五笔类趋势
    # Event(name="五笔类趋势买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="15分钟_类趋势买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="5分钟_类趋势买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="60分钟_类趋势买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #
    # ]),
    #
    # Event(name="五笔类趋势卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    #     Factor(name="15分钟_类趋势卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    #     Factor(name="5分钟_类趋势卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    #     Factor(name="60分钟_类趋势卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_五笔类趋势_任意_0")]),
    # ]),
    #
    # # 五笔三买
    # Event(name="五笔三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="15分钟_三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="5分钟_三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="60分钟_三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    # ]),
    #
    # Event(name="五笔三卖", operate=Operate.LO, factors=[
    #     Factor(name="30分钟_三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    #     Factor(name="日线_三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    #     Factor(name="15分钟_三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    #     Factor(name="5分钟_三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    #     Factor(name="60分钟_三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_五笔_任意_0")]),
    # ]),
    #
    # # 七笔aAbcd式
    # Event(name="七笔aAbcd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="15分钟_aAbcd式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="5分钟_aAbcd式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="60分钟_aAbcd式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    # ]),
    #
    # Event(name="七笔aAbcd式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="30分钟_aAbcd式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="15分钟_aAbcd式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="5分钟_aAbcd式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="60分钟_aAbcd式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔aAbcd式_任意_0")]),
    # ]),
    #
    # # 七笔abcAd式
    # Event(name="七笔abcAd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_abcAd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="30分钟_abcAd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="15分钟_abcAd式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="5分钟_abcAd式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="60分钟_abcAd式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    # ]),
    #
    # Event(name="七笔abcAd式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_abcAd式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="30分钟_abcAd式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="15分钟_abcAd式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="5分钟_abcAd式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="60分钟_abcAd式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔abcAd式_任意_0")]),
    # ]),
    #
    # # 七笔aAb式
    # Event(name="七笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    # ]),
    #
    # Event(name="七笔aAb式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔aAb式_任意_0")]),
    # ]),
    #
    # # 七笔三买
    # Event(name="七笔三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="15分钟_三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="5分钟_三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="60分钟_三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    # ]),
    #
    # Event(name="七笔三卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    #     Factor(name="30分钟_三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    #     Factor(name="15分钟_三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    #     Factor(name="5分钟_三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    #     Factor(name="60分钟_三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_七笔_任意_0")]),
    # ]),
    #
    # # 七笔类趋势
    # Event(name="七笔类趋势买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="15分钟_类趋势买", signals_all=[Signal("15分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="5分钟_类趋势买", signals_all=[Signal("5分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="60分钟_类趋势买", signals_all=[Signal("60分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    # ]),
    #
    # Event(name="七笔类趋势卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势卖", signals_all=[Signal("日线_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势卖", signals_all=[Signal("30分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    #     Factor(name="15分钟_类趋势卖", signals_all=[Signal("15分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    #     Factor(name="5分钟_类趋势卖", signals_all=[Signal("5分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    #     Factor(name="60分钟_类趋势卖", signals_all=[Signal("60分钟_倒1笔_基础形态_顶背驰_七笔类趋势_任意_0")]),
    # ]),
    #
    # # 九笔aAb式
    # Event(name="九笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    # ]),
    #
    # Event(name="九笔aAb式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    #     Factor(name="15分钟_aAb式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    #     Factor(name="5分钟_aAb式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    #     Factor(name="60分钟_aAb式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAb式_任意_0")]),
    # ]),
    #
    # # 九笔aAbcd式
    # Event(name="九笔aAbcd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="15分钟_aAbcd式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="5分钟_aAbcd式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="60分钟_aAbcd式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # Event(name="九笔aAbcd式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    #     Factor(name="30分钟_aAbcd式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    #     Factor(name="15分钟_aAbcd式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    #     Factor(name="5分钟_aAbcd式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    #     Factor(name="60分钟_aAbcd式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAbcd式_任意_0")]),
    # ]),
    #
    # # 九笔ABC式
    # Event(name="九笔ABC式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_ABC式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_ABC式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="15分钟_ABC式买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="5分钟_ABC式买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="60分钟_ABC式买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # Event(name="九笔ABC式卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_ABC式卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    #     Factor(name="30分钟_ABC式卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    #     Factor(name="15分钟_ABC式卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    #     Factor(name="5分钟_ABC式卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    #     Factor(name="60分钟_ABC式卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔ABC式_任意_0")]),
    # ]),
    #
    # # 九笔类一买 （2~4构成中枢A，6~8构成中枢B，9背驰）
    Event(name="九笔aAbBc式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
                                           Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    ]),
    #
    # Event(name="九笔aAbBc式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_九笔aAbBc式_任意_0")]),
    # ]),
    #
    # # 九笔类三买 （1357构成中枢，最低点在3或5）（357构成中枢，8的力度小于2，9回调不跌破GG构成三买）
    # Event(name="九笔GG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # # 九笔类三买 前五笔构成向下类趋势 567构成中枢，且8的高点大于GG
    # Event(name="九笔ZG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    # ]),
    #
    # # 九笔类二买
    # Event(name="九笔二买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类二买", signals_all=[Signal("日线_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="30分钟_类二买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="15分钟_类二买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="5分钟_类二买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="60分钟_类二买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    # ]),
    #
    # Event(name="九笔类二卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类二卖", signals_all=[Signal("日线_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    #     Factor(name="30分钟_类二卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    #     Factor(name="15分钟_类二卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    #     Factor(name="5分钟_类二卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    #     Factor(name="60分钟_类二卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二卖_九笔_任意_0")]),
    # ]),
    #
    # # 九笔类三卖
    # Event(name="九笔类三卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    #     Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    #     Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    #     Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    #     Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_九笔_任意_0")]),
    # ]),
    #
    # # 九笔类三卖 前五笔构成向下类趋势 567构成中枢，且8的高点大于GG
    # Event(name="九笔ZD三卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    #     Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    #     Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    #     Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    #     Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_九笔ZD三卖_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A5B3C3式
    # Event(name="11笔A5B3C3式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    # ]),
    #
    # Event(name="11笔A5B3C3式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A5B3C3式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A3B3C5式
    # Event(name="11笔A3B3C5式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    # ]),
    #
    # Event(name="11笔A3B3C5式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A3B3C5式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A3B5C3式
    # Event(name="11笔A3B5C3式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    # ]),
    #
    # Event(name="11笔A3B5C3式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_11笔A3B5C3式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔a1Ab式
    # Event(name="11笔a1Ab式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    # ]),
    #
    # # 11笔类三买 （1~9构成大级别中枢，10离开，11回调不跌破GG）
    # Event(name="11笔GG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_类三买",
    #            signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                         Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="15分钟_类三买",
    #            signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                         Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                         Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="60分钟_类三买",
    #            signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                         Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A5B3C5
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一卖，A5B3C5
    # Event(name="13笔ABC式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_13笔A5B3C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A3B5C5
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一卖，A3B5C5
    # Event(name="13笔ABC式类一卖", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_13笔A3B5C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A5B5C3
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一卖，A5B5C3
    # Event(name="小三买", operate=Operate.LO, factors=[
    #     Factor(name="30分钟_小三买",signals_all=[
    #             Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0"),
    #         ],
    #            signals_any=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("30分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #                         Signal("30分钟_倒1笔_类买卖点_类三买_13笔GG三买_任意_0")]),
    #     Factor(name="15分钟_小三买",signals_all=[
    #             Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0"),
    #         ],
    #            signals_any=[Signal("15分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("15分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #                         Signal("15分钟_倒1笔_类买卖点_类三买_13笔GG三买_任意_0")]),
    #     Factor(name="5分钟_小三买",signals_all=[
    #             Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0"),
    #         ],
    #            signals_any=[Signal("5分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("5分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #                         Signal("5分钟_倒1笔_类买卖点_类三买_13笔GG三买_任意_0")]),
    #     Factor(name="60分钟_小三买",signals_all=[
    #             Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0"),
    #         ],
    #            signals_any=[Signal("60分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("60分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #                         Signal("60分钟_倒1笔_类买卖点_类三买_13笔GG三买_任意_0")]),
    # ]),
    #
    # # 潜在三买
    # Event(name="潜在三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_潜在三买", signals_all=[Signal("日线_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_近7K突破中枢GG_0")]),
    #     Factor(name="30分钟_潜在三买", signals_all=[Signal("30分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="15分钟_潜在三买", signals_all=[Signal("15分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="5分钟_潜在三买", signals_all=[Signal("5分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="60分钟_潜在三买", signals_all=[Signal("60分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    # ]),

    Event(name="GG三买", operate=Operate.LO, factors=[
            Factor(name="日线_类三买", signals_all=[
                Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
            ], signals_any=[
                Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
                Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
                Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
            ]),
        ]),

    # Event(name="底分型停顿", operate=Operate.LO, factors=[
    #     Factor(name="日线_底分型停顿", signals_all=[Signal("日线_倒1K_四K形态_底分型_强势停顿_任意_0")], signals_any=[Signal("日线_倒0笔_长度_2根K线_任意_任意_0"), Signal("日线_倒0笔_长度_1根K线_任意_任意_0"), Signal("日线_倒0笔_长度_4根K线_任意_任意_0"), Signal("日线_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="30分钟_底分型停顿", signals_all=[Signal("30分钟_倒1K_四K形态_底分型_强势停顿_任意_0")], signals_any=[Signal("30分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="15分钟_底分型停顿", signals_all=[Signal("15分钟_倒1K_四K形态_底分型_强势停顿_任意_0")], signals_any=[Signal("15分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="5分钟_底分型停顿", signals_all=[Signal("5分钟_倒1K_四K形态_底分型_强势停顿_任意_0")], signals_any=[Signal("5分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="60分钟_底分型停顿", signals_all=[Signal("60分钟_倒1K_四K形态_底分型_强势停顿_任意_0")], signals_any=[Signal("60分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    # ]),

    # Event(name="底分型停顿", operate=Operate.LO, factors=[
    #     Factor(name="日线_底分型停顿", signals_all=[Signal("日线_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    #     Factor(name="30分钟_底分型停顿", signals_all=[Signal("30分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    #     Factor(name="15分钟_底分型停顿", signals_all=[Signal("15分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    #     Factor(name="5分钟_底分型停顿", signals_all=[Signal("5分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    #     Factor(name="60分钟_底分型停顿", signals_all=[Signal("60分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    # ]),

    # Event(name="底分型强势", operate=Operate.LO, factors=[
    #     Factor(name="日线_底分型强势", signals_all=[Signal("日线_倒1K_三K形态_底分型_强势_任意_0")], signals_any=[Signal("日线_倒0笔_长度_2根K线_任意_任意_0"), Signal("日线_倒0笔_长度_1根K线_任意_任意_0"), Signal("日线_倒0笔_长度_4根K线_任意_任意_0"), Signal("日线_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="30分钟_底分型强势", signals_all=[Signal("30分钟_倒1K_三K形态_底分型_强势_任意_0")], signals_any=[Signal("30分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("30分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="15分钟_底分型强势", signals_all=[Signal("15分钟_倒1K_三K形态_底分型_强势_任意_0")], signals_any=[Signal("15分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("15分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="5分钟_底分型强势", signals_all=[Signal("5分钟_倒1K_三K形态_底分型_强势_任意_0")], signals_any=[Signal("5分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("5分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    #     Factor(name="60分钟_底分型强势", signals_all=[Signal("60分钟_倒1K_三K形态_底分型_强势_任意_0")], signals_any=[Signal("60分钟_倒0笔_长度_2根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_1根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_4根K线_任意_任意_0"), Signal("60分钟_倒0笔_长度_3根K线_任意_任意_0")]),
    # ]),

    # Event(name="底分型强势", operate=Operate.LO, factors=[
    #     Factor(name="日线_底分型强势", signals_all=[Signal("日线_倒1K_三K形态_底分型_强势_任意_0")],),
    #     Factor(name="30分钟_底分型强势", signals_all=[Signal("30分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="15分钟_底分型强势", signals_all=[Signal("15分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="5分钟_底分型强势", signals_all=[Signal("5分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="60分钟_底分型强势", signals_all=[Signal("60分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    # ]),

    # Event(name="三买回踩", operate=Operate.LO, factors=[
    #     Factor(name="日线_60分钟_三买回踩", signals_all=[Signal("日线_60分钟_三买回踩10_确认_任意_任意_0")]),
    # ]),
    #
    # Event(name="中枢共振", operate=Operate.LO, factors=[
    #     Factor(name="日线_60分钟_中枢共振", signals_all=[Signal("日线_60分钟_中枢共振_看多_任意_任意_0")]),
    # ]),

    Event(name="vg三买", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买", signals_all=[Signal("日线_60分钟_vg三买_确认_任意_任意_0")]),
    ]),

    Event(name="vg三买确认", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买确认", signals_all=[Signal("日线_60分钟_vg三买确认_确认_任意_任意_0")]),
    ]),

    Event(name="vg一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg一买", signals_all=[Signal("日线_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="30分钟_vg一买", signals_all=[Signal("30分钟_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="60分钟_vg一买", signals_all=[Signal("60分钟_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="周线_vg一买", signals_all=[Signal("周线_vg一买_任意_确认_任意_任意_0")]),
    ]),

    Event(name="vg潜在一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg潜在一买", signals_all=[Signal("日线_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="30分钟_vg潜在一买", signals_all=[Signal("30分钟_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="60分钟_vg潜在一买", signals_all=[Signal("60分钟_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="周线_vg潜在一买", signals_all=[Signal("周线_vg潜在一买_任意_确认_任意_任意_0")]),
    ]),

    # # 开多
    # Event(name="一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_任意_任意_0")]),
    #     Factor(name="日线_形一买", signals_all=[Signal("日线_倒1笔_基础形态_类一买_任意_任意_0")]),
    #
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
    #     Factor(name="30分钟_形一买", signals_all=[Signal("30分钟_倒1笔_基础形态_类一买_任意_任意_0")]),
    #
    #     Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
    #     Factor(name="15分钟_形一买", signals_all=[Signal("15分钟_倒1笔_基础形态_类一买_任意_任意_0")]),
    #
    #     Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
    #     Factor(name="5分钟_形一买", signals_all=[Signal("5分钟_倒1笔_基础形态_类一买_任意_任意_0")]),
    #
    #     Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_任意_任意_0")]),
    #     Factor(name="60分钟_形一买", signals_all=[Signal("60分钟_倒1笔_基础形态_类一买_任意_任意_0")]),
    # ]),
    #
    # Event(name="二买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类二买", signals_all=[Signal("日线_倒1笔_类买卖点_类二买_任意_任意_0")]),
    #     Factor(name="日线_形二买", signals_all=[Signal("日线_倒1笔_基础形态_类二买_任意_任意_0")]),
    #
    #     Factor(name="30分钟_类二买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
    #     Factor(name="30分钟_形二买", signals_all=[Signal("30分钟_倒1笔_基础形态_类二买_任意_任意_0")]),
    #
    #     Factor(name="15分钟_类二买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
    #     Factor(name="15分钟_形二买", signals_all=[Signal("15分钟_倒1笔_基础形态_类二买_任意_任意_0")]),
    #
    #     Factor(name="5分钟_类二买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
    #     Factor(name="5分钟_形二买", signals_all=[Signal("5分钟_倒1笔_基础形态_类二买_任意_任意_0")]),
    #
    #     Factor(name="60分钟_类二买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二买_任意_任意_0")]),
    #     Factor(name="60分钟_形二买", signals_all=[Signal("60分钟_倒1笔_基础形态_类二买_任意_任意_0")]),
    # ]),
    # Event(name="三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_任意_任意_0")]),
    #     Factor(name="日线_形三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_任意_任意_0")]),
    #
    #     Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
    #     Factor(name="30分钟_形三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_任意_任意_0")]),
    #
    #     Factor(name="15分钟_类三买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
    #     Factor(name="15分钟_形三买", signals_all=[Signal("15分钟_倒1笔_基础形态_类三买_任意_任意_0")]),
    #
    #     Factor(name="5分钟_类三买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
    #     Factor(name="5分钟_形三买", signals_all=[Signal("5分钟_倒1笔_基础形态_类三买_任意_任意_0")]),
    #
    #     Factor(name="60分钟_类三买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三买_任意_任意_0")]),
    #     Factor(name="60分钟_形三买", signals_all=[Signal("60分钟_倒1笔_基础形态_类三买_任意_任意_0")]),
    # ]),
    #
    # # 平多
    # Event(name="一卖", operate=Operate.LE, factors=[
    #     Factor(name="日线_类一卖", signals_all=[Signal("日线_倒1笔_类买卖点_类一卖_任意_任意_0")]),
    #     Factor(name="日线_形一卖", signals_all=[Signal("日线_倒1笔_基础形态_类一卖_任意_任意_0")]),
    #
    #     Factor(name="30分钟_类一卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
    #     Factor(name="30分钟_形一卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),
    #
    #     Factor(name="15分钟_类一卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
    #     Factor(name="15分钟_形一卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),
    #
    #     Factor(name="5分钟_类一卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
    #     Factor(name="5分钟_形一卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),
    #
    #     Factor(name="60分钟_类一卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一卖_任意_任意_0")]),
    #     Factor(name="60分钟_形一卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类一卖_任意_任意_0")]),
    # ]),
    # Event(name="二卖", operate=Operate.LE, factors=[
    #     Factor(name="日线_类二卖", signals_all=[Signal("日线_倒1笔_类买卖点_类二卖_任意_任意_0")]),
    #     Factor(name="日线_形二卖", signals_all=[Signal("日线_倒1笔_基础形态_类二卖_任意_任意_0")]),
    #     Factor(name="30分钟_类二卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
    #     Factor(name="30分钟_形二卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
    #     Factor(name="15分钟_类二卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
    #     Factor(name="15分钟_形二卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
    #     Factor(name="5分钟_类二卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
    #     Factor(name="5分钟_形二卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
    #     Factor(name="60分钟_类二卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类二卖_任意_任意_0")]),
    #     Factor(name="60分钟_形二卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类二卖_任意_任意_0")]),
    # ]),
    # Event(name="三卖", operate=Operate.LE, factors=[
    #     Factor(name="日线_类三卖", signals_all=[Signal("日线_倒1笔_类买卖点_类三卖_任意_任意_0")]),
    #     Factor(name="日线_形三卖", signals_all=[Signal("日线_倒1笔_基础形态_类三卖_任意_任意_0")]),
    #     Factor(name="30分钟_类三卖", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
    #     Factor(name="30分钟_形三卖", signals_all=[Signal("30分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
    #     Factor(name="15分钟_类三卖", signals_all=[Signal("15分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
    #     Factor(name="15分钟_形三卖", signals_all=[Signal("15分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
    #     Factor(name="5分钟_类三卖", signals_all=[Signal("5分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
    #     Factor(name="5分钟_形三卖", signals_all=[Signal("5分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
    #     Factor(name="60分钟_类三卖", signals_all=[Signal("60分钟_倒1笔_类买卖点_类三卖_任意_任意_0")]),
    #     Factor(name="60分钟_形三卖", signals_all=[Signal("60分钟_倒1笔_基础形态_类三卖_任意_任意_0")]),
    # ]),
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
    try:
        threeBuyResult = pd.read_csv('/Users/guyeqi/Documents/Python/data/backtest/data/vg三买，day-60min20150101/finalResult.csv')
        # df.set_index('姓名', inplace=True)
        print()
    except Exception as e:
        print(e)
    for s in allcodes:
        print(k)
        if s.endswith('BJ'):
            continue
        k += 1
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct) and use_cache:
                ct: CzscAdvancedTrader = dill.load(open(file_ct, 'rb'))
                # hasChange = updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
                                 freqs=['30分钟', '60分钟', '日线', '周线'])
                ct = create_advanced_trader(bg=kg, raw_bars=[], strategy=trader_strategy_custom)
                hasChange = True
            # if hasChange:
            #     dill.dump(ct, open(file_ct, 'wb'))
            # continue
            # 每次执行，会在moni_path下面保存一份快照
            # file_html = os.path.join(moni_path, f"{ct.symbol}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
            # ct.take_snapshot(file_html, width="2000px", height="900px")

            # msg = f"标的代码：{s}\n同花顺F10：http://basic.10jqka.com.cn/{s.split('.')[0]}\n"
            msg = f"标的代码：{s}\n"
            msg += f"标的名称：{stockDf.loc[stockDf['ts_code'] == s]['name'].values[0]}\n"
            for event in events_monitor:
                m, f = event.is_match(ct.s)
                if m:
                    daoZeroKey = "{}_倒0笔_长度".format(f.split("_")[0])
                    if f in ct.s.keys():
                        msg += "监控提醒：{}@{} [{}], {}\n".format(event.name, f, ct.s[daoZeroKey], ct.s[f])
                    else:
                        msg += "监控提醒：{}@{} [{}]\n".format(event.name, f, ct.s[daoZeroKey])

                    if "3根K线" in ct.s[daoZeroKey]:
                        if f == "日线_vg一买":
                            confirm, zhongshu, bipower,score = ct.s[f].split("_")
                            bi1power, bi2power = bipower.split("-")
                            if float(bi1power) > float(bi2power):
                                dingmessage("【抄底】\n" + msg.strip("\n"))
                        elif f == "日线_60分钟_vg三买":
                            confirm, huitiao, dao0length, zhendanglength, dao1power = ct.s[f].split("_")
                            tmpThreeBuyResult = threeBuyResult.copy(deep=True)
                            tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['最后一笔天数'] == int(dao0length)]
                            if float(dao1power) < 1:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.05)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.05)]
                            elif float(dao1power) > 1 and float(dao1power) < 1.5:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.1)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.1)]
                            elif float(dao1power) > 1.5 and float(dao1power) < 2:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.2)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.2)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > 2]

                            if float(huitiao) < 0.2:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] > (float(huitiao) - 0.02)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] < (float(huitiao) + 0.02)]
                            elif float(huitiao) >=0.2 and float(huitiao) < 0.6:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] > (float(huitiao) - 0.03)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] < (float(huitiao) + 0.03)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] >= 0.6]

                            if int(zhendanglength) < 20:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] ==  int(zhendanglength)]
                            elif int(zhendanglength) >=20 and int(zhendanglength) < 40:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 2)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 2)]
                            elif int(zhendanglength) >= 40 and int(zhendanglength) < 60:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 5)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 5)]
                            elif int(zhendanglength) >= 60 and int(zhendanglength) < 100:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 10)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 10)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] >= 100]

                            isLikeOK = False
                            if float(huitiao) < 0.35 and int(dao0length) < 10 and int(zhendanglength) > 39 and float(
                                    dao1power) < 1:
                                isLikeOK = True

                            if isLikeOK:
                                dingMSG = '【追涨-还可以】\n'
                            else:
                                dingMSG = '【追涨-看一眼】\n'
                            dingMSG += f"标的代码：{s}\n"
                            dingMSG += f"标的名称：{stockDf.loc[stockDf['ts_code'] == s]['name'].values[0]}\n"
                            dingMSG += "最后一笔天数：{} \n".format(str(dao0length))
                            dingMSG += "上攻涨幅：{} \n".format(
                                str(dao1power).split('.')[0] + '.' + str(dao1power).split('.')[1][:2])
                            dingMSG += "回调幅度：{} \n".format(
                                str(huitiao).split('.')[0] + '.' + str(huitiao).split('.')[1][:2])
                            dingMSG += "震荡时间：{} \n".format(str(zhendanglength))
                            if tmpThreeBuyResult.empty == False:
                                dingMSG += "相似形态个数：{}\n".format(str(tmpThreeBuyResult.shape[0]))
                                dingMSG += "【平均】 "
                                dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format(
                                    round(np.nanmean(tmpThreeBuyResult['n1b']), 2), round(np.nanmean(tmpThreeBuyResult['n2b']), 2),
                                    round(np.nanmean(tmpThreeBuyResult['n3b']), 2), round(np.nanmean(tmpThreeBuyResult['n5b']), 2),
                                    round(np.nanmean(tmpThreeBuyResult['n8b']), 2), round(np.nanmean(tmpThreeBuyResult['n13b']), 2),
                                    round(np.nanmean(tmpThreeBuyResult['n21b']), 2))
                                dingMSG += "【中位数】 "
                                dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format(
                                    round(np.median(tmpThreeBuyResult['n1b']), 2), round(np.median(tmpThreeBuyResult['n2b']), 2),
                                    round(np.median(tmpThreeBuyResult['n3b']), 2), round(np.median(tmpThreeBuyResult['n5b']), 2),
                                    round(np.median(tmpThreeBuyResult['n8b']), 2), round(np.median(tmpThreeBuyResult['n13b']), 2),
                                    round(np.median(tmpThreeBuyResult['n21b']), 2))
                                dingMSG += "【胜率】 "
                                dingMSG += "n1b: {}% | n2b: {}%  | n3b: {}%  | n5b: {}%  | n8b: {}%  | n13b: {}%  | n21b: {}%\n".format(
                                    round(tmpThreeBuyResult['n1b'][tmpThreeBuyResult['n1b'] > 0].count() / tmpThreeBuyResult['n1b'].count() * 100, 2), round(tmpThreeBuyResult['n2b'][tmpThreeBuyResult['n2b'] > 0].count() / tmpThreeBuyResult['n2b'].count() * 100, 2),
                                    round(tmpThreeBuyResult['n3b'][tmpThreeBuyResult['n3b'] > 0].count() / tmpThreeBuyResult['n3b'].count() * 100, 2), round(tmpThreeBuyResult['n5b'][tmpThreeBuyResult['n5b'] > 0].count() / tmpThreeBuyResult['n5b'].count() * 100, 2),
                                    round(tmpThreeBuyResult['n8b'][tmpThreeBuyResult['n8b'] > 0].count() / tmpThreeBuyResult['n8b'].count() * 100, 2), round(tmpThreeBuyResult['n13b'][tmpThreeBuyResult['n13b'] > 0].count() / tmpThreeBuyResult['n13b'].count() * 100, 2),
                                    round(tmpThreeBuyResult['n21b'][tmpThreeBuyResult['n21b'] > 0].count() / tmpThreeBuyResult['n21b'].count() * 100, 2))
                                for i, row in tmpThreeBuyResult.iterrows():
                                    dingMSG += f"【参考标的】：{stockDf.loc[stockDf['ts_code'] == row['ts_code']]['name'].values[0]}， 代码： " + row['ts_code'] + "， 时间：" + row['trade_date'] + '\n'
                                    dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format((str(row['n1b']).split('.')[0] + '.' + str(row['n1b']).split('.')[1][:2]),(str(row['n2b']).split('.')[0] + '.' + str(row['n2b']).split('.')[1][:2]),(str(row['n3b']).split('.')[0] + '.' + str(row['n3b']).split('.')[1][:2]),(str(row['n5b']).split('.')[0] + '.' + str(row['n5b']).split('.')[1][:2]),(str(row['n8b']).split('.')[0] + '.' + str(row['n8b']).split('.')[1][:2]),(str(row['n13b']).split('.')[0] + '.' + str(row['n13b']).split('.')[1][:2]),(str(row['n21b']).split('.')[0] + '.' + str(row['n21b']).split('.')[1][:2]))
                                print(dingMSG)
                            dingmessage(dingMSG, shouldAt=isLikeOK)
            print(msg)
            # if "监控提醒" in msg:
            #     dingmessage(msg.strip("\n"))

        except Exception as e:
            traceback.print_exc()
            print("{} 执行失败 - {}".format(s, e))

    # dingmessage("自选股因子监控结束 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))


def get_init_bg(symbol: str,
                end_dt: [str, datetime],
                base_freq: str,
                freqs=('1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线'),
                max_count=1000,
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
    bg.symbol = symbol
    if "周线" in freqs or "月线" in freqs:
        d_bars = get_kline(ts_code=symbol, start_date=last_day - timedelta(days=2500), end_date=last_day,
                           freq=freq_cn_map["日线"])
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

            bars_ = get_kline(ts_code=symbol, start_date=start_dt, end_date=last_day, freq=freq_cn_map[freq], fq=fq)
        bg.bars[freq] = bars_
        print(f"{symbol} - {freq} - {len(bg.bars[freq])} - last_dt: {bg.bars[freq][-1].dt} - last_day: {last_day}")

    bars2 = get_kline(ts_code=symbol, start_date=last_day, end_date=end_dt, freq=Freq.F1, fq=None)
    data = [x for x in bars2 if x.dt > last_day]

    if data:
        print(f"{symbol}: 更新 bar generator 至 {end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            bg.update(row)
    return bg


def updateKline(trader: CzscAdvancedTrader):
    bars = get_kline(ts_code=trader.symbol, start_date=trader.end_dt, end_date=datetime.now(), freq=Freq.F1, fq=None)
    data = [x for x in bars if x.dt > trader.end_dt]

    if data:
        print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            trader.update(row)
        return True
    return False
            # trader.bg.update(row)
        # trader.end_dt = trader.bg.end_dt


if __name__ == '__main__':
    monitor(True)

