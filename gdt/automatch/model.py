import uuid
import json

# NOTE: None of these objects are meant to be immutable. They will be modified
# on the client side, and equivalent objects may be received from the client
# via JSON. Use their ids to identify them

# A Match is a collection of possibly-compatible seeks with a suggested host
# and room. Its id is random.
class Match:
    def __init__(self, seeks, hostname):
        self.seeks = seeks
        self.hostname = hostname
        self.roomname = None
        self.acceptors = set()
        self.matchid = uuid.uuid4().hex

    def to_dict(self):
        return {'seeks': [s.to_dict() for s in self.seeks],
                'hostname': self.hostname,
                'roomname': self.roomname,
                'acceptors': list(self.acceptors),
                'matchid': self.matchid}

    def get_pnames(self):
        return [s.player.pname for s in self.seeks]


# A Seek is a Player and his SeekRequirements. ID is random.
class Seek:
    def __init__(self, player, requirements):
        self.player = player
        self.requirements = requirements
        self.seekid = uuid.uuid4().hex

    @staticmethod
    def from_dict(d):
        player = Player.from_dict(d['player'])
        requirements = [Requirement.from_dict(r) for r in d['requirements']]
        return Seek(player, requirements)

    def to_dict(self):
        d = {}
        d['player'] = self.player.to_dict()
        d['requirements'] = [sr.to_dict() for sr in self.requirements]
        d['seekid'] = self.seekid
        return d


# A Player has a Goko username, Goko ratings, and a list of sets that he owns
# and can therefore play with if he hosts a game.
class Player:
    def __init__(self, pname, rating, sets_owned):
        self.pname = pname
        self.rating = rating
        self.sets_owned = sets_owned

    @staticmethod
    def from_dict(d):
        rating = Rating.from_dict(d['rating'])
        return Player(d['pname'], rating, d['sets_owned'])

    def to_dict(self):
        d = {}
        d['pname'] = self.pname
        d['rating'] = self.rating.to_dict()
        d['self_owned'] = self.pname
        return d


# A rating object consists of Goko pro and casual ratings, and possibly
# TrueSkill or other ratings derived elsewhere.
class Rating:
    def __init__(self, goko_casual_rating, goko_pro_rating):
        self.goko_casual_rating = goko_casual_rating
        self.goko_pro_rating = goko_pro_rating

    @staticmethod
    def from_dict(d):
        return Rating(d['goko_casual_rating'], d['goko_pro_rating'])

    def to_dict(self):
        d = {}
        d['goko_casual_rating'] = self.goko_casual_rating
        d['goko_pro_rating'] = self.goko_pro_rating
        return d


# A Requirement is a rule that determines whether a proposed match is
# acceptable to the seeker. This is an abstract class.
class Requirement():
    def is_match_ok(match):
        return NotImplemented

    @staticmethod
    def from_dict(self):
        return NotImplemented

    def to_dict(self):
        return NotImplemented


# A matchmaker generates Match objects from Seek objects. This is an abstract
# class.
class Matchmaker():
    def generate_matches(self, seeks):
        return NotImplemented


# TODO: Implement JSONDecoder too
# TODO: get rid of to_dict()
class AutomatchEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Match):
            return obj.to_dict()
        elif isinstance(obj, Seek):
            return obj.to_dict()
        elif isinstance(obj, Player):
            return obj.to_dict()
        elif isinstance(obj, Rating):
            return obj.to_dict()
        elif isinstance(obj, Requirement):
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)
