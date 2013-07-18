# Base Python modules
import time
import json
import threading
import os
import io

# Third party modules
import bidict
import tornado.websocket
import tornado.ioloop
import tornado.httpserver

# Other automatch modules
from ..model import match
from . import seekpool
from ..util import sync

# Implicitly acquired and released by the @sync.synchronized decorator
# TODO: should this be part of the class? i.e. object-specific?
lock = threading.RLock()

DEFAULT_PORT = 8080
LOOP_MS = 5000

debug = True


# WebSocketHandler for communication between clients and the AutomatchManager
#
class AutomatchWSH(tornado.websocket.WebSocketHandler):

    def open(self):
        debug and print('Connection opened')
        pname = self.get_argument('pname')
        AutomatchManager.instance().add_client(self, pname)

    def on_close(self):
        debug and print('Connection closed')
        AutomatchManager.instance().rem_client(self)

    # Call the AM method named _xxx, where xxx is the message's 'msgtype'
    def on_message(self, message_str):
        debug and print('Message received')
        message = json.loads(message_str)
        method = getattr(AutomatchManager, message['msgtype'])
        method(self, message)


# Singleton that handles communication with automatch clients, scheduling of
# match generation, and timeouts.
#
# This class should encapsulate all of the communication with clients, but none
# of the seek/match logic. This class is thread-safe, but calling methods out
# of order can still throw errors. It is the client's responsibility to use
# callbacks and blocking to avoid this.
#
class AutomatchManager():
    _instance = None

    # Retreive or create the singleton instance
    @staticmethod
    def instance():
        if AutomatchManager._instance is None:
            AutomatchManager._instance = AutomatchManager(seekpool.SeekPool())
        return AutomatchManager._instance

    # TODO: Make this a real singleton <?>
    def __init__(self, pool):

        # Helper that handles the seek/match logic
        self.pool = pool

        # Bijection mapping between handlers and player names
        self.wsh = bidict.bidict({})
        self.pname = ~self.wsh

        # Mapping from player names to ping times
        self.last_ping = {}
        self.ping_timeout = 30

    ###########################################################################
    # Client-initiated communication
    # Methods are called by client's websockethandler
    ###########################################################################
    #
    # Client connects. Map WSH to player name.
    @sync.synchronized(lock)
    def add_client(self, wsh, pname):
        self.pname[wsh] = pname
        self.last_ping[pname] = time.time()

    # Client disconnects or times out. Clean up.
    @sync.synchronized(lock)
    def rem_client(self, wsh):
        if wsh in self.wsh.values():
            pname = self.pname[wsh]
            self.pool.rem_player(pname)
            del self.wsh[pname]
            del self.last_ping[pname]

    # Client makes a seek request.
    @sync.synchronized(lock)
    def submit_seek(wsh, message):
        #TODO parse message.seek into a Seek object, including Requirements
        return NotImplemented
        seek = message['seek']
        self.pool.submit_seek(pname[wsh], seek)

    # Client cancels a seek request.
    @sync.synchronized(lock)
    def cancel_seek(wsh):
        self.pool.cancel_seek(pname[wsh])

    @sync.synchronized(lock)
    def accept_match(wsh, message):
        self.pool.accept(pname[wsh], message['matchid'])

    @sync.synchronized(lock)
    def cancel_accept(wsh, message):
        self.pool.accept(pname[wsh], message['matchid'])

    @sync.synchronized(lock)
    def decline_match(wsh, message):
        self.pool.decline(pname[wsh], message['matchid'])

    @sync.synchronized(lock)
    def ping(wsh, message):
        self.last_ping[pname[wsh]] = datetime.datetime.now()

    @sync.synchronized(lock)
    def send_match_offer(self, match):
        msg = MatchEncoder.encode({'msgtype': 'offer_match',
                                   'match': match})
        self.write_to_all(match.get_pnames(), msg)

    @sync.synchronized(lock)
    def rescind_match_offer(self, match, reason):
        msg = MatchEncoder.encode({'msgtype': 'rescind_match_offer',
                                   'matchid': match.matchid,
                                   'reason': reason})
        self.write_to_all(match.get_pnames(), msg)

    ###########################################################################
    # Communication from server to clients
    ###########################################################################
    #
    # Send the same message to each named player's client
    @sync.synchronized(lock)
    def write_to_all(self, pnames, msg):
        for pname in pnames:
            self.wsh[pname].write_message(msg)

    @sync.synchronized(lock)
    def announce_match(self, match):
        msg = MatchEncoder.encode({'msgtype': 'announce_match',
                                   'match': match})
        self.write_to_all(match.get_pnames(), msg)

    @sync.synchronized(lock)
    def cancel_match(self, match, reason):
        self.lock.acquire()
        msg = MatchEncoder.encode({'msgtype': 'unannounce_match',
                                   'match': match.matchid,
                                   'reason': reason})
        for wsh in [self.wsh[p] for p in match.get_pnames()]:
            wsh.write_message(msg)

    @sync.synchronized(lock)
    def do_matching(self):
        # Remove players who have timed out
        now = time.time()
        for pname in self.last_ping:
            if now - self.last_ping[pname] > self.ping_timeout:
                self._rem(pname)

        # Generate and offer new matches.
        self.pool.gen_and_offer_new_matches()

#if __name__ == '__main__':
#    # Run on requested port or on default
#    try:
#        port = int(sys.argv[-1])
#    except:
#        port = DEFAULT_PORT
#
#    # Close the existing server process, if any.
#    if os.path.exists('automatch.pid'):
#        f = open('automatch.pid', 'r')
#        pid = int(f.readline())
#        try:
#            print('Stopping old Automatch server.')
#            os.kill(pid, signal.SIGTERM)
#        except:
#            pass
#        os.remove('automatch.pid')
#
#    # Cache the new process id.
#    f = open('automatch.pid', 'w')
#    f.write("%d" % os.getpid())
#    f.close()
#
#    # Run the manager's matching algorithm every 5 seconds
#    tornado.ioloop.PeriodicCallback(
#        AutomatchManager.instance().do_matching, LOOP_MS).start()
#
#    # Start Automatch server and keep it running indefinitely
#    print('Starting Automatch server on port %d.' % port)
#    application = tornado.web.Application([(r'/ws', AutomatchWSH)])
#    http_server = tornado.httpserver.HTTPServer(application)
#    http_server.listen(port)
#    tornado.ioloop.IOLoop.instance().start()
