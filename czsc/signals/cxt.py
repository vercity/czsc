# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2022/11/7 19:29
describe:  cxt 代表 CZSC 形态信号
"""
import numpy as np
from loguru import logger
from typing import List
from czsc import CZSC
from czsc.traders.base import CzscSignals
from czsc.objects import FX, BI, Direction, ZS, Mark, FakeBI, Signal
from czsc.utils import get_sub_elements, create_single_signal, is_bis_up, is_bis_down
from czsc.utils.sig import get_zs_seq
from collections import OrderedDict
import copy
from ..utils.ta1 import MACD, SMA

from czsc.utils.sig import get_zs_seq


def cxt_bi_base_V230228(c: CZSC, **kwargs) -> OrderedDict:
    """BI基础信号

    **信号逻辑：**

    1. 取最后一个笔，最后一笔向下，则当前笔向上，最后一笔向上，则当前笔向下；
    2. 根据延伸K线数量判断当前笔的状态，中继或转折。

    **信号列表：**

    - Signal('15分钟_D0BL9_V230228_向下_中继_任意_0')
    - Signal('15分钟_D0BL9_V230228_向上_转折_任意_0')
    - Signal('15分钟_D0BL9_V230228_向下_转折_任意_0')
    - Signal('15分钟_D0BL9_V230228_向上_中继_任意_0')

    :param c: CZSC对象
    :param kwargs:
    :return: 信号识别结果
    """
    bi_init_length = kwargs.get('bi_init_length', 9)  # 笔的初始延伸长度，即笔的延伸长度小于该值时，笔的状态为转折，否则为中继
    k1, k2, k3 = f"{c.freq.value}_D0BL{bi_init_length}_V230228".split('_')
    v1 = '其他'
    if len(c.bi_list) < 3:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)

    last_bi = c.bi_list[-1]
    assert last_bi.direction in [Direction.Up, Direction.Down]
    v1 = '向上' if last_bi.direction == Direction.Down else '向下'
    v2 = "中继" if len(c.bars_ubi) >= bi_init_length else "转折"

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)


def cxt_fx_power_V221107(c: CZSC, di: int = 1, **kwargs) -> OrderedDict:
    """倒数第di个分型的强弱

    **信号列表：**

    - Signal('15分钟_D1F_分型强弱_中顶_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_弱底_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_强顶_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_弱顶_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_强底_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_中底_有中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_强顶_无中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_中顶_无中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_弱底_无中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_中底_无中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_弱顶_无中枢_任意_0')
    - Signal('15分钟_D1F_分型强弱_强底_无中枢_任意_0')

    :param c: CZSC 对象
    :param di: 倒数第di个分型
    :return:
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}F_分型强弱".split("_")
    last_fx: FX = c.fx_list[-di]
    v1 = f"{last_fx.power_str}{last_fx.mark.value[0]}"
    v2 = "有中枢" if last_fx.has_zs else "无中枢"
    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)


def cxt_first_buy_V221126(c: CZSC, di=1, **kwargs) -> OrderedDict:
    """一买信号

    **信号列表：**

    - Signal('15分钟_D1B_BUY1_一买_5笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_11笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_7笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_21笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_17笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_19笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_9笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_15笔_任意_0')
    - Signal('15分钟_D1B_BUY1_一买_13笔_任意_0')

    :param c: CZSC 对象
    :param di: CZSC 对象
    :return: 信号字典
    """

    def __check_first_buy(bis: List[BI]):
        """检查 bis 是否是一买的结束

        :param bis: 笔序列，按时间升序
        """
        res = {"match": False, "v1": "一买", "v2": f"{len(bis)}笔", 'v3': "任意"}
        if len(bis) % 2 != 1 or bis[-1].direction == Direction.Up or bis[0].direction != bis[-1].direction:
            return res

        if max([x.high for x in bis]) != bis[0].high or min([x.low for x in bis]) != bis[-1].low:
            return res

        # 检查背驰：获取向下突破的笔列表
        key_bis = []
        for i in range(0, len(bis) - 2, 2):
            if i == 0:
                key_bis.append(bis[i])
            else:
                b1, _, b3 = bis[i - 2:i + 1]
                if b3.low < b1.low:
                    key_bis.append(b3)

        # 检查背驰：最后一笔的 power_price，power_volume，length 同时满足背驰条件才算背驰
        bc_price = bis[-1].power_price < max(bis[-3].power_price, np.mean([x.power_price for x in key_bis]))
        bc_volume = bis[-1].power_volume < max(bis[-3].power_volume, np.mean([x.power_volume for x in key_bis]))
        bc_length = bis[-1].length < max(bis[-3].length, np.mean([x.length for x in key_bis]))

        if bc_price and (bc_volume or bc_length):
            res['match'] = True
        return res

    k1, k2, k3 = c.freq.value, f"D{di}B", "BUY1"
    v1, v2, v3 = "其他", '任意', '任意'

    for n in (21, 19, 17, 15, 13, 11, 9, 7, 5):
        _bis = get_sub_elements(c.bi_list, di=di, n=n)
        if len(_bis) != n:
            logger.warning('笔的数量不对')
            continue

        _res = __check_first_buy(_bis)
        if _res['match']:
            v1, v2, v3 = _res['v1'], _res['v2'], _res['v3']
            break

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3)


def cxt_first_sell_V221126(c: CZSC, di=1, **kwargs) -> OrderedDict:
    """一卖信号

    **信号列表：**

    - Signal('15分钟_D1B_SELL1_一卖_17笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_15笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_5笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_7笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_9笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_19笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_21笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_13笔_任意_0')
    - Signal('15分钟_D1B_SELL1_一卖_11笔_任意_0')

    :param c: CZSC 对象
    :param di: CZSC 对象
    :return: 信号字典
    """

    def __check_first_sell(bis: List[BI]):
        """检查 bis 是否是一卖的结束

        :param bis: 笔序列，按时间升序
        """
        res = {"match": False, "v1": "一卖", "v2": f"{len(bis)}笔", 'v3': "任意"}
        if len(bis) % 2 != 1 or bis[-1].direction == Direction.Down:
            return res

        if bis[0].direction != bis[-1].direction:
            return res

        max_high = max([x.high for x in bis])
        min_low = min([x.low for x in bis])

        if max_high != bis[-1].high or min_low != bis[0].low:
            return res

        # 检查背驰：获取向上突破的笔列表
        key_bis = []
        for i in range(0, len(bis) - 2, 2):
            if i == 0:
                key_bis.append(bis[i])
            else:
                b1, _, b3 = bis[i - 2:i + 1]
                if b3.high > b1.high:
                    key_bis.append(b3)

        # 检查背驰：最后一笔的 power_price，power_volume，length 同时满足背驰条件才算背驰
        bc_price = bis[-1].power_price < max(bis[-3].power_price, np.mean([x.power_price for x in key_bis]))
        bc_volume = bis[-1].power_volume < max(bis[-3].power_volume, np.mean([x.power_volume for x in key_bis]))
        bc_length = bis[-1].length < max(bis[-3].length, np.mean([x.length for x in key_bis]))

        if bc_price and (bc_volume or bc_length):
            res['match'] = True
        return res

    k1, k2, k3 = c.freq.value, f"D{di}B", "SELL1"
    v1, v2, v3 = "其他", '任意', '任意'

    for n in (21, 19, 17, 15, 13, 11, 9, 7, 5):
        _bis = get_sub_elements(c.bi_list, di=di, n=n)
        if len(_bis) != n:
            logger.warning('笔的数量不对，跳过')
            continue

        _res = __check_first_sell(_bis)
        if _res['match']:
            v1, v2, v3 = _res['v1'], _res['v2'], _res['v3']
            break

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3)


