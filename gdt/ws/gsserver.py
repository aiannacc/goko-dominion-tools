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
        logging.info('WS opened: %s' % id(self))
        req_detail = {'msgtype': 'REQUEST_CLIENT_INFO'}
        self.write_message(GSEncoder().encode(req_detail))
        logging.info('Requesting details from client: %s' % id(self))

    def on_close(self):
        logging.info('Received WS on_close: %s' % id(self))
        GSInterface.instance().handle_disconnect(self)

    def on_message(self, message_str):
        logging.debug('Message received from WS: %s' % id(self))
        msg = json.loads(message_str)
        GSInterface.instance().receiveFromClient(self, msg)


# Basic info for each connected client
#
class Client():

    def __init__(self, conn, playerName, playerId, gsVersion):
        self.conn = conn
        self.playerName = playerName
        self.playerId = playerId
        self.version = gsVersion
        self.last_pingtime = time.time()

    def update_lastping(self):
        self.last_pingtime = time.time()

    def timed_out(self):
        return time.time() - self.last_pingtime > 60

    def to_dict(self):
        d = {}
        d['conn'] = id(self.conn)
        d['playerName'] = self.playerName
        d['playerId'] = self.playerId
        d['version'] = self.version
        d['last_pingtime'] = time.strftime('%H:%M:%S',
                                           time.localtime(self.last_pingtime))
        return d

    def __str__(self):
        return "%s:%d:%s" % (self.playerId, id(self.conn), self.playerName)


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
    def do_disconnect(self, conn):
        if conn is not None:
            logging.info('Performing disconnection: %s ' % id(conn))
            if conn in self.clients:
                client = self.clients.pop(conn)
                self.manager.remClient(client)
            try:
                conn.close()
            except:
                pass

    @synchronized(lock)
    def handle_disconnect(self, conn):
        """ Remove and notify manager.  Ignore if called previously. """
        logging.info('Handling disconnection: %s ' % id(conn))
        if conn in self.clients:
            client = self.clients.pop(conn)
            self.manager.remClient(client)

    @synchronized(lock)
    def check_lastpings(self):
        to_close = set()
        for conn in self.clients:
            if self.clients[conn].timed_out():
                to_close.add(conn)

        for conn in to_close:
            logging.info('Client timed out.  Closing WS: %s' % id(conn))
            self.do_disconnect(conn)

    #########################################
    # Messages between client and GSManager #
    #########################################

    @synchronized(lock)
    def sendToClient(self, client, msgtype, **kwargs):

        # Create message object
        msg = {'msgtype': msgtype, 'message': {}}
        for k in kwargs:
            msg['message'][k] = kwargs[k]

        # Log and send message
        logging.debug('Sending message to %s:' % id(client.conn))
        logging.debug(msg)
        msgJSON = GSEncoder().encode(msg)
        client.conn.write_message(msgJSON)

    @synchronized(lock)
    def sendToAllClients(self, msgtype, **kwargs):
        for k in self.clients:
            self.sendToClient(self.clients[k], msgtype, **kwargs)

    def respondToClient(self, client, querytype, queryid, **kwargs):
        self.sendToClient(client, 'RESPONSE', querytype=querytype,
                          queryid=queryid, **kwargs)

    @synchronized(lock)
    def receiveFromClient(self, conn, msg):
        """ Handle client info and pings internally.  Pass all other
            client messages to GSManager. """

        # Receive client info directly
        if msg['msgtype'] == 'CLIENT_INFO':
            info = msg['message']
            client = Client(conn, info['playerName'], info['playerId'], info['gsversion'])
            self.clients[conn] = client
            self.manager.addClient(client)
            self.respondToClient(client, 'CLIENT_INFO', msg['msgid'])

        else:
            # Verify that we have client info 
            if conn in self.clients:
                client = self.clients[conn]
            else:
                logging.error("""Received message from WS Connection with no
                              registered client. Conn ID: %s""" % id(conn))
                logging.error(msg)
    
            # Handle pings directly
            if msg['msgtype'] == 'PING':
                logging.debug('Received ping from %s' % client)
                client.update_lastping()
                logging.debug('Sending pingback to %s' % client)
                self.respondToClient(client, 'PING', msg['msgid'])
    
            # Pass other messages to manager
            else:
                logging.info('Received message from client: %s ' % client)
                logging.info(msg)
                self.manager.receiveFromClient(client, msg['msgtype'],
                                               msg['msgid'], msg['message'])
