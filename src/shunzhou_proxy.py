# -*- coding: utf-8 -*-

import json,thread,time

from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from protocol import dataPrase

#保存连接相关数据
class ShunzhouProxy():

    def __init__(self, client, factory, transport):
        #用于发送消息
        self.transport = transport
        self.client = client
        self.factory = factory

        #缓存收到的数据
        self.recv_buf = ''
        self.recv_buf_len = 0
        self.recv_buf_analyse_pos = 0
        self.brace_stack = []
        self.data_recv_count_within_a_json = 0

        #连接的网关标识
        self.gw_id = ''
        self.gw_mac = ''

    #收到一个json包后，会调用此函数
    def handleJson(self, json_obj):
        print "handle json:"
        print json.dumps(json_obj)
        #self.transport.write(json.dumps(json_obj))
        #更新客户端信息
        self.factory.clients[self.client].update({"transport": self.transport})
        #处理接收数据
        gw_mac = dataPrase(self.factory.clients[self.client],json_obj)
        #更新客户端信息
        if gw_mac is not None:
            self.factory.clients[self.client].update({"gw" : gw_mac})
            print "get gw_mac message :" , self.factory.clients[self.client]



class ShunzhouProxyProtocol(Protocol):

    MAX_DATA_RECV_COUNT_WITH_A_JSON = 10

    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        print "shunzhou new connection come"
        self.transport.shunzhou_proxy = ShunzhouProxy(self ,self.factory, self.transport)
        self.factory.addClient(self)
        print "shunzhou clients num:" + str(len(self.factory.clients))

    def connectionLost(self, reason):
        print "connection lost: " + reason.getErrorMessage()
        self.factory.deleteClient(self)

    def dataReceived(self, data):
        print "data recv: " + data + "\n"

        self.transport.shunzhou_proxy.recv_buf += data
        self.transport.shunzhou_proxy.recv_buf_len += len(data)
        self.transport.shunzhou_proxy.data_recv_count_within_a_json += 1

        while True:
            json_obj = self.checkJsonComplete()
            if json_obj == None:
                break
            else:
                self.transport.shunzhou_proxy.handleJson(json_obj)

    def checkJsonComplete(self):
        '''
        需要大括号 { } 不出现在数据内容里

        TODO:
        1. 每次 } 都尝试一下获取json？
        2. 判断 { 后跟"（可有空格） 而不是只判断 { 作为开头 ？
        3. 错误消息过多，关闭连接，等待重连
        :return:
        '''
        json_obj = None
        i = self.transport.shunzhou_proxy.recv_buf_analyse_pos
        while i < self.transport.shunzhou_proxy.recv_buf_len:
            self.transport.shunzhou_proxy.recv_buf_analyse_pos += 1

            if self.transport.shunzhou_proxy.recv_buf[i] == '{':
                self.transport.shunzhou_proxy.brace_stack.append('{');
            elif self.transport.shunzhou_proxy.recv_buf[i] == '}':
                self.transport.shunzhou_proxy.brace_stack.pop();
                if len(self.transport.shunzhou_proxy.brace_stack) == 0:
                    #try to load json
                    try:
                        #print self.transport.shunzhou_proxy.recv_buf[0:i+1]
                        json_obj = json.loads(self.transport.shunzhou_proxy.recv_buf[0:i+1])

                        self.transport.shunzhou_proxy.recv_buf = self.transport.shunzhou_proxy.recv_buf[i + 1:]
                        self.transport.shunzhou_proxy.recv_buf_len = len(self.transport.shunzhou_proxy.recv_buf)
                        self.transport.shunzhou_proxy.recv_buf_analyse_pos = 0
                        self.transport.shunzhou_proxy.data_recv_count_within_a_json = 0
                        #print "left: " + self.transport.shunzhou_proxy.recv_buf
                        break
                    except:
                        print "try to load a complete json fail, wait for more data"

                        if self.transport.shunzhou_proxy.data_recv_count_within_a_json > self.MAX_DATA_RECV_COUNT_WITH_A_JSON:
                            print "can not build a json msg within too many data recved:"
                            print self.transport.shunzhou_proxy.recv_buf
                            print "close connection..."
                            self.transport.loseConnection()

                        pass
            else:
                pass
            i += 1

        return json_obj


class ShunzhouProxyFactory(Factory):
    clients = {}

    def buildProtocol(self, addr):
        return ShunzhouProxyProtocol(self)
    def addClient(self, newclient):
        print(newclient)
        self.clients[newclient] = { "gw" : None, "transport" : None}
    def deleteClient(self, client):
        print(client)
        del self.clients[client]

