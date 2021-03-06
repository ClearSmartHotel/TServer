# -*- coding: utf-8 -*-

import json
import threading

import paho.mqtt.client as mqtt

import haier_proxy
import protocol
import alive_protocol
from common import config
from common.DBBase import db
from scene import maker as scene
import constant
import copy
import re

mqttclient = mqtt.Client()

class mqtt_task(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        mqttclient.on_connect = on_connect
        mqttclient.on_message = on_message
        mqttclient.on_disconnect = on_disconnect

    def run(self):
        print "mqtt start work"
        mqttclient.connect(config.mqtt_host, config.mqtt_port, 60)
        mqttclient.loop_forever()

def on_connect(client, userdata, flags, rc):
    print("connected :" + str(rc))
    client.subscribe(config.project_name)
    client.subscribe('topicTime')

def on_message(client, userdata, msg):
    print client
    topic = msg.topic
    data = msg.payload.decode('gbk')
    print topic, data
    handle_message(topic, data)

def on_disconnect(client, userdata, rc):
    print "disconnect:", rc
    client.reconnect()

def publish_message(topic, payload):
    print "topic:",topic,"msg:",payload
    mqttclient.publish(topic, payload)

def publish_dev_status(statuDict, devStatus = None):
    print statuDict
    statusJson = {
        "wxCmd":"devStatus",
        "devName": statuDict.get("devName"),
        "onLine": statuDict.get("onLine"),
        "actionCode": statuDict.get("actionCode")
    }
    if devStatus is not None:
        statusJson['devStatus'] = devStatus
    mqttclient.publish(config.project_name + statuDict['roomNo'], json.dumps(statusJson))

def handle_message(topic, data):
    print "handle_message"
    try:
        cmdDict = json.loads(data)
        cmd = cmdDict.get('wxCmd')
        if cmd == "devList":
            # 处理房间列表发布mqtt消息
            print "devList"
            get_dev_list(cmdDict)
        elif cmd == "sceneControl":  # 微信场景控制
            print "sceneControl"
            crontrolScene(cmdDict)
        elif cmd == "devControl":
            print "devControl"
            devControl(cmdDict)
        elif cmd == "setScene":
            print "setScene"
            set_scene(cmdDict)
        elif cmd == "setGroup":
            print "setScene"
            scene.setGroup(cmdDict['roomNo'],cmdDict.get('groupName', None))
    except Exception as e:
        print e.message

def crontrolScene(dictData):
    sceneName = dictData.get('sceneName', None)
    roomNo = dictData.get('roomNo', None)

    if sceneName is not None and roomNo is not None:
        if sceneName == '灯光全开':
            scene.controlGroup(roomNo, constant.GROUP_ALL_LIGHT, {"on":1})
        elif sceneName == '灯光全关':
            scene.controlGroup(roomNo, constant.GROUP_ALL_LIGHT, {"on":0})
        dictData['devName'] = sceneName
        publish_dev_status(dictData)
    return copy.deepcopy(constant.OK_RES_JSON)

def set_scene(dictData):
    roomNo = dictData['roomNo']
    sceneName = dictData['sceneName']
    if sceneName == 'allScene':
        print "set all scene",roomNo
        scene.setAllScene(roomNo)
    else:
        print "set single scene:",roomNo,sceneName
        scene.setSingleScene(roomNo, sceneName)


def get_dev_list(dictData):
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (dictData['roomNo']))
    if len(roomInfo) < 1:
        #房间不存在
        print "房间不存在"
        return 0
    room = roomInfo[0]
    rcuInfo = db.query("select * from HAIER_DEVICE where authToken='%s'" % (room['authToken']))
    gwInfo = db.query("select * from DEVICE where gw='%s' and controlType=1" % (room['gw']))
    serviceInfo = db.query("select * from SERVICE where authToken='%s'" % (room['authToken']))
    aliveInfo = db.query("select * from ALIVE_DEVICE where aliveRcuId='%s'" % (room['aliveRcuId']))
    devListJson = {"wxCmd":"devList","devList":[]}
    for item in rcuInfo:
        devJson = {'devName': item['devName'],
                   'onLine': item['onLine'],
                   'devType': item['clearDevType'],
                   'devId': item['devId'],
                   'actionCode': item['devActionCode']}
        if item['devStatus']:
            devJson['devStatus'] = json.loads(item['devStatus'])
        devListJson['devList'].append(devJson)

    for item in gwInfo:
        devJson = {'devName': item['devName'],
                   'onLine': item['ol'],
                   'devType': item['clearDevType'],
                   'devId': item['id'] + str(item['ep']),
                   'actionCode': item['onoff']}
        devListJson['devList'].append(devJson)

    for item in serviceInfo:
        devJson = {'devName': item['devName'],
                   'onLine': 1,
                   'actionCode': item['serviceStatus']}
        devListJson['devList'].append(devJson)

    for item in aliveInfo:
        devJson = {'devName': item['devName'],
                   'onLine': 1,
                   'devType': item['clearDevType'],
                   'devId': item['devId'],
                   'actionCode': item['devActionCode']}
        if item['devStatus']:
            devJson['devStatus'] = json.loads(item['devStatus'])
        devListJson['devList'].append(devJson)

    publish_message(config.project_name + dictData['roomNo'], json.dumps(devListJson))

