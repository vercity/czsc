# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/5/6 13:24
describe: 提供一些策略的编写案例

以 trader_ 开头的是择时交易策略案例
"""
from czsc import signals
from czsc.objects import Freq, Operate, Signal, Factor, Event
from collections import OrderedDict
from czsc.traders import CzscAdvancedTrader
from czsc.objects import PositionLong, PositionShort, RawBar
from czsc.signals.bxt import get_s_like_bs, get_s_d0_bi, get_s_bi_status, get_s_di_bi, get_s_base_xt, get_s_three_bi
from czsc.signals.ta import get_s_single_k, get_s_three_k, get_s_sma, get_s_macd, get_s_tingdun_k
from czsc.signals.cxt import cxt_sub_b3_V221212, cxt_zhong_shu_gong_zhen_V221221, cxt_vg_customgongzhen, cxt_vg_threeBuy, cxt_vg_threeBuyConfirm, cxt_vg_oneBuy, cxt_vg_fakeOneBuy


def trader_standard(symbol, T0=False, min_interval=3600 * 4):
    """择时策略编写的一些标准说明

    输入参数：
    1. symbol 是必须要有的，且放在第一个位置，策略初始化过程指明交易哪个标的
    2. 除此之外的一些策略层面的参数可选，比如 T0，min_interval 等

    :param symbol: 择时策略初始化的必须参数，指明交易哪个标的
    :param T0:
    :param min_interval:
    :return:
    """
    pass


def trader_example1(symbol, T0=False, min_interval=3600 * 4):
    """A股市场择时策略样例，支持按交易标的独立设置参数

    :param symbol:
    :param T0: 是否允许T0交易
    :param min_interval: 最小开仓时间间隔，单位：秒
    :return:
    """

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=100))
        s.update(signals.pos.get_s_long02(cat, th=100))
        s.update(signals.pos.get_s_long05(cat, span='月', th=500))

        for _, c in cat.kas.items():
            s.update(signals.bxt.get_s_d0_bi(c))
            if c.freq in [Freq.F1]:
                s.update(signals.other.get_s_zdt(c, di=1))
                s.update(signals.other.get_s_op_time_span(c, op='开多', time_span=('13:00', '14:50')))
                s.update(signals.other.get_s_op_time_span(c, op='平多', time_span=('09:35', '14:50')))
            if c.freq in [Freq.F60, Freq.D, Freq.W]:
                s.update(signals.ta.get_s_macd(c, di=1))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=T0, long_min_interval=min_interval)

    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸", signals_all=[
                Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
                Signal("1分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
                Signal("1分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '1分钟',
        "freqs": ['5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线', '月线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_a(symbol):
    """A股市场择时策略A"""

    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:
        s = OrderedDict({"symbol": cat.symbol, "dt": cat.end_dt, "close": cat.latest_price})
        s.update(signals.pos.get_s_long01(cat, th=100))
        s.update(signals.pos.get_s_long02(cat, th=100))
        s.update(signals.pos.get_s_long05(cat, span='月', th=500))
        for _, c in cat.kas.items():
            if c.freq in [Freq.F15]:
                s.update(signals.bxt.get_s_d0_bi(c))
                s.update(signals.other.get_s_zdt(c, di=1))
                s.update(signals.other.get_s_op_time_span(c, op='开多', time_span=('13:00', '14:50')))
                s.update(signals.other.get_s_op_time_span(c, op='平多', time_span=('09:35', '14:50')))

            if c.freq in [Freq.F60, Freq.D, Freq.W]:
                s.update(signals.ta.get_s_macd(c, di=1))
        return s

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    long_events = [
        Event(name="开多", operate=Operate.LO, factors=[
            Factor(name="低吸", signals_all=[
                Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
            ]),
        ]),

        Event(name="平多", operate=Operate.LE, factors=[
            Factor(name="持有资金", signals_all=[
                Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
                Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
            ], signals_not=[
                Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
                Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
            ]),
        ]),
    ]

    tactic = {
        "base_freq": '15分钟',
        "freqs": ['60分钟', '日线'],
        "get_signals": get_signals,

        "long_pos": long_pos,
        "long_events": long_events,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_custom(symbol):
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:

        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()

        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})
            s.update(get_s_d0_bi(cat.kas[oneFreq]))
            s.update(get_s_three_k(cat.kas[oneFreq], 1))
            s.update(get_s_tingdun_k(cat.kas[oneFreq], 1))
            # s.update(get_s_di_bi(cat.kas[oneFreq], 1))
            s.update(get_s_macd(cat.kas[oneFreq], 1))
            s.update(get_s_single_k(cat.kas[oneFreq], 1))
            # 表里关系
            # s.update(get_s_bi_status(cat.kas[oneFreq]))
            # s.update(cxt_sub_b3_V221212(cat, "日线", "60分钟"))
            # s.update(cxt_zhong_shu_gong_zhen_V221221(cat, "日线", "60分钟"))
            if oneFreq == '日线':
                s.update(cxt_vg_threeBuy(cat, "日线", "60分钟"))
                s.update(cxt_vg_threeBuyConfirm(cat, "日线", "60分钟"))
                s.update(cxt_vg_fakeOneBuy(cat, oneFreq))
            s.update(cxt_vg_oneBuy(cat, oneFreq))
            # for di in range(1, 8):
            #     s.update(get_s_three_bi(cat.kas[oneFreq], di))

            # for di in range(1, 8):
            #     s.update(get_s_base_xt(cat.kas[oneFreq], di))

            for di in range(1, 8):
                s.update(get_s_like_bs(cat.kas[oneFreq], di))

            dictMerge.update(s)

        return dictMerge

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    # long_events = [
    #     Event(name="开多", operate=Operate.LO, factors=[
    #         Factor(name="低吸", signals_all=[
    #             # Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
    #             # Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
    #         ]),
    #     ]),
    #
    #     Event(name="平多", operate=Operate.LE, factors=[
    #         Factor(name="持有资金", signals_all=[
    #             # Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
    #             Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #         ], signals_not=[
    #             Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #         ]),
    #     ]),
    # ]

    tactic = {
        "base_freq": '1分钟',
        "freqs": ['1分钟', '5分钟', '15分钟', '30分钟', '60分钟', '日线', '周线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": None,
        "long_events": None,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_backtest(symbol):
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:

        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()

        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})
            s.update(get_s_d0_bi(cat.kas[oneFreq]))
            # s.update(get_s_three_k(cat.kas[oneFreq], 1))
            # s.update(get_s_tingdun_k(cat.kas[oneFreq], 1))
            # s.update(get_s_di_bi(cat.kas[oneFreq], 1))
            # s.update(get_s_macd(cat.kas[oneFreq], 1))
            # s.update(get_s_single_k(cat.kas[oneFreq], 1))
            # 表里关系
            # s.update(get_s_bi_status(cat.kas[oneFreq]))
            s.update(cxt_sub_b3_V221212(cat, "日线", "30分钟"))
            s.update(cxt_zhong_shu_gong_zhen_V221221(cat, "日线", "30分钟"))

            # for di in range(1, 8):
            #     s.update(get_s_three_bi(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_base_xt(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_like_bs(cat.kas[oneFreq], di))

            dictMerge.update(s)

        return dictMerge

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    # long_events = [
    #     Event(name="开多", operate=Operate.LO, factors=[
    #         Factor(name="三买", signals_all=[
    #             # Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
    #             # Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
    #             # Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #             Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
    #         ], signals_any=[
    #             Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
    #         ]),
    #     ]),
    #
    #     Event(name="平多", operate=Operate.LE, factors=[
    #         Factor(name="持有资金", signals_all=[
    #             # Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
    #             Signal("日线_倒1K_四K形态_顶分型_强势停顿_任意_0"),
    #             # Signal("日线_倒1笔_类买卖点_类一卖_任意_任意_0"),
    #         ], signals_not=[
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #         ]),
    #     ]),
    # ]

    tactic = {
        "base_freq": '30分钟',
        "freqs": ['30分钟', '日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": None,
        "long_events": None,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic


def trader_strategy_backtest2(symbol):
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:

        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()

        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})
            s.update(get_s_d0_bi(cat.kas[oneFreq]))
            # s.update(get_s_three_k(cat.kas[oneFreq], 1))
            # s.update(get_s_tingdun_k(cat.kas[oneFreq], 1))
            # s.update(get_s_di_bi(cat.kas[oneFreq], 1))
            # s.update(get_s_macd(cat.kas[oneFreq], 1))
            # s.update(get_s_single_k(cat.kas[oneFreq], 1))
            # 表里关系
            # s.update(get_s_bi_status(cat.kas[oneFreq]))
            s.update(cxt_sub_b3_V221212(cat, "日线", "60分钟"))
            s.update(cxt_zhong_shu_gong_zhen_V221221(cat, "日线", "60分钟"))

            # for di in range(1, 8):
            #     s.update(get_s_three_bi(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_base_xt(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_like_bs(cat.kas[oneFreq], di))

            dictMerge.update(s)

        return dictMerge

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    # long_events = [
    #     Event(name="开多", operate=Operate.LO, factors=[
    #         Factor(name="三买", signals_all=[
    #             # Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
    #             # Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
    #             # Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #             Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
    #         ], signals_any=[
    #             Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
    #         ]),
    #     ]),
    #
    #     Event(name="平多", operate=Operate.LE, factors=[
    #         Factor(name="持有资金", signals_all=[
    #             # Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
    #             Signal("日线_倒1K_四K形态_顶分型_强势停顿_任意_0"),
    #             # Signal("日线_倒1笔_类买卖点_类一卖_任意_任意_0"),
    #         ], signals_not=[
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #         ]),
    #     ]),
    # ]

    tactic = {
        "base_freq": '30分钟',
        "freqs": ['30分钟', '60分钟', '日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": None,
        "long_events": None,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic

def trader_strategy_backtest3(symbol):
    def get_signals(cat: CzscAdvancedTrader) -> OrderedDict:

        if cat.s:
            dictMerge = cat.s.copy()
        else:
            dictMerge = OrderedDict()

        for oneFreq in cat.kas.keys():
            s = OrderedDict({"symbol": cat.kas[oneFreq].symbol, "dt": cat.kas[oneFreq].bars_raw[-1].dt,
                             "close": cat.kas[oneFreq].bars_raw[-1].close})


            # s.update(get_s_tingdun_k(cat.kas[oneFreq], 1))
            # s.update(get_s_di_bi(cat.kas[oneFreq], 1))
            # s.update(get_s_macd(cat.kas[oneFreq], 1))

            # 表里关系
            # s.update(get_s_bi_status(cat.kas[oneFreq]))
            if oneFreq == '日线':
                s.update(cxt_vg_customgongzhen(cat, "日线", "60分钟", th=0))
                s.update(get_s_d0_bi(cat.kas[oneFreq]))
                # s.update(get_s_three_k(cat.kas[oneFreq], 1))
                s.update(get_s_single_k(cat.kas[oneFreq], 1))

            # s.update(cxt_zhong_shu_gong_zhen_V221221(cat, "日线", "60分钟"))

            # for di in range(1, 8):
            #     s.update(get_s_three_bi(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_base_xt(cat.kas[oneFreq], di))
            #
            # for di in range(1, 8):
            #     s.update(get_s_like_bs(cat.kas[oneFreq], di))

            dictMerge.update(s)

        return dictMerge

    # 定义多头持仓对象和交易事件
    long_pos = PositionLong(symbol, hold_long_a=1, hold_long_b=1, hold_long_c=1,
                            T0=False, long_min_interval=3600 * 4)
    # long_events = [
    #     Event(name="开多", operate=Operate.LO, factors=[
    #         Factor(name="三买", signals_all=[
    #             # Signal("开多时间范围_13:00_14:50_是_任意_任意_0"),
    #             # Signal("15分钟_倒1K_ZDT_非涨跌停_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("15分钟_倒0笔_长度_5根K线以下_任意_任意_0"),
    #             # Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #             Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
    #         ], signals_any=[
    #             Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
    #         ]),
    #     ]),
    #
    #     Event(name="平多", operate=Operate.LE, factors=[
    #         Factor(name="持有资金", signals_all=[
    #             # Signal("平多时间范围_09:35_14:50_是_任意_任意_0"),
    #             Signal("日线_倒1K_四K形态_顶分型_强势停顿_任意_0"),
    #             # Signal("日线_倒1笔_类买卖点_类一卖_任意_任意_0"),
    #         ], signals_not=[
    #             # Signal("15分钟_倒0笔_方向_向上_任意_任意_0"),
    #             # Signal("60分钟_倒1K_MACD多空_多头_任意_任意_0"),
    #         ]),
    #     ]),
    # ]

    tactic = {
        "base_freq": '30分钟',
        "freqs": ['30分钟', '60分钟', '日线'],
        "get_signals": get_signals,
        "signals_n": 0,

        "long_pos": None,
        "long_events": None,

        # 空头策略不进行定义，也就是不做空头交易
        "short_pos": None,
        "short_events": None,
    }

    return tactic