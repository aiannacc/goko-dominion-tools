import sys
import datetime
from gdt.model import db_manager
from gdt.ratings.history import RatingHistory
import gdt.ratings.rating_system


def rate_games_since(last_time, last_logfile, rating_systems,
                     allow_guests=False, rating_system='pro', min_turns=0):
    """ Retreive eligible games since the last one that we handled.  Eligible
        means 2-player, Pro, no guest players.  Update ratings for these.
        Return RatingHistory objects, but leave it to the invoking method to
        update the database.
    """
    rhistories = {}
    for s in rating_systems:
        rhistories[s] = RatingHistory(s, skip_player=0)

    # Process scores in chunks of 1000
    chunk_size = 1000
    more_rows = True
    while more_rows:
        rows = db_manager.get_2p_scores(chunk_size, last_time, last_logfile,
                                        allow_guests=allow_guests,
                                        rating_system=rating_system,
                                        min_turns=min_turns)
        more_rows = False
        i = 0
        for (gametime, logfile, pname_a, pname_b, score_a) in rows:
            more_rows = True
            i += 1
            for s in rating_systems:
                rh = rhistories[s]
                rh.add_game(pname_a, pname_b, score_a, gametime=gametime)
            last_time = gametime
            last_logfile = logfile

    return rhistories
