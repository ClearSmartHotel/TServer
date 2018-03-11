# -*- coding: utf-8 -*-

import time

from common.DBBase import db


def getGwList():
    gwList = db.select("ROOM")
    gwList = list(gwList)
    cTime = time.time()
    for gw in gwList:
        lastTime = gw.get("last_timestamp")
        if cTime - lastTime < 60:
            gw.update({"ol" : 1})
        else:
            gw.update({"ol" : 0})
    return gwList

def getGwInfo(gw_mac):
    gInfo = db.select("ROOM",where = {"gw":gw_mac}).first()
    if gInfo is None:
        return None
    cTime = time.time()
    lastTime = gInfo.get("last_timestamp")
    if cTime - lastTime < 60:
        gInfo.update({"ol" : 1})
    else:
        gInfo.update({"ol" : 0})
    return gInfo

def getDevList(gw_mac):
    devList = db.select("DEVICE", where = {"gw" : gw_mac})
    return list(devList)

def getDevInfo(id,ep):
    dev = db.select("DEVICE", where = {"id" : id, "ep" :ep }).first()
    if dev is None:
        print "Dev not found id: %s ep: %s" %(str(id),str(ep))
        return None
    else:
        return dev

