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
from czsc.objects import Signal, Factor, Event, Operate
from czsc.data.ts import get_kline, get_all_etfs
import pandas as pd
from czsc.enum import Freq
from czsc.utils.bar_generator import BarGenerator
from czsc.traders import CzscSignals, CzscTrader
from czsc.strategies import CzscStrategyBase, CzscStocksCustom
import dill
from czsc.utils.dingding import dingmessage

# =======================================================================================================
# 基础参数配置
# ct_path = "/Volumes/OuGuMore/Stock/etf/data"
ct_path = "/Users/guyeqi/Documents/Python/data/realtime/etfdata"
os.makedirs(ct_path, exist_ok=True)
allStocks = get_all_etfs()
stockDf = pd.DataFrame(allStocks, columns=['ts_code', 'name'])

allcodes = stockDf['ts_code'].values.tolist()
# allStocksAfter = []
# for oneCode in allcodes:
#     allStocksAfter.append()
# print(stockDf)

events_monitor = [
    Event(name="日线GG三买", operate=Operate.LO, factors=[
        Factor(name="日线_类三买", signals_all=[
            Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
        ], signals_any=[
            Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
            Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
            Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
        ]),
    ]),
    
    Event(name="周线GG三买", operate=Operate.LO, factors=[
        Factor(name="周线_类三买", signals_all=[
            Signal("周线_倒1K_MACD方向_向上_任意_任意_0"),
        ], signals_any=[
            Signal("周线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
            Signal("周线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
            Signal("周线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
        ]),
    ]),
    # # 五笔aAb式
    # Event(name="五笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    #     Factor(name="周线_aAb式买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_五笔aAb式_任意_0")]),
    # ]),
    #
    # # 五笔类趋势
    # Event(name="五笔类趋势买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    #     Factor(name="周线_类趋势买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_五笔类趋势_任意_0")]),
    # ]),
    #
    # # 五笔三买
    # Event(name="五笔三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_五笔_任意_0")]),
    #     Factor(name="周线_三买", signals_all=[Signal("周线_倒1笔_基础形态_类三买_五笔_任意_0")]),
    # ]),
    #
    # # 七笔aAbcd式
    # Event(name="七笔aAbcd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    #     Factor(name="周线_aAbcd式买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_七笔aAbcd式_任意_0")]),
    # ]),
    #
    # # 七笔abcAd式
    # Event(name="七笔abcAd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_abcAd式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="30分钟_abcAd式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    #     Factor(name="周线_abcAd式买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_七笔abcAd式_任意_0")]),
    # ]),
    #
    # # 七笔aAb式
    # Event(name="七笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    #     Factor(name="周线_aAb式买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_七笔aAb式_任意_0")]),
    # ]),
    #
    # # 七笔三买
    # Event(name="七笔三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_三买", signals_all=[Signal("日线_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="30分钟_三买", signals_all=[Signal("30分钟_倒1笔_基础形态_类三买_七笔_任意_0")]),
    #     Factor(name="周线_三买", signals_all=[Signal("周线_倒1笔_基础形态_类三买_七笔_任意_0")]),
    # ]),
    #
    # # 七笔类趋势
    # Event(name="七笔类趋势买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类趋势买", signals_all=[Signal("日线_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="30分钟_类趋势买", signals_all=[Signal("30分钟_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    #     Factor(name="周线_类趋势买", signals_all=[Signal("周线_倒1笔_基础形态_底背驰_七笔类趋势_任意_0")]),
    # ]),
    #
    # # 九笔aAb式
    # Event(name="九笔aAb式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAb式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="30分钟_aAb式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    #     Factor(name="周线_aAb式买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_九笔aAb式_任意_0")]),
    # ]),
    #
    # # 九笔aAbcd式
    # Event(name="九笔aAbcd式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_aAbcd式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_aAbcd式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="周线_aAbcd式买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_九笔aAbcd式_任意_0"), Signal("周线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("周线_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # # 九笔ABC式
    # Event(name="九笔ABC式买", operate=Operate.LO, factors=[
    #     Factor(name="日线_ABC式买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_ABC式买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="周线_ABC式买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_九笔ABC式_任意_0"), Signal("周线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("周线_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # 九笔类一买 （2~4构成中枢A，6~8构成中枢B，9背驰）
    Event(name="九笔aAbBc式类一买", operate=Operate.LO, factors=[
        Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
                                           Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
        Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
                                           Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("周线_倒1K_DIF回抽_0轴_任意_任意_0"),
                                           Signal("周线_倒1K_MACD方向_向上_任意_任意_0")]),
    ]),
    #
    # # 九笔类三买 （1357构成中枢，最低点在3或5）（357构成中枢，8的力度小于2，9回调不跌破GG构成三买）
    # Event(name="九笔GG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="周线_类三买", signals_all=[Signal("周线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"), Signal("周线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("周线_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # # 九笔类三买 前五笔构成向下类趋势 567构成中枢，且8的高点大于GG
    # Event(name="九笔ZG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="30分钟_类三买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    #     Factor(name="周线_类三买", signals_all=[Signal("周线_倒1笔_类买卖点_类三买_九笔ZG三买_任意_0")]),
    # ]),
    #
    # # 九笔类二买
    # Event(name="九笔二买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类二买", signals_all=[Signal("日线_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="30分钟_类二买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    #     Factor(name="周线_类二买", signals_all=[Signal("周线_倒1笔_类买卖点_类二买_九笔_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A5B3C3式
    # Event(name="11笔A5B3C3式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_11笔A5B3C3式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A3B3C5式
    # Event(name="11笔A3B3C5式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_11笔A3B3C5式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔A3B5C3式
    # Event(name="11笔A3B5C3式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_11笔A3B5C3式_任意_0")]),
    # ]),
    #
    # # 十一笔 11笔a1Ab式
    # Event(name="11笔a1Ab式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_11笔a1Ab式_任意_0")]),
    # ]),
    #
    # # 11笔类三买 （1~9构成大级别中枢，10离开，11回调不跌破GG）
    # Event(name="11笔GG三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类三买", signals_all=[Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="30分钟_类三买",
    #            signals_all=[Signal("30分钟_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                         Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    #     Factor(name="周线_类三买", signals_all=[Signal("周线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"), Signal("周线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("周线_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A5B3C5
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_13笔A5B3C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A3B5C5
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_13笔A3B5C5式_任意_0")]),
    # ]),
    #
    # # 13笔 ABC式类一买，A5B5C3
    # Event(name="13笔ABC式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    #     Factor(name="周线_类一买", signals_all=[Signal("周线_倒1笔_类买卖点_类一买_13笔A5B5C3式_任意_0")]),
    # ]),
    #
    # # 潜在三买
    # Event(name="潜在三买", operate=Operate.LO, factors=[
    #     Factor(name="日线_潜在三买", signals_all=[Signal("日线_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_近7K突破中枢GG_0")]),
    #     Factor(name="30分钟_潜在三买", signals_all=[Signal("30分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="15分钟_潜在三买", signals_all=[Signal("15分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="5分钟_潜在三买", signals_all=[Signal("5分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="60分钟_潜在三买", signals_all=[Signal("60分钟_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_任意_0")]),
    #     Factor(name="周线_潜在三买", signals_all=[Signal("周线_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_近7K突破中枢GG_0")]),
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

    Event(name="vg简单一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg简单一买", signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0")]),
        Factor(name="30分钟_vg简单一买", signals_all=[Signal("30分钟_vg简单一买_任意_确认_任意_任意_0")]),
        Factor(name="60分钟_vg简单一买", signals_all=[Signal("60分钟_vg简单一买_任意_确认_任意_任意_0")]),
        Factor(name="周线_vg简单一买", signals_all=[Signal("周线_vg简单一买_任意_确认_任意_任意_0")]),
    ]),

    Event(name="vg潜在一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg潜在一买", signals_all=[Signal("日线_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="30分钟_vg潜在一买", signals_all=[Signal("30分钟_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="60分钟_vg潜在一买", signals_all=[Signal("60分钟_vg潜在一买_任意_确认_任意_任意_0")]),
        # Factor(name="周线_vg潜在一买", signals_all=[Signal("周线_vg潜在一买_任意_确认_任意_任意_0")]),
    ]),

    Event(name="反转迹象", operate=Operate.LO, factors=[
        Factor(name="日线_反转迹象", signals_all=[Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="30分钟_反转迹象", signals_all=[Signal("30分钟_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="60分钟_反转迹象", signals_all=[Signal("60分钟_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="周线_反转迹象", signals_all=[Signal("周线_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="辅助一买", operate=Operate.LO, factors=[
        Factor(name="日线_辅助一买", signals_all=[Signal("日线_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="30分钟_辅助一买", signals_all=[Signal("30分钟_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="60分钟_辅助一买", signals_all=[Signal("60分钟_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="周线_辅助一买", signals_all=[Signal("周线_D1N20量价_BS1辅助_看多_任意_任意_0")]),
    ]),

    Event(name="TAS一买", operate=Operate.LO, factors=[
        Factor(name="日线_TAS一买", signals_all=[Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="30分钟_TAS一买", signals_all=[Signal("30分钟_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="60分钟_TAS一买", signals_all=[Signal("60分钟_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="周线_TAS一买", signals_all=[Signal("周线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
    ]),

    Event(name="vg一买反转orTAS", operate=Operate.LO, factors=[
        Factor(name="日线_vg一买反转orTAS", signals_all=[Signal("日线_vg一买_任意_确认_任意_任意_0")],
               signals_any=[Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0"),
                            Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="vg一买反转andTAS", operate=Operate.LO, factors=[
        Factor(name="日线_vg一买反转andTAS",
               signals_all=[Signal("日线_vg一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0"),
                            Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
    ]),

    Event(name="vg简单一买反转", operate=Operate.LO, factors=[
        Factor(name="日线_vg简单一买反转",
               signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="vg简单一买反转TAS", operate=Operate.LO, factors=[
        Factor(name="日线_vg简单一买反转TAS",
               signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0"),
                            Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
    ]),

    Event(name="vg复杂一买反转", operate=Operate.LO, factors=[
        Factor(name="日线_vg复杂一买反转",
               signals_all=[Signal("日线_vg复杂一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="周线_vg复杂一买反转",
               signals_all=[Signal("周线_vg复杂一买_任意_确认_任意_任意_0"), Signal("周线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="60分钟_vg复杂一买反转",
               signals_all=[Signal("60分钟_vg复杂一买_任意_确认_任意_任意_0"), Signal("60分钟_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="vg复杂一买多中枢", operate=Operate.LO, factors=[
        Factor(name="日线_vg复杂一买多中枢",signals_all=[],
               signals_any=[Signal("日线_vg复杂一买_任意_确认_2_任意_0"), Signal("日线_vg复杂一买_任意_确认_3_任意_0")]),
        Factor(name="周线_vg复杂一买2中枢",signals_all=[],
               signals_any=[Signal("周线_vg复杂一买_任意_确认_2_任意_0"), Signal("周线_vg复杂一买_任意_确认_3_任意_0")]),
        Factor(name="60分钟_vg复杂一买2中枢",signals_all=[],
               signals_any=[Signal("60分钟_vg复杂一买_任意_确认_2_任意_0"), Signal("60分钟_vg复杂一买_任意_确认_3_任意_0")]),
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
                ct: CzscTrader = dill.load(open(file_ct, 'rb'))
                ct.get_signals: Callable = CzscStocksCustom.get_signals
                hasChange = updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
                                 freqs=['30分钟', '60分钟', '日线', '周线'], asset='FD')
                ct = CzscTrader(bg=kg, get_signals=CzscStocksCustom.get_signals)
                hasChange = True
            if hasChange:
                dill.dump(ct, open(file_ct, 'wb'))
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
                        if f == "日线_vg复杂一买反转":
                            dingmessage("【抄底】\n" + "看下参数\n" + msg.strip("\n"), shouldAt=False, webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg简单一买反转":
                            dingmessage("【抄底】\n" + "6成胜率\n" + msg.strip("\n"), shouldAt=False, webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg简单一买反转TAS":
                            dingmessage("【抄底】\n" + "6.5成胜率\n" +  + msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买反转orTAS":
                            dingmessage("【抄底】\n" + "7成胜率\n" +  + msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买反转andTAS":
                            dingmessage("【抄底】\n" + "必买！！！！！！！\n必买！！！！！！！\n必买！！！！！！！\n8成胜率\n" +  + msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买":
                            confirm, zhongshu, bipower,score = ct.s[f].split("_")
                            bi1power, bi2power = bipower.split("-")
                            if float(bi1power) > float(bi2power):
                                dingmessage("【抄底】\n" + msg.strip("\n"))
                        elif f == "日线_60分钟_vg三买":
                            confirm, huitiao, dao0length, zhendanglength, dao1power = ct.s[f].split("_")
                            if float(huitiao) < 0.35 and int(dao0length) < 10 and int(zhendanglength) > 39 and float(dao1power) < 1:
                                dingmessage("【追涨】\n" + msg.strip("\n"))
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
                freqs=('30分钟', '60分钟', '日线'),
                max_count=1000,
                adjust='qfq',
                asset='E'):
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
                           freq=freq_cn_map["日线"], asset=asset)
        bgd = BarGenerator("日线", ['周线'])
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

            bars_ = get_kline(ts_code=symbol, start_date=start_dt, end_date=last_day, freq=freq_cn_map[freq], fq=fq, asset=asset)
        bg.bars[freq] = bars_
        print(f"{symbol} - {freq} - {len(bg.bars[freq])} - last_dt: {bg.bars[freq][-1].dt} - last_day: {last_day}")

    bars2 = get_kline(ts_code=symbol, start_date=last_day, end_date=end_dt, freq=Freq.F1, fq=None, asset=asset)
    data = [x for x in bars2 if x.dt > last_day]

    if data:
        print(f"{symbol}: 更新 bar generator 至 {end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            bg.update(row)
    return bg

def updateKline(trader: CzscSignals):
    bars = get_kline(ts_code=trader.symbol, start_date=trader.end_dt, end_date=datetime.now(), freq=Freq.F1, fq=None, asset='FD')
    data = [x for x in bars if x.dt > trader.end_dt]

    if data:
        print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            trader.update(row)
        return True


if __name__ == '__main__':
    monitor(True)

