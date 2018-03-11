# -*- coding: utf-8 -*-

import json,time,random
from common.DBBase import db,db_replace
from protocol import sendMessage
from common.func import str2List

def getSerial():
    return random.randint(0,1000)

class StrategyMaker:
    def __init__(self,gw_mac,room_type):
        self.room_type = room_type
        self.gw_mac = gw_mac
        self.sJson = {}
        pass

    def getSupportStrategyList(self):
        sList = db.select("STRATEGY_ALL_INDEX",what = "id,name")
        return  list(sList)

    def delStrategy(self,rid):
        req = {
            "code":1015,
            "rid" : rid,
            "serial" : getSerial(),
        }
        sendMessage(self.gw_mac, req)

    def makeStrategyJson(self,name):
        #得到策略 的 信息
        sInfo = db.select("STRATEGY_ALL_INDEX",where = {"name": name}).first()
        print sInfo
        if sInfo is None:
            print "Strategy is not support ! name: %s"%name
            raise Exception("Strategy is not support ! name: %s"%name)
        else:
            table = sInfo.get("table_name")

        #得到场景的设备列表
        sql = "select name,id,ep,gw,tigger,act from %s s,DEVICE d where d.gw = \"%s\" and s.name=d.devName and s.room_type=\"%s\"" %(str(table),self.gw_mac,self.room_type)
        print "json maker sql: " , sql
        sDevList = db.query(sql)
        sDevList = list(sDevList)
        print list(sDevList)

        self.rid = sInfo.get("rid"),
        #生成策略Josn
        sJson = {
            "code":1013,
            "serial" :getSerial(),
            "name":name,
            "rid": self.rid,
            "state":1,
            "trig" :1,
            "ct":time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
            "exp":"function main(a1,b1) if (a1==b1) then return true else return false end end",
            "cond" : [],
            "act" : []
        }
        #TODO: 获取策略列表 生成不重复 的rid  暂时用时间的Timestamp
        condIdx = 1
        actIdx = 1
        for dev in sDevList:
            if dev.get("tigger") == 1: #cond 触发器
                obj = {
                    "idx" : condIdx,
                    "type":2,
                    "id":dev["id"],
                    "ep":dev["ep"]
                }
                act = json.loads(dev.get("act"))
                obj.update(act)
                sJson["cond"].append(obj)
            else:                   #act 执行动作
                obj = {
                    "idx": actIdx,
                    "delay" : dev.get("delay",0),
                    "type" : 2,  # TODO: 确认para18参数的值
                    "id" : dev["id"],
                    "ep" : dev["ep"]
                }
                act = json.loads(dev.get("act"))
                obj.update(act)
                sJson["act"].append(obj)
        print json.dumps(sJson)
        self.sJson = sJson
        return  sJson

    def send2gw(self):
        self.delStrategy(self.rid)
        sendMessage(self.gw_mac,self.sJson)
        return

class GroupMaker:
    def __init__(self,gw_mac,room_type):
        self.room_type = room_type
        self.gw_mac = gw_mac
        pass
    def getInfo(self,name):
        gInfo = db.select("GROUP_INFO", where={"group_name": name}).first()
        if gInfo is None:
            print "group is not found ! name: %s"%name
            raise Exception("group is not found ! name: %s"%name)
        return gInfo

    def makeJson(self,name):
        # 得到分组 的 信息
        gInfo = self.getInfo(name)
        self.gid = gInfo.get("gid")
        gJson = {
            "code":1005,
            "name":name,
            "gid": self.gid,
            "serial" :getSerial(),
            "device":[]
        }
        #得到设备列表信息
        devList = gInfo.get("dev_list")
        devList = str2List(devList)
        for devName in devList:
            devInfo = db.select("DEVICE",where = {"devName":devName,"gw":self.gw_mac}).first()
            if devInfo is not None:
                gJson["device"].append({"id": devInfo["id"],"ep" : devInfo["ep"]})
        print json.dumps(gJson)
        self.gjson  = gJson

    def delGroup(self,gid):
        req = {
            "code":1007,
            "gid" : gid,
            "serial" : getSerial(),
        }
        sendMessage(self.gw_mac, req)

    def send2gw(self):
        self.delGroup(self.gid)
        sendMessage(self.gw_mac, self.gjson)

    def sendControlDict(self,group_name , paraDict):
        # 得到分组 的 信息
        gInfo = self.getInfo(group_name)
        self.gid = gInfo.get("gid")

        #发出请求
        req = {
            "code":1006,
            "gid":self.gid,
            "serial" :getSerial(),
            "streams": paraDict
        }
        sendMessage(self.gw_mac, self.gjson)



def testFunc():
    sMaker = StrategyMaker("2c:6a:6f:00:52:6f","标准")
    sMaker.makeStrategyJson("睡眠")
    sMaker.send2gw()

    gMaker = GroupMaker("2c:6a:6f:00:52:6f","标准")
    gMaker.makeJson("all_light")
    gMaker.send2gw()
    gMaker.sendControlDict("all_light",{"on" : 1})

#testFunc()