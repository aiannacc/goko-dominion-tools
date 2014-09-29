import hashlib
import sys
import os
import re
import time
import socket
import datetime
import logging
import copy
import math

import trueskill
import postgresql

from . import domgame
from . import constants


# Database connection object.
# TODO: Initialized on first use instead of on load
_con = postgresql.open(user='ai', host='gokosalvager.com', database='goko', password='RebuildScout')


def prepare(conn, sql, d):
    """ Convenience method for creating parameterized statements for use with
        py-postgresql. Allows values to be referenced by name rather than by
        index.
    """
    params = []
    m = re.findall('{(.*?)}', sql)
    for k in set(m):
        params.append(d[k] if k in d else None)
        sql = re.sub('{%s}' % k, "$%d" % len(params), sql)
    return (conn.prepare(sql), params)


def get_heads_up_record(pname1, pname2):
    rows = _con.prepare(
        """SELECT (0.5 + 0.5 * (p2.rank - p1.rank)) AS score, count(*)
             FROM presult p1
             JOIN presult p2 USING(logfile)
            WHERE p1.pname=$1
                  AND p2.pname=$2
            GROUP BY score
        """)(pname1, pname2)
    draws = 0
    wins = 0
    losses = 0
    for r in rows:
        if float(r[0]) == 0.0:
            losses = r[1]
        elif float(r[0]) == 0.5:
            draws = r[1]
        elif float(r[0]) == 1.0:
            wins = r[1]
        else:
            raise 'Impossible score value: %4.2f' % r[1]
    return {
        'wins': wins,
        'draws': draws,
        'losses': losses
    }


def search_game_results(search):
    return fetch_game_results(search_log_filenames(search))


def delete_logs(logfiles):
    _con.prepare('DELETE FROM game WHERE logfile=$1').load_rows(logfiles)
    _con.prepare('DELETE FROM presult WHERE logfile=$1').load_rows(logfiles)
    #_con.prepare('DELETE FROM gain WHERE logfile=$1').load_rows(logfiles)
    #_con.prepare('DELETE FROM ret WHERE logfile=$1').load_rows(logfiles)


def search_daily_log_filenames(day):
    start = datetime.datetime.strptime(day.strftime('%Y%m%d'), '%Y%m%d')
    start = start + datetime.timedelta(hours=-1)
    end = day + datetime.timedelta(days=1)
    sql = """SELECT logfile FROM game g WHERE g.time between $1 and $2"""
    out = []
    for r in _con.prepare(sql)(start, end):
        out.append(r[0])
    sql = """SELECT logfile FROM parsefail WHERE time between $1 and $2"""
    for r in _con.prepare(sql)(start, end):
        out.append(r[0])
    return out


def search_log_filenames(p):
    """ Fetch log filenames for matching games.
        - <p> is a dict of search parameters. Missing/None values ignored.
        Games are ordered from newest to oldest. If not None, <offset> skips
        results and <limit> restricts how many are returned."""

    # Don't modify the original <search> argument
    p = copy.deepcopy(p)

    # Cards in the supply list --> s1, s2, etc
    for i in range(0, 11):
        p['s%d' % i] = ('(^|, )%s($|, )' % p['supply'][i]
                        if 'supply' in p and len(p['supply']) > i
                        else None)
    del p['supply']

    # Cards in the not-in-supply list --> ns1, ns2, netc
    for i in range(0, 11):
        p['ns%d' % i] = (p['nonsupply'][i]
                         if 'nonsupply' in p and len(p['nonsupply']) > i
                         else None)
    del p['nonsupply']

    if 'p1score' in p and p['p1score'] is not None:
        p['p1score'] = int(p['p1score'])

    # Solo games require a different query
    if 'pcount' in p and p['pcount'] == 1:
        sql = log_search_sql_solo(p)
    else:
        sql = log_search_sql(p)

    (ps, params) = prepare(_con, sql, p)
    return [r[0] for r in ps(*params)]


