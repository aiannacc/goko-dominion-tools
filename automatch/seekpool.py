#!/usr/bin/env python

# Base
import threading

# Third Party
import bidict

# This module
import sync
import match
import greedymm

# Implicitly acquired and released by the @sync.synchronized decorator
# TODO: should this be part of the class? i.e. object-specific?
lock = threading.RLock()

# This class should encapsulated all of the seek/match logic, but none of the
# communication with the players' clients.
#
# This class is thread safe, but messages from players' clients may still
# get lost or arrive out of order. This class is responsible for handling this
# sort of error.
#
# States:
# 1. Player has nothing
# 2. Player has outstanding seek
# 3. Player has outstanding match offer
# 4. Player has outstanding announced match
#
class SeekPool:

    def __init__(self):
        # Map from players to open seek requests. Only one request per player.
        self.seeks = {}

        # Outstanding match offers.
        self.offered_matches = set()

        # Accepted matches that we're waiting for players to start.
        self.announced_matches = set()

        # Successfully startd matches
        self.started = []

        # Bijection mapping between matches and match id numbers
        # TODO: Reconsider this implementation. It's redundant.
        self.matchid = bidict.bidict({})
        self.match = ~self.matchid

        # Default matchmaker is the simple "greedy" matchmaker
        self.matchmaker = greedymm.GreedyMatchmaker()

    # A player submits a seek request.
    @sync.synchronized(lock)
    def submit_seek(self, pname, seek):
        self.seeks[pname] = seek
        # TODO: handle out-of-order messages and race conditions

    # A player cancels his seek request.
    def cancel_seek(self, pname):
        # TODO: implement
        return NotImplemented

    # Withdraw all seeks, decline all match offers, cancel any matches
    @sync.synchronized(lock)
    def kill_all(self, pname):
        if pname in self.seeks:
            del self.seeks[pname]
        # TODO: implement
        return NotImplemented

    # Called when a player leaves the pool entirely.
    # Remove all outstanding seeks and matches.
    @sync.synchronized(lock)
    def rem_player(self, pname):
        if pname in self.seek.keys():
            self.rem_seek(pname)
        # TODO Rescind any offered or announced matches

    # Called when player accepts a match offer.
    @sync.synchronized(lock)
    def accept_match(self, automatch_manager, pname, matchid):
        match = self.match[matchid]
        match.accepted_by.add(pname)
        # Announce match if all players have accepted
        if len(match.accepted_by) == len(match.seeks):
            self.offered_matches.remove(match)
            self.announced_matches.add(match)
            automatch_manager.announce_match(match)
        # TODO: handle out-of-order messages and race conditions

    # Called when player accepts a match offer.
    @sync.synchronized(lock)
    def cancel_accept(self, automatch_manager, pname, matchid):
        # TODO: implement
        return NotImplemented

    # Called when player declines a match offer.
    @sync.synchronized(lock)
    def decline_match(self, pname, matchid):
        reason = 'Match offer declined by %s' + pname
        match = self.match[matchid]
        self.offered_matches.remove(match)
        self.manager.rescind(match, reason)
        # TODO: handle out-of-order messages and race conditions

    # Called when a player backs out of a match that was already announced
    @sync.synchronized(lock)
    def cancel_match(self, pname, matchid):
        # TODO: implement
        return NotImplemented

    # Called when player confirms that a match has been started.
    @sync.synchronized(lock)
    def started(self, matchid):
        match = self.match[matchid]
        self.announced_matches.remove(match)
        self.started_matchesadd(match)
        # TODO: handle out-of-order messages and race conditions

    # Called when a player challenges another
    @sync.synchronized(lock)
    def challenge(self, pname, opps):
        # TODO: implement
        return NotImplemented

    @sync.synchronized(lock)
    def gen_and_offer_new_matches(self):
        for m in self.matchmaker.generate_matches(self.seeks):
            self.matchid[m] = id(m)
            self.offered_matches.add(m)
