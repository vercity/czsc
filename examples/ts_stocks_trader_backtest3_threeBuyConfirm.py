# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/2/14 21:50
"""
import os
import sys
import math

sys.path.insert(0, '.')
sys.path.insert(0, '..')

import pandas as pd
from czsc.data.ts_cache import TsDataCache
from czsc import CZSC, Freq
from czsc.utils import BarGenerator
from czsc.strategies import trader_strategy_backtest3
from czsc.traders.base import CzscSignals, CzscAdvancedTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks
from czsc.utils.dingding import dingmessage
import json
import hashlib
from czsc.utils.io import read_pkl, save_pkl
from multiprocessing import Process
import numpy as np
from collections import OrderedDict
from czsc.signals.bxt import get_s_like_bs, get_s_d0_bi
from czsc.signals.ta import get_s_single_k
from czsc.signals.cxt import cxt_vg_threeBuyConfirm

pd.set_option('mode.chained_assignment', None)
pd.set_option('display.max_rows', 10000)
pd.set_option('display.max_columns', 20)

data_path = "/Volumes/OuGuMore/Stock/backtest/data"
backup_data_path = "/Users/guyeqi/Documents/Python/data/backtest/data"

fromDate = 20150101
strategyName = "vg三买确认，day-60min" + str(fromDate)
strategyFolderPath = os.path.join(data_path, strategyName)
strategyFoldeBackrPath = os.path.join(backup_data_path, strategyName)
if not os.path.exists(strategyFolderPath):
    if not os.path.exists(strategyFoldeBackrPath):
        os.mkdir(strategyFolderPath)
    else:
        data_path = backup_data_path
        strategyFolderPath = strategyFoldeBackrPath

dc = TsDataCache(data_path, sdt='20100101', edt='20230112', refresh=False)
trade_cal = dc.trade_cal()
trade_cal = trade_cal[trade_cal.is_open == 1]
trade_dates = trade_cal.cal_date.to_list()
stock = '000001.SH'

allStocks = get_all_stocks()
stockDf = pd.DataFrame(allStocks, columns=['ts_code', 'name'])
allStockCodes = stockDf['ts_code'].values.tolist()


kCountThree = '3根K线'
kCountFour = '4根K线'
sanmaiqueren = "确认"

gaokaiNextDay = 0
dikaiNextDay = 0
n1bResult = []
n3bResult = []
n5bResult = []
n21bResult = []


def trader_strategy_backtestThis(symbol):
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:

        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()

        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})
            if oneFreq == '日线':
                s.update(get_s_d0_bi(cat.kas[oneFreq]))
                if s['日线_倒0笔_长度'].split("_")[0] == '3根K线' and s['日线_倒0笔_方向'].split("_")[0] == '向上':
                    s.update(cxt_vg_threeBuyConfirm(cat, "日线", "60分钟"))
                    s.update(get_s_single_k(cat.kas[oneFreq], 1))

            dictMerge.update(s)

        return dictMerge

    tactic = {
        "base_freq": '日线',
        "freqs": ['日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": None,
        "long_events": None,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


isBackTestResult = False
# ssss = np.load(os.path.join(strategyFolderPath, "btStock") + '.npy', allow_pickle=True).item()
btStock = {}

def calculateOtherSignals(c):
    signals = {}
    bars = c.kas['日线'].bars_raw
    if len(bars) >= 3:
        signal = "任意"
        tri = bars[-3:]
        if tri[0].high > tri[1].high < tri[2].high:
            signal = "底分型"
            # 倒数第一根收盘价比倒数第三根最高价还高
            if tri[2].close > tri[0].high:
                signal = "底分型强势"
        elif tri[0].high < tri[1].high < tri[2].high:
            signal = "向上走"
        elif tri[0].high < tri[1].high > tri[2].high:
            signal = "顶分型"
            # 倒数第一根收盘价比倒数第三根最低价还低
            if tri[2].close < tri[0].low:
                signal = "顶分型强势"
        elif tri[0].high > tri[1].high > tri[2].high:
            signal = "向下走"
    return {"3K形态" : signal}

def backtest(stocks):
    global dikaiNextDay, gaokaiNextDay
    global maxZF, maxDF
    maxZF = maxDF = 0

    for oneStock in stocks:
        if oneStock.endswith('BJ'):
            continue

        resultDataFrame = pd.DataFrame(columns=["日期", "标的", "3K形态", "倒1K状态", "回调幅度", "最后三笔天数", "震荡时间", "上攻涨幅"])
        print(oneStock)

        stockPath = os.path.join(strategyFolderPath, oneStock) + '.pkl'
        # 某天收盘为买点day
        hasCache = False
        if os.path.exists(stockPath):
            resultDataFrame = read_pkl(stockPath)
            hasCache = True

        if isBackTestResult:
            hasCache = True

        if not hasCache:
            # 回测暂时只和fromDate有关，别的都是读缓存的记录
            for oneEndDate in [date for date in trade_dates if int(date) > fromDate]:
                if int(oneEndDate) > 20230110:
                    continue
                dataCache = TsDataCache(data_path, sdt='20100101', edt=oneEndDate, refresh=False)
                # barMin = dataCache.pro_bar_minutes(ts_code=oneStock, sdt=trade_dates[trade_dates.index(oneEndDate) - 500],
                #                                   edt=oneEndDate, freq='30min')
                barMin = dataCache.pro_bar(ts_code=oneStock, start_date=trade_dates[trade_dates.index(oneEndDate) - 500],
                                                  end_date=oneEndDate)
                # 没有数据的情况
                if len(barMin) == 0:
                    continue
                bg = BarGenerator(base_freq='日线', freqs=[ ], max_count=10000)
                bg.init_freq_bars('日线', barMin)
                # for bar in barMin:
                #     bg.update(bar)
                trader = CzscAdvancedTrader(bg, trader_strategy_backtestThis)
                print(trader.s['dt'])
                kCount = trader.s['日线_倒0笔_长度']
                # zhongshugongzhenSignal = trader.s['日线_60分钟_中枢共振']
                if ('日线_60分钟_vg三买确认' in trader.s.keys()) == False:
                    continue
                sanmaihuicaiSignal = trader.s['日线_60分钟_vg三买确认']
                if kCountThree in kCount:
                    if sanmaiqueren in sanmaihuicaiSignal:
                        detailSignal = sanmaihuicaiSignal.split("_")
                        print(kCountThree + "三买确认")
                        otherSignals = calculateOtherSignals(trader)
                        otherSignals["日期"] = trade_dates[trade_dates.index(oneEndDate)]
                        otherSignals["倒1K状态"] = trader.s["日线_倒1K_状态"].split("_")[0]
                        trader.open_in_browser(filePath=os.path.join(strategyFolderPath, oneStock + "_" + trade_dates[trade_dates.index(oneEndDate)]) + '.html')

                        resultDataFrame = resultDataFrame.append(
                            {"日期": otherSignals["日期"], "标的": oneStock, "3K形态":otherSignals["3K形态"], "倒1K状态":otherSignals["倒1K状态"], "回调幅度":float(detailSignal[1]), "最后三笔天数":float(detailSignal[2]), "震荡时间":int(detailSignal[3]), "上攻涨幅":float(detailSignal[4])}, ignore_index=True)
                        # dingmessage(oneStock + "_" + str(trader.s['dt']) + "_" + "3根K线_中枢共振看多")
                        # oneEndDate是第二天的日期，比如出现了看多在5号，oneEndDate是6号
                        print(resultDataFrame)
            # 保存开多日期
            save_pkl(resultDataFrame, stockPath)
            if len(resultDataFrame) == 0:
                continue

        # print("所有开多日期是: " + str(buyPointsDt))
        if isBackTestResult:
            # 筛选
            # resultDataFrame = resultDataFrame.loc[~(resultDataFrame['3K形态'] == '底分型强势')]
            # resultDataFrame = resultDataFrame.loc[resultDataFrame['倒1K状态'] == '下跌']
            # resultDataFrame = resultDataFrame.loc[resultDataFrame['回调幅度'] < 0.3]
            resultDataFrame = resultDataFrame.loc[resultDataFrame['上攻涨幅'] < 1]
            # resultDataFrame = resultDataFrame.loc[resultDataFrame['震荡时间'] > 40]
            # resultDataFrame = resultDataFrame.loc[resultDataFrame['最后三笔天数'] <10]
            kaicangPrice = 0
            for oneDay in resultDataFrame['日期'].values.tolist():
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
                    print(resultDataFrame)
                    # print("{}, {} 开盘价开仓: {}".format(nextDay["ts_code"].iloc[0], trade_dates[trade_dates.index(oneDay) + 1], str(open)))
                # 计算第二天是高开还是低开
                if openPrice >= preclose:
                    gaokaiNextDay += 1
                else:
                    dikaiNextDay += 1
                # 买点出现后60天的数据
                next60DatasDF = probar.iloc[currentDay.index.values[0]+1:currentDay.index.values[0]+61]
                # 买点出现后最高价出现的index
                ind = next60DatasDF["close"].idxmax()
                ind2 = next60DatasDF["close"].idxmin()
                # 最高价当天的具体数据
                maxDayData = next60DatasDF.loc[ind]
                minDayData = next60DatasDF.loc[ind2]
                maxZhangfu = (maxDayData["close"] - preclose) / preclose
                maxDiefu = (minDayData["close"] - preclose) / preclose
                if maxZhangfu > maxZF:
                    maxZF = maxZhangfu
                    print("最大涨幅股票:" + oneStock)
                    print("最大涨幅是: " + str(maxZhangfu))
                    print("买点出现时间: " + oneDay + " 第: " + str(ind-100) + " 天, 收盘价: " + str(maxDayData["close"]))
                if maxDiefu < maxDF:
                    maxDF = maxDiefu
                    print("最大跌幅股票:" + oneStock)
                    print("最大跌幅是: " + str(maxDiefu))
                    print("买点出现时间: " + oneDay + " 第: " + str(ind2-100) + " 天, 收盘价: " + str(minDayData["close"]))
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
        print("1天就卖，平均赚 {}，中位数{}".format(str(np.nanmean(n1bResult)), str(np.median(n1bResult))))
        print("3天就卖，平均赚 {}，中位数{}".format(str(np.nanmean(n3bResult)), str(np.median([x for x in n3bResult if math.isnan(x) == False]))))
        print("5天就卖，平均赚 {}，中位数{}".format(str(np.nanmean(n5bResult)), str(np.median([x for x in n5bResult if math.isnan(x) == False]))))
        print("21天就卖，平均赚 {}，中位数{}".format(str(np.nanmean(n21bResult)), str(np.median([x for x in n21bResult if math.isnan(x) == False]))))

        tf = open(os.path.join(strategyFolderPath, "btStock") + '.json', "w")
        json.dump(btStock, tf)
        tf.close()
        # save_pkl(os.path.join(strategyFolderPath, "btStock") + '.npy', stockPath)
        # np.save(os.path.join(strategyFolderPath, "btStock") + '.npy', btStock)


if __name__ == '__main__':
    # backtest(allStockCodes)
    if isBackTestResult:
        backtest(allStockCodes)
    else:
        process = [Process(target=backtest, args=(allStockCodes[0:1000],)),
                   Process(target=backtest, args=(allStockCodes[1000:2000],)),
                   Process(target=backtest, args=(allStockCodes[2000:3000],)),
                   Process(target=backtest, args=(allStockCodes[3000:4000],)),
                   Process(target=backtest, args=(allStockCodes[4000:],)), ]
        [p.start() for p in process]
        [p.join() for p in process]