def log_search_sql_solo(p):
    # Parameterized search statement.
    return """SELECT DISTINCT logfile, time
               FROM game g
               JOIN presult p1 USING(logfile)
         WHERE ({p1name}::varchar IS NULL
                OR {casesensitive} AND {p1name} = p1.pname
                OR NOT {casesensitive} AND lower({p1name}) = p1.pname_lower)
           AND ({bot}::boolean       IS NULL OR {bot} = g.bot)
           AND ({guest}::boolean     IS NULL OR {guest} = g.guest)
           AND ({shelters}::boolean  IS NULL OR {shelters} = g.shelters)
           AND ({colony}::boolean    IS NULL OR {colony} = g.colony)
           AND ({pcount}::smallint   IS NULL OR {pcount} = g.pcount)
           AND ({s0}::varchar        IS NULL OR g.supply ~* {s0})
           AND ({s1}::varchar        IS NULL OR g.supply ~* {s1})
           AND ({s2}::varchar        IS NULL OR g.supply ~* {s2})
           AND ({s3}::varchar        IS NULL OR g.supply ~* {s3})
           AND ({s4}::varchar        IS NULL OR g.supply ~* {s4})
           AND ({s5}::varchar        IS NULL OR g.supply ~* {s5})
           AND ({s6}::varchar        IS NULL OR g.supply ~* {s6})
           AND ({s7}::varchar        IS NULL OR g.supply ~* {s7})
           AND ({s8}::varchar        IS NULL OR g.supply ~* {s8})
           AND ({s9}::varchar        IS NULL OR g.supply ~* {s9})
           AND ({s10}::varchar       IS NULL OR g.supply ~* {s10})
           AND ({ns0}::varchar       IS NULL OR g.supply ~* {ns0})
           AND ({ns1}::varchar       IS NULL OR g.supply ~* {ns1})
           AND ({ns2}::varchar       IS NULL OR g.supply ~* {ns2})
           AND ({ns3}::varchar       IS NULL OR g.supply ~* {ns3})
           AND ({ns4}::varchar       IS NULL OR g.supply ~* {ns4})
           AND ({ns5}::varchar       IS NULL OR g.supply ~* {ns5})
           AND ({ns6}::varchar       IS NULL OR g.supply ~* {ns6})
           AND ({ns7}::varchar       IS NULL OR g.supply ~* {ns7})
           AND ({ns8}::varchar       IS NULL OR g.supply ~* {ns8})
           AND ({ns9}::varchar       IS NULL OR g.supply ~* {ns9})
           AND ({ns10}::varchar      IS NULL OR g.supply ~* {ns10})
           AND ({maxturns}::smallint IS NULL OR {maxturns} >= p1.turns)
           AND ({minturns}::smallint IS NULL OR {minturns} <= p1.turns)
           AND ({quit}::boolean      IS NULL OR {quit} = p1.quit)
           AND ({resign}::boolean    IS NULL OR {resign} = p1.resign)
           AND ({startdate}::date    IS NULL OR g.time > {startdate})
           AND ({enddate}::date      IS NULL OR g.time < {enddate})
           AND ({rating}::varchar    IS NULL OR {rating} = g.rating
                OR {rating} = 'pro+' AND g.rating IN ('pro', 'unknown'))
         ORDER BY time DESC
         LIMIT {limit}
        OFFSET {offset}"""


