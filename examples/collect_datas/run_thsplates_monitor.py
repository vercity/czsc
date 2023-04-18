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

from czsc.data import TsDataCache
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks
# from czsc.data.jq import JqCzscTrader as CzscTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.utils.qywx import push_text, push_file
from czsc.utils.io import read_pkl, save_pkl
import requests
import json
from czsc.data.ts import get_kline,pro
import pandas as pd
from czsc.enum import Freq
from czsc.utils.bar_generator import BarGenerator
from czsc.traders import CzscSignals, CzscTrader
from czsc.strategies import CzscStrategyBase, CzscStocksCustom
import dill
from multiprocessing import Process
from examples.run_allplates_monitor import CzscStocksPlates

# =======================================================================================================
# 基础参数配置
# ct_path = "/Volumes/OuGuMore/Stock/data"
from examples.run_allplates_monitor import allPlatesInfo

ct_path = "/Users/guyeqi/Documents/Python/data/realtime/platesdata"
os.makedirs(ct_path, exist_ok=True)

conceptsDic = {}
alls = get_all_stocks()
relations =pd.read_csv(os.path.join(ct_path, "relations"), index_col=0)
cachedMembers = read_pkl(os.path.join(ct_path, "members"))

# def refreshConcepts(toPath):
#     concepts = pro.ths_index(exchange="A", type="N")
#     concepts.to_csv(os.path.join(ct_path, "concepts.csv"))
#     concepts = concepts.loc[concepts['count'] > 10]
#     concepts = concepts.loc[concepts['count'] < 700]
#     concepts = concepts.loc[~(concepts['ts_code'] == '883300.TI')]
#     concepts = concepts.loc[~(concepts['ts_code'] == '883301.TI')]
#     concepts = concepts.loc[~(concepts['ts_code'] == '883302.TI')]
#     concepts = concepts.loc[~(concepts['ts_code'] == '883303.TI')]
#     concepts = concepts.loc[~(concepts['ts_code'] == '883304.TI')]
#     concepts = concepts.loc[~(concepts['ts_code'] == '864038.TI')]
#     #gpt数据有问题
#     concepts = concepts.loc[~(concepts['ts_code'] == '864036.TI')]
#     for index, row in concepts.iterrows():
#         thisTypeConcept = {}
#         if row['type'] in conceptsDic.keys():
#             thisTypeConcept = conceptsDic[row['type']]
#         thisTypeConcept[row['ts_code']] = {"name": row['name'], "count": row['count'], 'list_date': row['list_date']}
#         time.sleep(0.5)
#         thisTypeConceptDetailStock = {}
#         detailDF = pro.ths_member(ts_code=row['ts_code'],
#                                   fields="ts_code,code,name,weight,in_date,out_date,is_new")
#         for index2, row2 in detailDF.iterrows():
#             # 判断是不是中国的股票
#             if row2['code'].endswith('.SH') or row2['code'].endswith('.SZ'):
#                 thisTypeConceptDetailStock[row2['code']] = row2['name']
#         if len(thisTypeConceptDetailStock.keys()) > 0:
#             thisTypeConcept[row['ts_code']]['stocks'] = thisTypeConceptDetailStock
#             conceptsDic[row['type']] = thisTypeConcept
#             # print(thisTypeConcept)
#     save_pkl(conceptsDic, toPath)
# #刷新接口
# refreshConcepts(os.path.join(ct_path, "members"))

#添加关系
# allConceptNames = []
# for oneConcept in  cachedMembers["N"].values():
#     if  "DRG/DIP" in oneConcept["name"]:
#         print("")
#     allConceptNames.append(oneConcept["name"])
# df1 = pd.DataFrame(0, columns=alls['name'].values.tolist(), index=allConceptNames)
# for oneConcept in  cachedMembers["N"].values():
#     if "stocks" in oneConcept.keys():
#         conceptName = oneConcept["name"]
#         for oneStock in oneConcept["stocks"].values():
#             df1.loc[conceptName, oneStock] = 1
# df1.to_csv(os.path.join(ct_path, "relations"), index=True)