def devControl(dictData):
    devName = dictData.get('devName', None)
    devType = dictData.get('devType', None)
    devId = dictData.get('devId', None)
    roomInfo = db.query("select * from ROOM where roomNo='%s'" % (dictData['roomNo']))
    resJson = copy.deepcopy(constant.BAD_REQUEST_RES_JSON)
    if len(roomInfo) < 1:
        print "no such roomNo"
        resJson['errInfo'] = 'parameter error : no such roomNo'
        return resJson
    # if devType is None or devId is None:
    if devName is None:
        print "no devName or on such roomNo"
        resJson['errInfo'] = 'parameter error :no clearDevType or devId or devName'
        return resJson

    room = roomInfo[0]
    # if re.match('sz', devType) is not None:
    #     paraDict = {'on': dictData['actionCode']}
    #     if devType == 'sz_curtain':
    #         paraDict = {"cts": dictData['actionCode']}
    #     print "sz cmd:"
    #     protocol.sendControlDev(id=devId[0:-1], ep=devId[-1:], paraDict=paraDict, gw_mac=room['gw'])
    # elif re.match('hr', devType) is not None:
    #     pass
    # elif re.match('alive', devType) is not None:
    #     pass
    rcuInfo = db.query("select * from HAIER_DEVICE where devName='%s' and authToken='%s'"%(devName, room['authToken']))
    gwInfo = db.query("select * from DEVICE where devName='%s'and gw='%s'" % (devName, room['gw']))
    serviceInfo = db.query("select * from SERVICE where devName='%s' and authToken='%s'" % (devName, room['authToken']))
    aliveInfo = db.query("select * from ALIVE_DEVICE where devName='%s' and aliveRcuId='%s'" % (devName, room['aliveRcuId']))
    devStatus = dictData.get('devStatus', None)
    if len(rcuInfo) < 1 and len(gwInfo) < 1 and len(serviceInfo) < 1 and len(aliveInfo) < 1:
        print "cant find device:", devName
        resJson['errInfo'] = "cant find device:'%s'"%(devName)
        return resJson
    elif len(rcuInfo) > 0:#rcu设备控制
        print "rcu control"
        dev = rcuInfo[0]
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
        print "cmdJson:",cmdJson
        haier_proxy.send_rcu_cmd(json.dumps(cmdJson))
    elif len(gwInfo) > 0:#gw设备控制
        print "gw control"
        dev = gwInfo[0]
        actionCode = dictData.get('actionCode')
        #先判断 是不是网关电机
        if dev['did'] == constant.SZ_CURTAIN_DID:
            protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict={"cts": actionCode}, gw_mac=room['gw'])
            return copy.deepcopy(constant.OK_RES_JSON)
        #开关面板如果actionCode是2，取反操作
        if actionCode == 2 and dev['onoff'] in {0, 1}:
            actionCode = 1 - dev['onoff']
        elif actionCode == 2:
            actionCode = 1
        paraDict = {"on": actionCode}
        protocol.sendControlDev(id=dev['id'], ep=dev['ep'], paraDict=paraDict, gw_mac=room['gw'])
    elif len(serviceInfo) > 0:#海尔service控制
        service = serviceInfo[0]
        haier_proxy.control_service(service, dictData.get('actionCode'))
    elif len(aliveInfo) > 0:
        dev = aliveInfo[0]
        if dev['clearDevType'] == 'alive_service':
            alive_protocol.controlService(dev, dictData)
        elif dev['clearDevType'] == 'alive_airCondition':
            alive_protocol.controlAirCondition(room, dev, devStatus)
    return copy.deepcopy(constant.OK_RES_JSON)


if __name__ == "__main__":
    m = mqtt_task()
    m.start()