import uuid
import json


# A Requirement is a rule that determines whether a proposed match is
# acceptable to the seeker. This is an abstract class.
class Requirement():
    def is_match_ok(self, player, match):
        return NotImplemented

    @staticmethod
    def from_dict(d):
        out = Requirement()
        out.__dict__ = d

    def to_dict(self):
        return self.__dict__


class NumPlayers(Requirement):

    def __init__(self, min_players, max_players):
        self.min_players = min_players
        self.max_players = max_players

    def is_match_ok(match):
        return self.min_players <= match.seeks.length <= self.max_players


class RatingSystem(Requirement):

    def __init__(self, ratingsys):
        self.ratingsys = ratingsys

    def is_match_ok(match):
        return match.ratingsys == self.ratingsys


class RelativeRating(Requirement):

    def __init__(self, ratingsys, pts_lower, pts_higher):
        self.ratingsys = ratingsys
        self.pts_lower = pts_lower
        self.pts_higher = pts_higher

    def is_match_ok(self, p, match):
        opps = set([s.player for s in match.seeks]) - set([p])
        for o in opps:
            toolow = (o.rating < p.rating - self.pts_lower)
            toohigh = (o.rating > p.rating + self.pts_higer)
            if (toolow or toohigh):
                return false
        return true


class AbsoluteRating(Requirement):

    def __init__(self, pts_lower, pts_higher):
        self.min_players = min_players
        self.max_players = max_players

    def is_match_ok(self, player, match):
        return self.min_players <= match.seeks.length <= self.max_players