def cxt_bi_break_V221126(c: CZSC, di=1, **kwargs) -> OrderedDict:
    """向上笔突破回调不破信号

    **信号列表：**

    - Signal('15分钟_D1B_向上_突破_5笔_任意_0')
    - Signal('15分钟_D1B_向上_突破_7笔_任意_0')
    - Signal('15分钟_D1B_向上_突破_9笔_任意_0')

    :param c: CZSC 对象
    :param di: CZSC 对象
    :return: 信号字典
    """

    def __check(bis: List[BI]):
        res = {"match": False, "v1": "突破", "v2": f"{len(bis)}笔", 'v3': "任意"}
        if len(bis) % 2 != 1 or bis[-1].direction == Direction.Up or bis[0].direction != bis[-1].direction:
            return res

        # 获取向上突破的笔列表
        key_bis = []
        for i in range(0, len(bis) - 2, 2):
            if i == 0:
                key_bis.append(bis[i])
            else:
                b1, _, b3 = bis[i - 2:i + 1]
                if b3.high > b1.high:
                    key_bis.append(b3)

        # 检查：
        # 1. 当下笔的最低点在任一向上突破笔的高点上
        # 2. 当下笔的最低点离笔序列最低点的距离不超过向上突破笔列表均值的1.618倍
        tb_break = bis[-1].low > min([x.high for x in key_bis])
        tb_price = bis[-1].low < min([x.low for x in bis]) + 1.618 * np.mean([x.power_price for x in key_bis])
        if tb_break and tb_price:
            res['match'] = True
        return res

    k1, k2, k3 = c.freq.value, f"D{di}B", "向上"
    v1, v2, v3 = "其他", '任意', '任意'

    for n in (9, 7, 5):
        _bis = get_sub_elements(c.bi_list, di=di, n=n)
        if len(_bis) != n:
            logger.warning('笔的数量不对，跳过')
            continue

        _res = __check(_bis)
        if _res['match']:
            v1, v2, v3 = _res['v1'], _res['v2'], _res['v3']
            break

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3)


def cxt_sub_b3_V221212(cat: CzscSignals, freq1='60分钟', freq2='15分钟', th=10, **kwargs) -> OrderedDict:
    """小级别突破大级别中枢形成三买，贡献者：魏永超

    **信号逻辑：**

    1. freq级别中产生笔中枢，最后一笔向上时，中枢由之前3笔构成；最后一笔向下时，中枢由最后3笔构成。
    2. sub_freq级别中出现向上笔超越大级别中枢最高点，且随后不回到大级别中枢区间的th%以内。

    **信号列表：**

    - Signal('60分钟_15分钟_3买回踩10_确认_任意_任意_0')

    :param cat:
    :param freq1: 中枢所在的大级别
    :param freq2: 突破大级别中枢，回踩形成小级别类3买的小级别
    :param th: 小级别回落对大级别中枢区间的回踩程度，0表示回踩不进大级别中枢，10表示回踩不超过中枢区间的10%
    :return: 信号识别结果
    """
    k1, k2, k3 = f"{freq1}_{freq2}_三买回踩{th}".split('_')

    c: CZSC = cat.kas[freq1]
    sub_c: CZSC = cat.kas[freq2]

    v1 = "其他"
    if len(c.bi_list) > 13 and len(sub_c.bi_list) > 10:
        last_bi = c.bi_list[-1]
        if last_bi.direction == Direction.Down:
            zs = ZS(symbol=cat.symbol, bis=c.bi_list[-3:])
        else:
            zs = ZS(symbol=cat.symbol, bis=c.bi_list[-4:-1])

        min7 = min([x.low for x in c.bi_list[-7:]])
        # 中枢成立，且中枢最低点不是最后7笔的最低点，且最后7笔最低点同时也是最后13笔最低点（保证低点起来第一个中枢）
        if zs.zd < zs.zg and zs.dd > min7 == min([x.low for x in c.bi_list[-13:]]):
            last_sub_bi = sub_c.bi_list[-1]

            if last_sub_bi.direction == Direction.Down and last_sub_bi.high > zs.gg \
                    and last_sub_bi.low > zs.zg - (th / 100) * (zs.zg - zs.zd):
                v1 = "确认"

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def cxt_vg_customgongzhen(cat: CzscSignals, freq='60分钟', sub_freq='15分钟', th=10, last3Count=30,
                          last6Count=50) -> OrderedDict:
    # 默认最后3笔的长度是40天
    k1, k2, k3 = f"{freq}_{sub_freq}_vg三买回踩{th}".split('_')

    c: CZSC = cat.kas[freq]
    sub_c: CZSC = cat.kas[sub_freq]

    v1 = "其他"
    # 最后一笔方向向上
    if len(c.bi_list) > 7 and (c.bi_list[-1].direction == Direction.Up):
        continueJudgeSub = False
        # 倒4至倒2形成中枢
        last_bi = c.bi_list[-1]
        zs = ZS(symbol=cat.symbol, bis=c.bi_list[-4:-1])
        # 最后一笔超过中枢最低点50不考虑
        if (last_bi.high - zs.dd) / zs.dd < 0.5:
            # 保证这个震荡长度够长
            if sum([x.length for x in c.bi_list[-4:-1]]) > last3Count \
                    or sum([x.length for x in c.bi_list[-7:-1]]) > last6Count:
                # 最后一根K线大于前n笔最高点
                if c.bars_raw[-1].close > max([x.high for x in c.bi_list[-7:-1]]):
                    # 中枢最高点是倒2到倒7的最高点，保证前面没有抛压
                    if zs.gg == max([x.high for x in c.bi_list[-7:-1]]) \
                            and (
                            max([x.high for x in c.bi_list[-7:-1]]) - min([x.high for x in c.bi_list[-7:-1]])) / min(
                        [x.high for x in c.bi_list[-7:-1]]) < 0.3:
                        continueJudgeSub = True

        if continueJudgeSub:
            last_sub_bi = sub_c.bi_list[-1]
            if last_sub_bi.direction == Direction.Down and last_sub_bi.high > zs.gg \
                    and last_sub_bi.low > zs.zg - (th / 100) * (zs.zg - zs.zd):
                v1 = "确认"

            # elif len(c.bi_list) > 13 and len(sub_c.bi_list) > 7:
            #     min7 = min([x.low for x in c.bi_list[-7:]])
            #     # 中枢成立，且中枢最低点不是最后7笔的最低点，且最后7笔最低点同时也是最后13笔最低点（保证低点起来第一个中枢）
            #     if zs.zd < zs.zg and zs.dd > min7 == min([x.low for x in c.bi_list[-13:]]):
            #         last_sub_bi = sub_c.bi_list[-1]
            #
            #         if last_sub_bi.direction == Direction.Down and last_sub_bi.high > zs.gg \
            #                 and last_sub_bi.low > zs.zg - (th / 100) * (zs.zg - zs.zd):
            #             v1 = "确认"

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1)
    s[signal.key] = signal.value
    return s


