
# -*- coding: utf-8 -*-

import json
from common.DBBase import db,db_replace
import time


def dataPrase(json_obj):
    code = json_obj.get("code","")
    if code == 101:
        heartBeat(json_obj)
        pass
    elif code == 104:
        pass

def heartBeat(data):
    print "Get Heart Beat ."
    # 更新网关状态:
    macInfo = {
        "MAC": data["gw"]["mac"],
        "LAST_TIMESTAMP": time.time()
    }
    db_replace("GETWAY",{"MAC": macInfo["MAC"]},macInfo)

    #更新设备列表:
    dList = data["device"]
    keyList = ["id","ol","ep","pid","did","on","coolset","heartset","thermode","pt","wtype"]
    for device in dList:
        devInfo = {
            "gw" : macInfo["MAC"],
            "time_last" : time.time()
        }
        for k in keyList:
            devInfo.update(k,device.get(k,None))

        db_replace("DEVICE", {"id": devInfo["id"] , "ep" :devInfo["ep"]}, devInfo)


