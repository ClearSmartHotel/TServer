
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

    # 更新网关状态:
    macInfo = {
        "MAC": data["gw"]["mac"],
        "LAST_TIMESTAMP": time.time()
    }
    db_replace("GETWAY",{"MAC": macInfo["MAC"]},macInfo)

    #更新设备列表:
    dList = data["device"]
    for device in dList:
        device["gw"]  = macInfo["MAC"]
        device["time_last"] = time.time()
        db_replace("DEVICE", {"id": device["id"] , "ep" :device["ep"]}, device)




