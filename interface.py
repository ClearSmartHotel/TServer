# -*- coding: utf-8 -*-

import json,time
from common.DBBase import db,db_replace

def getGwList():
    gwList = db.select("GETWAY")
    gwList = list(gwList)
    cTime = time.time()
    for gw in gwList:
        lastTime = gw.get("LAST_TIMESTAMP")
        if cTime - lastTime < 60:
            gw.update({"ol" : 1})
        else:
            gw.update({"ol" : 0})
    return gwList

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

