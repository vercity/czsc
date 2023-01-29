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
from czsc.strategies import trader_strategy_backtest2
from czsc.traders.base import CzscSignals, CzscAdvancedTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks
import requests
import json
import hashlib
from czsc.utils.io import read_pkl, save_pkl
from multiprocessing import Process
import numpy as np

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
sanmaihuicaiqueren = "确认"

gaokaiNextDay = 0
dikaiNextDay = 0
n1bResult = []
n3bResult = []
n5bResult = []
n21bResult = []

def dingmessage(dingMessage):
    return
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

fromDate = 20200101
strategyName = "三买回踩10，中枢共振，day-60min" + str(fromDate)
strategyFolderPath = os.path.join(data_path, strategyName)
if not os.path.exists(strategyFolderPath):
    os.mkdir(strategyFolderPath)

isBackTestResult = False
# ssss = np.load(os.path.join(strategyFolderPath, "btStock") + '.npy', allow_pickle=True).item()
btStock = {}

def backtest(stocks):
    global dikaiNextDay, gaokaiNextDay
    global maxZF
    maxZF = 0
    for oneStock in stocks:
        if oneStock.endswith('BJ'):
            continue

        # oneStock = '300678.SZ'
        print(oneStock)

        stockPath = os.path.join(strategyFolderPath, oneStock) + '.pkl'
        # 某天收盘为买点day
        buyPointsDt = []
        hasCache = False
        if os.path.exists(stockPath):
            buyPointsDt = read_pkl(stockPath)
            hasCache = True

        if isBackTestResult:
            hasCache = True

        if not hasCache:
            # 回测暂时只和fromDate有关，别的都是读缓存的记录
            for oneEndDate in [date for date in trade_dates if int(date) > fromDate]:
                if int(oneEndDate) > 20230110:
                    continue
                dataCache = TsDataCache(data_path, sdt='20100101', edt=oneEndDate, refresh=False)
                barMin = dataCache.pro_bar_minutes(ts_code=oneStock, sdt=trade_dates[trade_dates.index(oneEndDate) - 500],
                                                  edt=oneEndDate, freq='30min')
                # 没有数据的情况
                if len(barMin) == 0:
                    continue
                bg = BarGenerator(base_freq='30分钟', freqs=['60分钟', '日线'], max_count=10000)
                for bar in barMin:
                    bg.update(bar)
                trader = CzscAdvancedTrader(bg, trader_strategy_backtest2)
                # trader.open_in_browser()
                print(trader.s['dt'])
                kCount = trader.s['日线_倒0笔_长度']
                zhongshugongzhenSignal = trader.s['日线_60分钟_中枢共振']
                sanmaihuicaiSignal = trader.s['日线_60分钟_三买回踩10']
                if kCountThree in kCount:
                    # print("3根K线")
                    # print(sanmaihuicaiSignal)
                    if zhongshugongzhenkanduo in zhongshugongzhenSignal and sanmaihuicaiqueren in sanmaihuicaiSignal:
                        # print(trader.s['dt'])
                        print(oneStock)
                        print("3根K线_中枢共振看多 & 三买回踩确认")
                        # dingmessage(oneStock + "_" + str(trader.s['dt']) + "_" + "3根K线_中枢共振看多")
                        # oneEndDate是第二天的日期，比如出现了看多在5号，oneEndDate是6号
                        buyPointsDt.append(trade_dates[trade_dates.index(oneEndDate) - 1])
                elif kCountFour in kCount:
                    if zhongshugongzhenkanduo in zhongshugongzhenSignal and sanmaihuicaiqueren in sanmaihuicaiSignal:
                        # print(trader.s['dt'])
                        print("4根K线_中枢共振看多")
            # 保存开多日期
            save_pkl(buyPointsDt, stockPath)
            if len(buyPointsDt) == 0:
                continue

        print("所有开多日期是: " + str(buyPointsDt))
        if isBackTestResult:
            kaicangPrice = 0
            for oneDay in buyPointsDt:
                if oneDay in btStock.keys():
                    stockList = btStock[oneDay]
                    stockList.append(oneStock)
                else:
                    btStock[oneDay] = [oneStock]
                # 前后看100天
                probar = dc.pro_bar(ts_code=oneStock, start_date=trade_dates[trade_dates.index(oneDay) - 100],
                                           end_date=trade_dates[trade_dates.index(oneDay) + 100], raw_bar=False)
                ma5 = probar["close"].rolling(5).mean()
                ma10 = probar["close"].rolling(10).mean()
                currentDay = probar[probar["trade_date"] == oneDay]
                if currentDay.empty:
                    print("empty dataframe")
                    continue
                nextDay = probar.iloc[currentDay.index+1]
                preclose = nextDay["pre_close"].iloc[0]
                openPrice = nextDay["open"].iloc[0]
                if kaicangPrice == 0:
                    kaicangPrice = openPrice
                    print("{}, {} 开盘价开仓: {}".format(nextDay["ts_code"].iloc[0], trade_dates[trade_dates.index(oneDay) + 1], str(open)))
                # 计算第二天是高开还是低开
                if openPrice >= preclose:
                    gaokaiNextDay += 1
                else:
                    dikaiNextDay += 1
                # 买点出现后60天的数据
                next60DatasDF = probar.iloc[currentDay.index.values[0]+1:currentDay.index.values[0]+61]
                # 买点出现后最高价出现的index
                ind = next60DatasDF["close"].idxmax()
                # 最高价当天的具体数据
                maxDayData = next60DatasDF.loc[ind]
                maxZhangfu = (maxDayData["close"] - preclose) / preclose
                if maxZhangfu > maxZF:
                    maxZF = maxZhangfu
                    print("最大涨幅股票:" + oneStock)
                    print("最大涨幅是: " + str(maxZhangfu))
                    print("买点出现时间: " + oneDay + " 第: " + str(ind-100) + " 天, 收盘价: " + str(maxDayData["close"]))
                # 计算在出信号后第二天开盘价买入，持有一天后的开盘价收益(%)
                hold1Day = currentDay["n1b"].iloc[0] / 100
                n1bResult.append(hold1Day)
                # 计算在出信号后第二天开盘价买入，持有3天后的开盘价收益(%)
                hold3Day = currentDay["n3b"].iloc[0] / 100
                n3bResult.append(hold3Day)
                # 计算在出信号后第二天开盘价买入，5天后的开盘价收益(%)
                hold5Day = currentDay["n5b"].iloc[0] / 100
                n5bResult.append(hold5Day)
                # 计算在出信号后第二天开盘价买入，21天后的开盘价收益(%)
                hold21Day = currentDay["n21b"].iloc[0] / 100
                n21bResult.append(hold21Day)
    if isBackTestResult:
        # 统计汇总
        print("总共交易 {} 次".format(gaokaiNextDay + dikaiNextDay))
        print("高开占比 {}".format(gaokaiNextDay / (gaokaiNextDay + dikaiNextDay)))
        print("1天就卖，平均赚 {}".format(str(np.nanmean(n1bResult))))
        print("3天就卖，平均赚 {}".format(str(np.nanmean(n3bResult))))
        print("5天就卖，平均赚 {}".format(str(np.nanmean(n5bResult))))
        print("21天就卖，平均赚 {}".format(str(np.nanmean(n21bResult))))

        tf = open(os.path.join(strategyFolderPath, "btStock") + '.json', "w")
        json.dump(btStock, tf)
        tf.close()
        # save_pkl(os.path.join(strategyFolderPath, "btStock") + '.npy', stockPath)
        # np.save(os.path.join(strategyFolderPath, "btStock") + '.npy', btStock)

if __name__ == '__main__':
    if isBackTestResult:
        backtest(allStockCodes)
    else:
        process = [Process(target=backtest, args=(allStockCodes[0:1000],)),
                   Process(target=backtest, args=(allStockCodes[1000:2000],)),
                   Process(target=backtest, args=(allStockCodes[2000:3000],)),
                   Process(target=backtest, args=(allStockCodes[3000:4000],)), ]
        [p.start() for p in process]
        [p.join() for p in process]
