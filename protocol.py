
# -*- coding: utf-8 -*-

import json,time
from common.DBBase import db,db_replace
import mqtt_client
from common import config
import haier_proxy

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

#面板开关事件处理
def send_status_mqtt(id, ep):
    # mqtt发送状态更新
    print "dev status changed"
    gwInfo = db.query("select * from ROOM r,DEVICE d where r.gw=d.gw and d.id='%s' AND d.ep='%d'"
                      % (id, ep))
    if len(gwInfo) < 1:
        return 0
    dev = gwInfo[0]
    statusJson = {
        "wxCmd":"devStatus",
        "devName": dev['devName'],
        "onLine": dev['ol'],
        "actionCode": dev['onoff']
    }
    mqtt_client.publish_message(config.project_name + dev['roomNo'], json.dumps(statusJson))

    # 控制RCUservices
    if dev['controlType'] in {104, 105, 106} and dev['onoff'] in {0, 1}:
        haier_proxy.control_room_services(dev['authToken'], dev['controlType'], dev['onoff'])
        #请稍后104，请勿扰105，两个服务互斥处理，控制另一个面板关闭
        if dev['onoff'] == 1 and dev['controlType'] in {104, 105}:
            mutexType = 209 - dev['controlType']
            serviceDev = db.query("select * from DEVICE where gw='%s' and controlType='%d' and onoff='1'" % (dev['gw'], mutexType))
            if len(serviceDev) > 0:
                d = serviceDev[0]
                sendControlDev(d['id'], d['ep'], {"on" : 0}, d['gw'])

    #处理双控，判断设备controlType为201，主设备进行取反操作
    elif dev['controlType'] == 201 and dev['onoff'] in {1}:
        devInfo = db.query("select * from DEVICE where devName='%s' and controlType=1"%(dev['devName']))
        if len(devInfo) > 0:
            masterDev = devInfo[0]
            actionCode = 1
            if masterDev['onoff'] in {0, 1}:
                actionCode = 1 - masterDev['onoff']
            paraDict = {"on": actionCode}
            sendControlDev(id=masterDev['id'], ep=masterDev['ep'], paraDict=paraDict, gw_mac=masterDev['gw'])
        # 自己立即关闭不保存开关状态
        paraDict = {"on": 0}
        sendControlDev(id=dev['id'], ep=dev['ep'], paraDict=paraDict, gw_mac=dev['gw'])

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
        gw_mac = data.get("gw", {"mac" : clinet_msg["gw"]}).get("mac", None)
        revDevInfo(device,gw_mac)

    #发送心跳应答
    resp = {
        "code" : 1001,
        "result" : 0,
        "timestamp" : time.time()
    }
    sendRespose(clinet_msg,resp)
    # testFunc()

    if "gw" in data:
        return data["gw"]["mac"]
    return None


def sendControlDev(id,ep,paraDict,gw_mac=None):
    if gw_mac is None:
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

        # MQTT 通知设备状态改变
        send_status_mqtt(data.get("id"), data.get("ep"))


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
    # sendControlDev(id="010000124b00170f5e5f", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00170f865a", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00170f8d7d", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00170f8d7d", ep=2, paraDict=paraDict)
    # sendControlDev(id="010000124b00170f8d7d", ep=3, paraDict=paraDict)
    #
    # sendControlDev(id="010000124b00170fc364", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00170fc364", ep=2, paraDict=paraDict)
    # sendControlDev(id="010000124b00170fc364", ep=3, paraDict=paraDict)
    #
    # sendControlDev(id="010000124b00170a05c2", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00167d7a9d", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00167d7a9d", ep=2, paraDict=paraDict)
    # sendControlDev(id="010000124b00167d7422", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00167d6e53", ep=1, paraDict=paraDict)
    # sendControlDev(id="010000124b00167d6e53", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b000e4fbe26", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b000e0bd9f8", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b000e0bd9f8", ep=3, paraDict=paraDict)
    sendControlDev(id="010000124b000e0bd9f8", ep=4, paraDict=paraDict)
    sendControlDev(id="010000124b000e0bd9f8", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b000e0c03ae", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b000e0c03ae", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b000e0c03de", ep=1, paraDict=paraDict)
    sendControlDev(id="010000124b000e0c03de", ep=2, paraDict=paraDict)
    sendControlDev(id="010000124b000e0c03de", ep=3, paraDict=paraDict)

    paraDict = {"cts": onOff}
    # sendControlDev(id="010000124b000e31d29f", ep=8, paraDict=paraDict)
    # sendControlDev(id="010000124b000e5369f6", ep=8, paraDict=paraDict)

    if onOff:
        onOff = 0
    else:
        onOff = 1

def send_scene_json():
    print "send scene json"
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json1))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json2))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json3))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json4))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json5))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json6))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json7))
    # sendMessage("2c:6a:6f:00:52:6f", json.loads(json8))


