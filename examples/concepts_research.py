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
from czsc.data.ts import get_kline, freq_cn_map, dt_fmt, date_fmt, get_all_stocks, pro, format_kline, get_ths_members
# from czsc.data.jq import JqCzscTrader as CzscTrader
from czsc.objects import Signal, Factor, Event, Operate
from czsc.utils.qywx import push_text, push_file
from czsc.utils.io import read_pkl, save_pkl
import requests
import json
from czsc.data.ts import get_kline, get_all_cb, get_all_cbDaily
import pandas as pd
from czsc.enum import Freq
from czsc.utils.bar_generator import BarGenerator
from czsc.cb.advanced_cb import CzscCBTrader
from czsc.signals.signals import get_default_signals
import akshare as ak

# =======================================================================================================
# 基础参数配置
ct_path = "/Volumes/OuGuMore/Stock/cb"
os.makedirs(ct_path, exist_ok=True)


#前面是否小于后面
def compare_time(startTime, endTime):
    d_start = datetime.strptime(str(startTime), '%Y%m%d')
    d_end = datetime.strptime(str(endTime), '%Y%m%d')

    result = d_start < d_end

    return result

    # for oneDay in allTradingDates:
    #     stock_zt_pool_em_df = ak.stock_zt_pool_em(date=oneDay)
    #     pro.limit_list(trade_date='oneDay')
    #     for index, row in stock_zt_pool_em_df.iterrows():
    #         matchedCB = allCBs.loc[allCBs['stk_short_name'] == row['名称']]
    #         if matchedCB.empty == False:
    #             lastFeng = row['最后封板时间']
    #             if (int)(lastFeng) < 93000:
    #                 # if (int)(lastFeng) < 100000:
    #                 print(str(oneDay) + ' ' + row['名称'] + ' ' + matchedCB['ts_code'])
    #                 print('----------')

def refreshConcepts():
    conceptsDic = {}
    concepts = pro.ths_index(exchange="A")
    for index, row in concepts.iterrows():
        thisTypeConcept = {}
        if row['type'] in conceptsDic.keys():
            thisTypeConcept = conceptsDic[row['type']]
        thisTypeConcept[row['ts_code']] = {"name": row['name'], "count": row['count'], 'list_date': row['list_date']}
        time.sleep(0.3)
        thisTypeConceptDetailStock = {}
        detailDF = pro.ths_member(ts_code=row['ts_code'],
                                  fields="ts_code,code,name,weight,in_date,out_date,is_new")
        for index2, row2 in detailDF.iterrows():
            # 判断是不是中国的股票
            if row2['code'].endswith('.SH') or row2['code'].endswith('.SZ'):
                thisTypeConceptDetailStock[row2['code']] = row2['name']
        if len(thisTypeConceptDetailStock.keys()) > 0:
            thisTypeConcept[row['ts_code']]['stocks'] = thisTypeConceptDetailStock
            conceptsDic[row['type']] = thisTypeConcept
    save_pkl(conceptsDic, os.path.join(ct_path, "members"))

if __name__ == '__main__':
    # get_ths_members()
    conceptsDic = read_pkl(os.path.join(ct_path, "members"))
    # refreshConcepts()
    tradingDate = '20220321'
    todayInfo = {}
    stock_zt_pool_em_df = pro.limit_list(trade_date=tradingDate)
    print(stock_zt_pool_em_df)
    for index, row in stock_zt_pool_em_df.iterrows():
        oneStock = row['ts_code']
        for conceptCode, conceptDetail in conceptsDic['N'].items():
            listDate = conceptDetail['list_date']
            if compare_time(listDate, tradingDate):
                if 'stocks' in conceptDetail.keys():
                    stockDic = conceptDetail['stocks']
                    if oneStock in stockDic.keys():
                        if conceptDetail['name'] in todayInfo.keys():
                            originCount = todayInfo[conceptDetail['name']]
                            todayInfo[conceptDetail['name']] = originCount + 1
                        else:
                            todayInfo[conceptDetail['name']] = 1

    print(sorted(todayInfo.items(), key=lambda kv: (kv[1], kv[0])))
    # print("sss")
            # df = pro.trade_cal(exchange='', start_date='20220303')
    # allTradingDates = df.loc[df['is_open'] == 1]['cal_date'].values.tolist()
    # moni_path = os.path.join(ct_path, "monitor")
    #
    # for oneDay in allTradingDates:
    #     stock_zt_pool_em_df = pro.limit_list(trade_date=oneDay)
    #     for index, row in stock_zt_pool_em_df.iterrows():
    #         matchedCB = allCBs.loc[allCBs['stk_short_name'] == row['name']]
    #         if matchedCB.empty == False:
    #             strong = row['strth']
    #             if strong > 90:
    #             # if (int)(lastFeng) < 100000:
    #                 print(str(oneDay) + ' ' + row['name'] + ' ' + matchedCB['ts_code'])
    #                 print('----------')


        # allCBDaily = get_all_cbDaily(start_date=oneDay, end_date=oneDay)
        # print(str(oneDay))
        # for index, row in allCBDaily.iterrows():
        #     thisCBInfo = allCBs.loc[allCBs['ts_code']==row['ts_code']]
        #
        #     # bg = BarGenerator("日线", ['日线', '周线', '月线'], 1000)
        #     df2 = row.to_frame().T
        #     bars = format_kline(df2, Freq.D)
        #     bgd = BarGenerator("日线", ['周线', '月线'])
        #     for b in bars:
        #         bgd.update(b)
        #
        #     file_ct = os.path.join(ct_path, "{}.ct".format(row['ts_code']))
        #     if os.path.exists(file_ct):
        #         ct: CzscCBTrader = read_pkl(file_ct)
        #         if compare_time(ct.end_dt, bgd.end_dt):
        #             ct.update(b)
        #             print(f"{thisCBInfo['bond_short_name']}: 更新 bar generator 至 {ct.end_dt.strftime(dt_fmt)}")
        #         else:
        #             print(f"{ct.end_dt.strftime(dt_fmt)}过")
        #         # file_html = os.path.join(moni_path, f"{ct.symbol}_{ct.end_dt.strftime('%Y%m%d%H%M')}.html")
        #         # ct.take_snapshot(file_html, width="2000px", height="900px")
        #     else:
        #         ct = CzscCBTrader(bgd, get_default_signals, chineseName=thisCBInfo['bond_short_name'], stock=thisCBInfo['stk_code'])
        #         print(f"{thisCBInfo['bond_short_name']}: 新建 bar generator {ct.end_dt.strftime(dt_fmt)}")
        #     save_pkl(ct, file_ct)