def log_search_sql(p):
    # Parameterized search statement.
    return """SELECT DISTINCT logfile, time
               FROM game g
               JOIN presult p1 USING(logfile)
               JOIN presult p2 USING(logfile)
         WHERE (p1.pname != p2.pname)
           AND ({p1name}::varchar IS NULL
                OR {casesensitive} AND {p1name} = p1.pname
                OR NOT {casesensitive} AND lower({p1name}) = p1.pname_lower)
           AND ({p2name}::varchar IS NULL
                OR {casesensitive} AND {p2name} = p2.pname
                OR NOT {casesensitive} AND lower({p2name}) = p2.pname_lower)
           AND ({p1score}::smallint IS NULL OR {p1score} = (p2.rank - p1.rank))
           AND ({bot}::boolean      IS NULL OR {bot} = g.bot)
           AND ({guest}::boolean    IS NULL OR {guest} = g.guest)
           AND ({shelters}::boolean IS NULL OR {shelters} = g.shelters)
           AND ({colony}::boolean   IS NULL OR {colony} = g.colony)
           AND ({pcount}::smallint  IS NULL OR {pcount} = g.pcount)
           AND ({s0}::varchar       IS NULL OR g.supply ~* {s0})
           AND ({s1}::varchar       IS NULL OR g.supply ~* {s1})
           AND ({s2}::varchar       IS NULL OR g.supply ~* {s2})
           AND ({s3}::varchar       IS NULL OR g.supply ~* {s3})
           AND ({s4}::varchar       IS NULL OR g.supply ~* {s4})
           AND ({s5}::varchar       IS NULL OR g.supply ~* {s5})
           AND ({s6}::varchar       IS NULL OR g.supply ~* {s6})
           AND ({s7}::varchar       IS NULL OR g.supply ~* {s7})
           AND ({s8}::varchar       IS NULL OR g.supply ~* {s8})
           AND ({s9}::varchar       IS NULL OR g.supply ~* {s9})
           AND ({s10}::varchar      IS NULL OR g.supply ~* {s10})
           AND ({ns0}::varchar       IS NULL OR g.supply !~* {ns0})
           AND ({ns1}::varchar       IS NULL OR g.supply !~* {ns1})
           AND ({ns2}::varchar       IS NULL OR g.supply !~* {ns2})
           AND ({ns3}::varchar       IS NULL OR g.supply !~* {ns3})
           AND ({ns4}::varchar       IS NULL OR g.supply !~* {ns4})
           AND ({ns5}::varchar       IS NULL OR g.supply !~* {ns5})
           AND ({ns6}::varchar       IS NULL OR g.supply !~* {ns6})
           AND ({ns7}::varchar       IS NULL OR g.supply !~* {ns7})
           AND ({ns8}::varchar       IS NULL OR g.supply !~* {ns8})
           AND ({ns9}::varchar       IS NULL OR g.supply !~* {ns9})
           AND ({ns10}::varchar      IS NULL OR g.supply !~* {ns10})
           AND ({maxturns}::smallint IS NULL
                OR {maxturns} >= GREATEST(p1.turns, p2.turns))
           AND ({minturns}::smallint IS NULL
                OR {minturns} <= GREATEST(p1.turns, p2.turns))
           AND ({quit}::boolean     IS NULL OR {quit} = (p1.quit OR p2.quit))
           AND ({resign}::boolean   IS NULL
                OR {resign} = (p1.resign OR p2.resign))
           AND ({rating}::varchar   IS NULL OR {rating} = g.rating
                OR {rating} = 'pro+' AND g.rating IN ('pro', 'unknown'))
           AND ({startdate}::date IS NULL OR g.time > {startdate})
           AND ({enddate}::date IS NULL OR g.time < {enddate})
         ORDER BY time DESC
         LIMIT {limit}
        OFFSET {offset}"""


def fetch_game_results(log_filenames):
    """ Fetch supply, VPs per player, etc. Return a GameResult object.
        Return results in the same order as the original log files"""

    ps = _con.prepare("""SELECT * FROM game g WHERE logfile = ANY($1)""")
    games = {}
    for r in ps(log_filenames):
        g = domgame.GameResult.blank()
        for k in ['time', 'logfile', 'colony', 'shelters']:
            setattr(g, k, r[k])
        g.supply = []
        for s in r['supply'].split(','):
            if not(s.lower() in constants.CORE_CARDS):
                g.supply.append(s)
        g.supply = sorted(g.supply)
        games[g.logfile] = g

    # Fetch player-specific game results
    ps = _con.prepare("""SELECT * FROM presult p WHERE logfile = ANY($1)""")
    for r in ps(log_filenames):
        p = domgame.PlayerResult(r['pname'])
        for k in ['vps', 'turns', 'rank', 'quit', 'resign']:
            setattr(p, k, r[k])
        games[r['logfile']].presults[p.pname] = p

    return [games[lf] for lf in log_filenames]


