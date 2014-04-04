import sys
import datetime
from gdt.model import db_manager
from gdt.ratings.history import RatingHistory
import gdt.ratings.rating_system

count = 0

def rate_games_since(last_time, last_logfile, rating_systems):
    """ Retreive eligible games since the last one that we handled.  Eligible
        means 2-player, Pro, no guest players.  Update ratings for these.
    """
    global count

    rhistories = {}
    for s in rating_systems:
        rhistories[s] = RatingHistory(s, skip_player=0)

    # Get scores in chunks
    more_rows = True
    while more_rows:
        print()
        print(count)
        for s in rating_systems:
            print(rhistories[s])

        # I'm throwing out games in which each player doesn't take at least one
        # turn.  Yes, there's opportunity for abuse, but I expect it to be rare
        # compared to the number of Goko/MF game connections failures.
        rows = db_manager.get_2p_scores(1000, last_time, last_logfile,
                                        allow_guests=True, rating_system='pro',
                                        min_turns=0)
        more_rows = False
        for (gametime, logfile, pname_a, pname_b, score_a) in rows:
            more_rows = True
            count += 1
            for s in rating_systems:
                rh = rhistories[s]
                rh.add_game(pname_a, pname_b, score_a, gametime=gametime)
            last_time = gametime
            logfile = logfile
