# -*- coding: utf-8 -*-


import thread
import time

import haier_proxy
import mqtt_client
from protocol import testFunc
import scene.maker
from shunzhou_proxy import ShunzhouProxyFactory, reactor, TCP4ServerEndpoint


#测试用定时器线程，
def timerTest(no, interval):
    onOff = 1
    print "timer thread start"
    while True:
        time.sleep(interval)
        print "runing"
        scene.maker.testFunc()
        break

    thread.exit_thread()


thread.start_new_thread(timerTest,(1,10))

rcu_ws = haier_proxy.haier_rcu_websocket()
rcu_ws.start()
m = mqtt_client.mqtt_task()
m.start()

endpoint = TCP4ServerEndpoint(reactor, 6666)
endpoint.listen(ShunzhouProxyFactory())
reactor.run()



