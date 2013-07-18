#!/usr/bin/env python

from gdt.model.match import Match
from gdt.model.match import Matchmaker
from gdt.model.match import Seek
from gdt.model.match import Player
from gdt.model.match import Requirement


# Matches pairs of players without regard to their seek requirements
class BlindMatchmaker(Matchmaker):
    def generate_matches(self, seeks):
        seeklist = list(seeks)

        matches = []
        while len(seeklist) >= 2:
            host = seeklist.pop()
            guest = seeklist.pop()
            match = Match([host, guest], host)
            matches.append(match)

        return matches
