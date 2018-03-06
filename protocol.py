
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
    if "gw" in data:
        macInfo = {
            "MAC": data["gw"]["mac"],
            "LAST_TIMESTAMP": time.time()
        }
        db_replace("GETWAY",{"MAC": macInfo["MAC"]},macInfo)

    #更新设备列表:
    dList = data["device"]
    keyList = ["id","ol","ep","pid","did","coolset","heartset","thermode","pt","wtype"]
    for device in dList:
        devInfo = {
            "id" : device.get("id"),
            "gw" : data.get("gw",{}).get("mac",""),
            "ol" : device.get("ol"),
            "ep" : device.get("ep"),
            "pid" : device.get("pid",None),
            "did" : device.get("did",None),
            "onoff": device.get("sw", {}).get("on", None),
            "coolset" :  device.get("sw",{}).get("coolset",None),
            "heartset": device.get("sw", {}).get("heartset", None),
            "thermode": device.get("sw", {}).get("thermode", None),
            "pt": device.get("sw", {}).get("pt", None),
            "wtype": device.get("sw", {}).get("wtype", None),
            "time_last" : time.time()
        }

        db_replace("DEVICE", {"id": devInfo["id"] , "ep" :devInfo["ep"]}, devInfo)


