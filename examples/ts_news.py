# -*- coding: utf-8 -*-
import datetime
import json
import requests
import tushare as ts

def main():
    ts.set_token('a6d79c0088c6d2bb619fa9dfbdf72287800d1689f2f33653bd938995')
    pro = ts.pro_api()
    lastMinute = (datetime.datetime.now() + datetime.timedelta(minutes=-30)).strftime("%Y-%m-%d %H:%M:00")
    df = pro.news(src='sina', start_date=lastMinute)
    for row in df.itertuples():
        result = getattr(row, 'datetime') + '\n'
        result = result+(getattr(row, 'content'))

        webhook = "https://oapi.dingtalk.com/robot/send?access_token=48c7a649e0f1b4be1e699461a93e6392010074b07f48c60c058927b8f406423a"
        # 构建请求头部
        header = {
            "Content-Type": "application/json",
            "Charset": "UTF-8"
        }
        # 构建请求数据
        tex = "【NEWS】: {}".format(result)
        # print(tex)
        message = {

            "msgtype": "text",
            "text": {
                "content": tex
            },
            # "at": {
            #     "isAtAll": True
            # }
        }
        # 对请求的数据进行json封装
        message_json = json.dumps(message)
        # 发送请求
        info = requests.post(url=webhook, data=message_json, headers=header)
        # 打印返回的结果
        # print(info.text)


if __name__ == '__main__':
    main()

