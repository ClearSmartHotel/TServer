# -*- coding: utf-8 -*-


import thread
import time

import haier_proxy
import mqtt_client
from protocol import testFunc
from shunzhou_proxy import ShunzhouProxyFactory, reactor, TCP4ServerEndpoint
from alive_proxy import AliveProxyFactory
import websocketServer

#测试用定时器线程，
def timerTest(no, interval):
    print "timer thread start"
    while True:
        time.sleep(interval)
        print "runing"
        testFunc()

    thread.exit_thread()


# thread.start_new_thread(timerTest,(1,2))

#海尔websocket client
rcu_ws = haier_proxy.haier_rcu_websocket()
rcu_ws.start()

#启动mqtt
m = mqtt_client.mqtt_task()
m.start()

#启动websocketserver
websocketServer.websocket_server.start()

endpoint = TCP4ServerEndpoint(reactor, 6666)
endpoint.listen(ShunzhouProxyFactory())
endpoint_olv = TCP4ServerEndpoint(reactor, 6667)
endpoint_olv.listen(AliveProxyFactory())
reactor.run()



