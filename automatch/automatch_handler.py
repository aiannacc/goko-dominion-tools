#!/usr/bin/env python

# Automatch server for Goko Dominion
#
# Tracks players seeking games and suggests matches. For use with the 
# gokomatch.js JavaScript extension for Goko Dominion.
#
# Known limitations:
# - match logic not implemented
# - not thread-safe
# - no client-side confirmation of matches
# - uses stdout instead of real logging/debugging
# - doesn't handle client disconnects, timeouts, or cancellations
#
# Known bugs:
# - throws an exception if a client sends a second request
#
# Written for Python v3.3.2
# Required third-party libraries: 
# - Tornado 3.1 web framework: http://www.tornadoweb.org/en/stable/

import datetime
import sys
import os
import signal
import time

import tornado.ioloop
import tornado.web
import tornado.escape
import tornado.template

DEFAULT_PORT = 8080

# Representation of a Goko Dominion player seeking a game.
class Player:
    def __init__(self,playerName,playerId,proRating,sets,criteria):
        self.playerName=playerName
        self.playerId = playerId
        self.proRating = proRating
        self.sets = sets
        self.criteria = criteria

    def __str__(self):
        return vars(self).__str__()

    def __repr__(self):
        return vars(self).__repr__()

# A potential match between two players, includes suggested room/table.
class Match:
    def __init__(self,host,guest):
        self.host = host
        self.guest = guest

# Determine whether two players match.
# TODO: Add match logic here. Currently any two players will be matched.
def players_match(player1, player2):
    print('Matched players (%s,%s)' % (player1.playerName,player2.playerName))
    return True

# Create a new Match object.
# TODO: host should be the player with more sets. Currently it's arbitrary.
def create_match(player1,player2):
    return Match(player1,player2)

# The server object. Receives match requests, keeps the connection open until
# a match is found, and then notifies matched players.
# 
class AutomatchHandler(tornado.web.RequestHandler):

    # Players who didn't immediately match and are now waiting
    waiting_players = []

    # Callback methods for communication with waiting players
    # Use as dictionary hash: Player -> callback function 
    callbacks = {}

    # Allow requests from other servers (e.g. play.goko.com)
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    # Receive a match request. Either match the player immediately or add them
    # to the list of waiting players.
    #
    # Function is asyncronous. The request remains open until a match is found.
    #
    # TODO: Don't trust the client. Look up rating and sets directly, if
    #       possible.
    # TODO: Implement player's match criteria (e.g. rating > myrating - 1000)
    #              
    @tornado.web.asynchronous
    def get(self):

        # Get the player's personal info and match criteria. Instantiate Player.
        playerName = self.get_argument('playerName')
        playerId   = self.get_argument('playerId')
        proRating  = self.get_argument('proRating')
        sets       = self.get_argument('sets',default=['base'])
        criteria   = None # TODO
        player     = Player(playerName,playerId,proRating,sets,criteria);

        print('Received automatch request from %s' % playerName)

        # TODO: Handle multiple requests (e.g. same player, new criteria)

        # Match the new player with a seeker if possible.
        # Otherwise add him to the list of seekers.
        self.match_or_add(player)

    # Match a new player or add him to the list of waiting players
    def match_or_add(self,new_player):

        # Try to match with each waiting player. If a match is found, notify
        # the new player directly and callback the waiting player.
        for wp in AutomatchHandler.waiting_players:
            if players_match(new_player,wp):
                match = create_match(new_player,wp)
                # Notify the waiting player
                AutomatchHandler.callbacks[wp](match)

                # need to also remove waiting player from queue
                # TODO: don't modify the list while iterating through it
                AutomatchHandler.waiting_players.remove(wp)

                # Notify the new player
                self.notify_of_match(match)
                return

        # If no match, join the list of waiting players.
        AutomatchHandler.waiting_players.append(new_player)
        callback = self.async_callback(self.notify_of_match)
        AutomatchHandler.callbacks[new_player] = callback

    # Callback a newly matched player with match info. Close the request.
    # Match info is communicated via xml using the tornado templates framework.
    def notify_of_match(self, match):
        loader = tornado.template.Loader(".")
        result = loader.load('automatch.json').generate(match=match)
        print(result)
        self.write(result)
        self.finish()

# For running the Automatch server.
# Usage: ./automatch [port]
if __name__ == "__main__":

    # Run on requested port or on default
    try:
        port = int(sys.argv[-1])
    except:
        port = DEFAULT_PORT

    # Close the existing server process, if any.
    # TODO: Use pgrep or such, rather than the cached pid <?>
    # TODO: Make this OS independent <?>
    if os.path.exists('automatch.pid'):
        f = open('automatch.pid','r')
        pid = int(f.readline())
        try:
            print('Stopping old Automatch server.')
            os.kill(pid,signal.SIGTERM)
        except:
            # TODO: deal with potential errors here
            pass
        os.remove('automatch.pid')

    # Cache the new process id.
    f = open('automatch.pid','w')
    f.write("%d" % os.getpid())
    f.close()

    print('Starting Automatch server on port %d.' % port)

    # Start listening for requests at http://[host]:[port]/automatch
    application = tornado.web.Application([ (r"/automatch", AutomatchHandler) ])
    application.listen(port)

    # Keep the server running indefinitely
    tornado.ioloop.IOLoop.instance().start()
