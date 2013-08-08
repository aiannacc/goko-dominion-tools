import threading
import time
import logging

import tornado.ioloop

from gdt.automatch.model import AutomatchEncoder
from gdt.automatch.matchmaker.isotropic import IsotropicMatchmaker
from gdt.util.sync import synchronized

TIMEOUT = 2*1000
PERIOD = 5*1000

# For synchronization. Can be acquired multiple times by the same thread, but a
# second thread has to wait.
lock = threading.RLock()


# This class controls the execution flow of the automatch server. It
# is responsible for integrating client communication with the matching cycle.
# All methods are synchronized, but messages from players can still get lost or
# cross with messages from the server, or can get lost or arrive out of order.
# This class deals with all of the edge cases and race conditions that can
# occur.
#
# TODO: should this be a singleton and not the AutomatchCommunicator?
# TODO: implement a real matchmaker
# TODO: allow match offer timeout to differ from the matchmaking cyle's period.
#
class AutomatchManager():

    def __init__(self, automatch_communicator):

        self.seeks = {}      # Unmatched seeks, by seekid
        self.offers = {}     # Outstanding offers, by matchid
        self.games = {}      # Announced but unstarted games, by matchid
        self.last_ping = {}  # Most recent ping time, by player name
        self.history = []    # Successfully matched and started games

        # Start matchmaking cycle
        self.matchmaker = IsotropicMatchmaker()
        tornado.ioloop.PeriodicCallback(self.do_matchmaking, PERIOD).start()

        # For communicating with players
        self.comm = automatch_communicator

    ############################
    # Private Helper Functions #
    ############################

    def _rem_seek(self, seekid, reason):
        """ Remove seek request. """
        logging.debug('Removing seek %s' % seekid)
        self.seeks.pop(seekid, None)
        # TODO: Maybe tell player his seek has been removed <?>

    def _rem_offer(self, matchid, reason):
        """ Remove match offer. Notify involved players. """
        logging.debug('Removing offer %s' % matchid)
        o = self.offers.pop(matchid, None)
        if o:
            self.comm.rescind_offer(o, reason)

    def _rem_game(self, matchid, reason):
        """ Remove game. Notify involved players. """
        logging.debug('Removing game %s' % matchid)
        g = self.games.pop(matchid, None)
        if g:
            self.comm.unannounce_game(g, reason)

    def _rem_player(self, pname, reason, include_ping=True):
        """ Remove a player entirely: remove his seeks, cancel match offers and
        unannounce games that involve him, remove his ping times. """
        logging.debug('Removing all for player %s' % pname)
        if include_ping:
            self.last_ping.pop(pname, None)

        seek_is_from_pname = lambda s: s.player.pname == pname
        match_has_pname = lambda o: pname in o.get_pnames()

        # Remove player's outstanding seeks.
        for s in list(filter(seek_is_from_pname, self.seeks.values())):
            self._rem_seek(s.seekid, reason)

        # Remove player's outstanding match offers
        for o in list(filter(match_has_pname, self.offers.values())):
            self._rem_offer(o.matchid, reason)

        # Remove player's announced games
        for g in list(filter(match_has_pname, self.games.values())):
            self._rem_game(g.matchid, reason)

    ################################################
    # Methods invoked by the AutomatchCommunicator #
    ################################################

    @synchronized(lock)
    def ping(self, pname):
        self.last_ping[pname] = time.time()

    @synchronized(lock)
    def disconnected(self, pname):
        self._rem_player(pname, 'Player %s disconnected' % pname)

    @synchronized(lock)
    def submit_seek(self, pname, seek):
        self.seeks[seek.seekid] = seek
        self.comm.confirm_seek(seek)

    @synchronized(lock)
    def cancel_seek(self, pname, seekid):
        self._rem_seek(seekid, 'Seek canceled by player %s' % pname)

    @synchronized(lock)
    def accept_offer(self, pname, matchid):
        """ Add player name to the set of players that have accepted the match
        offer. If all involved players have accepted, announce game. """
        logging.debug('%s accepts offer %s' % (pname, matchid))
        o = self.offers.get(matchid, None)
        if o:
            o.acceptors.add(pname)
            if len(o.acceptors) == len(o.get_pnames()):
                logging.debug('All players accept offer %s' % matchid)
                self.games[matchid] = o
                self.offers.pop(matchid, None)
                self.comm.announce_game(o)

    @synchronized(lock)
    def decline_offer(self, pname, matchid):
        """ Player <pname> has declined match offer <matchid>. Rescind it. """
        msg = '%s declined the match.' % (pname)
        self._rem_offer(matchid, msg)

    @synchronized(lock)
    def unaccept_offer(self, pname, matchid):
        """ Player <pname> has canceled his acceptance of match offer
        <matchid>. Rescind the offer and/or cancel the game. """
        msg = '%s declined the match' % (pname)
        self._rem_offer(matchid, msg)
        msg = '%s canceled the game' % (pname)
        self._rem_game(matchid, msg)

    @synchronized(lock)
    def game_created(self, pname, game):
        """ Automatch host player tells server that the table is ready. """
        logging.debug('Game Created:')
        logging.debug(game)
        g = self.games.get(game['matchid'], None)
        if g:
            g.roomid = game['roomid']
            g.tableindex = game['tableindex']
            self.comm.game_ready(g)

    @synchronized(lock)
    def game_started(self, pname, matchid):
        """ Player tells server that he has started a game. """
        g = self.games.pop(matchid, None)
        if (g):
            # It's an automatch game. Save to history.
            logging.info('Automatch game started: %s' % matchid)
            self.history.append(g) 
        else:
            # It's not an automatch game. Remove player from seek queue, etc.
            msg = 'Player %s started a non-automatch game.' % pname
            logging.debug(msg)
            self._rem_player(pname, msg, False)

    @synchronized(lock)
    def cancel_game(self, pname, matchid):
        """ Player asks server to cancel the game. """
        g = self.games.get(matchid, None)
        if g:
            msg = 'Game %s canceled by %s' % (matchid, pname)
            self._rem_game(matchid, msg)

    @synchronized(lock)
    def game_failed(self, pname, matchid):
        """ Player tells server that game failed to start. """
        g = self.games.get(matchid, None)
        if g:
            msg = 'Game %s failed.' % (matchid)
            self._rem_game(matchid, msg)

    ########################################
    # Periodic matchmaking and maintenance #
    ########################################

    @synchronized(lock)
    def do_matchmaking(self):
        """ Remove timed-out players and match offers. Generate new offers. """
        # Remove seeks, offers, etc for lagged-out players
        now = time.time()
        for pname in self.last_ping:
            elapsed = now - self.last_ping[pname]
            logging.debug('Time since last ping: %f' % elapsed)
            if elapsed > TIMEOUT:
                msg = 'Lost contact with %s' % pname
                self._rem_player(pname, msg)

        # Remove outstanding (and now expired) match offers
        #for match in self.offers.values():
        #    msg = 'Match offer %s expired' % match.matchid
        #    self._rem_offer(match, msg)

        # Generate new match offers
        for m in self.matchmaker.generate_matches(self.seeks.values()):
            self.offers[m.matchid] = m
            for s in m.seeks:
                msg = 'Seek %s matched Match %s' % (s.seekid, m.matchid)
                self.seeks.pop(s.seekid, None)
            self.comm.offer_match(m)

    ###################################################
    # Communication with the server UI. For testting. #
    ###################################################

    def get_data(self):
        data = {}
        data['seeks'] = list(self.seeks.values())
        data['offers'] = list(self.offers.values())
        data['games'] = list(self.games.values())
        data['history'] = self.history;
        return data