def fetch_card_image_url(card):
    """ Retrieve third-party URL for a Dominion card image """
    return _con.prepare("""SELECT url FROM card_url WHERE
                        card=$1""")(card)[0][0]


def search_scores(search):
    logfiles = search_log_filenames(search)
    ps = _con.prepare(
        """SELECT logfile, p1.pname as p1name, p2.pname as p2name,
                  p2.rank - p1.rank as p1score
             FROM presult p1
             JOIN presult p2 USING(logfile)
            WHERE p1.pname < p2.pname
              AND logfile = ANY($1)""")
    return ps(logfiles)


def get_last_rated_game(system='isotropish'):
    return _con.prepare("""SELECT time, logfile
                             FROM ts_rating2
                            WHERE system=$2
                            ORDER BY time desc
                            LIMIT 1""")(system)[0]


def get_last_rated_game2(system):
    r = _con.prepare("""SELECT time, logfile
                             FROM ts_rating2
                            WHERE system=$1
                            ORDER BY time desc
                            LIMIT 1""")(system)
    if len(r) == 0:
        return [None, None]
    else:
        return r[0]


def get_cached_gameresults(limit, time, logfile, allow_guests=False,
                           allow_bots=False, min_turns=0, pcount=None):
    ps = _con.prepare(
        """SELECT time, logfile, pcount,
                  pname1, rank1,
                  pname2, rank2,
                  pname3, rank3,
                  pname4, rank4,
                  pname5, rank5,
                  pname6, rank6
             FROM game_result
            WHERE ($2::timestamp IS NULL OR time>=$2)
              AND ($3::varchar IS NULL OR logfile!=$3)
              AND ($4 OR NOT guest)
              AND ($5 OR NOT bot)
              AND (min_turns >= $6)
              AND ($7::int IS NULL OR pcount=$7)
            ORDER BY time ASC
            LIMIT $1
        """)
    out = []
    for row in ps(limit, time, logfile, allow_guests,
                  allow_bots, min_turns, pcount):
        (time, logfile, count, n1, r1, n2,
         r2, n3, r3, n4, r4, n5, r5, n6, r6) = row
        r = domgame.GameRanks(logfile, time)
        pnames = [n1, n2, n3, n4, n5, n6]
        pranks = [r1, r2, r3, r4, r5, r6]
        for i in range(count):
            r.add_player_result(pnames[i], pranks[i])
        out.append(r)
    return out


def search_all_2p_scores(limit, time, logfile):
    ps = _con.prepare(
        """SELECT g.time, g.logfile, p1.pname as p1name, p2.pname as p2name,
                  p2.rank - p1.rank as p1score
             FROM game g
             JOIN presult p1 USING(logfile)
             JOIN presult p2 USING(logfile)
            WHERE p1.pname < p2.pname
              AND g.rating = 'pro'
              AND g.pcount = 2
              AND NOT g.guest
              AND ($2::timestamp IS NULL OR g.time>=$2)
              AND ($3::varchar IS NULL OR g.logfile!=$3)
            ORDER BY g.time ASC
            LIMIT $1""")
    return ps(limit, time, logfile)