def getPlatesRankDf(smas=[1,3,5,10,20]):
    columns = ["code", "zhName"]
    for oneSMA in smas:
        columns.append("SMA"+str(oneSMA))
    df = pd.DataFrame(columns=columns)
    allcodes = list(allPlatesInfo['N'].keys())
    hasPrintTime = False
    for s in allcodes:
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct):
                result = {"code":s}
                result["zhName"] = cachedMembers["N"][s]["name"]
                ct: CzscTrader = read_pkl(file_ct)
                if hasPrintTime == False:
                    print("数据截止时间")
                    print(ct.end_dt.strftime("%Y-%m-%d"))
                    hasPrintTime = True
                close1 = ct.bg.bars["日线"][-1].close
                for oneSMA in smas:
                    if len(ct.bg.bars["日线"]) < oneSMA:
                        continue
                    close2 = ct.bg.bars["日线"][-oneSMA - 1].close
                    result[("SMA"+str(oneSMA))] = round((close1 - close2) / close2 * 100, 2)
                # df = df.append(result, ignore_index=True)
                df = pd.concat([df, pd.DataFrame.from_records([result])], ignore_index=True)
        except Exception as e:
            traceback.print_exc()
            print("{} 执行失败 - {}".format(s, e))
    return df

#股票 -> 概念
def stockToPlates(stock):
    return relations[relations[stock] == 1].index.tolist()

# ss = stockToPlates("文投控股")
# print("")

#概念 -> 股票
def plateToStocks(plate):
    relations2 = relations.T
    plateDF = relations2.loc[:, ~relations2.columns.duplicated()]
    return plateDF[plateDF[plate] == 1].index.tolist()

def calculatePlateInsideStock(sma, plateZhName, yuzhi = -100):
    stocks = plateToStocks(plateZhName)
    result = {}
    for oneStockZhName in stocks:
        try:
            if (alls.loc[alls["name"] == oneStockZhName]).empty:
                continue
            stockCode = alls.loc[alls["name"] == oneStockZhName]["ts_code"].iloc[0]
            ct_path1 = "/Users/guyeqi/Documents/Python/data/realtime/data"
            file_ct = os.path.join(ct_path1, "{}.ct".format(stockCode))
            ct = dill.load(open(file_ct, 'rb'))
            close1 = ct.bg.bars["日线"][-1].close
            if len(ct.bg.bars["日线"]) < sma:
                continue
            close2 = ct.bg.bars["日线"][- sma - 1].close
            priceChange = round((close1 - close2) / close2 * 100, 2)
            if priceChange >= yuzhi:
                result[oneStockZhName] = priceChange
        except:
            # traceback.print_exc()
            continue
    return sorted(result.items(), key=lambda x: -x[1])

# ss = calculatePlateInsideStock(1, "年报预增", yuzhi=5)
# print(str(ss))


