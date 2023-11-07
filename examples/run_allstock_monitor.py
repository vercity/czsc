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
from czsc.data.ts import freq_cn_map, dt_fmt, get_all_stocks
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
from czsc.traders import CzscSignals, CzscTrader
from czsc.strategies import CzscStrategyBase, CzscStocksCustom
import dill
from czsc.utils.dingding import dingmessage
import numpy as np

# =======================================================================================================
# 基础参数配置
# ct_path = "/Volumes/OuGuMore/Stock/data"
from examples.collect_datas.run_thsplates_monitor import stockToPlates

ct_path = "/Users/guyeqi/Documents/Python/data/realtime/data"
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

    # # 九笔类一买 （2~4构成中枢A，6~8构成中枢B，9背驰）
    # Event(name="九笔aAbBc式类一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_类一买", signals_all=[Signal("日线_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("日线_倒1K_DIF回抽_0轴_任意_任意_0"),
    #                                        Signal("日线_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="30分钟_类一买", signals_all=[Signal("30分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("30分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("30分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="15分钟_类一买", signals_all=[Signal("15分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("15分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("15分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="5分钟_类一买", signals_all=[Signal("5分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("5分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("5分钟_倒1K_MACD方向_向上_任意_任意_0")]),
        # Factor(name="60分钟_类一买", signals_all=[Signal("60分钟_倒1笔_类买卖点_类一买_九笔aAbBc式_任意_0"), Signal("60分钟_倒1K_DIF回抽_0轴_任意_任意_0"),
        #                                    Signal("60分钟_倒1K_MACD方向_向上_任意_任意_0")]),
    # ]),

    # Event(name="GG三买", operate=Operate.LO, factors=[
    #         Factor(name="日线_类三买", signals_all=[
    #             Signal("日线_倒1K_MACD方向_向上_任意_任意_0"),
    #         ], signals_any=[
    #             Signal("日线_倒1笔_类买卖点_类三买_九笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_11笔GG三买_任意_0"),
    #             Signal("日线_倒1笔_类买卖点_类三买_13笔GG三买_任意_0"),
    #         ]),
    #     ]),

    # Event(name="vg潜在一买", operate=Operate.LO, factors=[
    #     Factor(name="日线_vg潜在一买", signals_all=[Signal("日线_vg潜在一买_任意_确认_任意_任意_0")]),
    #     # Factor(name="30分钟_vg潜在一买", signals_all=[Signal("30分钟_vg潜在一买_任意_确认_任意_任意_0")]),
    #     # Factor(name="60分钟_vg潜在一买", signals_all=[Signal("60分钟_vg潜在一买_任意_确认_任意_任意_0")]),
    #     # Factor(name="周线_vg潜在一买", signals_all=[Signal("周线_vg潜在一买_任意_确认_任意_任意_0")]),
    # ]),

    Event(name="vg复杂一买反转", operate=Operate.LO, factors=[
        Factor(name="日线_vg复杂一买反转",
               signals_all=[Signal("日线_vg复杂一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="周线_vg复杂一买反转",
               signals_all=[Signal("周线_vg复杂一买_任意_确认_任意_任意_0"), Signal("周线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="60分钟_vg复杂一买反转",
               signals_all=[Signal("60分钟_vg复杂一买_任意_确认_任意_任意_0"), Signal("60分钟_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="vg三买确认", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买确认", signals_all=[Signal("日线_60分钟_vg三买确认_确认_任意_任意_0")]),
    ]),

    Event(name="反转迹象", operate=Operate.LO, factors=[
        Factor(name="日线_反转迹象", signals_all=[Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="30分钟_反转迹象", signals_all=[Signal("30分钟_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="60分钟_反转迹象", signals_all=[Signal("60分钟_D1A300_反转V230227_看多_任意_任意_0")]),
        Factor(name="周线_反转迹象", signals_all=[Signal("周线_D1A300_反转V230227_看多_任意_任意_0")]),
    ]),

    Event(name="辅助一买", operate=Operate.LO, factors=[
        Factor(name="日线_辅助一买", signals_all=[Signal("日线_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="30分钟_辅助一买", signals_all=[Signal("30分钟_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="60分钟_辅助一买", signals_all=[Signal("60分钟_D1N20量价_BS1辅助_看多_任意_任意_0")]),
        Factor(name="周线_辅助一买", signals_all=[Signal("周线_D1N20量价_BS1辅助_看多_任意_任意_0")]),
    ]),

    Event(name="TAS一买", operate=Operate.LO, factors=[
        Factor(name="日线_TAS一买", signals_all=[Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="30分钟_TAS一买", signals_all=[Signal("30分钟_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="60分钟_TAS一买", signals_all=[Signal("60分钟_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
        Factor(name="周线_TAS一买", signals_all=[Signal("周线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
    ]),

    Event(name="vg复杂一买多中枢", operate=Operate.LO, factors=[
        Factor(name="日线_vg复杂一买多中枢",signals_all=[],
               signals_any=[Signal("日线_vg复杂一买_任意_确认_2_任意_0"), Signal("日线_vg复杂一买_任意_确认_3_任意_0")]),
        Factor(name="周线_vg复杂一买2中枢",signals_all=[],
               signals_any=[Signal("周线_vg复杂一买_任意_确认_2_任意_0"), Signal("周线_vg复杂一买_任意_确认_3_任意_0")]),
        Factor(name="60分钟_vg复杂一买2中枢",signals_all=[],
               signals_any=[Signal("60分钟_vg复杂一买_任意_确认_2_任意_0"), Signal("60分钟_vg复杂一买_任意_确认_3_任意_0")]),
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

    # Event(name="vg简单一买反转TAS", operate=Operate.LO, factors=[
    #     Factor(name="日线_vg简单一买反转TAS",
    #            signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0"),
    #                         Signal("日线_D1N10SMA5_BS1辅助_一买_任意_任意_0")]),
    # ]),
    #
    # Event(name="vg简单一买反转", operate=Operate.LO, factors=[
    #     Factor(name="日线_vg简单一买反转",
    #            signals_all=[Signal("日线_vg简单一买_任意_确认_任意_任意_0"), Signal("日线_D1A300_反转V230227_看多_任意_任意_0")]),
    # ]),

    Event(name="vg三买", operate=Operate.LO, factors=[
        Factor(name="日线_60分钟_vg三买", signals_all=[Signal("日线_60分钟_vg三买_确认_任意_任意_0")]),
    ]),

    Event(name="vg一买", operate=Operate.LO, factors=[
        Factor(name="日线_vg一买", signals_all=[Signal("日线_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="30分钟_vg一买", signals_all=[Signal("30分钟_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="60分钟_vg一买", signals_all=[Signal("60分钟_vg一买_任意_确认_任意_任意_0")]),
        Factor(name="周线_vg一买", signals_all=[Signal("周线_vg一买_任意_确认_任意_任意_0")]),
    ]),
]


def monitor(use_cache=True):
    # dingmessage("自选股因子监控启动 @ {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    moni_path = os.path.join(ct_path, "monitor")
    # 首先清空历史快照
    if os.path.exists(moni_path):
        shutil.rmtree(moni_path)
    os.makedirs(moni_path, exist_ok=True)

    # print(len(symbols))
    k = 1
    try:
        threeBuyResult = pd.read_csv('/Users/guyeqi/Documents/Python/data/backtest/data/vg三买，day-60min20150101/finalResult.csv')
        # df.set_index('姓名', inplace=True)
        print()
    except Exception as e:
        print(e)
    for s in allcodes:
        print(k)
        if s.endswith('BJ'):
            continue
        k += 1
        try:
            file_ct = os.path.join(ct_path, "{}.ct".format(s))
            if os.path.exists(file_ct) and use_cache:
                ct: CzscTrader = dill.load(open(file_ct, 'rb'))
                # hasChange = updateKline(ct)
            else:
                kg = get_init_bg(s, datetime.now(), base_freq="1分钟",
                                 freqs=['30分钟', '60分钟', '日线', '周线'])
                ct = CzscTrader(bg=kg, get_signals=CzscStocksCustom.get_signals)
                hasChange = True
            # if hasChange:
            #     dill.dump(ct, open(file_ct, 'wb'))
            # continue
            # 每次执行，会在moni_path下面保存一份快照
            # file_html = os.path.join(moni_path, f"{ct.symbol}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
            # ct.take_snapshot(file_html, width="2000px", height="700px")

            # msg = f"标的代码：{s}\n同花顺F10：http://basic.10jqka.com.cn/{s.split('.')[0]}\n"
            msg = f"标的代码：{s}\n"
            msg += f"标的名称：{stockDf.loc[stockDf['ts_code'] == s]['name'].values[0]}\n"
            for event in events_monitor:
                m, f = event.is_match(ct.s)
                if m:
                    daoZeroKey = "{}_倒0笔_长度".format(f.split("_")[0])
                    if f in ct.s.keys():
                        msg += "监控提醒：{}@{} [{}], {}\n".format(event.name, f, ct.s[daoZeroKey], ct.s[f])
                    else:
                        msg += "监控提醒：{}@{} [{}]\n".format(event.name, f, ct.s[daoZeroKey])

                    if "3根K线" in ct.s[daoZeroKey]:
                        # if f == "日线_vg复杂一买反转":
                        #     msg += ct.s["日线_vg复杂一买"] + "\n"
                        #     dingmessage("【抄底】\n" + "看下参数\n" + msg.strip("\n"), shouldAt=False, webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        # if f == "日线_vg简单一买反转":
                        #     dingmessage("【抄底】\n" + "6成胜率\n" + msg.strip("\n"), shouldAt=False, webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        # if f == "日线_vg简单一买反转TAS":
                        #     dingmessage("【抄底】\n" + "6.5成胜率\n" +  msg.strip("\n"), shouldAt=True,
                        #                 webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        # if f == "日线_vg一买反转orTAS":
                        #     dingmessage("【抄底】\n" + "7成胜率\n" +  msg.strip("\n"), shouldAt=True,
                        #                 webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        if f == "日线_vg一买反转andTAS":
                            dingmessage("【抄底】\n" + "必买！！！！！！！\n必买！！！！！！！\n必买！！！！！！！\n8成胜率\n" +  msg.strip("\n"), shouldAt=True,
                                        webhook="https://oapi.dingtalk.com/robot/send?access_token=3571c54ee105cd3dc3a913b0ea97d3a6fd50809fe3f013a6c5e5903f847e341c")
                        # if f == "日线_vg一买":
                        #     confirm, zhongshu, bipower,score = ct.s[f].split("_")
                        #     bi1power, bi2power = bipower.split("-")
                        #     if float(bi1power) > float(bi2power):
                        #         dingmessage("【抄底】\n" + msg.strip("\n"))
                        elif f == "日线_60分钟_vg三买确认":
                            dingmessage("【追涨】\n" + msg.strip("\n"))
                        elif f == "日线_60分钟_vg三买":
                            confirm, huitiao, dao0length, zhendanglength, dao1power = ct.s[f].split("_")
                            tmpThreeBuyResult = threeBuyResult.copy(deep=True)
                            tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['最后一笔天数'] == int(dao0length)]
                            if float(dao1power) < 1:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.05)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.05)]
                            elif float(dao1power) > 1 and float(dao1power) < 1.5:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.1)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.1)]
                            elif float(dao1power) > 1.5 and float(dao1power) < 2:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > (float(dao1power) - 0.2)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] < (float(dao1power) + 0.2)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['上攻涨幅'] > 2]

                            if float(huitiao) < 0.2:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] > (float(huitiao) - 0.02)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] < (float(huitiao) + 0.02)]
                            elif float(huitiao) >=0.2 and float(huitiao) < 0.6:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] > (float(huitiao) - 0.03)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] < (float(huitiao) + 0.03)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['回调幅度'] >= 0.6]

                            if int(zhendanglength) < 20:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] ==  int(zhendanglength)]
                            elif int(zhendanglength) >=20 and int(zhendanglength) < 40:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 2)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 2)]
                            elif int(zhendanglength) >= 40 and int(zhendanglength) < 60:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 5)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 5)]
                            elif int(zhendanglength) >= 60 and int(zhendanglength) < 100:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] > (int(zhendanglength) - 10)]
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] < (int(zhendanglength) + 10)]
                            else:
                                tmpThreeBuyResult = tmpThreeBuyResult.loc[tmpThreeBuyResult['震荡时间'] >= 100]

                            isLikeOK = False
                            if  int(dao0length) < 10 and  int(zhendanglength) > 60:
                                isLikeOK = True
                            # if float(huitiao) < 0.35 and int(dao0length) < 9 and int(zhendanglength) > 60 and float(
                            #         dao1power) < 1 and float(dao1power) > 0.5:
                            #     isLikeOK = True

                            if isLikeOK:
                                dingMSG = '【追涨-还可以】\n'
                            else:
                                dingMSG = '【追涨-看一眼】\n'
                            dingMSG += f"标的代码：{s}\n"
                            dingMSG += f"标的名称：{stockDf.loc[stockDf['ts_code'] == s]['name'].values[0]}\n"
                            dingMSG += "最后一笔天数：{} \n".format(str(dao0length))
                            dingMSG += "上攻涨幅：{} \n".format(
                                str(dao1power).split('.')[0] + '.' + str(dao1power).split('.')[1][:2])
                            dingMSG += "回调幅度：{} \n".format(
                                str(huitiao).split('.')[0] + '.' + str(huitiao).split('.')[1][:2])
                            dingMSG += "震荡时间：{} \n".format(str(zhendanglength))
                            dingMSG += "概念：{}\n".format(str(stockToPlates(stockDf.loc[stockDf['ts_code'] == s]['name'].values[0])))
                            # if tmpThreeBuyResult.empty == False:
                            #     dingMSG += "相似形态个数：{}\n".format(str(tmpThreeBuyResult.shape[0]))
                            #     dingMSG += "【平均】 "
                            #     dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format(
                            #         round(np.nanmean(tmpThreeBuyResult['n1b']), 2), round(np.nanmean(tmpThreeBuyResult['n2b']), 2),
                            #         round(np.nanmean(tmpThreeBuyResult['n3b']), 2), round(np.nanmean(tmpThreeBuyResult['n5b']), 2),
                            #         round(np.nanmean(tmpThreeBuyResult['n8b']), 2), round(np.nanmean(tmpThreeBuyResult['n13b']), 2),
                            #         round(np.nanmean(tmpThreeBuyResult['n21b']), 2))
                            #     dingMSG += "【中位数】 "
                            #     dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format(
                            #         round(np.median(tmpThreeBuyResult['n1b']), 2), round(np.median(tmpThreeBuyResult['n2b']), 2),
                            #         round(np.median(tmpThreeBuyResult['n3b']), 2), round(np.median(tmpThreeBuyResult['n5b']), 2),
                            #         round(np.median(tmpThreeBuyResult['n8b']), 2), round(np.median(tmpThreeBuyResult['n13b']), 2),
                            #         round(np.median(tmpThreeBuyResult['n21b']), 2))
                            #     dingMSG += "【胜率】 "
                            #     dingMSG += "n1b: {}% | n2b: {}%  | n3b: {}%  | n5b: {}%  | n8b: {}%  | n13b: {}%  | n21b: {}%\n".format(
                            #         round(tmpThreeBuyResult['n1b'][tmpThreeBuyResult['n1b'] > 0].count() / tmpThreeBuyResult['n1b'].count() * 100, 2), round(tmpThreeBuyResult['n2b'][tmpThreeBuyResult['n2b'] > 0].count() / tmpThreeBuyResult['n2b'].count() * 100, 2),
                            #         round(tmpThreeBuyResult['n3b'][tmpThreeBuyResult['n3b'] > 0].count() / tmpThreeBuyResult['n3b'].count() * 100, 2), round(tmpThreeBuyResult['n5b'][tmpThreeBuyResult['n5b'] > 0].count() / tmpThreeBuyResult['n5b'].count() * 100, 2),
                            #         round(tmpThreeBuyResult['n8b'][tmpThreeBuyResult['n8b'] > 0].count() / tmpThreeBuyResult['n8b'].count() * 100, 2), round(tmpThreeBuyResult['n13b'][tmpThreeBuyResult['n13b'] > 0].count() / tmpThreeBuyResult['n13b'].count() * 100, 2),
                            #         round(tmpThreeBuyResult['n21b'][tmpThreeBuyResult['n21b'] > 0].count() / tmpThreeBuyResult['n21b'].count() * 100, 2))
                            #     for i, row in tmpThreeBuyResult.iterrows():
                            #         dingMSG += f"【参考标的】：{stockDf.loc[stockDf['ts_code'] == row['ts_code']]['name'].values[0]}， 代码： " + row['ts_code'] + "， 时间：" + row['trade_date'] + '\n'
                            #         dingMSG += "n1b: {} | n2b: {}  | n3b: {}  | n5b: {}  | n8b: {}  | n13b: {}  | n21b: {}\n".format((str(row['n1b']).split('.')[0] + '.' + str(row['n1b']).split('.')[1][:2]),(str(row['n2b']).split('.')[0] + '.' + str(row['n2b']).split('.')[1][:2]),(str(row['n3b']).split('.')[0] + '.' + str(row['n3b']).split('.')[1][:2]),(str(row['n5b']).split('.')[0] + '.' + str(row['n5b']).split('.')[1][:2]),(str(row['n8b']).split('.')[0] + '.' + str(row['n8b']).split('.')[1][:2]),(str(row['n13b']).split('.')[0] + '.' + str(row['n13b']).split('.')[1][:2]),(str(row['n21b']).split('.')[0] + '.' + str(row['n21b']).split('.')[1][:2]))
                            #     print(dingMSG)
                            if isLikeOK:
                                dingmessage(dingMSG, shouldAt=isLikeOK)
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


def updateKline(trader: CzscSignals):
    bars = get_kline(ts_code=trader.symbol, start_date=trader.end_dt, end_date=datetime.now(), freq=Freq.F1, fq=None)
    data = [x for x in bars if x.dt > trader.end_dt]

    if data:
        print(f"{trader.symbol}: 更新 bar generator 至 {trader.end_dt.strftime(dt_fmt)}，共有{len(data)}行数据需要update")
        for row in data:
            trader.update(row)


if __name__ == '__main__':
    monitor(True)

