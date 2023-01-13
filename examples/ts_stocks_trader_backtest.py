# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/2/14 21:50
"""
import os
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

import pandas as pd
from czsc.data.ts_cache import TsDataCache
from czsc import CZSC, Freq
from czsc.utils import BarGenerator
from czsc.strategies import trader_strategy_backtest
from czsc.traders.base import CzscSignals, CzscAdvancedTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks

pd.set_option('mode.chained_assignment', None)
pd.set_option('display.max_rows', 10000)
pd.set_option('display.max_columns', 20)

data_path = "/Users/guyeqi/Documents/Python/data"
dc = TsDataCache(data_path, sdt='20100101', edt='20230112', refresh=False)
trade_cal = dc.trade_cal()
trade_cal = trade_cal[trade_cal.is_open == 1]
trade_dates = trade_cal.cal_date.to_list()
stock = '000001.SH'

allStocks = get_all_stocks()
stockDf = pd.DataFrame(allStocks, columns=['ts_code', 'name'])
allStockCodes = stockDf['ts_code'].values.tolist()

events_monitor = [
    Event(name="三买回踩", operate=Operate.LO, factors=[
        Factor(name="日线_30分钟_三买回踩", signals_all=[Signal("日线_30分钟_三买回踩10_确认_任意_任意_0")]),
    ]),

    Event(name="中枢共振", operate=Operate.LO, factors=[
        Factor(name="日线_30分钟_中枢共振", signals_all=[Signal("日线_30分钟_中枢共振_看多_任意_任意_0")]),
    ]),
]
if __name__ == '__main__':
    # bars = dc.pro_bar(ts_code=stock, asset='I', start_date='20150101', end_date="20230109", freq='D')
    # c = CZSC(bar30, max_bi_num=200)
    count = 0
    for oneStock in allStockCodes:
        if oneStock.endswith('BJ'):
            continue
        count += 1
        print(count)
        print(oneStock)
        dataCache = TsDataCache(data_path, sdt='20100101', edt='20230112', refresh=False)
        bar30 = dataCache.pro_bar_minutes(ts_code=oneStock, freq='30min')
        bg = BarGenerator(base_freq='30分钟', freqs=['日线'], max_count=50000)
        for bar in bar30:
            bg.update(bar)
        # for oneEndDate in  [date for date in trade_dates if int(date) > 20160101]:
        #     dataCache = TsDataCache(data_path, sdt='20100101', edt=oneEndDate, refresh=False)
        #     bar30 = dataCache.pro_bar_minutes(ts_code=oneStock, freq='30min')
        #     bg = BarGenerator(base_freq='30分钟', freqs=['日线'], max_count=50000)
        #     for bar in bar30:
        #         bg.update(bar)
            # trader = CzscAdvancedTrader(bg, trader_strategy_backtest)
            # trader.open_in_browser()
            # print(trader.s['dt'])
            # trader.s
            # zhongshugongzhenSignal = trader.s['日线_30分钟_中枢共振']