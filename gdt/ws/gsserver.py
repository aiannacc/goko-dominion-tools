import time
import threading
import json
import datetime
import logging
import math

import tornado.web
import tornado.websocket
import tornado.ioloop

from gdt.ws.gsmanager import GSManager
from gdt.util.sync import synchronized

# For synchronization. Can be acquired multiple times by the same thread, but a
# second thread has to wait.
lock = threading.RLock()


# WebSocket protocol for Client-Server communication
#
class MainWSH(tornado.websocket.WebSocketHandler):

    def open(self):
        logging.info('WS connection opened: %s' % id(self))
        req_detail = {'msgtype': 'REQUEST_CLIENT_INFO'}
        self.write_message(GSEncoder().encode(req_detail))
        logging.info('Requesting details from client: %s' % id(self))

    def on_close(self):
        logging.info('WS connection closed: %s' % id(self))
        GSInterface.instance().disconnect(self)

    def on_message(self, message_str):
        logging.debug('Message received from WS connection: %s' % id(self))
        msg = json.loads(message_str)
        GSInterface.instance().receiveFromClient(self, msg)


# Basic info for each connected client
#
class Client():

    def __init__(self, conn, username, gsVersion):
        self.conn = conn
        self.username = username
        self.version = gsVersion
        self.last_pingtime = time.time()

    def update_lastping(self):
        self.last_pingtime = time.time()

    def timed_out(self):
        return time.time() - self.last_pingtime > 60

    def to_dict(self):
        d = {}
        d['conn'] = id(self.conn)
        d['username'] = self.username
        d['version'] = self.version
        d['last_pingtime'] = time.strftime('%H:%M:%S',
                                           time.localtime(self.last_pingtime))
        return d


# Encodes dictionary-type objects to JSON
class GSEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Client):
            return obj.to_dict()
        elif isinstance(obj, MainWSH):
            return id(obj)
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, dict):
            return obj
        else:
            return json.JSONEncoder.default(self, obj)


# Singleton class that receives and submits websocket messages.  All actual
# server logic is delegated to the GSManager object.  This class is really
# just a convenience wrapper for WSH communication.
#
class GSInterface():
    _instance = None

    @staticmethod
    @synchronized(lock)
    def instance():
        if not GSInterface._instance:
            GSInterface._instance = GSInterface()
        return GSInterface._instance

    def __init__(self):
        # Open connections: wsh --> Client
        self.clients = {}

        # Delegate server logic to a separate class
        self.manager = GSManager(self)

        # Check for lagged-out clients
        tornado.ioloop.PeriodicCallback(self.check_lastpings, 60).start()

    ##################################################
    # Handle connection, disconnection, and timeouts #
    ##################################################

    @synchronized(lock)
    def disconnect(self, conn):
        """ Remove and notify manager.  Ignore if called previously. """
        client = self.clients.pop(conn)
        if (client is not None):
            self.manager.remClient(client)
            conn.close()

    @synchronized(lock)
    def check_lastpings(self):
        to_close = set()
        for conn in self.clients:
            if self.clients[conn].timed_out():
                to_close.add(conn)
        
        for conn in to_close:
            logging.info('Client timed out.  Closing: %s' % id(conn))
            self.disconnect(conn)


    #########################################
    # Messages between client and GSManager #
    #########################################

    @synchronized(lock)
    def sendToClient(self, conn, msgtype, **kwargs):
        """ Send a message to a client on behalf of the GSManager. """

        # Create the message object
        msg = {'msgtype': msgtype, 'message': {}}
        for k in kwargs:
            msg['message'][k] = kwargs[k]

        # Log and send message
        logging.info('Sending message to %s:' % id(conn))
        logging.info(msg)
        conn.write_message(GSEncoder().encode(msg))

    @synchronized(lock)
    def receiveFromClient(self, conn, msg):
        """ Handle pings but pass all other client messages to GSManager. """

        if msg['msgtype'] == 'PING':
            # Handle pings directly
            self.clients[conn].update_lastping()
            logging.debug('Ping from %s' % id(conn))
        elif msg['msgtype'] == 'CLIENT_INFO':
            info = msg['message']
            client = Client(conn, info['username'], info['gsversion'])
            self.clients[conn] = client
            self.manager.addClient(client)
        else:
            # Pass other messages to manager
            self.manager.receiveFromClient(conn,
                                           msg['msgtype'], msg['message'])
            logging.info('Received message from client: %s ' % id(conn))
            logging.info(msg)

        # Tell client the message was received (also constitutes a pingback).
        confirm = {'msgtype': 'CONFIRM_RECEIPT', 'msgid': msg['msgid']}
        conn.write_message(GSEncoder().encode(confirm))