json1 = '''
{
  "code": 1013,
  "serial": 1520667056959,
  "name": "shuangkong",
  "rid": 231111,
  "state": 1, 
  "trig": 0,
  "ct": "2018-03-10T15:30:57",
  "exp": "function main(a1,b1) if (a1==b1) then return true else return false end end",
  "cond": [
    {
      "idx": 1,
      "type": 2,
      "id": "010000124b00170f865a",
      "ep": 1,
      "op": 1,
      "cmd": "on",
      "val": "true"
    }
  ],
  "act": [
    {
      "idx": 1,
      "delay": 1,
      "type": 1,
      "id": "010000124b00170a05c2",
      "ep": 1,
      "cmd": "on",
      "val": true
    }
  ]
}
'''

json2 = '''
{
  "code": 1013,
  "serial": 1520667056959,
  "name": "shuangkong",
  "rid": 231112,
  "state": 1,
  "trig": 0,
  "ct": "2018-03-10T15:30:57",
  "exp": "function main(a1,b1) if (a1==b1) then return true else return false end end",
  "cond": [
    {
      "idx": 1,
      "type": 2,
      "id": "010000124b00170f865a",
      "ep": 1,
      "op": 1,
      "cmd": "on",
      "val": "false"
    }
  ],
  "act": [
    {
      "idx": 1,
      "delay": 1,
      "type": 1,
      "id": "010000124b00170a05c2",
      "ep": 1,
      "cmd": "on",
      "val": false
    }
  ]
}
'''

json3 = '''
{
  "code": 1013,
  "serial": 1520667056959,
  "name": "shuangkong",
  "rid": 231113,
  "state": 1,
  "trig": 0,
  "ct": "2018-03-10T15:30:57",
  "exp": "function main(a1,b1) if (a1==b1) then return true else return false end end",
  "cond": [
    {
      "idx": 1,
      "type": 2,
      "id": "010000124b00170a05c2",
      "ep": 1,
      "op": 1,
      "cmd": "on",
      "val": "false"
    }
  ],
  "act": [
    {
      "idx": 1,
      "delay": 1,
      "type": 1,
      "id": "010000124b00170f865a",
      "ep": 1,
      "cmd": "on",
      "val": false
    }
  ]
}
'''

json4 = '''
{
  "code": 1013,
  "serial": 1520667056959,
  "name": "shuangkong",
  "rid": 231114,
  "state": 1,
  "trig": 0,
  "ct": "2018-03-10T15:30:57",
  "exp": "function main(a1,b1) if (a1==b1) then return true else return false end end",
  "cond": [
    {
      "idx": 1,
      "type": 2,
      "id": "010000124b00170a05c2",
      "ep": 1,
      "op": 1,
      "cmd": "on",
      "val": "true"
    }
  ],
  "act": [
    {
      "idx": 1,
      "delay": 1,
      "type": 1,
      "id": "010000124b00170f865a",
      "ep": 1,
      "cmd": "on",
      "val": true
    }
  ]
}
'''

json5 = '''
{
"code":1015,
"rid":231111,
"serial" :12004
}'''

json6 = '''
{
"code":1015,
"rid":231112,
"serial" :12004
}'''

json7 = '''
{
"code":1015,
"rid":231113,
"serial" :12004
}'''

json8 = '''
{
"code":1015,
"rid":231114,
"serial" :12004
}'''