# stockDf = pd.DataFrame(allStocks, columns=['ts_code', 'name'])
#
# allcodes = stockDf['ts_code'].values.tolist()
#
# def monitor(needCacheStocks, use_cache=True):
#     # dingmessage("自选股因子监控启动 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
#     moni_path = os.path.join(ct_path, "monitor")
#     # 首先清空历史快照
#     if os.path.exists(moni_path):
#         shutil.rmtree(moni_path)
#     os.makedirs(moni_path, exist_ok=True)
#
#     # print(len(symbols))
#     k = 1
#     for s in needCacheStocks:
#         if s.endswith('BJ'):
#             continue
#         print(k)
#         k += 1
#         try:
#             file_ct = os.path.join(ct_path, "{}.ct".format(s))
#             if os.path.exists(file_ct) and use_cache:
#                 ct: CzscTrader = dill.load(open(file_ct, 'rb'))
#                 ct.get_signals: Callable =CzscStocksCustom.get_signals
#                 updateKline(ct)
#             else:
#                 kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
#                                  freqs=['30分钟', '60分钟', '日线', '周线'])
#                 ct = CzscTrader(bg=kg, get_signals=CzscStocksCustom.get_signals)
#             dill.dump(ct, open(file_ct, 'wb'))
#         except Exception as e:
#             traceback.print_exc()
#             print("{} 执行失败 - {}".format(s, e))
#
# def get_init_bg(symbol: str,
#                 end_dt: [str, datetime],
#                 base_freq: str,
#                 freqs=('1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线'),
#                 max_count=1000,
#                 adjust='qfq'):
#     """获取 symbol 的初始化 bar generator"""
#     last_day = (end_dt - timedelta(days=1)).replace(hour=16, minute=0)
#
#     bg = BarGenerator(base_freq, freqs, max_count)
#     bg.symbol = symbol
#     if "周线" in freqs or "月线" in freqs:
#         d_bars = get_kline(ts_code=symbol, start_date=last_day - timedelta(days=2500), end_date=last_day,
#                            freq=freq_cn_map["日线"])
#         bgd = BarGenerator("日线", ['周线'])
#         for b in d_bars:
#             bgd.update(b)
#     else:
#         bgd = None
#
#     for freq in bg.bars.keys():
#         if freq in ['周线', '月线', '季线', '年线']:
#             bars_ = bgd.bars[freq]
#         else:
#             if freq == Freq.F1.value:
#                 start_dt = end_dt - timedelta(days=21)
#                 fq = None
#             elif freq == Freq.F5.value:
#                 start_dt = end_dt - timedelta(days=21 * 5)
#                 fq = None
#             elif freq == Freq.F15.value:
#                 start_dt = end_dt - timedelta(days=21 * 15)
#                 fq = None
#             elif freq == Freq.F30.value:
#                 start_dt = end_dt - timedelta(days=500)
#                 fq = None
#             elif freq == Freq.F60.value:
#                 start_dt = end_dt - timedelta(days=1000)
#                 fq = None
#             elif freq == Freq.D.value:
#                 start_dt = end_dt - timedelta(days=1500)
#                 fq = "qfq"
#             else:
#                 raise ValueError(freq.value)
#
#             bars_ = get_kline(ts_code=symbol, start_date=start_dt, end_date=last_day, freq=freq_cn_map[freq], fq=fq)
#         bg.bars[freq] = bars_
#         print(f"{symbol} - {freq} - {len(bg.bars[freq])} - last_dt: {bg.bars[freq][-1].dt} - last_day: {last_day}")
#
#     bars2 = get_kline(ts_code=symbol, start_date=last_day, end_date=end_dt, freq=Freq.F1, fq=None)
#     data = [x for x in bars2 if x.dt > last_day]
#
#     if data:
#         print(f"{symbol}: 更新 bar generator 至 {end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
#         for row in data:
#             bg.update(row)
#     return bg
#
#
# def updateKline(trader: CzscSignals):
#     bars = get_kline(ts_code=trader.symbol, start_date=trader.end_dt, end_date=datetime.now(), freq=Freq.F1, fq=None)
#     data = [x for x in bars if x.dt > trader.end_dt]
#
#     if data:
#         print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
#         for row in data:
#             trader.update(row)
#
#
# if __name__ == '__main__':
#     process = [Process(target=monitor, args=(allcodes[0:1000], True,)),
#                Process(target=monitor, args=(allcodes[1000:2000], True,)),
#                Process(target=monitor, args=(allcodes[2000:3000], True,)),
#                Process(target=monitor, args=(allcodes[3000:4000], True,)),
#                Process(target=monitor, args=(allcodes[4000:], True,)), ]
#     [p.start() for p in process]
#     [p.join() for p in process]
#     # monitor(allcodes[0:1000], True)
