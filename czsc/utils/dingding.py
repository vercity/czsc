# -*- coding: utf-8 -*-
import requests

def dingmessage(dingMessage):
    return
    # 请求的URL，WebHook地址
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=48c7a649e0f1b4be1e699461a93e6392010074b07f48c60c058927b8f406423a"
    # 构建请求头部
    header = {
        "Content-Type": "application/json",
        "Charset": "UTF-8"
    }
    # 构建请求数据
    tex = "【backtest】: {}".format(dingMessage)
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