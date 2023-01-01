# -*- coding: utf-8 -*-
"""
author: zengbin93
email: zeng_bin8888@163.com
create_dt: 2021/11/17 22:26
describe: 使用掘金数据验证买卖点
"""
from czsc.data import ts

if __name__ == '__main__':


    df = ts.pro.news(start_date='2022-11-05 19:00:00')
    print(df)