def cxt_zhong_shu_gong_zhen_V221221(cat: CzscSignals, freq1='日线', freq2='60分钟', **kwargs) -> OrderedDict:
    """大小级别中枢共振，类二买共振；贡献者：琅盎

    **信号逻辑：**

    1. 不区分上涨或下跌中枢
    2. 次级别中枢 DD 大于本级别中枢中轴
    3. 次级别向下笔出底分型开多；反之看空

    **信号列表：**

    - Signal('日线_60分钟_中枢共振_看多_任意_任意_0')
    - Signal('日线_60分钟_中枢共振_看空_任意_任意_0')

    :param cat:
    :param freq1:大级别周期
    :param freq2: 小级别周期
    :return: 信号识别结果
    """
    k1, k2, k3 = f"{freq1}_{freq2}_中枢共振".split('_')

    max_freq: CZSC = cat.kas[freq1]
    min_freq: CZSC = cat.kas[freq2]
    symbol = cat.symbol

    def __is_zs(_bis):
        _zs = ZS(symbol=symbol, bis=_bis)
        if _zs.zd < _zs.zg:
            return True
        else:
            return False

    v1 = "其他"
    if len(max_freq.bi_list) >= 5 and __is_zs(max_freq.bi_list[-3:]) \
            and len(min_freq.bi_list) >= 5 and __is_zs(min_freq.bi_list[-3:]):

        big_zs = ZS(symbol=symbol, bis=max_freq.bi_list[-3:])
        small_zs = ZS(symbol=symbol, bis=min_freq.bi_list[-3:])

        if small_zs.dd > big_zs.zz and min_freq.bi_list[-1].direction == Direction.Down:
            v1 = "看多"

        if small_zs.gg < big_zs.zz and min_freq.bi_list[-1].direction == Direction.Up:
            v1 = "看空"

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def cxt_bi_end_V230222(c: CZSC, **kwargs) -> OrderedDict:
    """当前是最后笔的第几次新低底分型或新高顶分型，用于笔结束辅助

    **信号逻辑：**

    1. 取最后笔及未成笔的分型，
    2. 当前如果是顶分型，则看当前顶分型是否新高，是第几个新高
    2. 当前如果是底分型，则看当前底分型是否新低，是第几个新低

    **信号列表：**

    - Signal('15分钟_D1MO3_结束辅助_新低_第1次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第2次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第1次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第2次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第3次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第4次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第3次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第4次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第5次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第5次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第6次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第6次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新高_第7次_任意_0')
    - Signal('15分钟_D1MO3_结束辅助_新低_第7次_任意_0')

    :param c: CZSC对象
    :param kwargs:
    :return: 信号识别结果
    """
    max_overlap = int(kwargs.get('max_overlap', 3))
    k1, k2, k3 = f"{c.freq.value}_D1MO{max_overlap}_结束辅助".split('_')
    v1 = '其他'
    v2 = '其他'

    if not c.ubi_fxs:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)

    # 为了只取最后一笔以来的分型，没有用底层fx_list
    fxs = []
    if c.bi_list:
        fxs.extend(c.bi_list[-1].fxs[1:])
    ubi_fxs = c.ubi_fxs
    for x in ubi_fxs:
        if not fxs or x.dt > fxs[-1].dt:
            fxs.append(x)

    # 出分型那刻出信号，或者分型和最后一根bar相差 max_overlap 根K线时间内
    if (fxs[-1].elements[-1].dt == c.bars_ubi[-1].dt) or (c.bars_raw[-1].id - fxs[-1].raw_bars[-1].id <= max_overlap):
        if fxs[-1].mark == Mark.G:
            up = [x for x in fxs if x.mark == Mark.G]
            high_max = float('-inf')
            cnt = 0
            for fx in up:
                if fx.high > high_max:
                    cnt += 1
                    high_max = fx.high
            if fxs[-1].high == high_max:
                v1 = '新高'
                v2 = cnt

        else:
            down = [x for x in fxs if x.mark == Mark.D]
            low_min = float('inf')
            cnt = 0
            for fx in down:
                if fx.low < low_min:
                    cnt += 1
                    low_min = fx.low
            if fxs[-1].low == low_min:
                v1 = '新低'
                v2 = cnt

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=f"第{v2}次")


def cxt_bi_end_V230224(c: CZSC, **kwargs):
    """量价配合的笔结束辅助

    **信号逻辑：**

    1. 向下笔结束：fx_b 内最低的那根K线下影大于上影的两倍，同时fx_b内的平均成交量小于当前笔的平均成交量的0.618
    2. 向上笔结束：fx_b 内最高的那根K线上影大于下影的两倍，同时fx_b内的平均成交量大于当前笔的平均成交量的2倍

    **信号列表：**

    - Signal('15分钟_D1MO3_笔结束V230224_看多_任意_任意_0')
    - Signal('15分钟_D1MO3_笔结束V230224_看空_任意_任意_0')

    :param c: CZSC 对象
    :return: 信号字典
    """
    max_overlap = int(kwargs.get('max_overlap', 3))
    k1, k2, k3 = f"{c.freq.value}_D1MO{max_overlap}_笔结束V230224".split('_')
    v1 = '其他'
    if len(c.bi_list) <= 3:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)

    last_bi = c.bi_list[-1]
    bi_bars = last_bi.raw_bars
    bi_vol_mean = np.mean([x.vol for x in bi_bars])
    fx_bars = last_bi.fx_b.raw_bars
    fx_vol_mean = np.mean([x.vol for x in fx_bars])

    bar1 = fx_bars[np.argmin([x.low for x in fx_bars])]
    bar2 = fx_bars[np.argmax([x.high for x in fx_bars])]

    if bar1.upper > bar1.lower * 2 and fx_vol_mean > bi_vol_mean * 2:
        v1 = '看空'
    elif 2 * bar2.upper < bar2.lower and fx_vol_mean < bi_vol_mean * 0.618:
        v1 = '看多'
    else:
        v1 = '其他'

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


