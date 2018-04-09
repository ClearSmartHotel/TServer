# -*- coding: utf-8 -*-

from websocket_server import  WebsocketServer
import threading
import common.config as c

class wsServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server = WebsocketServer(c.ws_port,"0.0.0.0")
        self.server.set_fn_new_client(new_client)
        self.server.set_fn_client_left(client_left)
        self.server.set_fn_message_received(message_received)

    def run(self):
        self.server.run_forever()

def new_client(client, server):
    print("New client connected and was given id %d" %(client['id']))
    server.send_message_to_all("new client has joined us")
    # server.send_message(client,"only you")

def client_left(client, server):
    print("client %d disconnected" %(client['id']))

def message_received(client, server, message):
    if len(message) > 200:
        message = message[:200]+'..'
    print("Client %d said: %s"%(client['id'], message))

if __name__ == "__main__":
    w = wsServer()
    w.start()
