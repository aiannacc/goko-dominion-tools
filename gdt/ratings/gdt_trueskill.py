import trueskill
from trueskill import Rating
import sys
import time
from ..model import db_manager

# TODO: use player hash instead of player names

# This class is in serious need of refactoring, as is all of the trueskill
# leaderboard code.


dominion_env = trueskill.TrueSkill(draw_probability=0.0175, backend='scipy')
isodominion_env = trueskill.TrueSkill(mu=25, sigma=25, beta=25, tau=25/100, draw_probability=0.05, backend='scipy')


def pwin(rA=Rating(), rB=Rating(), env=None):
    deltaMu = rA.mu - rB.mu
    rsss = (rA.sigma**2 + rB.sigma**2)**(0.5)
    return env.cdf(deltaMu/rsss)


def rate(ra, rb, score, env):
    if score == 1:
        return trueskill.rate_1vs1(ra, rb, env=env)
    elif score == -1:
        return reversed(trueskill.rate_1vs1(rb, ra, env=env))
    else:
        return trueskill.rate_1vs1(ra, rb, env=env, drawn=True)

def generate_ratings(limit, last_time, last_logfile, do_lookup, env):
    history = []
    r = {}
    n = {}
    for row in db_manager.search_all_2p_scores(limit, last_time, last_logfile):
        (time, logfile, p1name, p2name, p1score) = row

        # Initialize or look up ratings if necessary
        for pname in (p1name, p2name):
            if not pname in r:
                if do_lookup:
                    ms = db_manager.get_rating(pname)
                    if ms:
                        r[pname] = env.create_rating(ms[0], ms[1])
                        n[pname] = db_manager.get_game_count(pname)
                        if n[pname] is None:
                            n[pname] = 0
                    else:
                        r[pname] = env.create_rating()
                        n[pname] = 0
                else:
                    r[pname] = env.create_rating(ms[0], ms[1])
                    n[pname] = 0

        # Update ratings
        (oldr1, oldr2) = (r[p1name], r[p2name])
        (r[p1name], r[p2name]) = rate(r[p1name], r[p2name], p1score, env)
        n[p1name] = n[p1name] + 1
        n[p2name] = n[p2name] + 1

        # Cache game and rating info
        history.append({'time': time,
                        'logfile': logfile,
                        'pname': p1name,
                        'old_rating': oldr1,
                        'old_opp_rating': oldr2,
                        'score': p1score,
                        'new_rating': r[p1name],
                        'numgames': n[p1name]})
        history.append({'time': time,
                        'logfile': logfile,
                        'pname': p2name,
                        'old_rating': oldr2,
                        'old_opp_rating': oldr1,
                        'score': -p1score,
                        'new_rating': r[p2name],
                        'numgames': n[p2name]})

    return (history, r)


def record_ratings(limit, last_time, last_logfile, env):
    """Starting with the first game after <last_logfile>, process the next
       <count> games, updating and caching players' ratings"""

    (history, ratings) = generate_ratings(limit, last_time, last_logfile, True, env)
    db_manager.insert_ratings(history)
    return len(history)
