# -*- coding: utf-8 -*-

import json,time,random
from common.DBBase import db,db_replace
from protocol import sendMessage

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
            "code":rid,
            "serial" : getSerial(),
        }
        sendMessage(self.gw_mac, req)

    def makeStrategyJson(self,name):
        #得到场景 的 信息
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
            "serial" :random.randint(0,1000),
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


def testFunc():
    testMaker = StrategyMaker("2c:6a:6f:00:52:6f","标准")
    testMaker.makeStrategyJson("睡眠")
    testMaker.send2gw()

testFunc()