def cxt_third_buy_V230228(c: CZSC, di=1, **kwargs) -> OrderedDict:
    """笔三买辅助

    **信号逻辑：**

    1. 定义大于前一个向上笔的高点的笔为向上突破笔，最近所有向上突破笔有价格重叠
    2. 当下笔的最低点在任一向上突破笔的高点上，且当下笔的最低点离笔序列最低点的距离不超过向上突破笔列表均值的1.618倍

    **信号列表：**

    - Signal('15分钟_D1三买辅助_V230228_三买_14笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_10笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_6笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_8笔_任意_0')
    - Signal('15分钟_D1三买辅助_V230228_三买_12笔_任意_0')

    :param c: CZSC对象
    :param di: 倒数第几笔
    :param kwargs:
    :return: 信号识别结果
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}三买辅助_V230228".split('_')
    v1, v2 = '其他', '其他'
    if len(c.bi_list) < di + 11:
        return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)

    def check_third_buy(bis):
        """检查 bis 是否是三买的结束

        :param bis: 笔序列，按时间升序
        :return:
        """
        res = {"match": False, "v1": "三买", "v2": f"{len(bis)}笔", 'v3': "任意"}
        if bis[-1].direction == Direction.Up or bis[0].direction == bis[-1].direction:
            return res

        # 检查三买：获取向上突破的笔列表
        key_bis = []
        for i in range(0, len(bis) - 2, 2):
            if i == 0:
                key_bis.append(bis[i])
            else:
                b1, _, b3 = bis[i - 2:i + 1]
                if b3.high > b1.high:
                    key_bis.append(b3)
        if len(key_bis) < 2:
            return res

        tb_break = bis[-1].low > min([x.high for x in key_bis]) > max([x.low for x in key_bis])
        tb_price = bis[-1].low < min([x.low for x in bis]) + 1.618 * np.mean([x.power_price for x in key_bis])

        if tb_break and tb_price:
            res['match'] = True
        return res

    for n in (13, 11, 9, 7, 5):
        _bis = get_sub_elements(c.bi_list, di=di, n=n + 1)
        if len(_bis) != n + 1:
            continue

        _res = check_third_buy(_bis)
        if _res['match']:
            v1 = _res['v1']
            v2 = _res['v2']
            break

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2)


def cxt_double_zs_V230311(c: CZSC, di=1, **kwargs):
    """两个中枢组合辅助判断BS1

    **信号逻辑：**

    1. 最后一笔向下，最近两个中枢依次向下，最后一个中枢的倒数第一笔的K线长度大于倒数第二笔的K线长度，看多；
    2. 最后一笔向上，最近两个中枢依次向上，最后一个中枢的倒数第一笔的K线长度大于倒数第二笔的K线长度，看空；

    **信号列表：**

    - Signal('15分钟_D1双中枢_BS1辅助V230311_看多_任意_任意_0')
    - Signal('15分钟_D1双中枢_BS1辅助V230311_看空_任意_任意_0')

    :param c: CZSC对象
    :param di: 倒数第 di 笔
    :return: s
    """
    k1, k2, k3 = f"{c.freq.value}_D{di}双中枢_BS1辅助V230311".split("_")
    v1 = "其他"

    bis: List[BI] = get_sub_elements(c.bi_list, di=di, n=20)
    zss = get_zs_seq(bis)

    if len(zss) >= 2 and len(zss[-2].bis) >= 2 and len(zss[-1].bis) >= 2:
        zs1, zs2 = zss[-2], zss[-1]

        ts1 = len(zs2.bis[-1].bars)
        ts2 = len(zs2.bis[-2].bars)

        if bis[-1].direction == Direction.Down and ts1 >= ts2 * 2 and zs1.gg > zs2.gg:
            v1 = "看多"

        if bis[-1].direction == Direction.Up and ts1 >= ts2 * 2 and zs1.dd < zs2.dd:
            v1 = "看空"

    return create_single_signal(k1=k1, k2=k2, k3=k3, v1=v1)


class BXT:
    """缠论笔形态识别基础类"""

    def __init__(self, bis: List[BI]):
        self.bis = bis
        self.xt_map = {
            '标准趋势': self.aAbBc,
            '类趋势': self.abcde,
            'aAb式盘整': self.aAb,
            'aAbcd式盘整': self.aAbcd,
            'abcAd式盘整': self.abcAd,
            'ABC式盘整': self.ABC,
            'BS2': self.BS2,
            'BS3': self.BS3,
        }

    @staticmethod
    def is_aAbBc(bis):
        """标准趋势"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}

        if len(bis) >= 11:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11 = bis[-11:]
            max_high = max([x.high for x in bis[-11:]])
            min_low = min([x.low for x in bis[-11:]])

            # 十一笔（2~4构成中枢A，8~10构成中枢B）
            if bi11.direction == Direction.Down and max_high == bi1.high and min_low == bi11.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and is_bis_down([bi5, bi6, bi7]) \
                    and min(bi2.low, bi4.low) > max(bi8.high, bi10.high) \
                    and min(bi8.high, bi10.high) > max(bi8.low, bi10.low):
                res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A3B3"}
                return res

            if bi11.direction == Direction.Up and max_high == bi11.high and min_low == bi1.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and is_bis_up([bi5, bi6, bi7]) \
                    and max(bi2.high, bi4.high) < min(bi8.low, bi10.low) \
                    and min(bi8.high, bi10.high) > max(bi8.low, bi10.low):
                res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A3B3"}
                return res

            # 十一笔（2~4构成中枢A，6~10构成中枢B）
            if bi11.direction == Direction.Down and max_high == bi1.high and min_low == bi11.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and min(bi2.low, bi4.low) > max(bi6.high, bi8.high, bi10.high) \
                    and min(bi6.high, bi8.high, bi10.high) > max(bi6.low, bi8.low, bi10.low):
                res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A3B5"}
                return res

            if bi11.direction == Direction.Up and max_high == bi11.high and min_low == bi1.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and max(bi2.high, bi4.high) < min(bi6.low, bi8.low, bi10.low) \
                    and min(bi6.high, bi8.high, bi10.high) > max(bi6.low, bi8.low, bi10.low):
                res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A3B5"}
                return res

            # 十一笔（2~6构成中枢A，8~10构成中枢B）
            if bi11.direction == Direction.Down and max_high == bi1.high and min_low == bi11.low \
                    and min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) \
                    and min(bi2.low, bi4.low, bi6.low) > max(bi8.high, bi10.high) \
                    and min(bi8.high, bi10.high) > max(bi8.low, bi10.low):
                res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A5B3"}
                return res

            if bi11.direction == Direction.Up and max_high == bi11.high and min_low == bi1.low \
                    and min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low) \
                    and max(bi2.high, bi4.high, bi6.high) < min(bi8.low, bi10.low) \
                    and min(bi8.high, bi10.high) > max(bi8.low, bi10.low):
                res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A5B3"}
                return res

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            max_high = max([x.high for x in bis[-9:]])
            min_low = min([x.low for x in bis[-9:]])

            # 九笔（2~4构成中枢A，6~8构成中枢B）
            if bi9.direction == Direction.Down and max_high == bi1.high and min_low == bi9.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and min(bi2.low, bi4.low) > max(bi6.high, bi8.high) \
                    and min(bi6.high, bi8.high) > max(bi6.low, bi8.low):
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "A3B3"}
                return res

            if bi9.direction == Direction.Up and max_high == bi9.high and min_low == bi1.low \
                    and min(bi2.high, bi4.high) > max(bi2.low, bi4.low) \
                    and max(bi2.high, bi4.high) < min(bi6.low, bi8.low) \
                    and min(bi6.high, bi8.high) > max(bi6.low, bi8.low):
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "A3B3"}
                return res

        return res

    @property
    def aAbBc(self):
        """标准趋势"""
        return self.is_aAbBc(self.bis)

    @staticmethod
    def is_abcde(bis):
        """类趋势"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}
        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]

            if bi9.direction == Direction.Down and is_bis_down(bis[-9:]) \
                    and bi2.low > bi4.high and bi4.low > bi6.high and bi6.low > bi8.high:
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "任意"}
                return res

            if bi9.direction == Direction.Up and is_bis_up(bis[-9:]) \
                    and bi8.low > bi6.high and bi6.low > bi4.high and bi4.low > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "任意"}
                return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]

            if bi7.direction == Direction.Down and is_bis_down(bis[-7:]) \
                    and bi2.low > bi4.high and bi4.low > bi6.high:
                res = {'match': True, 'v1': "向下", 'v2': "7笔", 'v3': "任意"}
                return res

            if bi7.direction == Direction.Up and is_bis_up(bis[-7:]) \
                    and bi6.low > bi4.high and bi4.low > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "7笔", 'v3': "任意"}
                return res

        if len(bis) >= 5:
            bi1, bi2, bi3, bi4, bi5 = bis[-5:]

            if bi5.direction == Direction.Down and is_bis_down(bis[-5:]) \
                    and bi2.low > bi4.high:
                res = {'match': True, 'v1': "向下", 'v2': "5笔", 'v3': "任意"}
                return res

            if bi5.direction == Direction.Up and is_bis_up(bis[-5:]) \
                    and bi4.low > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "5笔", 'v3': "任意"}
                return res

        return res

    @property
    def abcde(self):
        """类趋势"""
        return self.is_abcde(self.bis)

    @staticmethod
    def is_aAb(bis):
        """aAb式盘整"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}
        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            max_high = max([x.high for x in bis[-9:]])
            min_low = min([x.low for x in bis[-9:]])

            if bi9.direction == Direction.Down and max_high == bi1.high and bi9.low == min_low \
                    and min(bi2.high, bi4.high, bi6.high, bi8.high) > max(bi2.low, bi4.low, bi6.low, bi8.low):
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "任意"}
                return res

            if bi9.direction == Direction.Up and max_high == bi9.high and bi1.low == min_low \
                    and min(bi2.high, bi4.high, bi6.high, bi8.high) > max(bi2.low, bi4.low, bi6.low, bi8.low):
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "任意"}
                return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]
            max_high = max([x.high for x in bis[-7:]])
            min_low = min([x.low for x in bis[-7:]])

            if bi7.direction == Direction.Down and max_high == bi1.high and bi7.low == min_low \
                    and min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low):
                res = {'match': True, 'v1': "向下", 'v2': "7笔", 'v3': "任意"}
                return res

            if bi7.direction == Direction.Up and max_high == bi7.high and bi1.low == min_low \
                    and min(bi2.high, bi4.high, bi6.high) > max(bi2.low, bi4.low, bi6.low):
                res = {'match': True, 'v1': "向上", 'v2': "7笔", 'v3': "任意"}
                return res

        if len(bis) >= 5:
            bi1, bi2, bi3, bi4, bi5 = bis[-5:]
            max_high = max([x.high for x in bis[-5:]])
            min_low = min([x.low for x in bis[-5:]])

            if bi5.direction == Direction.Down and max_high == bi1.high and bi5.low == min_low \
                    and bi2.low < bi4.high:
                res = {'match': True, 'v1': "向下", 'v2': "5笔", 'v3': "任意"}
                return res

            if bi5.direction == Direction.Up and max_high == bi5.high and bi1.low == min_low \
                    and bi4.low < bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "5笔", 'v3': "任意"}
                return res

        return res

    @property
    def aAb(self):
        """aAb式盘整"""
        return self.is_aAb(self.bis)

    @staticmethod
    def is_aAbcd(bis):
        """aAbcd式盘整"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}

        if len(bis) >= 11:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11 = bis[-11:]
            max_high = max([x.high for x in bis[-11:]])
            min_low = min([x.low for x in bis[-11:]])

            gg = max(bi2.high, bi4.high, bi6.high, bi8.high)
            zg = min(bi2.high, bi4.high, bi6.high, bi8.high)
            zd = max(bi2.low, bi4.low, bi6.low, bi8.low)
            dd = min(bi2.low, bi4.low, bi6.low, bi8.low)

            if bi11.direction == Direction.Down and max_high == bi1.high and bi11.low == min_low \
                    and zg >= zd >= dd > bi10.high:
                res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "任意"}
                return res

            if bi11.direction == Direction.Up and max_high == bi11.high and bi1.low == min_low \
                    and bi10.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "任意"}
                return res

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            max_high = max([x.high for x in bis[-9:]])
            min_low = min([x.low for x in bis[-9:]])

            gg = max(bi2.high, bi4.high, bi6.high)
            zg = min(bi2.high, bi4.high, bi6.high)
            zd = max(bi2.low, bi4.low, bi6.low)
            dd = min(bi2.low, bi4.low, bi6.low)

            if bi9.direction == Direction.Down and max_high == bi1.high and bi9.low == min_low \
                    and zg >= zd >= dd > bi8.high:
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "任意"}
                return res

            if bi9.direction == Direction.Up and max_high == bi9.high and bi1.low == min_low \
                    and bi8.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "任意"}
                return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]
            max_high = max([x.high for x in bis[-7:]])
            min_low = min([x.low for x in bis[-7:]])

            gg = max(bi2.high, bi4.high)
            zg = min(bi2.high, bi4.high)
            zd = max(bi2.low, bi4.low)
            dd = min(bi2.low, bi4.low)

            if bi7.direction == Direction.Down and max_high == bi1.high and bi7.low == min_low \
                    and zg >= zd >= dd > bi6.high:
                res = {'match': True, 'v1': "向下", 'v2': "7笔", 'v3': "任意"}
                return res

            if bi7.direction == Direction.Up and max_high == bi7.high and bi1.low == min_low \
                    and bi6.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向上", 'v2': "7笔", 'v3': "任意"}
                return res

        return res

    @property
    def aAbcd(self):
        """aAbcd式盘整"""
        return self.is_aAbcd(self.bis)

    @staticmethod
    def is_abcAd(bis):
        """abcAd式盘整"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}
        if len(bis) >= 11:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11 = bis[-11:]
            max_high = max([x.high for x in bis[-11:]])
            min_low = min([x.low for x in bis[-11:]])

            gg = max(bi4.high, bi6.high, bi8.high, bi10.high)
            zg = min(bi4.high, bi6.high, bi8.high, bi10.high)
            zd = max(bi4.low, bi6.low, bi8.low, bi10.low)
            dd = min(bi4.low, bi6.low, bi8.low, bi10.low)

            if bi11.direction == Direction.Down and max_high == bi1.high and bi11.low == min_low \
                    and bi2.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "任意"}
                return res

            if bi11.direction == Direction.Up and max_high == bi11.high and bi1.low == min_low \
                    and zg >= zd >= dd > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "任意"}
                return res

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            max_high = max([x.high for x in bis[-9:]])
            min_low = min([x.low for x in bis[-9:]])

            gg = max(bi4.high, bi6.high, bi8.high)
            zg = min(bi4.high, bi6.high, bi8.high)
            zd = max(bi4.low, bi6.low, bi8.low)
            dd = min(bi4.low, bi6.low, bi8.low)

            if bi9.direction == Direction.Down and max_high == bi1.high and bi9.low == min_low \
                    and bi2.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "任意"}
                return res

            if bi9.direction == Direction.Up and max_high == bi9.high and bi1.low == min_low \
                    and zg >= zd >= dd > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "任意"}
                return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]
            max_high = max([x.high for x in bis[-7:]])
            min_low = min([x.low for x in bis[-7:]])

            gg = max(bi4.high, bi6.high)
            zg = min(bi4.high, bi6.high)
            zd = max(bi4.low, bi6.low)
            dd = min(bi4.low, bi6.low)

            if bi7.direction == Direction.Down and max_high == bi1.high and bi7.low == min_low \
                    and bi2.low > gg >= zg >= zd:
                res = {'match': True, 'v1': "向下", 'v2': "7笔", 'v3': "任意"}
                return res

            if bi7.direction == Direction.Up and max_high == bi7.high and bi1.low == min_low \
                    and zg >= zd >= dd > bi2.high:
                res = {'match': True, 'v1': "向上", 'v2': "7笔", 'v3': "任意"}
                return res

        return res

    @property
    def abcAd(self):
        """abcAd式盘整"""
        return self.is_abcAd(self.bis)

    @staticmethod
    def is_ABC(bis):
        """ABC式盘整"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}

        if len(bis) >= 11:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9, bi10, bi11 = bis[-11:]
            max_high = max([x.high for x in bis[-11:]])
            min_low = min([x.low for x in bis[-11:]])

            if bi11.direction == Direction.Down and max_high == bi1.high and bi11.low == min_low:
                # A3B5C3
                if is_bis_down([bi1, bi2, bi3]) and is_bis_down([bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A3B5C3"}
                    return res

                # A5B3C3
                if is_bis_down([bi1, bi2, bi3, bi4, bi5]) and is_bis_down([bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A5B3C3"}
                    return res

                # A3B3C5
                if is_bis_down([bi1, bi2, bi3]) and is_bis_down([bi7, bi8, bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向下", 'v2': "11笔", 'v3': "A3B3C5"}
                    return res

            if bi11.direction == Direction.Up and max_high == bi11.high and bi1.low == min_low:
                # A3B5C3
                if is_bis_up([bi1, bi2, bi3]) and is_bis_up([bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A3B5C3"}
                    return res

                # A5B3C3
                if is_bis_up([bi1, bi2, bi3, bi4, bi5]) and is_bis_up([bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A5B3C3"}
                    return res

                # A3B3C5
                if is_bis_up([bi1, bi2, bi3]) and is_bis_up([bi7, bi8, bi9, bi10, bi11]):
                    res = {'match': True, 'v1': "向上", 'v2': "11笔", 'v3': "A3B3C5"}
                    return res

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            max_high = max([x.high for x in bis[-9:]])
            min_low = min([x.low for x in bis[-9:]])

            if bi9.direction == Direction.Down and max_high == bi1.high and bi9.low == min_low \
                    and is_bis_down([bi1, bi2, bi3]) and is_bis_down([bi7, bi8, bi9]):
                res = {'match': True, 'v1': "向下", 'v2': "9笔", 'v3': "任意"}
                return res

            if bi9.direction == Direction.Up and max_high == bi9.high and bi1.low == min_low \
                    and is_bis_up([bi1, bi2, bi3]) and is_bis_up([bi7, bi8, bi9]):
                res = {'match': True, 'v1': "向上", 'v2': "9笔", 'v3': "任意"}
                return res

        return res

    @property
    def ABC(self):
        """ABC式盘整"""
        return self.is_ABC(self.bis)

    @staticmethod
    def is_BS2(bis):
        """BS2"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            gg = max([bi2.high, bi4.high])
            zg = min([bi2.high, bi4.high])
            zd = max([bi2.low, bi4.low])
            dd = min([bi2.low, bi4.low])

            if bi9.direction == Direction.Down and is_bis_down([bi1, bi2, bi3, bi4, bi5]):
                if gg > bi9.low >= zg:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右4", 'v3': "24上沿"}
                    return res

                if zg > bi9.low >= zd:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右4", 'v3': "24内部"}
                    return res

                if zd > bi9.low >= dd:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右4", 'v3': "24下沿"}
                    return res

            if bi9.direction == Direction.Up and is_bis_up([bi1, bi2, bi3, bi4, bi5]):
                if gg > bi9.high >= zg:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右4", 'v3': "24上沿"}
                    return res

                if zg > bi9.high >= zd:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右4", 'v3': "24内部"}
                    return res

                if zd > bi9.high >= dd:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右4", 'v3': "24下沿"}
                    return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]
            gg = max([bi2.high, bi4.high])
            zg = min([bi2.high, bi4.high])
            zd = max([bi2.low, bi4.low])
            dd = min([bi2.low, bi4.low])

            if bi7.direction == Direction.Down and is_bis_down([bi1, bi2, bi3, bi4, bi5]):
                if gg > bi7.low >= zg:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右2", 'v3': "24上沿"}
                    return res

                if zg > bi7.low >= zd:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右2", 'v3': "24内部"}
                    return res

                if zd > bi7.low >= dd:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右2", 'v3': "24下沿"}
                    return res

            if bi7.direction == Direction.Up and is_bis_up([bi1, bi2, bi3, bi4, bi5]):
                if gg > bi7.high >= zg:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右2", 'v3': "24上沿"}
                    return res

                if zg > bi7.high >= zd:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右2", 'v3': "24内部"}
                    return res

                if zd > bi7.high >= dd:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右2", 'v3': "24下沿"}
                    return res

        if len(bis) >= 5:
            bi1, bi2, bi3, bi4, bi5 = bis[-5:]
            if bi5.direction == Direction.Down and is_bis_down([bi1, bi2, bi3]):
                if bi2.high > bi5.low > bi2.low:
                    res = {'match': True, 'v1': "向下", 'v2': "左3右2", 'v3': "笔2内部"}
                    return res

                if bi5.high > bi3.high > bi5.low > bi3.low:
                    res = {'match': True, 'v1': "向下", 'v2': "左3右2", 'v3': "笔3内部"}
                    return res

            if bi5.direction == Direction.Up and is_bis_up([bi1, bi2, bi3]):
                if bi2.high > bi5.high > bi2.low:
                    res = {'match': True, 'v1': "向上", 'v2': "左3右2", 'v3': "笔2内部"}
                    return res

                if bi5.high < bi3.high and bi5.low < bi3.low:
                    res = {'match': True, 'v1': "向上", 'v2': "左3右2", 'v3': "笔3内部"}
                    return res

        return res

    @property
    def BS2(self):
        return self.is_BS2(self.bis)

    @staticmethod
    def is_BS3(bis):
        """BS3"""
        # res 定义返回值标准
        res = {'match': False, 'v1': "任意", 'v2': "任意", 'v3': "任意"}

        if len(bis) >= 9:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7, bi8, bi9 = bis[-9:]
            gg = max([bi2.high, bi4.high])
            dd = min([bi2.low, bi4.low])

            if bi9.direction == Direction.Down and is_bis_down([bi1, bi2, bi3, bi4, bi5]):
                if bi7.low < gg < bi9.low:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右4", 'v3': "24上沿"}
                    return res

            if bi9.direction == Direction.Up and is_bis_up([bi1, bi2, bi3, bi4, bi5]):
                if bi9.high < dd < bi7.high:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右4", 'v3': "24下沿"}
                    return res

        if len(bis) >= 7:
            bi1, bi2, bi3, bi4, bi5, bi6, bi7 = bis[-7:]
            gg = max([bi2.high, bi4.high])
            dd = min([bi2.low, bi4.low])

            if bi7.direction == Direction.Down and is_bis_down([bi1, bi2, bi3, bi4, bi5]):
                if bi7.low > gg:
                    res = {'match': True, 'v1': "向下", 'v2': "左5右2", 'v3': "24上沿"}
                    return res

            if bi7.direction == Direction.Up and is_bis_up([bi1, bi2, bi3, bi4, bi5]):
                if bi7.high < dd:
                    res = {'match': True, 'v1': "向上", 'v2': "左5右2", 'v3': "24下沿"}
                    return res

        if len(bis) >= 5:
            bi1, bi2, bi3, bi4, bi5 = bis[-5:]
            if bi5.direction == Direction.Down and is_bis_down([bi1, bi2, bi3]):
                if bi5.low > max(bi1.high, bi3.high):
                    res = {'match': True, 'v1': "向下", 'v2': "左3右2", 'v3': "任意"}
                    return res

            if bi5.direction == Direction.Up and is_bis_up([bi1, bi2, bi3]):
                if bi5.high < min(bi1.low, bi3.low):
                    res = {'match': True, 'v1': "向上", 'v2': "左3右2", 'v3': "任意"}
                    return res
        return res

    @property
    def BS3(self):
        return self.is_BS3(self.bis)


