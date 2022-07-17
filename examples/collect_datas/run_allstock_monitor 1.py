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
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks
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
from czsc.signals.signals import get_default_signals
from czsc.traders import create_advanced_trader
from czsc.strategies import trader_strategy_custom
import dill

# =======================================================================================================
# 基础参数配置
ct_path = "/Volumes/OuGuMore/Stock/data"
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
    Event(name="底分型停顿", operate=Operate.LO, factors=[
        Factor(name="日线_底分型停顿", signals_all=[Signal("日线_倒1K_四K形态_底分型_强势停顿_任意_0")]),
        # Factor(name="30分钟_底分型停顿", signals_all=[Signal("30分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
        # Factor(name="15分钟_底分型停顿", signals_all=[Signal("15分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
        # Factor(name="5分钟_底分型停顿", signals_all=[Signal("5分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
        # Factor(name="60分钟_底分型停顿", signals_all=[Signal("60分钟_倒1K_四K形态_底分型_强势停顿_任意_0")]),
    ]),

    # Event(name="底分型强势", operate=Operate.LO, factors=[
    #     Factor(name="日线_底分型强势", signals_all=[Signal("日线_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="30分钟_底分型强势", signals_all=[Signal("30分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="15分钟_底分型强势", signals_all=[Signal("15分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="5分钟_底分型强势", signals_all=[Signal("5分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    #     Factor(name="60分钟_底分型强势", signals_all=[Signal("60分钟_倒1K_三K形态_底分型_强势_任意_0")]),
    # ]),
]


def monitor(needCacheStocks, use_cache=True):
    # dingmessage("自选股因子监控启动 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    moni_path = os.path.join(ct_path, "monitor")
    # 首先清空历史快照
    if os.path.exists(moni_path):
        shutil.rmtree(moni_path)
    os.makedirs(moni_path, exist_ok=True)

    # print(len(symbols))
    k = 1
    for s in needCacheStocks:
        if s.endswith('BJ'):
            continue
        print(k)
        k += 1
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct) and use_cache:
                ct: CzscAdvancedTrader = dill.load(open(file_ct, 'rb'))
                updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
                                 freqs=['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线'])
                ct = create_advanced_trader(bg=kg, raw_bars=[], strategy=trader_strategy_custom)
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
                    msg += "监控提醒：{}@{} [{}]\n".format(event.name, f, ct.s[daoZeroKey])
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

if __name__ == '__main__':
    monitor(allcodes[0:1000], True)

