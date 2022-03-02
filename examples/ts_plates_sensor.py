# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/11/4 17:39
describe: A股强势板块传感器，板块是概念板块、行业板块、指数的统称
"""
import sys
sys.path.insert(0, '.')
sys.path.insert(0, '..')

import os
from czsc import CZSC
from czsc.sensors.plates import ThsConceptsSensor, TsDataCache
from czsc.objects import Freq, Signal, Factor, Event, Operate
from czsc.signals.ta import get_s_macd, get_s_sma, OrderedDict


def get_signals(c: CZSC):
    s = OrderedDict()

    if c.freq == Freq.D:
        s.update(get_s_sma(c, di=1, t_seq=(5, 20, 120, 250)))
    return s


def get_event():
    event = Event(name="SMA_V1", operate=Operate.LO, factors=[
        Factor(name="日超强", signals_all=[
            Signal(k1='日线', k2='倒1K', k3='SMA120多空', v1='多头'),
            Signal(k1='日线', k2='倒1K', k3='SMA120方向', v1='向上'),

            Signal(k1='日线', k2='倒1K', k3='SMA20多空', v1='多头'),
            Signal(k1='日线', k2='倒1K', k3='SMA20方向', v1='向上'),
        ]),
    ])
    return event


if __name__ == '__main__':
    data_path = "/Volumes/OuGuMore/Stock/sensors"
    dc = TsDataCache(data_path, sdt='2010-01-01', edt='20220225')
    sdt = "20210601"
    edt = "20220225"
    results_path = os.path.join(data_path, f"ths_concepts_{get_event().name}_{sdt}_{edt}")
    tcs = ThsConceptsSensor(results_path, sdt, edt, dc, get_signals, get_event, 'I')
    df_daily, df_detail = tcs.validate()

