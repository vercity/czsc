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
import requests
import json

pd.set_option('mode.chained_assignment', None)
pd.set_option('display.max_rows', 10000)
pd.set_option('display.max_columns', 20)

data_path = "/Volumes/OuGuMore/Stock/backtest/data"
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

kCountThree = '3根K线'
kCountFour = '4根K线'
zhongshugongzhenkanduo = "看多"


def dingmessage(dingMessage):
    # 请求的URL，WebHook地址
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=48c7a649e0f1b4be1e699461a93e6392010074b07f48c60c058927b8f406423a"
    # 构建请求头部
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    # 构建请求数据
    tex = "【backtest】: {}".format(dingMessage)
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
        for oneEndDate in  [date for date in trade_dates if int(date) > 20150101]:
            if int(oneEndDate) > 20230110:
                continue
            dataCache = TsDataCache(data_path, sdt='20100101', edt=oneEndDate, refresh=False)
            bar30 = dataCache.pro_bar_minutes(ts_code=oneStock, sdt=trade_dates[trade_dates.index(oneEndDate) - 500], edt=oneEndDate, freq='30min')
            bg = BarGenerator(base_freq='30分钟', freqs=['日线'], max_count=50000)
            for bar in bar30:
                bg.update(bar)
            trader = CzscAdvancedTrader(bg, trader_strategy_backtest)
            trader.open_in_browser()
            print(trader.s['dt'])
            kCount = trader.s['日线_倒0笔_长度']
            zhongshugongzhenSignal = trader.s['日线_30分钟_中枢共振']
            if kCountThree in kCount:
                # print("3根K线")
                # print(zhongshugongzhenSignal)
                if zhongshugongzhenkanduo in zhongshugongzhenSignal:
                    # print(trader.s['dt'])
                    print("3根K线_中枢共振看多")
                    dingmessage(oneStock+"_"+str(trader.s['dt'])+"_"+"3根K线_中枢共振看多")
            elif kCountFour in kCount:
                if zhongshugongzhenkanduo in zhongshugongzhenSignal:
                    # print(trader.s['dt'])
                    print("4根K线_中枢共振看多")


