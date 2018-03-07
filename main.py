# -*- coding: utf-8 -*-


import thread,time
from shunzhou_proxy import ShunzhouProxyFactory,reactor,TCP4ServerEndpoint
from protocol import testFunc

#测试用定时器线程，
def timerTest(no, interval):
    onOff = 1
    print "timer thread start"
    while True:
        time.sleep(interval)
        print "runing"
        testFunc()
    thread.exit_thread()

thread.start_new_thread(timerTest,(1,5))

endpoint = TCP4ServerEndpoint(reactor, 6666)
endpoint.listen(ShunzhouProxyFactory())
reactor.run()
