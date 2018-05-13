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
import os
import re
import haier_proxy
import alive_protocol

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
    # server.send_message_to_all("new client has joined us")
    # id = os.getpid()
    # server.send_message(client,"your id :"+str(id))

def client_left(client, server):
    print "client disconnected"

def message_received(client, server, message):
    print("Client %d said: %s"%(client['id'], message))
    try:
        messageJson = json.loads(message)
    except:
        resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
        resJson['errInfo'] = 'not json data:' + str(message)
        server.send_message(client, json.dumps(resJson))
        return 0

    try:
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
        resJson['wsCmd'] = wsCmd
        resJson['cmdMessage'] = messageJson
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
    resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    devType = messageJson.get('devType', None)
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
    if devType is None or len(roomInfo) < 1:
        print "no devType or on such roomNo"
        resJson['errInfo'] = 'parameter error ,no devType or no such roomNo'
        return resJson
    room = roomInfo[0]
    # 顺舟设备控制，devType以'sz_'开头
    if re.match('sz', devType) is not None:
        whereDict = {'id' : messageJson['devId'][0:-1],
                     'ep' : messageJson['devId'][-1:],
                     'gw' : room['gw']}
        # dev = db.select('DEVICE', where = whereDict).first()
        if dev is None:
            resJson['errInfo'] = 'no such device'
            return resJson
        paraDict = {'on' : messageJson['actionCode']}
        if devType == 'sz_curtain':
            paraDict = {"cts" : messageJson['actionCode']}
        print "sz cmd:"
        protocol.sendControlDev(id=whereDict['id'], ep=whereDict['ep'], paraDict=paraDict, gw_mac=dev['gw'])
    elif re.match('hr', devType) is not None:
        whereDict = {'devId': messageJson['devId'],
                     'authToken' : room['authToken']}
        dev = db.select('HAIER_DEVICE', where=whereDict).first()
        if dev is None:
            resJson['errInfo'] = 'no such device'
            return resJson
        devStatus = messageJson.get('devStatus', None)
        cmdJson = {
            "devId": dev['devId'],
            "devType": dev['devType'],
            "authToken": dev['authToken'],
            "ignoreCardStatus": 0,
            "actionCode": 1,
            "cmd": "requestDeviceControl",
            "devSecretKey": dev['devSecretKey']
        }
        if dev['devType'] == 64 and devStatus:
            print "devstatus:", devStatus
            cmdJson['mode'] = devStatus['mode']
            cmdJson['setTemp'] = devStatus['setTemp']
            cmdJson['speed'] = devStatus['speed']
            cmdJson['actionCode'] = devStatus['switch']
        print "cmdJson:", cmdJson
        haier_proxy.send_rcu_cmd(json.dumps(cmdJson))
    elif re.match('alive', devType) is not None:
        if devType == 'alive_airCondition':
            whereDict = {'devId': messageJson['devId'],
                         'aliveRcuId': room['aliveRcuId']}
            dev = db.select('ALIVE_DEVICE', where=whereDict).first()
            alive_protocol.controlAirCondition(room, dev, messageJson.get('devStatus', None))
    print "control complette"
    return copy.deepcopy(constant.OK_RES_JSON)

def controlScene(messageJson):
    sceneName = messageJson.get("sceneName", None)
    resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    if sceneName is None:
        resJson['errInfo'] = 'parameter error ,no sceneName'
        return resJson
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (messageJson['roomNo']))
    if len(roomInfo) < 1:
        resJson['errInfo'] = 'no such roomNo'
        return resJson
    room = roomInfo[0]
    print "scnenName:",sceneName
    if "模式" in sceneName:#普通模式，控制顺舟开关面板
        print "4 scene"
        whereDict = {'gw': room['gw'],
                     'devName': sceneName}
        dictJson = copy.deepcopy(messageJson)
        dev = db.select(constant.TABLE_SHUNZHOU,where=whereDict).first()
        if dev is None:
            resJson['errInfo'] = 'can not set this sceneName: %s'%(sceneName)
            return resJson
        dictJson['devName'] = sceneName
        dictJson['devType'] = dev['clearDevType']
        dictJson['actionCode'] = 1
        dictJson['devId'] = dev['id'] + str(dev['ep'])
        return controlDevice(dictJson)
    elif sceneName in {"灯光全开", "灯光全关"}:
        return mqtt_client.crontrolScene(messageJson)
    elif sceneName == '打开窗帘':
        protocol.openWindow(room)
    elif sceneName == '关闭窗帘':
        protocol.closeWindow(room)
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
    aliveInfo = db.query("select * from ALIVE_DEVICE where aliveRcuId='%s'" % (room['aliveRcuId']))
    # serviceInfo = db.query("select * from SERVICE where authToken='%s'" % (room['authToken']))
    devListJson = {"rescode":"200",
                   "devList": []}
    for item in rcuInfo:
        if item.get('clearDevType', 'null') not in {'hr_lock', 'hr_airCondition', 'hr_card'}:
            continue
        devJson = {'devName': item['devName'],
                   'onLine': item['onLine'],
                   'devType': item['clearDevType'],
                   'devId': item['devId'],
                   'actionCode': item['devActionCode']}
        if item['devStatus']:
            devJson['devStatus'] = json.loads(item['devStatus'])
        devListJson['devList'].append(devJson)

    for item in gwInfo:
        if item.get('clearDevType', 'null') not in {'sz_switch', 'sz_curtain', 'sz_adapter'}:
            continue
        devJson = {'devName': item['devName'],
                   'onLine': item['ol'],
                   'devType': item['clearDevType'],
                   'devId': item['id'] + str(item['ep']),
                   'actionCode': item['onoff']}
        devListJson['devList'].append(devJson)

    for item in aliveInfo:
        if item.get('clearDevType', 'null') not in {'alive_airCondition'}:
            continue
        devJson = {'devName': item['devName'],
                   'onLine': item['onLine'],
                   'devType': item['clearDevType'],
                   'devId': item['devId'],
                   'actionCode': item['devActionCode']}
        devListJson['devList'].append(devJson)

    # for item in serviceInfo:
    #     devJson = {'devName': item['devName'],
    #                'onLine': 1,
    #                'actionCode': item['serviceStatus']}
    #     devListJson['devList'].append(devJson)

    return devListJson

websocket_server = wsServer()

if __name__ == "__main__":
    websocket_server.start()
