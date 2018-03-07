
# -*- coding: utf-8 -*-

import json
from common.DBBase import db,db_replace
import time

serial = 1  #发送消息的序列号

def sendMessage(gw_mac,msg):
    # TODO: 添加更加网关mac 发送到相关socket的功能
    pass

def sendRespose(msg):
    # TODO: 添加直接发送response的功能
    pass

def dataPrase(json_obj):
    code = json_obj.get("code","")
    if code == 101:
        revHeartBeat(json_obj)
        return
    elif code == 104:
        revStatusData(json_obj)
        return
    elif code == 114:
        revSceneStateResp(json_obj)
        return

def revDevInfo(device,gw_mac = None):
    devInfo = {
        "id": device.get("id"),
        "ol": device.get("ol"),
        "ep": device.get("ep"),
        "pid": device.get("pid", None),
        "did": device.get("did", None),
        "onoff": device.get("st", {}).get("on", None),
        "coolset": device.get("st", {}).get("coolset", None),
        "heartset": device.get("st", {}).get("heartset", None),
        "thermode": device.get("st", {}).get("thermode", None),
        "pt": device.get("st", {}).get("pt", None),
        "wtype": device.get("st", {}).get("wtype", None),
        "time_last": time.time()
    }
    if gw_mac is not None:
        devInfo.update({"gw" : gw_mac})

    db_replace("DEVICE", {"id": devInfo["id"], "ep": devInfo["ep"]}, devInfo)

def revHeartBeat(data):
    print "Get Heart Beat ."
    # 更新网关状态:
    if "gw" in data:
        macInfo = {
            "MAC": data["gw"]["mac"],
            "LAST_TIMESTAMP": time.time()
        }
        db_replace("GETWAY",{"MAC": macInfo["MAC"]},macInfo)

    #更新设备列表:
    dList = data["device"]
    for device in dList:
        gw_mac = data.get("gw", {}).get("mac", None)
        revDevInfo(device,gw_mac)

    #发送心跳应答
    resp = {
        "code" : 1001,
        "result" : 0,
        "timestamp" : time.time()
    }
    if "gw" in data:
        sendMessage(data["gw"]["mac"],resp)


def sendControlDev(id,ep,paraDict):
    devInfo = db.select("DEVICE" , where = {"id" : id, "ep" : ep}).first()
    if devInfo is None:
        raise Exception("ID %s, ep %s not found" %(str(id),str(ep)) )
    gw_mac = devInfo["gw"]

    controlJson = {
        "code" : 1002,
        "id" : id,
        "ep" : ep,
        "serial" : serial,
        "control":paraDict
    }
    sendMessage(gw_mac,controlJson)

def revStatusData(data):
    control = data.get("control")
    if control == 0:
        #上报网关信息

        #返回response
        resp = { "code": 1004, "control": 0,"result": 0 }
        sendRespose(resp)
        return
    elif control == 1:
        #上报设备删除退网

        #返回response
        resp = data
        resp.update({"code" : 1004 , "result" : 0})
        sendRespose(resp)
        return
    elif control == 2:
        #上报状态改变
        revDevInfo(data)
        # TODO: MQTT 通知设备状态改变

        #返回 response
        resp = {
            "code": 1004,
            "id": data.get("id"),
            "ep": data.get("ep"),
            "pid" : data.get("pid"),
            "did" : data.get("did"),
            "control" : 2,
            "result": 0
        }
        sendRespose(resp)

def sendEnableScene(gw_mac ,rid , state = 1):
    cmd = {
        "code" : 1014,
        "rid" :rid,
        "serial" : serial,
        "state" : state
    }
    sendMessage(gw_mac,cmd)

def revSceneStateResp(data):
    result = data.get("result")
    if result != 0:
        print "Scene state set faild : rid:%s state:%s " %(str(data["rid"]),str(data["state"]))
    else:
        sceneState = {
            "rid" : data.get("rid"),
            "state" : data.get("state")
        }
        #TODO: ADD gw_mac filter
        db_replace("SCENE",{"rid" : data.get("rid")},sceneState)
        #TODO: sendto MQTT
