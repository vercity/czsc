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
import sys

sys.path.append("/Users/guyeqi/Documents/Python/czsc")
from collections import OrderedDict
from datetime import datetime, timedelta
from czsc.data.ts import freq_cn_map, dt_fmt, get_all_stocks, get_all_plates, get_ths_daily
from czsc.objects import Signal, Factor, Event, Operate
from czsc.data.ts import get_kline, get_all_etfs
import pandas as pd
from czsc.enum import Freq
from czsc.signals import bar_reversal_V230227, bar_vol_bs1_V230224, tas_first_bs_V230217
from czsc.signals.bxt import get_s_d0_bi
from czsc.signals.cxt import cxt_vg_threeBuy, cxt_vg_threeBuyConfirm, cxt_vg_oneBuy, cxt_vg_easyOneBuy, \
    cxt_vg_fuzaOneBuy
from czsc.signals.ta import get_s_single_k
from czsc.utils.bar_generator import BarGenerator
from czsc.traders import CzscSignals, CzscTrader
from czsc.strategies import CzscStrategyBase, CzscStocksCustom
import dill
from czsc.utils.dingding import dingmessage

# =======================================================================================================
# 基础参数配置
# ct_path = "/Volumes/OuGuMore/Stock/etf/data"
from czsc.utils.io import save_pkl, read_pkl

ct_path = "/Users/guyeqi/Documents/Python/data/realtime/platesdata"
os.makedirs(ct_path, exist_ok=True)
allPlatesInfo = get_all_plates()
allcodes = list(allPlatesInfo['N'].keys())


events_monitor = [
    Event(name="vg三买", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买", signals_all=[Signal("日线_60分钟_vg三买_确认_任意_任意_0")]),
    ]),

    Event(name="vg三买确认", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买确认", signals_all=[Signal("日线_60分钟_vg三买确认_确认_任意_任意_0")]),
    ]),

    Event(name="vg一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg一买", signals_all=[Signal("日线_vg一买_任意_确认_任意_任意_0")]),
    ]),

    Event(name="vg简单一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg简单一买", signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0")]),
    ]),

    Event(name="反转迹象", operate=Operate.LO, factors=[
        Factor(name="日线_反转迹象", signals_all=[Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="TAS一买", operate=Operate.LO, factors=[
        Factor(name="日线_TAS一买", signals_all=[Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
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
    ]),

    Event(name="vg复杂一买多中枢", operate=Operate.LO, factors=[
        Factor(name="日线_vg复杂一买多中枢",signals_all=[],
               signals_any=[Signal("日线_vg复杂一买_任意_确认_2_任意_0"), Signal("日线_vg复杂一买_任意_确认_3_任意_0")]),
    ]),
]

class CzscStocksPlates(CzscStrategyBase):
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
                s.update(get_s_d0_bi(cat.kas[oneFreq]))
                s.update(bar_reversal_V230227(cat.kas[oneFreq]))
                s.update(tas_first_bs_V230217(cat.kas[oneFreq]))
                s.update(cxt_vg_threeBuy(cat, "日线", "60分钟"))
                s.update(cxt_vg_threeBuyConfirm(cat, "日线", "60分钟"))
                s.update(get_s_single_k(cat.kas[oneFreq], 1))
                s.update(cxt_vg_oneBuy(cat, oneFreq))
                s.update(cxt_vg_easyOneBuy(cat, oneFreq))
                s.update(cxt_vg_fuzaOneBuy(cat, oneFreq))

            dictMerge.update(s)

        return dictMerge

    @property
    def positions(self):
        return []

    @property
    def freqs(self):
        return ['日线']

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
                ct: CzscTrader =read_pkl(file_ct)
                ct.get_signals: Callable = CzscStocksPlates.get_signals
                hasChange = updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="日线",
                                 freqs=[], asset='FD')
                ct = CzscTrader(bg=kg, get_signals=CzscStocksPlates.get_signals)
                hasChange = True
            if hasChange:
                save_pkl(ct, file_ct)

            msg = f"标的代码：{s}\n"
            msg += f"标的名称：{nameOfPlateCode(s)}\n"
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
                            dingmessage("【抄底】\n" + "6.5成胜率\n" +  msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买反转orTAS":
                            dingmessage("【抄底】\n" + "7成胜率\n" +  msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买反转andTAS":
                            dingmessage("【抄底】\n" + "必买！！！！！！！\n必买！！！！！！！\n必买！！！！！！！\n8成胜率\n" +  msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买":
                            confirm, zhongshu, bipower,score = ct.s[f].split("_")
                            bi1power, bi2power = bipower.split("-")
                            if float(bi1power) > float(bi2power):
                                dingmessage("【抄底】\n" + msg.strip("\n"))
                        elif f == "日线_60分钟_vg三买确认":
                            dingmessage("【追涨】\n" + msg.strip("\n"))
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

    # if isinstance(end_dt, str):t
    #     end_dt = pd.to_datetime(end_dt, utc=True)
    #     end_dt = end_dt.tz_convert('dateutil/PRC')
    #     # 时区转换之后，要减去8个小时才是设置的时间
    #     end_dt = end_dt - timedelta(hours=8)
    # else:
    #     assert end_dt.tzinfo._filename == 'PRC'
    last_day = end_dt

    bg = BarGenerator(base_freq, freqs, max_count)
    bg.symbol = symbol
    if "周线" in freqs or "月线" in freqs:
        d_bars = get_ths_daily(ts_code=symbol, start_date=last_day - timedelta(days=2500), end_date=last_day)
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

            bars_ = get_ths_daily(ts_code=symbol, start_date=start_dt, end_date=last_day)
        bg.bars[freq] = bars_
        print(f"{symbol} - {freq} - {len(bg.bars[freq])} - last_dt: {bg.bars[freq][-1].dt} - last_day: {last_day}")

    bars2 = get_ths_daily(ts_code=symbol, start_date=last_day, end_date=end_dt)
    data = [x for x in bars2 if x.dt > last_day]

    if data:
        print(f"{symbol}: 更新 bar generator 至 {end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            bg.update(row)
    return bg

def updateKline(trader: CzscSignals):
    bars = get_ths_daily(ts_code=trader.symbol, start_date=trader.end_dt, end_date=datetime.now())
    data = [x for x in bars if x.dt >= trader.end_dt]

    if data:
        print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            trader.update(row)
        return True

def nameOfPlateCode(code):
    return allPlatesInfo['N'][code]['name']

if __name__ == '__main__':
    monitor(True)

