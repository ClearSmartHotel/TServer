# -*- coding: utf-8 -*-
import time

from common.DBBase import db, db_replace
import json
import constant
import mqtt_client
from common import config
import protocol
import thread


'''
包头|版本号|主机ID     |包总数|包序号|包类型       |包详情      |   数据长度 |数据    |校验字段
1Byte|1Byte|3Byte[4:10]|1Byte |1Byte | 1Byte[14:16]|2Byte[16:20]|1Byte[20:22]|  NByte|  1Byte|
'''
def dataPrase(clinet_msg, msg):
    packetType = msg[14:16]
    print "packetType:",packetType
    if packetType == '01':# 查询推送响应
        statusNotify(msg)
    elif packetType == '02':# 控制推送响应
        controlResponePacket(msg)
    elif packetType == '03':# 服务上传请求回复
        serviceUploadPacket(clinet_msg, msg)
    print clinet_msg,msg

def statusNotify(msg):
    statusType = msg[16:18]
    print "statusType:",statusType
    if statusType == '01':#温湿度
        curTemp = int(msg[22:24],16)
        print "curTemp:",curTemp
        ret = db.select("ALIVE_DEVICE", where={"aliveRcuId": msg[4:10],"clearDevType": 'alive_airCondition'}).first()
        if ret is not None:
            st = ret.get("devStatus", None)
            if st is not None:
                stJson = json.loads(ret['devStatus'])
                stJson['currentTemp'] = curTemp
            else:
                stJson = {'currentTemp' : curTemp}
            print "stJson:", stJson
            devInfo = {'devStatus': json.dumps(stJson)}
            db.update("ALIVE_DEVICE", where={"aliveRcuId": msg[4:10],"clearDevType": 'alive_airCondition'}, **devInfo)
    elif statusType == '02':#服务状态
        pass
    elif statusType == '03':#空调状态
        pass
    elif statusType == '04':#主机ID查询
        rcuInfo = {'aliveRcuId': msg[4:10],
                   'last_timestamp': time.time()}
        db_replace("ROOM", {"aliveRcuId": msg[4:10]}, rcuInfo)
        send_cmd(msg[4:10])

def controlResponePacket(msg):
    result = msg[-4:-3]
    print "control result:",result
    if result == '00':
        print "control cmd success"
    elif result == '01':
        print "control cmd busy"
    elif result == '02':
        print "control cmd error"

