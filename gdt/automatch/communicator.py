import time
import threading
import json
import datetime
import logging

import tornado.web
import tornado.websocket

from gdt.automatch.model import Seek
from gdt.automatch.model import Requirement
from gdt.automatch.model import AutomatchEncoder
from gdt.automatch.manager import AutomatchManager
from gdt.util.sync import synchronized

# For synchronization. Can be acquired multiple times by the same thread, but a
# second thread has to wait.
lock = threading.RLock()


# WebSocket protocol for Client-Server communication
#
class AutomatchWSH(tornado.websocket.WebSocketHandler):
    def open(self):
        """ Tell the AutomatchCommunicator about a newly-connected automatch
        client. """
        pname = self.get_argument('pname', None)
        if (pname is None):
            # TODO: close websocket
            pass
        else:
            logging.info('Browser connected: pname=%s, wsh=%s' % (pname, self))
            AutomatchCommunicator.instance()._connect(self, pname)
            AutomatchCommunicator.instance().update_server_view()

    def on_close(self):
        """ Tell the AutomatchCommunicator that an automatch client has
        disconnected. """
        logging.info('Browser closed: wsh = %s' % self.__repr__())
        AutomatchCommunicator.instance()._disconnect(self)
        AutomatchCommunicator.instance().update_server_view()

    def on_message(self, message_str):
        """ Forward a message from an automatch client to the
        AutomatchCommunicator. """
        #logging.info('Message received: wsh = %s' % self.__repr__())
        msg = json.loads(message_str)
        AutomatchCommunicator.instance().receive_message(self, msg)
        AutomatchCommunicator.instance().update_server_view()