def get_multiplayer_scores(limit, time, logfile, allow_guests=False,
                           allow_bots=False, rating_system='pro',
                           include_unknown_rs=False, min_turns=0,
                           pcount=None):

    # I just changed WHERE ($2::timestamp IS NULL OR g.time>=$2)
    #             to WHERE ($2::timestamp IS NULL OR g.time>$2)
    # in an attempt to eliminate the 50k games problem.  I'm not really sure
    # if this logic is right.  I think I may end up sometimes dropping the
    # game with the smaller logfile when two games have an identical timestamp.

    ps = _con.prepare(
        """SELECT g.time, g.logfile, p.pname, p.rank, g.pcount
             FROM game g
             JOIN presult p USING(logfile)
            WHERE ($2::timestamp IS NULL OR g.time>$2)
              AND ($3::varchar IS NULL OR g.logfile!=$3)
              AND ($4::boolean OR $4 OR (NOT g.guest))
              AND ($5::boolean OR $5 OR (NOT g.bot))
              AND (($6::varchar IS NULL OR g.rating=$6)
                   OR ($7 AND g.rating IS NULL))
              AND ($8::smallint IS NULL OR p.turns>=$8)
              AND ($9::smallint IS NULL OR g.pcount=$9)
              AND (g.pcount > 1)
            ORDER BY g.time ASC
            LIMIT $1""")

    # On rare occasions, two games will have identical time stamps.  It's more
    # efficient to handle these manually then to have the database query sort
    # by both time and logfile.
    out = []
    results = {}
    pcounts = {}
    last_time = None
    print(limit, time, logfile, allow_guests, allow_bots, rating_system, include_unknown_rs, min_turns, pcount)
    for (t, l, p, r, n) in ps.rows(limit, time, logfile, allow_guests,
                                   allow_bots, rating_system,
                                   include_unknown_rs, min_turns, pcount):
        if l not in results:
            results[l] = domgame.GameRanks(l, t)
            pcounts[l] = n
            out.append(results[l])
        results[l].add_player_result(p, r)
        last_time = t

    # Don't return incomplete games.  These can happen if one of the presult
    # rows gets dropped because of the minimum number of turns, or if the
    # LIMIT value lands in the middle of a game's set of presults.
    return [r for r in out if len(r.pnames) == pcounts[r.logfile]]


def fetch_rated_game_counts():
    ps = _con.prepare("""SELECT pname, COUNT(pname) FROM ts_rating_history
                      GROUP BY pname""")
    return ps()


def fetch_ratings2(system, min_level=None, min_games=None, active_since=None,
                   guest=True, offset=0, count=sys.maxsize, sortkey='level'):
    # TODO: Fix the Boodaloo problem more elegantly
    q = """SELECT pname, (mu - 3 * sigma) as level,
                  mu, sigma, numgames, time, logfile
             FROM ts_rating2
            WHERE pname != 'Boodaloo'
              AND pname != 'ottocar'
              AND ($1::int IS NULL OR (mu - 3*sigma) >= $1)
              AND ($2::int IS NULL OR numgames >= $2)
              AND ($3::timestamp IS NULL OR time >= $3)
              AND ($4 OR guest IS NULL OR NOT guest)
              AND system = $5
            ORDER BY %s DESC
            LIMIT $7
           OFFSET $6
        """ % (sortkey)
    ps = _con.prepare(q)
    out = []
    i = 0
    for (p, l, m, s, n, t, lf) in ps(min_level, min_games, active_since, guest,
                                     system, offset, count):
        i += 1
        out.append({
            'pname': p,
            'mu': float(m),
            'level': float(l),
            'sigma': float(s),
            'numgames': int(n),
            'rank': i,
            'last_gametime': t,
            'last_logfile': lf
        })
    return out


def fetch_ratings(min_level=None, min_games=None, active_since=None,
                  guest=True, offset=0, count=sys.maxsize, sortkey='level',
                  system='isotropish'):
    # TODO: Fix the Boodaloo problem more elegantly
    q = """SELECT pname, (mu - 3 * sigma) as level, mu, sigma, numgames
             FROM ts_rating2
            WHERE pname != 'Boodaloo'
              AND pname != 'ottocar'
              AND ($1::int IS NULL OR (mu - 3*sigma) >= $1)
              AND ($2::int IS NULL OR numgames >= $2)
              AND ($3::timestamp IS NULL OR time >= $3)
              AND ($4 OR guest IS NULL OR NOT guest)
              AND (system=$7)
            ORDER BY %s DESC
            LIMIT $6
           OFFSET $5
        """ % (sortkey)
    ps = _con.prepare(q)
    out = []
    i = 0

    for (p, l, m, s, n) in ps(min_level, min_games, active_since, guest,
                              offset, count, system):
        i += 1
        out.append({
            'pname': p,
            'mu': float(m),
            'level': float(l),
            'sigma': float(s),
            'numgames': int(n),
            'rank': i
        })
    return out


