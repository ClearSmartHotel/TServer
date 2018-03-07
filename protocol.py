
# -*- coding: utf-8 -*-

import json,time
from common.DBBase import db,db_replace

serial = 0  #发送消息的序列号

def sendMessage(gw_mac,msg):
    # TODO: 添加更加网关mac 发送到相关socket的功能
    sendOut = 0
    from shunzhou_proxy import ShunzhouProxyFactory

    for info in ShunzhouProxyFactory.clients.values():
        print "gw Info item : ",info
        if info.get("gw") == gw_mac:
            transport = info.get("transport")
            transport.write(json.dumps(msg))
            sendOut = 1
            break
    if sendOut == 0:
        print "!! Send msg faild!, mac : ",gw_mac
        print " faild msg : ",msg
    else:
        print "Send Msg ok : gw_mac %s" %gw_mac ,msg

def sendRespose(clinet_msg , msg):
    transport = clinet_msg.get("transport")
    transport.write(json.dumps(msg))
    print "Send response ok: " , msg
    pass

def dataPrase(clinet_msg ,json_obj):
    code = json_obj.get("code","")
    if code == 101:
        gw_mac = revHeartBeat(clinet_msg,json_obj)
        return gw_mac
    elif code == 104:
        revStatusData(clinet_msg,json_obj)
        return
    elif code == 114:
        revSceneStateResp(clinet_msg,json_obj)
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

def revHeartBeat(clinet_msg,data):
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
    sendRespose(clinet_msg,resp)
    testFunc()

    if "gw" in data:
        return data["gw"]["mac"]
    return None


def sendControlDev(id,ep,paraDict):
    devInfo = db.select("DEVICE" , where = {"id" : id, "ep" : ep}).first()
    if devInfo is None:
        raise Exception("ID %s, ep %s not found" %(str(id),str(ep)) )
    gw_mac = devInfo["gw"]

    global serial
    serial += 1
    controlJson = {
        "code" : 1002,
        "id" : id,
        "ep" : ep,
        "serial" : serial,
        "control":paraDict
    }
    sendMessage(gw_mac,controlJson)

def revStatusData(clinet_msg , data):
    control = data.get("control")
    if control == 0:
        #上报网关信息

        #返回response
        resp = { "code": 1004, "control": 0,"result": 0 }
        sendRespose(clinet_msg,resp)
        return
    elif control == 1:
        #上报设备删除退网

        #返回response
        resp = data
        resp.update({"code" : 1004 , "result" : 0})
        sendRespose(clinet_msg , resp)
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
        sendRespose(clinet_msg, resp)

def sendEnableScene(gw_mac ,rid , state = 1):
    global serial
    serial += 1

    cmd = {
        "code" : 1014,
        "rid" :rid,
        "serial" : serial,
        "state" : state
    }
    sendMessage(gw_mac,cmd)

def revSceneStateResp(clinet_msg , data):
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

onOff  =1
def testFunc():
    global onOff
    print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    paraDict = {"on": onOff}
    sendControlDev(id="010000124b00170f5e5f", ep=1, paraDict=paraDict)
    #time.sleep(1)
    sendControlDev(id="010000124b00170f865a", ep=1, paraDict=paraDict)
    #time.sleep(1)
    sendControlDev(id="010000124b00170f8d7d", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00170f8d7d", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b00170f8d7d", ep=3, paraDict=paraDict)

    sendControlDev(id="010000124b00170fc364", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00170fc364", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b00170fc364", ep=3, paraDict=paraDict)

    sendControlDev(id="010000124b00170a05c2", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00167d7a9d", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00167d7a9d", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b00167d7422", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00167d6e53", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b00167d6e53", ep=2, paraDict=paraDict)
    if onOff:
        onOff = 0
    else:
        onOff = 1