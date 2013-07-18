#!/usr/bin/env python

from gdt.model.match import Match
from gdt.model.match import Matchmaker


class GreedyMatchmaker(Matchmaker):
    def generate_matches(self, seeks):
        return []