def serviceUploadPacket(clinet_msg, msg):
    msgInfo = {'aliveRcuId':msg[4:10],
               'onLine':1}
    devId = msg[4:10] + msg[14:20]
    msgInfo['devId'] = devId
    room = db.select("ROOM", where={"aliveRcuId": msg[4:10]}).first()
    if room is None:
        return 0
    if msg[18:20] == '01': #插卡取电
        msgInfo['devActionCode'] = int(msg[22:24], 16)
        db_replace("ALIVE_DEVICE", {"aliveRcuId": msg[4:10], "devId": devId}, msgInfo)
        if msgInfo['devActionCode'] == 0:#插卡
            thread.start_new_thread(welcomeStrategy, (room, 1))
        else:#拔卡
            thread.start_new_thread(goodbyeStrategy, (room, 2))
            thread.start_new_thread(goodbyeStrategy, (room, 4))
    elif msg[18:20] == '02':#服务状态
        for id in range(1, int(msg[20:22], 16), 2):
            step = id * 2
            msgInfo['devId'] = msg[4:10] + msg[14:20] + msg[20+step:22+step]
            msgInfo['devActionCode'] = int(msg[22+step:24+step], 16)

            print "service id:", msg[20+step:22+step]
            if msg[20+step:22+step] not in {'1a', '1b', '1c'}:#除了service继电器，其它继电器不用记录
                continue
            db_replace("ALIVE_DEVICE", {"aliveRcuId": msg[4:10], "devId": msgInfo['devId']}, msgInfo)

            mqttJson = {
                "wxCmd": "devStatus",
                "devName": constant.ALIVE_SERVICE[msg[20+step:22+step]],
                "onLine": 1,
                "actionCode": msgInfo['devActionCode']
            }
            mqtt_client.publish_message(config.project_name + room['roomNo'], json.dumps(mqttJson))
    elif msg[18:20] == '03':#空调状态
        stringValue = msg[24:52]
        statusJson = {'stringValue': stringValue,
                      'mode':constant.ALVIE_2API_MODE_TUP[int(stringValue[0:2], 16)],
                      'setTemp': int(stringValue[2:4], 16) + 16,
                      'speed': constant.ALVIE_2API_SPEED_TUP[int(stringValue[4:6], 16)],
                      'switch': 2 - int(stringValue[20:22], 16)%2}
        ret = db.select("ALIVE_DEVICE", where={"aliveRcuId": msg[4:10], "clearDevType": 'alive_airCondition'}).first()
        if ret is not None:
            stJson = json.loads(ret['devStatus'])
            statusJson['currentTemp'] = stJson['currentTemp']
        else:
            statusJson['currentTemp'] = 20
            send_cmd(msg[4:10])

        msgInfo['devActionCode'] = int(msg[44:46],16)
        msgInfo['devStatus'] = json.dumps(statusJson)

        db_replace("ALIVE_DEVICE", {"aliveRcuId": msg[4:10],"devId":devId}, msgInfo)

        mqttJson = {
            "wxCmd": "devStatus",
            "devName": '空调',
            "onLine": 1,
            "actionCode": msgInfo['devActionCode'],
            'devStatus':statusJson
        }
        mqtt_client.publish_message(config.project_name + room['roomNo'], json.dumps(mqttJson))


    elif msg[18:20] == '04':#当前温度上传
        curTemp = int(msg[22:24], 16)
        print "curTemp:", curTemp
        ret = db.select("ALIVE_DEVICE", where={"aliveRcuId": msg[4:10],"clearDevType": 'alive_airCondition'}).first()
        if ret is not None:
            st = ret.get("devStatus", None)
            if st is not None:
                stJson = json.loads(ret['devStatus'])
                print "stjson:",stJson
                stJson['currentTemp'] = curTemp
            else:
                stJson = {'currentTemp': curTemp}
            print "stJson:", stJson
            devInfo = {'devStatus': json.dumps(stJson)}
            db.update("ALIVE_DEVICE", where={"aliveRcuId": msg[4:10], "clearDevType": 'alive_airCondition'},**devInfo)

    #将状态更新推送到websocket客户端
    statusJson['wsCmd'] = statusJson.pop('wxCmd')
    statusJson['roomNo'] = dev['roomNo']
    websocketServer.send_message_to_all(json.dumps(statusJson))


def checkMsg(hexString):
    # print "response hexString:",hexString
    bytesData = bytearray.fromhex(hexString)
    totalNum = 0
    for b in bytesData[0:]:
        totalNum += b
    chekcNum = totalNum % 256
    bytesData.append(chekcNum)
    return str(bytesData)

def send_cmd(aliveRcuId):
    from alive_proxy import AliveProxyFactory
    # valueString = '9f01' + aliveRcuId + '0101' + '020102' + '0f01' + '0000000000000000000000000000'
    cmdMsg = '9f01' + aliveRcuId + '0101' + '010100' + '00'
    sendOut = 0

    for info in AliveProxyFactory.clients.values():
        print "alive rcu Info item : ", info
        if info.get("aliveRcuId") == aliveRcuId:
            transport = info.get("transport")
            transport.write(checkMsg(cmdMsg))
            sendOut = 1
            break
    if sendOut == 0:
        print "!! Send msg faild!, aliveRcuId : ", aliveRcuId
        print " faild msg : ", cmdMsg
    else:
        print "Send Msg ok : aliveRcuId %s" % aliveRcuId, cmdMsg

def controlService(dev, dictData):
    aliveRcuId = dev['devId'][0:6]
    dev = dev['devId'][-2:]
    action = dictData['actionCode']
    cmdMsg = '9f01' + aliveRcuId + '0101' + '020201' + '02' + dev + '0' + str(action)
    sendOut = sendMessage(aliveRcuId, cmdMsg)



