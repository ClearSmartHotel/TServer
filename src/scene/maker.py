# -*- coding: utf-8 -*-

import json,time,random
from common.DBBase import db,db_replace
from common.func import str2List
import protocol
import thread

def getSerial():
    return random.randint(0,1000)

class StrategyMaker:
    def __init__(self,roomNo):
        rInfo = db.select("ROOM", where={"roomNo" : roomNo}).first()
        if rInfo is None:
            print "roomNo is not exist: %s" % str(roomNo)
            raise Exception("roomNo is not exist: %s" % str(roomNo))

        self.room_type = rInfo["room_type"]
        self.gw_mac = rInfo["gw"]
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
        protocol.sendMessage(self.gw_mac, req)

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
        sql = "select name,id,ep,gw,tigger,act,delay from %s s,DEVICE d where d.gw = \"%s\" and s.name=d.devName and s.room_type=\"%s\"" %(str(table),self.gw_mac,self.room_type)
        print "json maker sql: " , sql
        sDevList = db.query(sql)
        sDevList = list(sDevList)
        print json.dumps(sDevList)

        self.rid = sInfo.get("rid")
        #生成策略Josn
        sJson = {
            "code":1013,
            "serial" :getSerial(),
            "name":name,
            "rid": self.rid,
            "state":1,
            "trig" :0,
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
                condIdx += 1
            else:                   #act 执行动作
                obj = {
                    "idx": actIdx,
                    "delay" : dev.get("delay",0),
                    "type" : 1,
                    "id" : dev["id"],
                    "ep" : dev["ep"]
                }
                print "act:" ,str(dev.get("act"))
                act = json.loads(dev.get("act"))
                obj.update(act)
                sJson["act"].append(obj)
                actIdx += 1
        print "scene json"
        print json.dumps(sJson)
        # self.sJson = sJson
        # return  sJson
        self.sJson = ruleJson
        return json.dumps(ruleJson)

    def send2gw(self):
        self.delStrategy(self.rid)
        protocol.sendMessage(self.gw_mac,self.sJson)
        return

class GroupMaker:
    def __init__(self,roomNo):
        rInfo = db.select("ROOM", where={"roomNo" : roomNo}).first()
        if rInfo is None:
            print "roomNo is not exist: %s" % str(roomNo)
            raise Exception("roomNo is not exist: %s" % str(roomNo))
        self.room_type = rInfo["room_type"]
        self.gw_mac = rInfo["gw"]
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
        protocol.sendMessage(self.gw_mac, req)

    def send2gw(self):
        self.delGroup(self.gid)
        protocol.sendMessage(self.gw_mac, self.gjson)

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
        protocol.sendMessage(self.gw_mac, req)

def setAllScene(roomNo):
    sMaker = StrategyMaker(roomNo)
    sList = sMaker.getSupportStrategyList()
    sleepTime = 1
    for s in sList:
        thread.start_new_thread(makeStrategyFun,(sMaker, s['name'], sleepTime))
        sleepTime += 2
        # sMaker.makeStrategyJson(s['name'])
        # sMaker.send2gw()


    gMaker = GroupMaker(roomNo)
    gMaker.makeJson("all_light")
    gMaker.send2gw()

def makeStrategyFun(sMaker, name, sleepTime):
    time.sleep(sleepTime)
    sMaker.makeStrategyJson(name)
    sMaker.send2gw()

def setSingleScene(roomNo, stragegy):
    sMaker = StrategyMaker(roomNo)
    sMaker.makeStrategyJson(stragegy)
    sMaker.send2gw()

def setGroup(roomNo, groupName):
    gMaker = GroupMaker(roomNo)
    gMaker.makeJson(groupName)
    gMaker.send2gw()

def controlGroup(roomNo, groupName, paraDict):
    gMaker = GroupMaker(roomNo)
    gMaker.sendControlDict(groupName, paraDict)

ruleJson = {
	"state": 1,
	"code": 1013,
	"cond": [{
		"val": "true",
		"idx": 1,
		"cmd": "on",
		"type": 2,
		"id": "010000124b000e0c0395",
		"ep": 1
	}],
	"name": "明亮模式",
	"exp": "function main(a1,b1) if (a1==b1) then return true else return false end end",
	"act": [{
		"delay": 0,
		"val": 1,
		"idx": 1,
		"cmd": "on",
		"type": 3,
		"gid": 1
	}],
	"serial": 346,
	"rid": 3,
	"trig": 0,
	"ct": "2018-03-17T20:04:38"
}