def fetch_last_rated_log_time(system='isotropish'):
    return _con.prepare("""SELECT max(time) 
                             FROM ts_rating2
                            WHERE system=$1""")(system)[0]


def get_all_ratings_by_id(system='isotropish'):
    qrows = _con.prepare("""SELECT r.time, i.playerid,
                                   r.mu - 3 * r.sigma as level
                              FROM ts_rating2 r
                              JOIN playerinfo i
                                ON r.pname = i.playername
                             WHERE r.system=$1""")(system)
    out = {}
    last_time = None
    for (time, playerid, level) in qrows:
        if last_time is None:
            last_time = time
        last_time = max(last_time, time)
        out[playerid] = math.floor(level).__float__()
    return (out, last_time)


def get_new_ratings(since_time, system='isotropish'):
    qrows = _con.prepare("""SELECT r.time, i.playerid,
                                   r.mu - 3 * r.sigma as level
                              FROM ts_rating2 r
                              JOIN playerinfo i
                                ON r.pname = i.playername
                             WHERE r.time > $1
                               AND r.system = $2
                         """)(since_time, system)
    out = {}
    last_time = since_time
    for (time, playerid, level) in qrows:
        last_time = max(last_time, time)
        out[playerid] = math.floor(level).__float__()
    return (out, last_time)


def get_rating_by_id(playerId, system='isotropish'):
    ps = _con.prepare("""SELECT r.mu, r.sigma, r.numgames
                            FROM ts_rating2 r
                            JOIN playerinfo i
                              ON r.pname = i.playerName
                           WHERE i.playerId=$1
                             AND r.system=$2
                           ORDER BY time DESC""")
    msn = ps.first(playerId, system)
    if msn:
        return (float(msn[0]), float(msn[1]), msn[2])
    else:
        return msn


def get_rating(pname, system='isotropish'):
    ps = _con.prepare("""SELECT mu, sigma, numgames
                            FROM ts_rating2
                           WHERE pname=$1
                             AND system=$2
                           ORDER BY time DESC""")
    msn = ps.first(pname, system)
    if msn:
        return (float(msn[0]), float(msn[1]), msn[2])
    else:
        return msn


def summarize_scores(pname, search):
    result_counts = {-1: 0, 0: 0, 1: 0}
    for r in search_scores(search):
        if pname == r['p1name']:
            result_counts[r['p1score']] += 1
        if pname == r['p2name']:
            result_counts[r['p1score']] += 1
    return result_counts


def get_bot_names():
    """Goko's lobby bots"""
    ps = _con.prepare('SELECT pname from bot')
    return [r[0] for r in ps()]


def is_bot(pname):
    """Check if given player is a lobby bot. Note that this"""
    for bot in get_bot_names():
        # Match names like 'Conqueror Bot III'
        if pname and pname.startswith(bot):
            return True
    return False


def get_advbot_names():
    """Oppponents in the Goko adventures quest"""
    return _con.prepare('SELECT pname from advbot')()


def fetch_supply_cards():
    """ All the cards in the game, lowercased """
    ps = _con.prepare("SELECT card FROM card_url")
    return [r[0].lower() for r in ps()]


def insert_card_url(card, url):
    """ Store third-party URL for a Dominion card image. """
    _con.prepare("""INSERT INTO card_url VALUES ($1, $2)""")(card, url)


def insert_parsefail(time, logfile, error):
    _con.prepare("""INSERT INTO parsefail VALUES ($1, $2, $3)
                 """)(time, logfile, error)


