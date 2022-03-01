# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/11/7 17:09
describe: 支持分批买入卖出的高级交易员
"""

from typing import Callable, List

from .. import CzscAdvancedTrader
from ..objects import PositionLong, PositionShort, Operate, Signal, Event, RawBar
from ..utils.bar_generator import BarGenerator

class CzscCBTrader(CzscAdvancedTrader):
    """缠中说禅技术分析理论之多级别联立交易决策类（支持分批开平仓 / 支持从任意周期开始交易）"""

    def __init__(self,
                 bg: BarGenerator,
                 get_signals: Callable,
                 long_events: List[Event] = None,
                 long_pos: PositionLong = None,
                 short_events: List[Event] = None,
                 short_pos: PositionShort = None,
                 max_bi_count: int = 50,
                 bi_min_len: int = 7,
                 signals_n: int = 0,
                 verbose: bool = False,
                 chineseName: str = "kezhuanzhai",
                 stock: str = "stock",
                 ):

        super(CzscCBTrader, self).__init__(bg,get_signals,long_events,long_pos,short_events,short_pos,max_bi_count,bi_min_len,signals_n,verbose)
        self.chineseName = chineseName
        self.stock = stock

    def __repr__(self):
        return "<{} for {}>".format(self.name, self.symbol)



