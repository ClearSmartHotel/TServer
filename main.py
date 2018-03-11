# -*- coding: utf-8 -*-


import thread,time
from shunzhou_proxy import ShunzhouProxyFactory,reactor,TCP4ServerEndpoint
from protocol import testFunc,sendControlDev
import mqtt_client
import haier_proxy

#测试用定时器线程，
def timerTest(no, interval):
    onOff = 1
    print "timer thread start"
    while True:
        time.sleep(interval)
        print "runing"
        testFunc()

    thread.exit_thread()

thread.start_new_thread(timerTest,(1,2))

rcu_ws = haier_proxy.haier_rcu_websocket()
rcu_ws.start()
m = mqtt_client.mqtt_task()
m.start()

endpoint = TCP4ServerEndpoint(reactor, 6666)
endpoint.listen(ShunzhouProxyFactory())
reactor.run()