# Singleton class that translates messages between the AutomatchManager and
# the websocket handlers. Not responsible for any matchmaking logic.
# Responsible for thread safety of client communication.
#
# This class is thread-safe, though the synchronized decorators are a bit
# excessive. Many of them can be safely removed.
#
class AutomatchCommunicator():
    _instance = None

    def __init__(self):
        # Bijection between handlers and player names
        self.wsh = {}
        self.pname = {}

        # Handles timing and match logic
        self.manager = AutomatchManager(self)

    @staticmethod
    @synchronized(lock)
    def instance():
        if not AutomatchCommunicator._instance:
            AutomatchCommunicator._instance = AutomatchCommunicator()
        return AutomatchCommunicator._instance

    ####################
    # Helper functions #
    ####################

    @synchronized(lock)
    def _send_message(self, pname, msgtype, **kwargs):
        """ Send a message to player <pname>'s websocket client. Also update
        the server view websocket. Construct a message object using the
        keyword arguments. """

        # Create the message object
        msg = {'msgtype': msgtype, 'message': {}}
        for k in kwargs:
            msg['message'][k] = kwargs[k]

        # Find <pname>'s websocket handler and send the message
        wsh = self.wsh.get(pname, None)
        if wsh:
            logging.info('Sending message to %s:' % pname)
            logging.info(msg)
            wsh.write_message(AutomatchEncoder().encode(msg))
        else:
            logging.warn("""Couldn't find websocket for %s to send message: \n
                            %s\n
                            Websockets:\n
                            %s""" % (pname, msg.__repr__(),
                                     self.wsh.__repr__()))

        self.update_server_view()

    @synchronized(lock)
    def _send_message_to_all(self, pnames, msgtype, **kwargs):
        """ Send the same message to several different players. """
        for pname in pnames:
            self._send_message(pname, msgtype, **kwargs)

    def update_server_view(self):
        """ Send the current automatch info the the server view UI. """
        view = self.wsh.get('SERVER_VIEW', None)
        if view:
            data = self.manager.get_data()
            data['clients'] = list(self.pname.values())
            msg = AutomatchEncoder().encode(data)
            view.write_message(msg)

    # Message arrives from client. Handle with the approriate function.
    @synchronized(lock)
    def receive_message(self, wsh, msg):
        """ When any websocket client sends a message, invoke the method it
        specifies with the player's name and message. """
        methods = {'disconnect': self._disconnect_pname,
                   'ping': self._ping,
                   'submit_seek': self._submit_seek,
                   'cancel_seek': self._cancel_seek,
                   'accept_offer': self._accept_offer,
                   'decline_offer': self._decline_offer,
                   'unaccept_offer': self._unaccept_offer,
                   'game_started': self._game_started,
                   'game_failed': self._game_failed,
                   'cancel_game': self._cancel_game}
        pname = self.pname.get(wsh, None)
        logging.info('Received message from %s: ' % pname)
        logging.info(msg)
        methods[msg['msgtype']](pname, msg['message'])

    ############################
    # Connection communication #
    ############################

    @synchronized(lock)
    def _connect(self, wsh, pname):
        """ When a client connects, associate his player name with his
        websocket handler. """
        self.pname[wsh] = pname
        self.wsh[pname] = wsh
        self.confirm_receipt(pname)

    @synchronized(lock)
    def _disconnect(self, wsh):
        """ When a client disconnects, remove its websocket handlers and notify
        the AutomatchManager. """
        if wsh in self.pname:
            pname = self.pname.pop(wsh)
            self.wsh.pop(pname)
            self.manager.disconnected(pname)

    @synchronized(lock)
    def _disconnect_pname(self, pname, message):
        """ When a client disconnects, remove its websocket handlers and notify
        the AutomatchManager. """
        wsh = self.wsh.get(pname, None)
        if (wsh):
            self._disconnect(wsh)

    @synchronized(lock)
    def _ping(self, pname, msg):
        """ Process a player's ping. """
        self.manager.ping(pname)

    @synchronized(lock)
    def confirm_receipt(self, pname):
        """ Tell the client that the server has just received a message.
        Intented for synchronizing client-server communication. To be sent when
        the server wouldn't otherwise respond to the client's message. """
        self._send_message(pname, 'confirm_receipt')

    ######################
    # Seek communication #
    ######################

    @synchronized(lock)
    def _submit_seek(self, pname, msg):
        """ Forward a player's seek request to the AutomatchManager. """
        seek = Seek.from_dict(msg['seek'])
        self.manager.submit_seek(pname, seek)

    # Server confirms receipt of a seek request and gives the player its id.
    # TODO: make sure client can match the seek with its seekid
    @synchronized(lock)
    def confirm_seek(self, seek):
        """ Tell a player that his seek request has been received. """
        self._send_message(seek.player.pname, 'confirm_seek', seek=seek)

    # Player cancels a seek request.
    @synchronized(lock)
    def _cancel_seek(self, pname, msg):
        """ Forward a player's request to cancel his seek to the
        AutomatchManager. """
        self.manager.cancel_seek(pname, msg['seekid'])

    #######################
    # Match communication #
    #######################

    @synchronized(lock)
    def offer_match(self, match):
        """ Send a match offer to all players involved. """
        self._send_message_to_all(match.get_pnames(),
                                  'offer_match', offer=match)

    @synchronized(lock)
    def _accept_offer(self, pname, msg):
        """ Forward a player's offer accept to the AutomatchManager. """
        self.manager.accept_offer(pname, msg['matchid'])

    @synchronized(lock)
    def _decline_offer(self, pname, msg):
        """ Forward a player's offer decline to the AutomatchManager. """
        self.manager.decline_offer(pname, msg['matchid'])

    @synchronized(lock)
    def _unaccept_offer(self, pname, msg):
        """ Forward a player's cancelation of his previous offer acceptance to
        the AutomatchManager. """
        self.manager.unaccept_offer(pname, msg['matchid'])

    @synchronized(lock)
    def rescind_offer(self, match, reason):
        """ Tell all involved players that a match offer has been canceled. """
        self._send_message_to_all(match.get_pnames(), msgtype='rescind_offer',
                                  offer=match, reason=reason)

    ######################
    # Game communication #
    ######################

    @synchronized(lock)
    def announce_game(self, game):
        """ Server tells players to start a game. """
        self._send_message_to_all(game.get_pnames(),
                                  'announce_game', game=game)

    @synchronized(lock)
    def _game_started(self, pname, msg):
        """ Player tells server that game has started. """
        self.manager.game_started(pname, msg['matchid'])

    @synchronized(lock)
    def _game_failed(self, pname, msg):
        """ Player tells server that game failed to start. """
        self.manager.game_failed(pname, msg['matchid'])

    @synchronized(lock)
    def _cancel_game(self, pname, msg):
        """ Player asks server to cancel the game. """
        self.manager.cancel_game(pname, msg['matchid'])

    @synchronized(lock)
    def unannounce_game(self, game, reason):
        """ Server tells players that a game is canceled. """
        self._send_message_to_all(game.get_pnames(),
                                  'unannounce_game', game=game, reason=reason)
