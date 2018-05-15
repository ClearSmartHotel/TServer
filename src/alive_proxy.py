# -*- coding: utf-8 -*-

import re

from twisted.internet.protocol import Factory, Protocol
from alive_protocol import dataPrase

#保存连接相关数据
class AliveProxy():

    def __init__(self, client, factory, transport):
        #用于发送消息
        self.transport = transport
        self.client = client
        self.factory = factory

        #缓存收到的数据
        self.recv_buf = ''
        self.recv_buf_len = 0
        self.recv_buf_analyse_pos = 0
        self.data_recv_count_within_a_data = 0

    #收到一个有效包后，会调用此函数
    def handleData(self, hexString):
        print "handle hexString:",hexString
        #更新客户端信息
        print "aliveRcuId:",hexString[4:10]
        self.factory.clients[self.client].update({"aliveRcuId": hexString[4:10]})
        self.factory.clients[self.client].update({"transport": self.transport})

        dataPrase(self.factory.clients[self.client], hexString)

class AliveProxyProtocol(Protocol):

    MAX_DATA_RECV_COUNT_WITH_A_DATA = 4

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        print "alive new connection come"
        self.transport.alive_proxy = AliveProxy(self ,self.factory, self.transport)
        print "info:",self.transport.getPeer()
        # a = '9f01001d4c0101010100000d'
        # 查询RCUID
        a = '9f01ffffff010101040000a4'
        b = bytearray.fromhex(a)
        self.transport.write(str(b))
        self.factory.addClient(self)
        print "alive clients num:" + str(len(self.factory.clients))

    def connectionLost(self, reason):
        print "connection lost: " + reason.getErrorMessage()
        self.factory.deleteClient(self)

    def dataReceived(self, data):
        try:
            hexString = data.encode('hex')
            print "recive data:",hexString
            self.transport.alive_proxy.recv_buf += hexString
            self.transport.alive_proxy.recv_buf_len += len(hexString)
            self.transport.alive_proxy.data_recv_count_within_a_data += 1
        except Exception as e:
            print "get wrong data,error msg:",e.message

        while True:
            valuedStr = self.checkValuedStr()
            if valuedStr == None:
                break
            else:
                self.transport.alive_proxy.handleData(valuedStr)

    def checkValuedStr(self):
        valuedStr = None
        if self.transport.alive_proxy.recv_buf_len < 24:
            return valuedStr
        i = self.transport.alive_proxy.recv_buf_analyse_pos
        while i < self.transport.alive_proxy.recv_buf_len:
            self.transport.alive_proxy.recv_buf_analyse_pos += 1
            # 包头为0x9f,协议为01，且长度不小于12个字节为有效数据包
            if re.match('9f01', self.transport.alive_proxy.recv_buf[i:]):
                try:
                    packetDataByte = self.transport.alive_proxy.recv_buf[i + 20:i + 22]
                    packetLen = 24 + 2 * int(packetDataByte, 16)
                    valuedStr = self.transport.alive_proxy.recv_buf[i:i + packetLen]

                    bytesData = bytearray.fromhex(valuedStr)
                    chekcNum = bytesData[-1]
                    totalNum = 0
                    for b in bytesData[0:-1]:
                        totalNum += b
                    # 最后一个字节为校验字段，值为所有字段求和%256
                    if totalNum % 256 == chekcNum:
                        self.transport.alive_proxy.recv_buf = self.transport.alive_proxy.recv_buf[i + packetLen:]
                        self.transport.alive_proxy.recv_buf_len = len(self.transport.alive_proxy.recv_buf)
                        self.transport.alive_proxy.recv_buf_analyse_pos = 0
                        self.transport.alive_proxy.data_recv_count_within_a_data = 0
                        break
                    else:
                        valuedStr = None
                except:
                    print "try to load a valued data fail, wait for more data"
                    if self.transport.alive_proxy.data_recv_count_within_a_data > self.MAX_DATA_RECV_COUNT_WITH_A_DATA:
                        print "can not build a json msg within too many data recved:"
                        print self.transport.alive_proxy.recv_buf
                        print "close connection..."
                        self.transport.loseConnection()
                    valuedStr = None
            else:
                pass
            i += 1

        return valuedStr

class AliveProxyFactory(Factory):
    clients = {}

    def buildProtocol(self, addr):
        print "addr:",addr
        return AliveProxyProtocol(self)
    def addClient(self, newclient):
        print(newclient)
        self.clients[newclient] = { "aliveRcuId" : None, "transport" : None}
    def deleteClient(self, client):
        print(client)
        del self.clients[client]

