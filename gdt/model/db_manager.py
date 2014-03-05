import hashlib
import sys
import os
import re
import time
import socket
import datetime
import copy

import postgresql

from . import domgame
from . import constants


# Database connection object.
# TODO: Initialized on first use instead of on load
_con = postgresql.open(user='ai', host='localhost', database='goko')


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


def search_game_results(search):
    return fetch_game_results(search_log_filenames(search))


def delete_logs(logfiles):
    _con.prepare('DELETE FROM game WHERE logfile=$1').load_rows(logfiles)
    _con.prepare('DELETE FROM presult WHERE logfile=$1').load_rows(logfiles)
    #_con.prepare('DELETE FROM gain WHERE logfile=$1').load_rows(logfiles)
    #_con.prepare('DELETE FROM ret WHERE logfile=$1').load_rows(logfiles)


def search_daily_log_filenames(day):
    start = datetime.datetime.strptime(day.strftime('%Y%m%d'), '%Y%m%d')
    end = day + datetime.timedelta(days=1)
    sql = """SELECT logfile FROM game g WHERE g.time between $1 and $2"""
    return [r[0] for r in _con.prepare(sql)(start, end)]


def search_log_filenames(p):
    """ Fetch log filenames for matching games.
        - <p> is a dict of search parameters. Missing/None values ignored.
        Games are ordered from newest to oldest. If not None, <offset> skips
        results and <limit> restricts how many are returned."""

    # Don't modify the original <search> argument
    p = copy.deepcopy(p)

    # Cards in the supply list --> s1, s2, etc
    for i in range(0, 11):
        p['s%d' % i] = (p['supply'][i]
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
           AND ({p1score}::smallint    IS NULL OR {p1score} = (p2.rank - p1.rank))
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


def get_last_rated_game():
    return _con.query.first("""SELECT time, logfile FROM ts_rating
                                ORDER BY time desc LIMIT 1""")


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


def fetch_rated_game_counts():
    ps = _con.prepare("""SELECT pname, COUNT(pname) FROM ts_rating_history
                      GROUP BY pname""")
    return ps()


def fetch_all_ratings(mingames, lastactive, minlevel):
    mu_sig_num = {}
    # TODO: Fix the Boodaloo problem more elegantly
    ps = _con.prepare(
        """SELECT pname, mu, sigma, numgames
             FROM ts_rating
            WHERE pname != 'Boodaloo'
              AND pname != 'ottocar'
              AND ($1::smallint IS NULL OR numgames >= $1)
              AND ($2::timestamp IS NULL OR time >= $2)
              AND ($3::smallint IS NULL OR (mu - 3*sigma) >= $3)""")
    for (p, m, s, n) in ps(mingames, lastactive, minlevel):
        mu_sig_num[p] = {'mu': m, 'sigma': s, 'n': n}
    return mu_sig_num


def fetch_last_rated_log_time():
    return _con.query.first("""SELECT max(time) from ts_rating""")


def get_rating(pname):
    ps = _con.prepare("""SELECT mu, sigma, numgames
                            FROM ts_rating
                           WHERE pname=$1
                           ORDER BY time DESC""")
    msn = ps.first(pname)
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


def insert_parsefail(failedlog):
    print('TODO: Record that parsing failed for log: %s' + failedlog)


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
            pres_keys = ['pname', 'vps', 'turns', 'rank', 'quit',
                         'resign', 'logfile', 'pcount', 'pname_lower']
            for k in pres_keys:
                pd[k] = getattr(p, k, None)
            pd['pcount'] = len(g.presults)
            pd['pname_lower'] = pname.lower()
            pd['logfile'] = g.logfile
            rows['pres'].append([pd[k] for k in pres_keys])

        ## Copy values from GainRet object.
        #for gain in g.gains:
        #    gaind = {}
        #    gain_keys = ['logfile', 'cname', 'cpile', 'pname', 'turn']
        #    for k in gain_keys:
        #        gaind[k] = getattr(gain, k, None)
        #    gaind['logfile'] = g.logfile
        #    rows['gain'].append([gaind[k] for k in gain_keys])

        ## Copy values from GainRet object.
        #for ret in g.rets:
        #    retd = {}
        #    ret_keys = ['logfile', 'cname', 'cpile', 'pname', 'turn']
        #    for k in ret_keys:
        #        retd[k] = getattr(ret, k, None)
        #    retd['logfile'] = g.logfile
        #    rows['ret'].append([retd[k] for k in ret_keys])

    if len(games) == 0: 
        return

    # Insert game data
    sql = """INSERT INTO game (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                  VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
          """ % tuple(game_keys)
    _con.prepare(sql).load_rows(rows['game'])

    # Insert player data
    sql = """INSERT INTO presult (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                  VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
          """ % tuple(pres_keys)
    _con.prepare(sql).load_rows(rows['pres'])

    ## Insert card gained data
    #sql = """INSERT INTO gain (%s,%s,%s,%s,%s)
    #                VALUES ($1,$2,$3,$4,$5)
    #      """ % tuple(gain_keys)
    #_con.prepare(sql).load_rows(rows['gain'])

    ## Insert card returned data
    #sql = """INSERT INTO gain (%s,%s,%s,%s,%s)
    #                VALUES ($1,$2,$3,$4,$5)
    #      """ % tuple(gain_keys)
    #_con.prepare(sql).load_rows(rows['ret'])


def get_ts_rating_history(limit):
    return _con.prepare("""SELECT *
                             FROM ts_rating_history
                            ORDER BY time
                            LIMIT $1""")(limit)


def get_game_count(pname):
    x = _con.prepare("""SELECT numgames
                          FROM ts_rating
                         WHERE pname = $1""")(pname)
    n = x[0][0] if len(x) > 0 else 0
    return n


def insert_ratings(rating_history):
    h_rows = []
    r_rows = {}

    for r in rating_history:
        # Store last rating for each player
        r_rows[r['pname']] = (r['time'], r['logfile'], r['pname'],
                              r['new_rating'].mu, r['new_rating'].sigma,
                              r['numgames'])

        # Store rating history entry
        h_rows.append((r['time'], r['logfile'], r['pname'],
                       r['old_rating'].mu, r['old_rating'].sigma,
                       r['old_opp_rating'].mu, r['old_opp_rating'].sigma,
                       r['new_rating'].mu, r['new_rating'].sigma))

    # Insert or update rating
    ps = _con.prepare("""UPDATE ts_rating
                            SET time=$1, logfile=$2, mu=$4, sigma=$5, numgames=$6
                          WHERE pname=$3""").load_rows(r_rows.values())
    for pname in r_rows:
        ps = _con.prepare("SELECT 1 FROM ts_rating WHERE pname=$1")
        if not ps(pname):
            try:
                ps = _con.prepare("""INSERT INTO ts_rating
                                        (time, logfile, pname, mu, sigma, numgames)
                                 VALUES ($1,$2,$3,$4,$5,$6)""")(*r_rows[pname])
            except:
                raise

    # Insert rating histories
    ps = _con.prepare("""INSERT INTO ts_rating_history
                                (time, logfile, pname, old_mu, old_sigma,
                                 old_opp_mu, old_opp_sigma, new_mu, new_sigma)
                         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)""")
    ps.load_rows(h_rows)


def insert_leaderboard(rating_tuples):
    ps = _con.prepare("""INSERT INTO rating VALUES ($1, $2, $3, $4)""")
    ps.load_rows(rating_tuples)


def get_avatar_info(playerid):
    ps = _con.prepare("""SELECT playerid, hasCustom from avatars
                                WHERE playerid=$1""")
    return ps.first(playerid)

def save_avatar_info(playerid, hasCustom):
    ps = _con.prepare("""INSERT INTO avatars VALUES ($1,$2)""")(playerid,
                                                                hasCustom)
