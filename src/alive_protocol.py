# -*- coding: utf-8 -*-
import time

from common.DBBase import db, db_replace

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
        pass
    elif statusType == '02':#服务状态
        pass
    elif statusType == '03':#空调状态
        pass
    elif statusType == '04':#主机ID查询
        rcuInfo = {'aliveRcuId': msg[4:10],
                   'last_timestamp': time.time()}
        db_replace("ROOM", {"aliveRcuId": msg[4:10]}, rcuInfo)

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
    responseMsg = msg[0:20] + '00'
    transport = clinet_msg.get("transport")
    msgInfo = {'rcuId':msg[4:10],
               'onLine':1,
               'devActionCode':int(msg[22:24],16)}
    db_replace("ALIVE_DEVICE", {"rcuId": msg[4:10]}, msgInfo)
    responeStr = checkMsg(responseMsg)
    transport.write(responeStr)
    print "Send response ok: ", responseMsg

def checkMsg(hexString):
    print "response hexString:",hexString
    bytesData = bytearray.fromhex(hexString)
    totalNum = 0
    for b in bytesData[0:]:
        totalNum += b
    chekcNum = totalNum % 256
    bytesData.append(chekcNum)
    return str(bytesData)