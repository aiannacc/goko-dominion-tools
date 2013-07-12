#!/usr/bin/env python


# Data structure for stored Dominion Games
class GameResult:
    def __init__(self, supply, gains, rets, rating, shelters, guest, bot,
                 pCount, colony, presults, adventure):
        self.supply = supply  # List of supply card names
        self.rating = rating  # Rating system used (only after May 12, 2013)
        self.shelters = shelters
        self.gains = gains
        self.rets = rets

        # Redundant metadata for convenience
        self.guest = guest
        self.bot = bot
        self.colony = colony
        self.adventure = adventure

        # Identifying information, if available
        self.logfile = None
        self.time = None

        # Organize player result info in a hash.
        # NOTE: Duplicate bot names are possible in early logs.
        #       I've skipped those games.
        self.presults = presults

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()


class PlayerResult:
    def __init__(self, pname):
        self.pname = pname
        self.vps = None
        self.turns = 0
        self.rank = None
        self.quit = False
        self.order = None
        self.resign = False

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()


class GainRet:
    def __init__(self, cname, cpile, pname, turn):
        self.pname = pname
        self.cpile = cpile
        self.cname = cname
        self.turn = turn

    def __str__(self):
        return self.__dict__.__str__()

    def __repr__(self):
        return self.__dict__.__repr__()
