import sys
import datetime
import trueskill
import logging
import time

from gdt.model import db_manager
from gdt.ratings.history import RatingHistory


logger = logging.getLogger('logwatcher')

def record_ratings(rating_history, system):
    rh = rating_history
    logger.info('Recording %d changed ratings' % len(rh.updated))
    for pname in rh.updated:
        db_manager.record_ts_rating(system, pname, rh.rating[pname],
                                    rh.numgames[pname],
                                    rh.last_gametime[pname],
                                    rh.last_logfile[pname])
    rh.clear_updated()


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
                     min_turns=0, only_2p_games=True,
                     chunk_size=1000, max_games=sys.maxsize,
                     use_gameresult_cache=False,
                     gokomode='pro', include_unknown_rs=False):
    """ Retreive eligible games since the last one that we handled.  Eligible
        means 2-player, Pro, no guest players.  Update ratings for these.
        Return RatingHistory objects, but leave it to the invoking method to
        update the database.
    """
    more_results = True
    i = 0
    while more_results and i < max_games:
        logger.debug('Fetching game results from database')
        #for x in [last_time, last_logfile, rhistories, allow_guests,
        #          allow_bots, min_turns, only_2p_games, chunk_size, max_games,
        #          use_gameresult_cache, gokomode, include_unknown_rs]:
        #    logger.debug(x)
        if use_gameresult_cache:
            pcount = (2 if only_2p_games else None)
            results = db_manager.get_cached_multiplayer_scores(
                chunk_size, last_time, last_logfile,
                allow_guests=allow_guests, allow_bots=allow_bots,
                min_turns=min_turns, pcount=pcount)
        else:
            results = db_manager.get_multiplayer_scores(
                chunk_size, last_time, last_logfile,
                rating_system=gokomode,
                allow_guests=allow_guests, allow_bots=allow_bots,
                include_unknown_rs=include_unknown_rs, min_turns=min_turns,
                pcount=(2 if only_2p_games else None))
        logger.debug('Got %d games to rate' % len(results))
        more_results = False
        for gr in results:
            # Manual name change for user 'Burning Skull'
            for j in range(len(gr.pnames)):
                if gr.pnames[j] == 'burning_scull':
                    gr.pnames[j] = 'Burning Skull'
                if gr.pnames[j] == 'hugovj':
                    gr.pnames[j] = 'Hugovj'
            if i >= max_games:
                break
            for rh in rhistories:
                old_ratings = rh.get_pregame_ratings(gr)
                rh.add_game(gr)
                new_ratings = rh.get_pregame_ratings(gr)
            last_time = gr.time
            last_logfile = gr.logfile
            more_results = True

            i += 1
            if i % 1000 == 0:
                logger.debug('Rated %d games so far.' % i)

    logger.info('Rated %d games in total.' % i)
