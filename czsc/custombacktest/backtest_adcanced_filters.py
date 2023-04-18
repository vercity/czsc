# -*- coding: utf-8 -*-
import os
import sys
import math
from collections import OrderedDict

from pandas import DataFrame
from czsc import CZSC, BarGenerator, CzscTrader, CzscStrategyBase
from czsc.data import TsDataCache
from czsc.signals import bar_vol_bs1_V230224, bar_reversal_V230227, tas_first_bs_V230217, jcc_san_szx_V221122, \
    jcc_shan_chun_V221121, bar_fake_break_V230204
import pandas as pd

data_path = "/Users/guyeqi/Documents/Python/data/backtest/data"
dc = TsDataCache(data_path, sdt='20100101', edt='20230112', refresh=False)
trade_cal = dc.trade_cal()
trade_cal = trade_cal[trade_cal.is_open == 1]
trade_dates = trade_cal.cal_date.to_list()

class CzscStocksCustomBacktest(CzscStrategyBase):
    """CZSC 股票 Custom 策略"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def get_signals(cls, cat) -> OrderedDict:
        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()
        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})
            if oneFreq == '日线':
                #日线_D1T10_三星
                s.update(jcc_san_szx_V221122(c=cat.kas[oneFreq], lastN=5, appearTimes=2))
                #日线_D1B_山川形态
                # s.update(jcc_shan_chun_V221121(c=cat.kas[oneFreq]))
                #'日线_D1N20M5_假突破'
                # s.update(bar_fake_break_V230204(c=cat.kas[oneFreq]))

            dictMerge.update(s)

        return dictMerge

def advanced_filter_result(rawDataframe:DataFrame, oneStock:str):
    resultDF = rawDataframe.copy(deep=True)
    for oneDay in resultDF['日期'].values.tolist():
        dataCache = TsDataCache(data_path, sdt='20100101', edt=oneDay, refresh=False)
        barMin = dataCache.pro_bar(ts_code=oneStock,
                                   start_date=trade_dates[trade_dates.index(oneDay) - 500],
                                   end_date=oneDay)
        # 没有数据的情况
        if len(barMin) == 0:
            continue
        bg = BarGenerator(base_freq='日线', freqs=[], max_count=10000)
        bg.init_freq_bars('日线', barMin)
        trader = CzscTrader(bg=bg, get_signals=CzscStocksCustomBacktest.get_signals)

        if (trader.s["日线_D1T10_三星"].split("_")[0] == "满足"):
            print("")
        else:
            dropIndex = rawDataframe[rawDataframe['日期'] == oneDay].index
            rawDataframe = rawDataframe.drop(dropIndex)

        # if (trader.s["日线_D1B_山川形态"].split("_")[0] == "三川"):
        #     print("")
        # else:
        #     dropIndex = rawDataframe[rawDataframe['日期'] == oneDay].index
        #     rawDataframe = rawDataframe.drop(dropIndex)

        # if (trader.s["日线_D1N20M5_假突破"].split("_")[0] == "看多"):
        #     print("")
        # else:
        #     dropIndex = rawDataframe[rawDataframe['日期'] == oneDay].index
        #     rawDataframe = rawDataframe.drop(dropIndex)

    return rawDataframe