def cxt_vg_threeBuy(cat: CzscSignals, freq='日线', sub_freq='30分钟', th=38.2) -> OrderedDict:
    # 默认最后3笔的长度是40天
    k1, k2, k3 = f"{freq}_{sub_freq}_vg三买".split('_')
    # Signal('日线_30分钟_vg三买_确认_38.2_10_0')
    # 确认_{回调幅度相对于倒数第二笔}_{最后一笔天数}_震荡天数_倒数第二笔上攻涨幅
    c: CZSC = cat.kas[freq]
    # sub_c: CZSC = cat.kas[sub_freq]

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    # 最后一笔方向向下
    if len(c.bi_list) > 7 and (c.bi_list[-1].direction == Direction.Down):
        continueJudgeSub = False
        # 倒5至倒3形成中枢
        last_bi = c.bi_list[-1]
        zs = ZS(symbol=cat.symbol, bis=c.bi_list[-5:-2])
        # 倒数第一笔最低比中枢最高点高
        biCount = sum([x.length for x in c.bi_list[-5:-2]])
        if last_bi.low > zs.gg:
            # 从倒数第六根开始往前推震荡区间，假设往前推笔，最高点不高于倒1的最低，最低点低于zs的10%，就算震荡
            index = 0
            for i in reversed(c.bi_list[0:-5]):
                thisB = i
                if thisB.high > last_bi.low:
                    break
                if index % 2 == 0:
                    if thisB.low > zs.zg:
                        break
                else:
                    if thisB.high < zs.zd:
                        break
                index += 1
                # 加上这一笔的长度
                biCount = biCount + thisB.length
            v1 = "确认"
            v2 = str((c.bi_list[-2].high - last_bi.low) / (c.bi_list[-2].high - c.bi_list[-2].low))
            v3 = str(last_bi.length) + "_" + str(biCount)
            score = (c.bi_list[-2].high - c.bi_list[-2].low) / c.bi_list[-2].low

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s


