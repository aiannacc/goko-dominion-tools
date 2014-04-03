import uuid
import json
import collections
from gdt.automatch.requirement import Requirement

# NOTE: These objects are not guaranteed to be immutable. Use their unique ids
# to identify them in hashes or client-server communication.


# A Match is a collection of possibly-compatible seeks plus the information
# necessary to start a game on goko: rating system, host, and room. The
# roomname may be provided later. The id is random.
#
# A Match can represent either a game offer or an actual game.
#
class Match:
    def __init__(self, seeks, rating_system, hostname, roomname=None,
                 roomid=None, tableindex=None):
        self.seeks = seeks
        self.rating_system = rating_system
        self.hostname = hostname
        self.roomname = roomname
        self.roomid = roomid
        self.tableindex = tableindex
        self.acceptors = set()
        self.vpcounter = None
        self.matchid = uuid.uuid4().hex

    # Verify that match satisfies requirements for all seeks
    def is_match_ok(self):
        if not self.rating_system or not self.hostname:
            return False

        # No player can appear twice in the same game
        pnames = [s.player.pname for s in self.seeks]
        seen = set()
        for p in pnames:
            if (p in seen):
                return False
            seen.add(p)

        if ('timmytucker' in pnames):
            return False

        # Verify that no seek's requirements are violated and that no
        # blacklisted players are included
        for s in self.seeks:
            for r in s.requirements:
                if not r.is_match_ok(s.player, self):
                    return False
            pnamesLC = [p.lower() for p in pnames]
            blackLC = [b.lower() for b in s.blacklist]
            if len(list(set(pnamesLC) & set(blackLC))) > 0:
                print('Blacklisted player(s):')
                print(list(set(pnamesLC) & set(blackLC)))
                return False

        return True

    def to_dict(self):
        return {'seeks': [s.to_dict() for s in self.seeks],
                'hostname': self.hostname,
                'roomname': self.roomname,
                'roomid': self.roomid,
                'tableindex': self.tableindex,
                'rating_system': self.rating_system,
                'acceptors': list(self.acceptors),
                'vpcounter': self.vpcounter,
                'matchid': self.matchid}

    def get_pnames(self):
        return [s.player.pname for s in self.seeks]

    def get_host(self):
        is_host = lambda s: s.player.pname == self.hostname
        hosts = list(filter(is_host, self.seeks))
        if len(hosts) >= 1:
            return hosts[0].player
        else:
            return None

    def get_guests(self):
        is_guest = lambda s: s.player.pname != self.hostname
        return list(filter(is_guest, self.seeks))


# A Seek is a Player and his SeekRequirements. ID is random.
class Seek:
    def __init__(self, player, requirements, blacklist):
        self.player = player
        self.requirements = requirements
        self.blacklist = blacklist
        self.seekid = uuid.uuid4().hex

    @staticmethod
    def from_dict(d):
        player = Player.from_dict(d['player'])
        requirements = [Requirement.from_dict(r) for r in d['requirements']]
        if 'blacklist' in d:
            blacklist = d['blacklist']
        else:
            blacklist = []
        return Seek(player, requirements, blacklist)

    def to_dict(self):
        d = {}
        d['player'] = self.player.to_dict()
        d['requirements'] = [sr.to_dict() for sr in self.requirements]
        d['blacklist'] = self.blacklist
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
        d['sets_owned'] = self.sets_owned
        return d


# A player's Rating consists of his "official" Goko pro and casual ratings,
# and possibly an unofficial iso-style TrueSkill or other rating system
# provided by the CouncilRoom or drunkensailor server.
class Rating:
    def __init__(self, goko_casual_rating, goko_pro_rating, isotropish_rating):
        self.goko_casual_rating = goko_casual_rating
        self.goko_pro_rating = goko_pro_rating
        self.isotropish_rating = isotropish_rating

    @staticmethod
    def from_dict(d):
        ir = None
        if 'isotropish_rating' in d:
            ir = d['isotropish_rating']
        return Rating(d['goko_casual_rating'], d['goko_pro_rating'], ir)

    def to_dict(self):
        d = {}
        d['goko_casual_rating'] = self.goko_casual_rating
        d['goko_pro_rating'] = self.goko_pro_rating
        d['isotropish_rating'] = self.isotropish_rating
        return d


# TODO: Implement JSONDecoder too
# TODO: get rid of to_dict()?
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
        elif isinstance(obj, dict):
            return obj
        return json.JSONEncoder.default(self, obj)
