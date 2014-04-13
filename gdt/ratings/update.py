import sys
import datetime
import trueskill
import logging

from gdt.model import db_manager
from gdt.ratings.history import RatingHistory
import gdt.ratings.rating_system


def record_ratings(rating_history, system):
    rh = rating_history
    for pname in rh.rating:
        db_manager.record_ts_rating(system, pname, rh.rating[pname],
                                    rh.numgames[pname],
                                    rh.last_gametime[pname],
                                    rh.last_logfile[pname])


def get_rating_history_stub(rating_system, system_dbname):
    rhistory = RatingHistory(rating_system)
    ratings = db_manager.fetch_ratings2(system_dbname)
    for m in ratings:
        r = trueskill.Rating(m['mu'], m['sigma'])
        rhistory.set_player(m['pname'], r, m['numgames'],
                            m['last_gametime'], m['last_logfile'])
    return rhistory


def rate_games_since(last_time, last_logfile, rhistories,
                     allow_guests=False, allow_bots=True,
                     rating_system='pro', include_unknown_rs=False,
                     min_turns=0, chunk_size=1000, max_games=sys.maxsize,
                     only_2p_games=True):
    """ Retreive eligible games since the last one that we handled.  Eligible
        means 2-player, Pro, no guest players.  Update ratings for these.
        Return RatingHistory objects, but leave it to the invoking method to
        update the database.
    """
    # Process scores in chunks of 1000
    more_results = True
    i = 0
    while more_results and i < max_games:
        results = db_manager.get_multiplayer_scores(
            chunk_size, last_time, last_logfile, allow_guests=allow_guests,
            allow_bots=allow_bots, rating_system=rating_system,
            include_unknown_rs=include_unknown_rs, min_turns=min_turns,
            pcount=(2 if only_2p_games else None))
        more_results = False
        for gr in results:
            i += 1

            for rh in rhistories:

                old_ratings = rh.get_pregame_ratings(gr)
                rh.add_game(gr)
                new_ratings = rh.get_pregame_ratings(gr)

                ## Verify by checking against existing table
                #ps = db_manager._con.prepare("""
                #    SELECT pname, old_mu, old_sigma, new_mu, new_sigma
                #      FROM ts_rating_history
                #     WHERE logfile = $1""")
                #for (p, m1, s1, m2, s2) in ps(gr.logfile):
                #    m1 = float(m1)
                #    s1 = float(s1)
                #    m2 = float(m2)
                #    s2 = float(s2)
                #    if round(old_ratings[p].mu - m1, 3) != 0:
                #        print(old_ratings)
                #        print(gr)
                #        print(new_ratings)
                #        print('Old mu:', p, m1, old_ratings[p].mu)
                #        sys.exit(-1)
                #    if round(old_ratings[p].sigma - s1, 3) != 0:
                #        print(old_ratings)
                #        print(gr)
                #        print(new_ratings)
                #        print('Old sigma:', p, s1, old_ratings[p].sigma)
                #        sys.exit(-1)
                #    if round(new_ratings[p].mu - m2, 3) != 0:
                #        print(old_ratings)
                #        print(gr)
                #        print(new_ratings)
                #        print('New mu:', p, m2, new_ratings[p].mu)
                #        sys.exit(-1)
                #    if round(new_ratings[p].sigma - s2, 3) != 0:
                #        print(old_ratings)
                #        print(gr)
                #        print(new_ratings)
                #        print('New sigma:', p, s2, new_ratings[p].sigma)
                #        sys.exit(-1)

            last_time = gr.time
            logging.debug(gr)
            logging.debug('')


            last_logfile = gr.logfile
            more_results = True
