# -*- coding: utf-8 -*-

import json
import ssl
import threading
import time
import requests
import websocket
from common import config
from common.DBBase import db
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
        send_rcu_cmd(get_room_auth_cmd())
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
    print "handle haier rcu msg:", msg
    try:
        data = json.loads(msg)
        cmd = data.get("cmd", None)
        roomNo = data.get("roomNo", None)
        statusJosn = data.get('info', None)
        token = data.get('authToken', None)
        print "cmd:", cmd
        if not cmd or not token:
            return 0
        if cmd == "deviceStatusNotify":
            dev_status_notify(data)

    except Exception as e:
        print e

def dev_status_notify(data):
    token = data.get('authToken', None)
    statusJson = data.get('info', None)
    roomInfo = db.query("select * from ROOM where authToken='%s'"%(token))
    devId = statusJson['devId']
    if len(roomInfo) < 1 or statusJson is None:
        raise Exception("room token: %s or status: %s not found" % (token, statusJson))
    room = roomInfo[0]

    res = db.query("select * from HAIER_DEVICE where devId='%s'" % (devId))
    devStatus = statusJson.get('devStatus', None)
    onLine = 0 if statusJson['offLine'] else 1
    if len(res) < 1:
        # 设备不存在，插入
        db.insert('HAIER_DEVICE',
                  devId=statusJson['devId'],
                  devName=statusJson['devName'],
                  devType=statusJson['devType'],
                  devSecretKey=statusJson['devSecretKey'],
                  devActionCode=statusJson['devActionCode'],
                  devStatus=json.dumps(devStatus),
                  onLine=onLine,
                  authToken=token)
    else:
        #更新rcu状态到数据库
        db.update('HAIER_DEVICE', where="devId = $ID",
                                  vars={'ID': devId},
                                  authToken=token)

    # mqtt发送状态更新
    devInfo = db.query("select * from ROOM r,HAIER_DEVICE d where r.authToken=d.authToken and d.devId='%s'"
                      % (statusJson['devId']))
    if len(devInfo) > 0:
        dev = devInfo[0]
        mqttJson = {
            "wxCmd": "devStatus",
            "devName": dev['devName'],
            "onLine": dev['onLine'],
            "actionCode": dev['devActionCode']
        }
        if devStatus is not None:
            mqttJson['devStatus'] = devStatus
        mqtt_client.publish_message(config.project_name + room['roomNo'], json.dumps(mqttJson))


def send_rcu_cmd(cmd):
    url = "https://" + config.haier_rcu_host + ":40443/puietelRcuApi"
    header = {'Content-Type': 'application/json'}
    r = requests.post(url, cmd, verify=False, headers=header)
    r.encoding = 'utf-8'
    print r.status_code
    if r.status_code != 200:
        return 0
    handle_message(r.text)
    print r.text
    #todo 向RCU发送控制指令，需要处理好数据格式
    data = json.loads(r.text)
    print data.get('cmd')

def get_room_auth_cmd():
    cmd = '''
        {
            "useHierarchy": 0,
            "cmd": "fetchRoomAuthTokens",
            "projectAuthKey": "%s"
        }
        '''%(config.haier_rcu_project_autoken)
    return cmd

def get_room_services():
    cmd = '''
        {
            "authToken": "%s",
            "cmd": "fetchServices"
        }
        ''' % (config.haier_rcu_project_autoken)
    return cmd

if __name__ == "__main__":
    rcu_ws = haier_rcu_websocket()
    rcu_ws.start()
    m = mqtt_client.mqtt_task()
    m.start()
