# -*- coding: utf-8 -*-

import json
import threading
import paho.mqtt.client as mqtt
from common import config
import haier_proxy


mqttclient = mqtt.Client()

class mqtt_task(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        mqttclient.on_connect = on_connect
        mqttclient.on_message = on_message
        mqttclient.on_disconnect = on_disconnect

    def run(self):
        print "mqtt start work"
        mqttclient.connect(config.mqtt_host, config.mqtt_port, 60)
        mqttclient.loop_forever()

def on_connect(client, userdata, flags, rc):
    print("connected :" + str(rc))
    client.subscribe(config.project_name)

def on_message(client, userdata, msg):
    topic = msg.topic
    data = msg.payload.decode('gbk')
    print topic, data
    handle_message(topic, data)

def on_disconnect(client, userdata, rc):
    print "disconnect:", rc
    client.reconnect()

def publish_message(topic, payload):
    mqttclient.publish(topic, payload)

def handle_message(topic, data):
    print "handle_message"
    try:
        cmdDict = json.loads(data)
        cmd = cmdDict.get('wxCmd')
        roomNo = cmdDict.get('roomNo')
        if cmd == "devList":
            # 处理房间列表发布mqtt消息
            print "devList"
            #socketserver.getList
            #self.publish_message
        elif cmd == "sceneControl":  # 微信场景控制
            print "sceneControl"
        elif cmd == "requestDeviceControl":
            print "devControl"
            haier_proxy.send_rcu_cmd(data)
    except Exception as e:
        print e.message

if __name__ == "__main__":
    m = mqtt_task()
    m.start()