# -*- coding: utf-8 -*-

from websocket_server import WebsocketServer
import threading
import common.config as c
import json
import constant
from common.DBBase import db
import mqtt_client
import protocol
import datetime
import copy

class wsServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server = WebsocketServer(c.ws_port,"0.0.0.0")
        self.server.set_fn_new_client(new_client)
        self.server.set_fn_client_left(client_left)
        self.server.set_fn_message_received(message_received)

    def run(self):
        self.server.run_forever()

    def send_message_to_all(self, msg):
        self.server.send_message_to_all(msg)

def send_message_to_all(msg):
    print "websocket server send message to all:",msg
    websocket_server.send_message_to_all(msg)

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
        wsCmd = messageJson.get('wsCmd', None)
        print "roomNo:", roomNo
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
        resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
        # if len(roomInfo) < 1 and wsCmd is None:
        #     resJson['errInfo'] = 'no such roomNo:%s'%(roomNo)
        if wsCmd == 'getDevList':#获取设备列表
            resJson = getDevList(roomNo)
        elif wsCmd == 'getSceneList':#获取场景列表
            resJson = getSceneList(roomNo)
        elif wsCmd == 'controlScene':#控制场景
            resJson = controlScene(messageJson)
        elif wsCmd == 'controlDevice':#控制设备
            resJson = controlDevice(messageJson)
        elif wsCmd == 'getGowildList':#猎取狗尾草设备和房间对应列表
            resJson = getGowildList(messageJson)
        elif wsCmd == 'heartbeat':  # 心跳连接
            resJson = copy.deepcopy(constant.OK_RES_JSON)
            resJson['heartSuccessTime'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            resJson['errInfo'] = 'unknow command'
        resJson['wsCmd'] = wsCmd
        resJson['cmdMessage'] = messageJson
        print "websocket server send message %s to client %d:"%(json.dumps(resJson),client['id'])
        server.send_message(client,  json.dumps(resJson))
    except Exception as e:
        print "invalid message",str(e)
        resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
        resJson['errInfo'] = 'invalid message' + str(e)
        resJson['cmdMessage'] = message
        server.send_message(client, json.dumps(resJson))

def getGowildList(messageJson):
    gowildId = messageJson.get('gowildId', None)
    if gowildId is None:
        roomInfo = db.query("select roomNo,gowildId from ROOM")
    else:
        roomInfo = db.query("select roomNo,gowildId from ROOM where gowildId='%s'"%(gowildId))
    if len(roomInfo) < 1:
        resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
        resJson['errInfo'] = 'no such gowildId'
        resJson['gowildId'] = gowildId
        return resJson
    resJson = copy.deepcopy(constant.OK_RES_JSON)
    resJson['gowildList'] = []
    for r in roomInfo:
        rJson = {'roomNo':r['roomNo'],
                 'gowildId':r['gowildId']}
        resJson['gowildList'].append(rJson)
    return resJson

def controlDevice(messageJson):
    return mqtt_client.send_cmd(messageJson)

def controlScene(messageJson):
    sceneName = messageJson.get("sceneName", None)
    resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    if sceneName is None:
        resJson['errInfo'] = 'parameter error ,no sceneName'
        return resJson
    print "scnenName:",sceneName
    if "模式" in sceneName:
        print "4 scene"
        dictJson = copy.deepcopy(messageJson)
        dictJson['devName'] = sceneName
        return controlDevice(dictJson)
    elif sceneName in {"灯光全开", "灯光全关"}:
        return mqtt_client.crontrolScene(messageJson)
    elif sceneName == '打开窗帘':
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
        if len(roomInfo) < 1:
            resJson['errInfo'] = 'no such roomNo'
            return resJson
        room = roomInfo[0]
        curtainInfo = db.select('DEVICE', where={'did': constant.SZ_CURTAIN_DID, 'gw': room['gw']})
        for dev in curtainInfo:
            protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 1}, gw_mac=room['gw'])
    elif sceneName == '关闭窗帘':
        roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
        if len(roomInfo) < 1:
            resJson['errInfo'] = 'no such roomNo'
            return resJson
        room = roomInfo[0]
        curtainInfo = db.select('DEVICE', where={'did': constant.SZ_CURTAIN_DID, 'gw': room['gw']})
        for dev in curtainInfo:
            protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": 0}, gw_mac=room['gw'])
    return copy.deepcopy(constant.OK_RES_JSON)

def getSceneList(roomNo):
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
    resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    if len(roomInfo) < 1:
        resJson['errInfo'] = 'no such roomNo'
        return resJson
    sceneJson = {"rescode": "200",
                 "sceneList": []}
    sceneJson['sceneList'].append("灯光全开")
    sceneJson['sceneList'].append("灯光全关")
    sceneJson['sceneList'].append("明亮模式")
    sceneJson['sceneList'].append("睡眠模式")
    sceneJson['sceneList'].append("起夜模式")
    sceneJson['sceneList'].append("影音模式")
    sceneJson['sceneList'].append("打开窗帘")
    sceneJson['sceneList'].append("关闭窗帘")
    return sceneJson

def getDevList(roomNo):
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (roomNo))
    if len(roomInfo) < 1:
        print "房间不存在"
        return copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    room = roomInfo[0]
    rcuInfo = db.query("select * from HAIER_DEVICE where authToken='%s'" % (room['authToken']))
    gwInfo = db.query("select * from DEVICE where gw='%s' and controlType=1" % (room['gw']))
    serviceInfo = db.query("select * from SERVICE where authToken='%s'" % (room['authToken']))
    devListJson = {"rescode":"200",
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

    return devListJson

websocket_server = wsServer()

if __name__ == "__main__":
    websocket_server.start()