def inserts(games):
    """ Insert GameResult objects into the database. """

    # Aggregate data for each game into arrays. Don't actually insert into the
    # database yet
    rows = {'game': [], 'pres': [], 'gain': [], 'ret': []}
    for g in games:

        # Copy values from GameResult object.
        gd = {}
        game_keys = ['time', 'logfile', 'supply', 'colony', 'shelters',
                     'pcount', 'plist', 'bot', 'guest', 'rating', 'adventure']
        for k in game_keys:
            gd[k] = getattr(g, k, None)
        gd['supply'] = ', '.join(g.supply)
        gd['plist'] = ', '.join(list(g.presults.keys()))
        gd['pcount'] = len(g.presults)
        rows['game'].append([gd[k] for k in game_keys])

        # Copy values from PlayerResult object.
        for pname in g.presults:
            p = g.presults[pname]
            pd = {}
            pres_keys = ['pname', 'vps', 'turns', 'rank', 'quit', 'turnorder',
                         'resign', 'logfile', 'pcount', 'pname_lower']
            for k in pres_keys:
                pd[k] = getattr(p, k, None)
            pd['pcount'] = len(g.presults)
            pd['pname_lower'] = pname.lower()
            pd['logfile'] = g.logfile
            pd['turnorder'] = g.presults[pname].order
            rows['pres'].append([pd[k] for k in pres_keys])

    if len(games) == 0:
        return

    x = _con.xact()
    x.start()
    try:
        # Insert game data
        sql = """INSERT INTO game (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
              """ % tuple(game_keys)
        _con.prepare(sql).load_rows(rows['game'])

        # Insert player data
        sql = """INSERT INTO presult (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                      VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
              """ % tuple(pres_keys)
        _con.prepare(sql).load_rows(rows['pres'])

        x.commit()
    except Exception as e:
        print(e)
        x.rollback()


def get_ts_rating_history(limit):
    return _con.prepare("""SELECT *
                             FROM ts_rating_history
                            ORDER BY time
                            LIMIT $1""")(limit)


def get_game_count(pname, system='isotropish'):
    x = _con.prepare("""SELECT numgames
                          FROM ts_rating2
                         WHERE pname = $1
                           AND system=$2
                     """)(pname, system)
    n = x[0][0] if len(x) > 0 else 0
    return n


def insert_leaderboard(rating_tuples):
    ps = _con.prepare("""INSERT INTO rating VALUES ($1, $2, $3, $4)""")
    ps.load_rows(rating_tuples)


def get_avatar_info(playerid):
    ps = _con.prepare("""SELECT playerid, hasCustom from avatars
                                WHERE playerid=$1""")
    return ps.first(playerid)


def get_all_avatar_info():
    qrows = _con.query.rows("""SELECT playerid, hascustom from avatars""")
    l = {}
    for (playerid, hascustom) in qrows:
        l[playerid] = hascustom
    return l


def save_avatar_info(playerid, hasCustom):
    if get_avatar_info(playerid) is None:
        _con.prepare("""INSERT INTO avatars VALUES ($1,$2)
                     """)(playerid, hasCustom)
    else:
        _con.prepare("""UPDATE avatars SET hasCustom=($1) WHERE
                        playerid=($2)""")(hasCustom, playerid)


def fetch_blacklist(playerid):
    ps = _con.prepare("""SELECT blackname, noplay, nomatch, censor
                           FROM blacklist WHERE playerid=$1
                       ORDER BY blackname""")
    blist = {}
    for (name, noplay, nomatch, censor) in ps(playerid):
        blist[name] = {
            'noplay': noplay,
            'nomatch': nomatch,
            'censor': censor
        }
    return blist


def store_blacklist(playerid, newlist, merge):
    oldlist = fetch_blacklist(playerid)
    for bname in newlist:
        if bname in oldlist:
            ps = _con.prepare("""UPDATE blacklist
                                    SET noplay=$3, nomatch=$4, censor=$5
                                  WHERE playerid=$1 AND blackname=$2""")
        else:
            ps = _con.prepare("""INSERT INTO blacklist (playerid, blackname,
                                        noplay, nomatch, censor)
                                 VALUES ($1,$2,$3,$4,$5)""")
        o = newlist[bname]
        ps(playerid, bname, o['noplay'], o['nomatch'], o['censor'])

    # Delete old DB entries, unless merge is enabled
    if not merge:
        for bname in oldlist:
            if bname not in newlist:
                ps = _con.prepare("""DELETE FROM blacklist
                                      WHERE playerid=$1 and blackname=$2""")
                ps(playerid, bname)


