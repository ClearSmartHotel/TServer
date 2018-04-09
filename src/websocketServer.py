# -*- coding: utf-8 -*-

from websocket_server import WebsocketServer
import threading
import common.config as c
import json
import constant
from common.DBBase import db
import mqtt_client
import protocol

class wsServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server = WebsocketServer(c.ws_port,"0.0.0.0")
        self.server.set_fn_new_client(new_client)
        self.server.set_fn_client_left(client_left)
        self.server.set_fn_message_received(message_received)

    def run(self):
        self.server.run_forever()

def new_client(client, server):
    print("New client connected and was given id %d" %(client['id']))
    server.send_message_to_all("new client has joined us")
    server.send_message(client,"only you")

def client_left(client, server):
    print("client %d disconnected" %(client['id']))

def message_received(client, server, message):
    print("Client %d said: %s"%(client['id'], message))
    try:
        messageJson = json.loads(message)
        roomNo = messageJson.get('roomNo', None)
        command = messageJson.get('command', None)
        print "roomNo:", roomNo
        if roomNo is not None:
            print "roomNo:", roomNo
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
        if len(roomInfo) < 1:
            return json.dumps(constant.BAD_REQUEST_RES_JSON)
        if command == 'getDevList':
            server.send_message(client, getDevList(roomNo))
        elif command == 'getSceneList':
            server.send_message(client, getSceneList(roomNo))
        elif command == 'controlScene':
            server.send_message(client, controlScene(messageJson))
        elif command == 'controlDevice':
            server.send_message(client, controlDevice(roomNo))
    except Exception as e:
        print "invalid message",str(e)
        server.send_message(client, json.dumps(constant.BAD_REQUEST_RES_JSON))

def controlDevice(messageJson):
    devName = messageJson.get('devName', None)
    if devName is None:
        return json.dumps(constant.BAD_REQUEST_RES_JSON)
    return mqtt_client.send_cmd(messageJson)

def controlScene(messageJson):
    sceneName = messageJson.get("sceneName", None)
    if sceneName is None:
        return json.dumps(constant.BAD_REQUEST_RES_JSON)
    if sceneName in {"明亮模式", "睡眠模式", "起夜模式", "影音模式"}:
        messageJson['devName'] = sceneName
        return controlDevice(messageJson)
    elif sceneName in {"灯光全开", "灯光全关"}:
        return mqtt_client.crontrolScene(messageJson)
    elif sceneName == '打开窗帘':
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
        if len(roomInfo) < 1:
            return json.dumps(constant.BAD_REQUEST_RES_JSON)
        room = roomInfo[0]
        curtainInfo = db.select('DEVICE', where={'did': constant.SZ_CURTAIN_DID, 'gw': room['gw']})
        for dev in curtainInfo:
            protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 1}, gw_mac=room['gw'])
    elif sceneName == '关闭窗帘':
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
        if len(roomInfo) < 1:
            return json.dumps(constant.BAD_REQUEST_RES_JSON)
        room = roomInfo[0]
        curtainInfo = db.select('DEVICE', where={'did': constant.SZ_CURTAIN_DID, 'gw': room['gw']})
        for dev in curtainInfo:
            protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 0}, gw_mac=room['gw'])
    return json.dumps(constant.OK_RES_JSON)

def getSceneList(roomNo):
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
    if len(roomInfo) < 1:
        return json.dumps(constant.BAD_REQUEST_RES_JSON)
    sceneJson = {"commond": "getSceneList",
                   "roomNo": roomNo,
                   "rescode": "200",
                   "sceneList": []}
    sceneJson['sceneList'].append("灯光全开")
    sceneJson['sceneList'].append("灯光全关")
    sceneJson['sceneList'].append("明亮模式")
    sceneJson['sceneList'].append("睡眠模式")
    sceneJson['sceneList'].append("起夜模式")
    sceneJson['sceneList'].append("影音模式")
    sceneJson['sceneList'].append("打开窗帘")
    sceneJson['sceneList'].append("关闭窗帘")

def getDevList(roomNo):
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
    if len(roomInfo) < 1:
        print "房间不存在"
        return json.dumps(constant.BAD_REQUEST_RES_JSON)
    room = roomInfo[0]
    rcuInfo = db.query("select * from HAIER_DEVICE where authToken='%s'" % (room['authToken']))
    gwInfo = db.query("select * from DEVICE where gw='%s' and controlType=1" % (room['gw']))
    serviceInfo = db.query("select * from SERVICE where authToken='%s'" % (room['authToken']))
    devListJson = {"commond": "getDevList",
                   "roomNo": roomNo,
                   "rescode":"200",
                   "devList": []}
    for item in rcuInfo:
        devJson = {'devName': item['devName'],
                   'onLine': item['onLine'],
                   'actionCode': item['devActionCode']}
        if item['devStatus']:
            devJson['devStatus'] = json.loads(item['devStatus'])
        devListJson['devList'].append(devJson)

    for item in gwInfo:
        devJson = {'devName': item['devName'],
                   'onLine': item['ol'],
                   'actionCode': item['onoff']}
        devListJson['devList'].append(devJson)

    for item in serviceInfo:
        devJson = {'devName': item['devName'],
                   'onLine': 1,
                   'actionCode': item['serviceStatus']}
        devListJson['devList'].append(devJson)

    return json.dumps(devListJson)

if __name__ == "__main__":
    w = wsServer()
    w.start()
