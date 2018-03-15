# -*- coding: utf-8 -*-

import json
import ssl
import threading
import time

import requests
import websocket

import mqtt_client
from common import config
from common.DBBase import db, db_replace
import scene.maker
import protocol
import constant
import thread
import sys
reload(sys)
sys.setdefaultencoding('utf-8')


class haier_rcu_websocket(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.rcu_server = "wss://" + config.haier_rcu_host + ":50443/puietelRcuApiPush"
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

#websocket收到消息统一在这里处理
def handle_message(msg):
    print "handle haier rcu msg:", str(msg)
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
        elif cmd == "fetchServices":
            updateService(data)
        elif cmd == "fetchDevices":
            update_room_devices(data)
        elif cmd == "serviceStatusNotify":
            pass
    except Exception as e:
        print e

#rcu设备状态更新
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
        #更新rcu设备状态到数据库
        db.update('HAIER_DEVICE', where="devId = $ID",
                                  vars={'ID': devId},
                                  onLine=onLine,
                                  devStatus=json.dumps(devStatus),
                                  devActionCode=statusJson['devActionCode'])
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

    #插卡取电
    if statusJson['devType'] == 2 and devStatus is not None:
        if devStatus['cardStatus'] == 1:
            get_room_devices(token)
            thread.start_new_thread(welcomeStrategy,(room, 3))
            thread.start_new_thread(welcomeStrategy, (room, 4))
        elif devStatus['cardStatus'] == 0:
            thread.start_new_thread(goodbyeStrategy, (room, 9))
            thread.start_new_thread(goodbyeStrategy, (room, 10))



def send_rcu_cmd(cmd):
    url = "https://" + config.haier_rcu_host + ":40443/puietelRcuApi"
    header = {'Content-Type': 'application/json'}
    r = requests.post(url, cmd, verify=False, headers=header, timeout=2)
    r.encoding = 'utf-8'
    print r.status_code
    if r.status_code != 200:
        return 0
    handle_message(r.text)

#获取整个项目所有房间的authToken
def get_room_auth_cmd():
    cmd = '''
        {
            "useHierarchy": 0,
            "cmd": "fetchRoomAuthTokens",
            "projectAuthKey": "%s"
        }
        '''%(config.haier_rcu_project_autoken)
    return cmd

#获取房间services状态
def get_room_services(authToken):
    cmd = '''
        {
            "authToken": "%s",
            "cmd": "fetchServices"
        }
        ''' % (authToken)
    send_rcu_cmd(cmd)

#获取房间设备列表
def get_room_devices(authToken):
    cmd = {
                "cmd": "fetchDevices",
                "authToken": authToken,
                "type": "req"
            }

    send_rcu_cmd(json.dumps(cmd))

#迎宾模式，延时3秒打开所有灯
def welcomeStrategy(room, interval):
    print "welcomeStrategy:",room['roomNo']
    time.sleep(interval)
    cardInfo = db.select('HAIER_DEVICE', where={'devType': constant.HAIER_CARD_TYPE, 'authToken': room['authToken']})
    for card in cardInfo:
        cStatus = json.loads(card['devStatus'])
        print "cardStatus:", cStatus
        if cStatus['cardStatus'] == 0:
            thread.exit()
    scene.maker.controlGroup(room['roomNo'], constant.GROUP_ALL_LIGHT, {"on":1})
    #打开所有窗
    curtainInfo = db.select('DEVICE', where={'did': constant.SZ_CURTAIN_DID, 'gw': room['gw']})
    for dev in curtainInfo:
        protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 1}, gw_mac=room['gw'])
    thread.exit_thread()

#送宾模式，关掉所有窗
def goodbyeStrategy(room, interval):
    print "goodbyeStrategy:", room['roomNo']
    time.sleep(interval)
    print "goodbyeStrategy thread"
    cardInfo = db.select('HAIER_DEVICE', where={'devType':constant.HAIER_CARD_TYPE,'authToken':room['authToken']})
    for card in cardInfo:
        cStatus = json.loads(card['devStatus'])
        print "cardStatus:",cStatus
        if cStatus['cardStatus'] == 0:
            curtainInfo = db.select('DEVICE', where={'did':constant.SZ_CURTAIN_DID,'gw':room['gw']})
            for dev in curtainInfo:
                protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 0}, gw_mac=room['gw'])
    thread.exit_thread()

#将房间设备状态更新到数据库
def update_room_devices(data):
    authToken = data.get('authToken', None)
    devInfo = data.get('devInfos', None)
    if authToken is None or len(devInfo) < 1:
        print "no devices found"
        return 0
    for d in devInfo:
        d['onLine'] = 1 - d['offLine']
        d['authToken'] = authToken
        d.pop('offLine')
        if d.get('devStatus', None) is not None:
            d['devStatus'] = json.dumps(d.get('devStatus'))
        ret = db.select('HAIER_DEVICE', where={'devId':d['devId']}).first()
        if ret is None:
            db.insert('HAIER_DEVICE', **d)
        else:
            d.pop('devName')
            db.update('HAIER_DEVICE', where={'devId':d['devId']}, **d)

#更新房间service token
def updateService(data):
    services = data.get('services', None)
    authToken = data.get('authToken', None)
    if services is not None and authToken is not None:
        for s in services:
            s['authToken'] = authToken
            db_replace("SERVICE", {"serviceType": s["serviceType"],
                                   "serviceStatus": s["serviceStatus"],
                                   "serviceToken": s["serviceToken"],
                                   "serviceNameChs": s["serviceNameChs"],
                                   "authToken": s['authToken']}, s)

#控制RCUservice状态
def control_room_services(authToken, type, enable):
    serviceInfo = db.query("select * from SERVICE where authToken='%s' and serviceType='%d'"%(authToken, type))
    if len(serviceInfo) < 1:
        get_room_services(authToken)
        global serviceInfo
        serviceInfo = db.query("select * from SERVICE where authToken='%s' and serviceType='%d'" % (authToken, type))
        if len(serviceInfo) < 1:
            print "cant find service info"
            return 0

    service = serviceInfo[0]

    cmd = {
                "serviceType": type,
                "authToken": authToken,
                "cmd": "requestServiceControl",
                "ignoreCardStatus": 0,
                "serviceToken": service['serviceToken'],
                "enableService": enable,
            }

    send_rcu_cmd(json.dumps(cmd))

if __name__ == "__main__":
    rcu_ws = haier_rcu_websocket()
    rcu_ws.start()
    m = mqtt_client.mqtt_task()
    m.start()
