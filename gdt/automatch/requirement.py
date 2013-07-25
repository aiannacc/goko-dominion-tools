import uuid
import json
import copy
from pprint import pprint as pprint


# A Requirement is a rule that determines whether a proposed match is
# acceptable to the seeker. This is an abstract class.
class Requirement():
    def is_match_ok(self, player, match):
        return NotImplemented

    @staticmethod
    def from_dict(d):
        out = globals()[d['class']]()
        out.__dict__ = d['props']
        return out

    def to_dict(self):
        return {'class': self.__class__.__name__,
                'props': copy.deepcopy(self.__dict__)}


class NumSets(Requirement):
    def __init__(self, min_sets=None, max_sets=None):
        self.min_sets = min_sets
        self.max_sets = max_sets

    def is_match_ok(self, player, match):
        host = match.get_host()
        if self.min_sets and len(host.sets_owned) < self.min_sets:
            return False
        if self.max_sets and len(host.sets_owned) > self.max_sets:
            return False
        return True


class BaseOnly(NumSets):
    def __init__(self):
        super.__init__(1,1)


class AllCards(NumSets):
    def __init__(self):
        super.__init__(15,15)


class NumPlayers(Requirement):

    def __init__(self, min_players=None, max_players=None):
        self.min_players = min_players
        self.max_players = max_players

    def is_match_ok(self, player, match):
        return self.min_players <= len(match.seeks) <= self.max_players


class RatingSystem(Requirement):

    def __init__(self, rating_system=None):
        self.rating_system = rating_system

    def is_match_ok(self, player, match):
        return match.rating_system == self.rating_system


class RelativeRating(Requirement):

    def __init__(self, rating_system=None, pts_lower=None, pts_higher=None):
        self.rating_system = rating_system
        self.pts_lower = pts_lower
        self.pts_higher = pts_higher

    def is_match_ok(self, player, match):
        assert self.rating_system in ('pro', 'casual', 'aits'),\
            'Unknown rating system: ' + self.rating_system

        def r(p):
            if self.rating_system == 'pro':
                return p.rating.goko_pro_rating
            elif self.rating_system == 'casual':
                return p.rating.goko_casual_rating
            else:
                return NotImplemented

        opps = set([s.player for s in match.seeks]) - set([player])
        for o in opps:
            if self.pts_lower and (r(o) < r(player) - self.pts_lower):
                return False
            if self.pts_higher and (r(o) > r(player) + self.pts_higher):
                return False
        return True


#class AbsoluteRating(Requirement):
#
#    def __init__(self, rating_system=None, min_pts=None, max_pts=None):
#        self.rating_system = rating_system
#        self.min_pts = min_pts
#        self.max_pts = max_pts
#
#    def is_match_ok(self, player, match):
#        opps = set([s.player for s in match.seeks]) - set([player])
#        for o in opps:
#            toolow = (o.rating < self.pts_lower)
#            toohigh = (o.rating > self.pts_higher)
#            if (toolow or toohigh):
#                return False
#        return True
