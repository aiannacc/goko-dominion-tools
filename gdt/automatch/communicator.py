import time
import threading
import json
import datetime
import logging
from pprint import pprint

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
            logging.debug('Browser connected: pname=%s, wsh=%s' % (pname, self))
            AutomatchCommunicator.instance()._connect(self, pname)
            AutomatchCommunicator.instance().update_server_view()

    def on_close(self):
        """ Tell the AutomatchCommunicator that an automatch client has
        disconnected. """
        logging.debug('Browser closed: wsh = %s' % self.__repr__())
        AutomatchCommunicator.instance()._disconnect(self)
        AutomatchCommunicator.instance().update_server_view()

    def on_message(self, message_str):
        """ Forward a message from an automatch client to the
        AutomatchCommunicator. """
        logging.debug('Message received: wsh = %s' % self.__repr__())
        msg = json.loads(message_str)
        AutomatchCommunicator.instance().receive_message(self, msg)
        AutomatchCommunicator.instance().update_server_view()
        AutomatchCommunicator.instance().log_server_state()


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

        # WSH connections from server view UIs
        self.server_views = set()

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
            logging.debug('Sending message to %s:' % pname)
            wsh.write_message(AutomatchEncoder().encode(msg))
            #logging.debug(AutomatchEncoder().encode(msg))
            #pprint(msg, width=1)
            if msgtype == 'CONFIRM_RECEIPT':
                logging.debug(msg)
            else:
                logging.info(msg)
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

    @synchronized(lock)
    def log_server_state(self):
        data = self.manager.get_data()
        logging.debug('Clients:')
        [logging.debug('%20s' % p) for p in self.pname.values()]
        logging.debug('Seeks:')
        [logging.debug('%20s' % p) for p in data['seeks']]
        logging.debug('Offers:')
        [logging.debug('%20s' % p) for p in data['offers']]
        logging.debug('Games:')
        [logging.debug('%20s' % p) for p in data['games']]
        logging.debug('History:')
        [logging.debug('%20s' % p) for p in data['history']]

    @synchronized(lock)
    def update_server_view(self):
        """ Send the current automatch info the the server view UI. """
        data = self.manager.get_data()
        data['clients'] = list(self.pname.values())
        msg = {'SERVER_DATA': data, 'msgtype': 'SERVER_STATE'}
        msg = AutomatchEncoder().encode(msg)
        for view in self.server_views:
            logging.debug(msg)
            view.write_message(msg)

    @synchronized(lock)
    def receive_message(self, wsh, msg):
        """ When any websocket client sends a message, invoke the method it
        specifies with the player's name and message, then confirm reciept. """

        pname = self.pname.get(wsh, None)
        if msg['msgtype'] == 'PING':
            logging.debug('Ping from %s' % pname)
        else:
            logging.info('Received message from %s: ' % pname)
            logging.info(msg)

        # Handle with the named method
        methods = {'DISCONNECT': self._disconnect_pname,
                   'PING': self._ping,
                   'SUBMIT_SEEK': self._submit_seek,
                   'CANCEL_SEEK': self._cancel_seek,
                   'ACCEPT_OFFER': self._accept_offer,
                   'DECLINE_OFFER': self._decline_offer,
                   'UNACCEPT_OFFEr': self._unaccept_offer,
                   'GAME_CREATED': self._game_created,
                   'GAME_STARTED': self._game_started,
                   'GAME_FAILED': self._game_failed,
                   'CANCEL_GAME': self._cancel_game}

        methods[msg['msgtype']](pname, msg['message'])

        # Confirm receipt
        self.confirm_receipt(pname, msg['msgid'])

    ############################
    # Connection communication #
    ############################

    @synchronized(lock)
    def _connect(self, wsh, pname):
        """ When a client connects, associate his player name with his
        websocket handler. """
        if pname == 'SERVER_VIEW':
            self.server_views.add(wsh)
        else:
            self.pname[wsh] = pname
            self.wsh[pname] = wsh

    @synchronized(lock)
    def _disconnect(self, wsh):
        """ When a client disconnects, remove its websocket handlers and notify
        the AutomatchManager. """
        if wsh in self.server_views:
            self.server_views.remove(wsh)
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
    def confirm_receipt(self, pname, msgid):
        """ Tell the client that the server has just received a message.
        Intented for synchronizing client-server communication. """
        self._send_message(pname, 'CONFIRM_RECEIPT', msgid=msgid)

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
        self._send_message(seek.player.pname, 'CONFIRM_SEEK', seek=seek)

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
                                  'OFFER_MATCH', offer=match)

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
        self._send_message_to_all(match.get_pnames(), msgtype='RESCIND_OFFER',
                                  offer=match, reason=reason)

    ######################
    # Game communication #
    ######################

    @synchronized(lock)
    def announce_game(self, game):
        """ Server tells players to start a game. """
        self._send_message_to_all(game.get_pnames(),
                                  'ANNOUNCE_GAME', game=game)

    @synchronized(lock)
    def _game_created(self, pname, msg):
        """ Automatch hostlplayer tells server that he created the table. """
        self.manager.game_created(pname, msg['game'])

    @synchronized(lock)
    def game_ready(self, game):
        """ Server tells players to start a game. """
        self._send_message_to_all(game.get_pnames(),
                                  'GAME_READY', game=game)

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
                                  'UNANNOUNCE_GAME', game=game, reason=reason)
