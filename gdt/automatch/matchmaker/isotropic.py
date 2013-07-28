#!/usr/bin/env python

import random
import logging

from gdt.automatch.model import Match
from gdt.automatch.model import Seek
from gdt.automatch.model import Player
from gdt.automatch.model import Requirement
from gdt.automatch.matchmaker.matchmaker import Matchmaker
from gdt.automatch.requirement import NumPlayers
from gdt.automatch.requirement import RatingSystem


# Implementation of isotropic's matchmaking algorithm, as described by dougz at
# http://forum.dominionstrategy.com/index.php?topic=8720.msg264754#msg264754:
#
# > every 30 seconds or so:
# >   for N in (4, 3, 2):
# >     let S be the set of all players interested in an N-player match.
# >     while |S| >= N:
# >       randomly choose a player X, remove from S.
# >       try 5 times:
# >         randomly choose N-1 other players from S (but don't remove them from S).
# >         see if {X + the N-1 other players} is a feasible game (no conflicting requirements).
# >         if it is, remove the N-1 other players from S and propose the game.
#
# Modified to deal with Goko's multiple rating systems and the possibility of
# six-player games. Prioritizes Pro > Casual > Unrated.
#
# This slightly violates my intended design architecture, in which the
# implementation of the seek Requirement classes are encapsulated from the
# Matchmaker. This Matchmaker needs to know about the NumPlayers and
# RatingSystem classes.
#
# TODO: Move knowledge of NumPlayers and Rating system into the Matchmaker
# superclass. Other Matchmakers will need that knowledge too and it's better to
# keep it contained.
#
class IsotropicMatchmaker(Matchmaker):

    # Return a function that returns true when applied to a Seek that accepts
    # an N-player game with the given rating system.
    @staticmethod
    def accepts(N, rsys):
        def acc_N_rs(seek):
            for r in seek.requirements:
                if isinstance(r, NumPlayers):
                    if not (r.min_players <= N <= r.max_players):
                        return False
                if isinstance(r, RatingSystem):
                    if r.rating_system != rsys:
                        return False
            return True
        return acc_N_rs

    # Finds a player who can host the game without violating anyone's
    # Requirements (probably the player with most sets). Return the match
    # object with him as the host. If no host found, return None.
    #
    # TODO: move this to the Match class. Maybe even into the constructor?
    @staticmethod
    def choose_host(match):
        for s in match.seeks:
            match.hostname = s.player.pname
            if match.is_match_ok():
                return match
        return None

    def generate_matches(self, seeks):

        matches = []

        # Don't modify the original seeks object
        seeks = set(seeks)

        # Prioritize Pro > Casual > Unrated and then larger games first
        for rsys in ['pro', 'casual', 'unrated']:
            for N in [6, 5, 4, 3, 2]:

                # Unmatched seeks that want N-player <rating_system>-rated game
                S = list(filter(IsotropicMatchmaker.accepts(N, rsys), seeks))
                if len(S) < N:
                    continue

                # Remove random player X from S
                X = S.pop(random.randrange(len(S)))

                for i in range(5):

                    # Match X with N-1 other random players from S
                    random.shuffle(S)
                    players = [X] + S[0:N-1]

                    # Find an acceptable host, if any
                    match = Match(players, rsys, None)
                    match = IsotropicMatchmaker.choose_host(match)

                    # Assign the game to Outpost
                    # TODO: choose this dynamically?
                    if match != None:
                        match.roomname = 'Outpost';

                    # Save match and remove seeking players
                    if (match):
                        logging.info('Found match: ')
                        logging.info(match.to_dict())
                        matches.append(match)
                        seeks = seeks - set(players)
                        break

        # Return matches
        return matches
