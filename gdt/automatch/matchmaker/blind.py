#!/usr/bin/env python

from gdt.automatch.model import Match
from gdt.automatch.model import Seek
from gdt.automatch.model import Player
from gdt.automatch.model import Requirement
from gdt.automatch.model import Matchmaker


# Matches pairs of players without regard to their seek requirements
class BlindMatchmaker(Matchmaker):
    def generate_matches(self, seeks):
        seeks = list(seeks)
        matches = []
        while len(seeks) >= 2:
            (host_seek, guest_seek) = (seeks.pop(), seeks.pop())
            match = Match([host_seek, guest_seek], host_seek.player.pname)
            matches.append(match)
        return matches