def cxt_vg_threeBuyConfirm(cat: CzscSignals, freq='日线', sub_freq='30分钟', th=38.2) -> OrderedDict:
    # 默认最后3笔的长度是40天
    k1, k2, k3 = f"{freq}_{sub_freq}_vg三买确认".split('_')
    # Signal('日线_30分钟_vg三买确认_确认_38.2_10_0')
    # 确认_{回调幅度相对于倒数第二笔}_{最后一笔天数}_震荡天数_倒数第二笔上攻涨幅
    c: CZSC = cat.kas[freq]
    # sub_c: CZSC = cat.kas[sub_freq]

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    # 最后一笔方向向下
    if len(c.bi_list) > 7 and (c.bi_list[-1].direction == Direction.Down) and (
            c.bi_list[-1].low > c.bi_list[-3].low > c.bi_list[5].high) and (c.bi_list[-3].high > c.bi_list[-1].high):
        #判断均线
        shouldContinue = True
        close = np.array([x.close for x in c.bars_raw[-70:]])
        for n in [5, 10, 20, 30, 60]:
            sma = SMA(close, timeperiod=n)
            if close[-1] < sma[-1]:
                shouldContinue = False

        if shouldContinue:
            # 倒7至倒5形成中枢
            last_bi = c.bi_list[-1]
            zs = ZS(symbol=cat.symbol, bis=c.bi_list[-7:-4])
            zs2 = ZS(symbol=cat.symbol, bis=c.bi_list[-3:])
            # 倒数第一笔最低比中枢最高点高
            biCount = sum([x.length for x in c.bi_list[-7:-4]])
            if zs2.dd > zs.gg:
                index = 0
                for thisB in reversed(c.bi_list[0:-7]):
                    if thisB.high > last_bi.low:
                        break
                    if index % 2 == 0:
                        if thisB.low > zs.zg:
                            break
                    else:
                        if thisB.high < zs.zd:
                            break
                    # 加上这一笔的长度
                    biCount = biCount + thisB.length
                    index += 1
                v1 = "确认"
                v2 = str((c.bi_list[-4].high - min(c.bi_list[-2].low, c.bi_list[-1].low)) / (
                        c.bi_list[-4].high - c.bi_list[-4].low))
                v3 = str(c.bi_list[-1].length + c.bi_list[-2].length + c.bi_list[-3].length) + "_" + str(biCount)
                score = (c.bi_list[-4].high - c.bi_list[-4].low) / c.bi_list[-4].low

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s


