# -*- coding: utf-8 -*-

import json
import ssl
import threading
import time
import requests
import websocket
from common import config
import mqtt_client

class haier_rcu_websocket(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.rcu_server = "wss://" + config.haier_rcu_host +":50443/puietelRcuApiPush"
        self.ws = websocket.WebSocketApp(self.rcu_server,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)

    def run(self):
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

def on_message(ws, msg):
    print msg
    handle_message(msg)

def on_error(ws, error):
    print error

def on_close(ws):
    print "---close---"
    #todo 异常处理重新连接

def on_open(ws):
    print "on open"
    #心跳注册监听整个项目所有设备状态变化
    def heartbeat_thread():
        cmdJson = '''
            {
                "cmd":"registerGlobalObserver",
                "projectTokens":["%s"]
            }
            ''' % (config.haier_rcu_project_autoken)
        while True:
            ws.send(cmdJson)
            time.sleep(60)

    thread = threading.Thread(target=heartbeat_thread)
    thread.start()

def handle_message(msg):
    try:
        data = json.loads(msg)
        roomNo = data.get("roomNo", None)
        statusJosn = data.get('info', None)
        if not roomNo or not statusJosn:
            return 0
        print "roomNo:", roomNo
        print "status:", statusJosn
        mqtt_client.publish_message(config.project_name + roomNo, json.dumps(statusJosn))
    except Exception as e:
        print e

def send_rcu_cmd(cmd):
    url = "https://" + config.haier_rcu_host + ":40443/puietelRcuApi"
    header = {'Content-Type': 'application/json'}
    r = requests.post(url, cmd, verify=False, headers=header)
    r.encoding = 'utf-8'
    print r.text
    #todo 向RCU发送控制指令，需要处理好数据格式

if __name__ == "__main__":
    rcu_ws = haier_rcu_websocket()
    rcu_ws.start()
    m = mqtt_client.mqtt_task()
    m.start()
