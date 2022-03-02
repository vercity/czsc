# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/10/30 20:21
"""
import os
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

from czsc.data.ts_cache import TsDataCache
from czsc.sensors.stocks import StocksDaySensor
from czsc.objects import Operate, Signal, Factor, Event
from czsc.signals.signals import *


def get_signals(c: analyze.CZSC) -> OrderedDict:
    """在 CZSC 对象上计算选股信号

    :param c: CZSC 对象
    :return: 信号字典
    """
    freq: Freq = c.freq
    s = OrderedDict({"symbol": c.symbol, "dt": c.bars_raw[-1].dt, "close": c.bars_raw[-1].close})

    default_signals = [
        # 以下是技术指标相关信号
        Signal(k1=str(freq.value), k2="MA5状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="KDJ状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="MACD状态", v1="其他", v2='其他', v3='其他'),
        Signal(k1=str(freq.value), k2="倒0笔", k3="潜在三买", v1="其他", v2='其他', v3='其他'),
    ]
    for signal in default_signals:
        s[signal.key] = signal.value

    if not c.bi_list:
        return s

    if len(c.bars_raw) > 30 and c.freq in [Freq.W, Freq.M]:
        if kdj_gold_cross(c.bars_raw, just=False):
            v = Signal(k1=str(freq.value), k2="KDJ状态", v1="金叉")
            s[v.key] = v.value

    if len(c.bars_raw) > 100 and c.freq == Freq.D:
        close = np.array([x.close for x in c.bars_raw[-100:]])
        ma5 = SMA(close, timeperiod=5)
        if c.bars_raw[-1].close >= ma5[-1]:
            v = Signal(k1=str(freq.value), k2="MA5状态", v1="收盘价在MA5上方", v2='')
            s[v.key] = v.value
            if ma5[-1] > ma5[-2] > ma5[-3]:
                v = Signal(k1=str(freq.value), k2="MA5状态", v1='收盘价在MA5上方', v2="向上趋势")
                s[v.key] = v.value

        diff, dea, macd = MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        if diff[-3:-1].mean() > 0 and dea[-3:-1].mean() > 0 and macd[-3] < macd[-2] < macd[-1]:
            v = Signal(k1=str(freq.value), k2="MACD状态", v1="DIFF大于0", v2='DEA大于0', v3='柱子增大')
            s[v.key] = v.value

    # 倒0笔潜在三买
    if c.freq == Freq.D and len(c.bi_list) >= 5:
        if c.bi_list[-1].direction == Direction.Down:
            gg = max(c.bi_list[-1].high, c.bi_list[-3].high)
            zg = min(c.bi_list[-1].high, c.bi_list[-3].high)
            zd = max(c.bi_list[-1].low, c.bi_list[-3].low)
        else:
            gg = max(c.bi_list[-2].high, c.bi_list[-4].high)
            zg = min(c.bi_list[-2].high, c.bi_list[-4].high)
            zd = max(c.bi_list[-2].low, c.bi_list[-4].low)

        if zg > zd:
            k1 = str(freq.value)
            k2 = "倒0笔"
            k3 = "潜在三买"
            v = Signal(k1=k1, k2=k2, k3=k3, v1="构成中枢")
            if gg * 1.1 > min([x.low for x in c.bars_raw[-3:]]) > zg > zd:
                v = Signal(k1=k1, k2=k2, k3=k3,  v1="构成中枢", v2="近3K在中枢上沿附近")
                if max([x.high for x in c.bars_raw[-7:-3]]) > gg:
                    v = Signal(k1=k1, k2=k2, k3=k3, v1="构成中枢", v2="近3K在中枢上沿附近", v3='近7K突破中枢GG')

            if v and "其他" not in v.value:
                s[v.key] = v.value

    return s


def get_event():
    event = Event(name="选股测试", operate=Operate.LO, factors=[
        Factor(name="月线KDJ金叉_日线MACD强势", signals_all=[
            Signal("月线_KDJ状态_任意_金叉_任意_任意_0"),
            Signal('日线_MACD状态_任意_DIFF大于0_DEA大于0_柱子增大_0'),
            Signal('日线_MA5状态_任意_收盘价在MA5上方_任意_任意_0'),
        ]),

        Factor(name="月线KDJ金叉_日线潜在三买", signals_all=[
            Signal("月线_KDJ状态_任意_金叉_任意_任意_0"),
            Signal('日线_倒0笔_潜在三买_构成中枢_近3K在中枢上沿附近_近7K突破中枢GG_0'),
            Signal('日线_MA5状态_任意_收盘价在MA5上方_任意_任意_0'),
        ]),
    ])
    return event


if __name__ == '__main__':
    data_path = "/Volumes/OuGuMore/Stock/sensors"
    dc = TsDataCache(data_path, sdt='2000-01-01', edt='20220223')
    sdt = "20210223"
    edt = "20220223"
    results_path = os.path.join(data_path, f"{get_event().name}_{sdt}_{edt}")
    sss = StocksDaySensor(results_path, sdt, edt, dc, get_signals, get_event)
    grid_params = {
        "fc_top_n": list(range(10, 50, 10)),
        "fc_min_n": list(range(1, 3, 1)),
        "min_total_mv": [5e5, 10e5],
        "max_count": [300],
    }
    # sss.grip_search(grid_params)

    filter_params = [
        # 不加任何过滤
        {"index_code": None, "fc_top_n": None, 'fc_min_n': None, "min_total_mv": None},

        # 验证指数过滤
        {"index_code": "000905.SH", "fc_top_n": None, 'fc_min_n': None, "min_total_mv": None},
        {"index_code": '000300.SH', "fc_top_n": None, 'fc_min_n': None, "min_total_mv": None},

        # 验证市值效应
        {"index_code": None, "fc_top_n": None, 'fc_min_n': None, "min_total_mv": 5e5},
        {"index_code": None, "fc_top_n": None, 'fc_min_n': None, "min_total_mv": 10e5},
        {"index_code": None, "fc_top_n": None, 'fc_min_n': None, "min_total_mv": 15e5},
        {"index_code": None, "fc_top_n": None, 'fc_min_n': None, "min_total_mv": 20e5},

        # 验证板块效应
        {"index_code": None, "fc_top_n": 30, 'fc_min_n': 3, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 30, 'fc_min_n': 2, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 30, 'fc_min_n': 1, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 20, 'fc_min_n': 3, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 20, 'fc_min_n': 2, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 20, 'fc_min_n': 1, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 10, 'fc_min_n': 2, "min_total_mv": 1e6},
        {"index_code": None, "fc_top_n": 10, 'fc_min_n': 1, "min_total_mv": 1e6},
    ]

    file_docx = sss.report_performance(filter_params)
    print(f"选股性能评估结果：{file_docx}")

    # 获取最近一个交易日的选股结果
    df1, df2 = sss.get_latest_strong(fc_top_n=20, fc_min_n=2, min_total_mv=2e6)