def cxt_vg_oneBuy(cat: CzscSignals, freq='日线') -> OrderedDict:
    def isValidZS(bis, zs) -> bool:
        for ind in range(3, len(bis)):
            oneBi = bis[ind]
            if ind % 2 == 0:
                if oneBi.high < zs.zd:
                    return False
            else:
                if oneBi.low > zs.zg:
                    return False
        return True

    c: CZSC = cat.kas[freq]
    k1, k2, k3 = f"{freq}_任意_vg一买".split('_')

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    s = OrderedDict()

    biCount = len(c.bi_list)
    if biCount < 9:
        defaultSignal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
        s[defaultSignal.key] = defaultSignal.value
        return s

    if (biCount % 2) == 0:
        calculateBiList = c.bi_list[-(biCount - 1):]
    else:
        calculateBiList = c.bi_list

    # 9~count笔，步长为2
    for biCountPossible in range(9, len(calculateBiList) + 1, 2):
        calculateBiListPossible = calculateBiList[-biCountPossible:]
        if calculateBiListPossible[-1].direction == Direction.Up:
            continue
        # 标准数 1-x-1-x-1，x最小3
        standardZSCount = int((len(calculateBiListPossible) - 3) / 2)
        max_high = max([x.high for x in calculateBiListPossible])
        min_low = min([x.low for x in calculateBiListPossible])
        minus = standardZSCount - 3
        # 第一笔最高是最高，倒一笔最低是最低
        if max_high == calculateBiListPossible[0].high and min_low == calculateBiListPossible[-1].low:
            for oneCount in range(3, 2 * standardZSCount - 2):
                zs1Bis = calculateBiListPossible[1:1 + oneCount]
                zs2Bis = calculateBiListPossible[-(len(calculateBiListPossible) - 3 - oneCount + 1):-1]
                zs1_min_low = min([x.low for x in zs1Bis])
                zs2_max_high = max([x.high for x in zs2Bis])
                # 保证中枢1高于中枢2
                if zs1_min_low <= zs2_max_high:
                    continue
                # 保证中枢1和中枢2是合理的
                zs1 = ZS(symbol=c.symbol, bis=zs1Bis[0:3])
                zs2 = ZS(symbol=c.symbol, bis=zs2Bis[0:3])
                if isValidZS(zs1Bis, zs1) and isValidZS(zs2Bis, zs2):
                    v1 = "确认"
                    v2 = f"{str(len(zs1Bis))}-{str(len(zs2Bis))}"  # 第一个中枢多少笔-第二个中枢多少笔
                    # ss = 1+len(zs2Bis)+1
                    v3 = f"{calculateBiListPossible[-(1 + len(zs2Bis) + 1)].power}-{calculateBiListPossible[-1].power}"  # 第一个中枢过渡笔力度-第二个中枢过渡笔力度
    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s