def fetch_blacklist_common(percentage):
    def add_blacklistees(percentage, bltype, out):
        rs = _con.prepare("""SELECT blackname, count(*)
                               FROM blacklist
                              WHERE %s
                              GROUP by blackname
                              ORDER BY count DESC""" % (bltype))()
        i = 0
        for (pname, count) in rs:
            if ((i/len(rs) <= percentage/100 and count > 1)
                    or (count == 1 and percentage == 100)):
                if pname not in out:
                    out[pname] = {'noplay': False,
                                  'nomatch': False,
                                  'censor': False}
                out[pname][bltype] = True
            i += 1

    common = {}
    add_blacklistees(percentage, 'noplay', common)
    add_blacklistees(percentage, 'nomatch', common)
    add_blacklistees(percentage, 'censor', common)
    return common


def record_ts_rating(system, pname, rating, numgames,
                     last_gametime, last_logfile):
    level = rating.mu - 3 * rating.sigma
    guest = pname.lower().find('guest') == 0

    if _con.query.first('SELECT 1 FROM ts_rating2 '
                        ' WHERE pname=$1 AND system=$2', pname, system):
        _con.prepare("""UPDATE ts_rating2
                           SET time=$1, logfile=$2, mu=$4, sigma=$5,
                               numgames=$6, level_m3s=$7, guest=$8
                         WHERE pname=$3 AND system=$9
                     """)(last_gametime, last_logfile, pname, rating.mu,
                          rating.sigma, numgames, level, guest, system)
    else:
        _con.prepare("""INSERT INTO ts_rating2
                               (time, logfile, pname, mu, sigma, numgames,
                                level_m3s, guest, system)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                     """)(last_gametime, last_logfile, pname, rating.mu,
                          rating.sigma, numgames, level, guest, system)


def record_player_id(playerId, playerName):
    r = _con.prepare("""SELECT *
                          FROM playerinfo
                         WHERE playerId=$1""")(playerId)
    if len(r) == 0:
        _con.prepare("""INSERT INTO playerinfo (observed, playerId, playerName)
                             VALUES ($1, $2, $3)
                     """)(datetime.datetime.now(), playerId, playerName)
    else:
        # TODO: update playerId-playerName connection
        pass


def record_login(playerId, version):
    _con.prepare("""INSERT INTO extlogin (time, playerId, version)
                         VALUES ($1, $2, $3)
                 """)(datetime.datetime.now(), playerId, version)


def record_pro_rating(playerid, mu, sigma, displayed):
    qcheck = """SELECT 1 FROM goko_pro_rating
                 WHERE playerid=$1"""
    qupdate = """UPDATE goko_pro_rating
                    SET mu=$2, sigma=$3, displayed=$4
                  WHERE playerid=$1"""
    qinsert = """INSERT INTO goko_pro_rating (playerid, mu, sigma, displayed)
                 VALUES ($1, $2, $3, $4)"""
    if _con.query.first(qcheck, playerid):
        _con.prepare(qupdate)(playerid, mu, sigma, displayed)
    else:
        _con.prepare(qinsert)(playerid, mu, sigma, displayed)

def fetch_ts2_rating(player_name, system_dbname):
    r = _con.prepare(
        """SELECT mu, sigma
             FROM ts_rating2
            WHERE pname = $1
              AND system = $2
        """)(player_name, system_dbname)
    if len(r) == 0:
        return None
    else:
        (mu, sigma) = r[0]
        return trueskill.Rating(float(mu), float(sigma))


def fetch_pro_rating(player_id):
    return _con.prepare(
        """SELECT r.mu, r.sigma, r.displayed
             FROM goko_pro_rating r
             JOIN playerinfo i USING(playerid)
            WHERE i.playerid=$1
        """)(player_id)[0]


def fetch_all_pro_ratings():
    return _con.prepare(
        """SELECT r.playerid, i.playername, r.mu, r.sigma, r.displayed
             FROM goko_pro_rating r
             JOIN playerinfo i USING(playerid)
        """)()