def controlAirCondition(room, dev, devStatus):
    localStatus = json.loads(dev.get('devStatus', {}))
    airConditionCmd = localStatus['stringValue']
    print "airConditionCmd:", airConditionCmd
    for k, v in devStatus.items():
        if localStatus[k] != v:
            print "key:", k
            if k == 'setTemp':
                airConditionCmd = airConditionCmd[0:2] + str(int(str(hex(v))[-2]) - 1) + str(hex(v))[
                    -1] + airConditionCmd[4:]
                if localStatus[k] < v:  # 温度加
                    print "add temp :", devStatus['mode'], localStatus['currentTemp'], v
                    if devStatus['mode'] == 1 and localStatus['currentTemp'] >= v:  # 制冷时setTemp大于currentTemp，无效
                        print "invalid temp"
                        # fixme 错误数据处理
                        return 0
                    else:
                        airConditionCmd = airConditionCmd[0:18] + '01' + airConditionCmd[20:]

                else:  # 温度减
                    if devStatus['mode'] == 2 and localStatus['currentTemp'] >= v:  # 制热时setTemp小于currentTemp，无效

                        print "invalid temp"
                        # fixme 错误数据处理
                        return 0
                    else:
                        airConditionCmd = airConditionCmd[0:18] + '02' + airConditionCmd[20:]
            elif k == 'switch':
                if v == 2:  # 关闭空调
                    airConditionCmd = '0000000000000000000000000000'
                else:
                    airConditionCmd = '0000000000000000000021000000'
            elif k == 'mode':
                airConditionCmd = constant.ALVIE_AIRMODE_TUP[v - 1] + airConditionCmd[2:18] + '03' + airConditionCmd[20:]
            elif k == 'speed':
                airConditionCmd = airConditionCmd[0:4] + constant.ALVIE_AIRSPEED_TUP[v - 1] + airConditionCmd[6:18] + '04' + airConditionCmd[20:]
            break

    cmdMsg = '9f01' + room['aliveRcuId'] + '0101' + '020102' + '0f01' + airConditionCmd

    sendOut = sendMessage(room['aliveRcuId'], cmdMsg)

    if sendOut == 1:
        statusJson = {'stringValue': airConditionCmd,
                      'mode': constant.ALVIE_2API_MODE_TUP[int(airConditionCmd[0:2], 16)],
                      'setTemp': int(airConditionCmd[2:4], 16) + 16,
                      'speed': constant.ALVIE_2API_SPEED_TUP[int(airConditionCmd[4:6], 16)],
                      'switch': 2 - int(airConditionCmd[20:22], 16) % 2}
        ret = db.select("ALIVE_DEVICE", where={"aliveRcuId": room['aliveRcuId'], "clearDevType": 'alive_airCondition'}).first()
        if ret is not None:
            stJson = json.loads(ret['devStatus'])
            statusJson['currentTemp'] = stJson['currentTemp']
        else:
            statusJson['currentTemp'] = 20
            send_cmd(room['aliveRcuId'])
        msgInfo = {'devStatus': json.dumps(statusJson)}
        db_replace("ALIVE_DEVICE", {"aliveRcuId": room['aliveRcuId'], "clearDevType": 'alive_airCondition'}, msgInfo)


def sendMessage(aliveRcuId, cmdMsg):
    from alive_proxy import AliveProxyFactory
    sendOut = 0

    for info in AliveProxyFactory.clients.values():
        print "alive rcu Info item : ",info
        if info.get("aliveRcuId") == aliveRcuId:
            transport = info.get("transport")
            transport.write(checkMsg(cmdMsg))
            sendOut = 1
            break
    if sendOut == 0:
        print "!! Send msg faild!, aliveRcuId : ",aliveRcuId
        print " faild msg : ",cmdMsg
    else:
        print "Send Msg ok : aliveRcuId %s" %aliveRcuId,cmdMsg
    return sendOut

def welcomeStrategy(room, interval):
    print "welcomeStrategy:", room['roomNo']
    protocol.openWindow(room)
    time.sleep(2)
    cardInfo = db.select('ALIVE_DEVICE', where={'clearDevType': constant.ALIVE_CLEARTYPE_CARD, 'aliveRcuId': room['aliveRcuId']}).first()
    if cardInfo is not None and cardInfo['devActionCode'] == 0:
        protocol.welcomeFunc(room)
    thread.exit()

def goodbyeStrategy(room, interval):
    print "goodbyeStrategy:", room['roomNo']
    time.sleep(interval)
    print "goodbyeStrategy thread"
    cardInfo = db.select('ALIVE_DEVICE', where={'clearDevType': constant.ALIVE_CLEARTYPE_CARD,
                                                'aliveRcuId': room['aliveRcuId']}).first()
    if cardInfo is not None and cardInfo['devActionCode'] == 1:
        protocol.closeWindow(room)
    thread.exit()