def cxt_vg_fakeOneBuy(cat: CzscSignals, freq='日线') -> OrderedDict:
    def isValidZS(bis, zs) -> bool:
        for ind in range(3, len(bis)):
            oneBi = bis[ind]
            if ind % 2 == 0:
                if oneBi.high < zs.zd:
                    return False
            else:
                if oneBi.low > zs.zg:
                    return False
        return True

    c: CZSC = cat.kas[freq]
    k1, k2, k3 = f"{freq}_任意_vg潜在一买".split('_')

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    s = OrderedDict()

    biCount = len(c.bi_list)
    if biCount < 8 or c.finished_bis[-1].direction == Direction.Down:
        defaultSignal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
        s[defaultSignal.key] = defaultSignal.value
        return s

    tmp_list = copy.deepcopy(c.bi_list)
    fake_bi = FakeBI(symbol=c.symbol, sdt=c.bars_ubi[1].dt, edt=c.bars_ubi[-1].dt, direction=Direction.Down,
                     high=c.bars_ubi[1].high, low=c.bars_ubi[-1].low,
                     power=round(c.bars_ubi[1].high - c.bars_ubi[-1].low, 2))
    tmp_list.append(fake_bi)

    if (biCount % 2) == 0:
        calculateBiList = tmp_list[-(biCount - 1):]
    else:
        calculateBiList = tmp_list

    # 9~count笔，步长为2
    for biCountPossible in range(9, len(calculateBiList) + 1, 2):
        calculateBiListPossible = calculateBiList[-biCountPossible:]
        if calculateBiListPossible[-1].direction == Direction.Up:
            continue
        # 标准数 1-x-1-x-1，x最小3
        standardZSCount = int((len(calculateBiListPossible) - 3) / 2)
        max_high = max([x.high for x in calculateBiListPossible])
        min_low = min([x.low for x in calculateBiListPossible])
        minus = standardZSCount - 3
        # 第一笔最高是最高，倒一笔最低是最低
        if max_high == calculateBiListPossible[0].high and min_low == calculateBiListPossible[-1].low:
            for oneCount in range(3, 2 * standardZSCount - 2):
                zs1Bis = calculateBiListPossible[1:1 + oneCount]
                zs2Bis = calculateBiListPossible[-(len(calculateBiListPossible) - 3 - oneCount + 1):-1]
                zs1_min_low = min([x.low for x in zs1Bis])
                zs2_max_high = max([x.high for x in zs2Bis])
                # 保证中枢1高于中枢2
                if zs1_min_low <= zs2_max_high:
                    continue
                # 保证中枢1和中枢2是合理的
                zs1 = ZS(symbol=c.symbol, bis=zs1Bis[0:3])
                zs2 = ZS(symbol=c.symbol, bis=zs2Bis[0:3])
                if isValidZS(zs1Bis, zs1) and isValidZS(zs2Bis, zs2):
                    v1 = "确认"
                    v2 = f"{str(len(zs1Bis))}-{str(len(zs2Bis))}"  # 第一个中枢多少笔-第二个中枢多少笔
                    # ss = 1+len(zs2Bis)+1
                    v3 = f"{calculateBiListPossible[-(1 + len(zs2Bis) + 1)].power}-{calculateBiListPossible[-1].power}"  # 第一个中枢过渡笔力度-第二个中枢过渡笔力度
    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s


def cxt_vg_easyOneBuy(cat: CzscSignals, freq='日线') -> OrderedDict:
    c: CZSC = cat.kas[freq]
    k1, k2, k3 = f"{freq}_任意_vg简单一买".split('_')

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    s = OrderedDict()

    biCount = len(c.bi_list)
    if biCount < 4:
        defaultSignal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
        s[defaultSignal.key] = defaultSignal.value
        return s

    # 最后一笔方向向下
    if len(c.bi_list) > 3 and (c.bi_list[-1].direction == Direction.Down):
        continueJudgeSub = False
        # 倒5至倒3形成中枢
        last_bi = c.bi_list[-1]
        zs = ZS(symbol=cat.symbol, bis=c.bi_list[-4:-1])
        # 倒数第一笔最低比中枢最低点低
        biCount = sum([x.length for x in c.bi_list[-4:-1]])
        if last_bi.low < zs.dd:
            index = 0
            for i in reversed(c.bi_list[0:-4]):
                thisB = i
                if thisB.low < last_bi.low:
                    break
                if index % 2 == 0:
                    if thisB.high < zs.zd:
                        break
                else:
                    if thisB.low > zs.zg:
                        break
                index += 1
                # 加上这一笔的长度
                biCount = biCount + thisB.length
            v1 = "确认"
            v2 = str((c.bi_list[-2].high - last_bi.low) / (c.bi_list[-2].high - c.bi_list[-2].low))
            v3 = str(last_bi.length) + "_" + str(biCount)
            score = (c.bi_list[-1].low - c.bi_list[-1].high) / c.bi_list[-1].high

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s


def cxt_vg_fuzaOneBuy(cat: CzscSignals, freq='日线') -> OrderedDict:
    c: CZSC = cat.kas[freq]
    k1, k2, k3 = f"{freq}_任意_vg复杂一买".split('_')

    v1 = "其他"
    v2 = "0"
    v3 = "0"
    score = 0
    s = OrderedDict()

    biCount = len(c.bi_list)
    if biCount < 4:
        defaultSignal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
        s[defaultSignal.key] = defaultSignal.value
        return s

    # 最后一笔方向向下
    if len(c.bi_list) > 3 and (c.bi_list[-1].direction == Direction.Down):
        continueJudgeSub = False
        # 倒5至倒3形成中枢
        last_bi = c.bi_list[-1]
        zs = ZS(symbol=cat.symbol, bis=c.bi_list[-4:-1])
        # 倒数第一笔最低比中枢最低点低
        biCount = sum([x.length for x in c.bi_list[-4:-1]])
        if last_bi.low < zs.dd:
            zss = get_zs_seq(c.bi_list)

            lianxuZS = 0
            for ind in range(0, len(zss) - 1):
                if zss[-ind - 1].zz < zss[-ind - 1 - 1].zz and last_bi.low < zss[-ind - 1 - 1].dd:
                    lianxuZS += 1
                    continue
                else:
                    break
            if lianxuZS > 0:
                v1 = "确认"
                v2 = str(lianxuZS)
                v3 = str(zss[-1].bis[-1].power) + "_" + str(zss[-1].bis[-2].power)
                score = (c.bars_raw[-1].high - zs.dd) / zs.dd

    s = OrderedDict()
    signal = Signal(k1=k1, k2=k2, k3=k3, v1=v1, v2=v2, v3=v3, score=score)
    s[signal.key] = signal.value
    return s
