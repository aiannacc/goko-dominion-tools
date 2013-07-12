# Base modules
import hashlib
import sys
import os
import re
import time
import socket
import datetime

# Third party modules
import postgresql

# Project modules
from dominiongame import GameResult
from dominiongame import PlayerResult

# Connect to the "dominionlogs" database
if socket.gethostname() == 'iron' and sys.argv[-1] != 'test':
    db = postgresql.open(user='ai', host='localhost', database='goko')
else: 
    db = postgresql.open(user='forum', host='gokologs.drunkensailor.org',
                         database='goko', password='fds')


def insert_card_url(card, url):
    ps_insert_card = db.prepare("""INSERT INTO card_url VALUES ($1, $2)""")
    ps_insert_card(card, url)


def fetch_card_image_url(card):
    ps_fetch_card = db.prepare("""SELECT url FROM card_url WHERE card=$1""")
    x = ps_fetch_card(card)
    return(x[0][0])


def fetch_winners_losers(startdate):
    qry = """SELECT p1.pname, p1.rank, p2.pname, p2.rank
               FROM game g
               JOIN presult p1 USING(logfile)
               JOIN presult p2 USING(logfile)
              WHERE g.pcount=2 AND g.bot=0 AND g.guest=0
                    AND p1.pname != p2.pname AND adventure=0
                    AND (rating IS NULL OR rating="pro")
                    AND time > "%s"
              ORDER BY g.time""" % startdate.strftime('%Y-%m-%d')
    db.execute(qry)
    return db.fetchall()

ps_countlogs = db.prepare("""SELECT count(logfile) FROM game
                              WHERE time BETWEEN $1 AND $2""")


def count_logs(date):
    start = date.strftime("%Y-%m-%d 00:00:00")
    end = date.strftime("%Y-%m-%d 23:59:59")
    return ps_countlogs(start, end)[0]

# Get a list of all recorded logs from a given day
ps_list = db.prepare('SELECT logfile FROM game WHERE time BETWEEN $1 AND $2')


def list_logs(date):
    out = []
    for r in ps_list.rows(date, date + datetime.timedelta(days=1)):
        out.append(r[0])
    return out


def is_bot(pname):
    for bot in get_bot_names():
        if pname and pname.startswith(bot):
            return True
    return False


def get_bot_names():
    ps = db.prepare('SELECT pname from bot')
    return [r[0] for r in ps()]


def get_advbot_names():
    ps = db.prepare('SELECT pname from advbot')
    return [r[0] for r in ps()]


def get_gainable_cards(lowercase):
    ps = db.prepare("SELECT card FROM card_url")
    return [r[0].lower() for r in ps()]

ps_search = db.prepare("""
                SELECT time, logfile, supply, colony, shelters
                  FROM game g
                  JOIN presult pa USING(logfile)
                  JOIN presult pb USING(logfile)
                 WHERE 1=1
                   AND ($1::varchar IS NULL
                       OR (($23 AND pb.pname = $1)
                       OR (NOT $23 AND pb.pname_lower = lower($1))))
                   AND ($2::varchar IS NULL
                       OR (($23 AND pb.pname = $2)
                       OR (NOT $23 AND pb.pname_lower = lower($2))))
                   AND pb.pname != pa.pname
                   AND ($3::smallint is NULL OR pa.rank=$3)
                   AND ($4::boolean is NULL OR g.bot=$4)
                   AND ($5::boolean is NULL OR g.guest=$5)
                   AND ($6::varchar is NULL OR g.rating=$6
                        OR ($6='pro+' AND g.rating IN ('pro', 'unknown')))
                   AND ($7::smallint is NULL OR g.pcount=$7)
                   AND ($8::boolean is NULL OR g.colony=$8)
                   AND ($9::boolean is NULL OR g.shelters=$9)
                   AND ($10::boolean is NULL
                       OR ($10 = (pa.quit OR pb.quit)))
                   AND ($11::smallint is NULL
                       OR ($11 <= GREATEST(pa.turns, pb.turns)))
                   AND ($12::smallint is NULL
                       OR ($12 >= GREATEST(pa.turns, pb.turns)))
                   AND ($13::varchar IS NULL OR supply ~* $13)
                   AND ($14::varchar IS NULL OR supply ~* $14)
                   AND ($15::varchar IS NULL OR supply ~* $15)
                   AND ($16::varchar IS NULL OR supply ~* $16)
                   AND ($17::varchar IS NULL OR supply ~* $17)
                   AND ($18::varchar IS NULL OR supply ~* $18)
                   AND ($19::varchar IS NULL OR supply ~* $19)
                   AND ($20::varchar IS NULL OR supply ~* $20)
                   AND ($21::varchar IS NULL OR supply ~* $21)
                   AND ($22::varchar IS NULL OR supply ~* $22)
                   AND g.time BETWEEN $24 AND $25
                 ORDER BY time desc""")


def search(pname1, pname2, casesensitive, p1rank, minturns, maxturns, kingdom,
           bot, guest, rating, pcount, colony, shelters, quit, supply,
           startdate, enddate):
    print('Search', (pname1, pname2, p1rank, minturns, maxturns, kingdom, bot,
                     guest, rating, pcount, colony, shelters, quit, supply,
                     startdate, enddate))
    start1 = time.time()
    if pname2 and not pname1:
        pname1 = pname2
        pname2 = None

    s = []
    for i in range(10):
        if supply and i < len(supply):
            s.append('.*' + supply[i] + '.*')
        else:
            s.append(None)

    tlscs_list = ps_search(pname1, pname2, p1rank, bot, guest, rating, pcount,
                           colony, shelters, quit, minturns, maxturns,
                           s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7],
                           s[8], s[9], casesensitive, startdate,
                           enddate + datetime.timedelta(days=1))
    start2 = time.time()
    out = build_games(tlscs_list)
    end = time.time()
    print("Elapsed1: %f" % (start2-start1))
    print("Elapsed2: %f" % (end-start2))

    return out

ps_pfetch = db.prepare("""SELECT logfile, pname, vps, turns, rank,
                                 quit, turnorder, resign
                            FROM presult JOIN game USING(logfile)
                           WHERE logfile = ANY($1)""")


def build_games(tlscs_list):
    presults_hash = {}
    logfiles = [tlscs[1] for tlscs in tlscs_list]
    for pr in ps_pfetch(logfiles):
        (logfile, pname, vps, turns, rank, quit, turnorder, resign) = pr
        p = PlayerResult(pname)
        p.vps = vps
        p.turns = turns
        p.rank = rank
        p.quit = quit
        p.order = turnorder
        p.resign = resign
        if not logfile in presults_hash:
            presults_hash[logfile] = {}
        presults_hash[logfile][pname] = p
    games = []
    for (t, logfile, supply, colony, shelters) in tlscs_list:
        presults = presults_hash[logfile]
        g = GameResult(supply.split(', '), None, None, None, None, None, None,
                       None, len(presults), presults, None)
        g.time = t
        g.colony = colony
        g.shelters = shelters
        g.logfile = logfile
        games.append(g)
    return(games)

# Write a dominion GameResult object to the database
# Note: all tables use the log's goko filename as primary/foreign key
ps_game_insert = db.prepare("""INSERT INTO game VALUES($1, $2, $3, $4, $5, $6,
                            $7, $8, $9, $10, $11, $12)""")
ps_presult_insert = db.prepare("""INSERT INTO presult VALUES($1, $2, $3, $4,
                               $5, $6, $7, $8, $9, $10)""")
ps_gain_insert = db.prepare("INSERT INTO gain VALUES($1, $2, $3, $4, $5)")
ps_ret_insert = db.prepare("INSERT INTO ret VALUES($1, $2, $3, $4, $5)")


def inserts(games):
    (game_arr, presult_arr, gain_arr, ret_arr) = ([], [], [], [])
    for g in games:

        # Write supply/plist in db-friendly comma-separated format
        supply = ', '.join(g.supply)
        plist = ', '.join(list(g.presults.keys()))

        # Prepare game summary info
        game_arr.append((g.time, g.logfile, supply, g.colony, g.shelters,
                         len(g.presults), plist, g.bot, g.guest, g.rating,
                         g.adventure, None))

        # Prepare player result info
        for pname in g.presults:
            p = g.presults[pname]
            presult_arr.append((pname, p.vps, p.turns, p.rank, p.quit,
                                p.order, p.resign, g.logfile, len(g.presults),
                                pname.lower()))

        # Prepare gains/returns
        for gain in g.gains:
            gain_arr.append((g.logfile, gain.cname, gain.cpile,
                             gain.pname, gain.turn))
        for ret in g.rets:
            ret_arr.append((g.logfile, ret.cname, ret.cpile, ret.pname,
                            ret.turn))

    # Write everything
    ps_game_insert.load_rows(game_arr)
    ps_presult_insert.load_rows(presult_arr)
    ps_gain_insert.load_rows(gain_arr)
    ps_ret_insert.load_rows(ret_arr)

ps_leaderboard_insert = db.prepare("""INSERT INTO rating
                                      VALUES ($1, $2, $3, $4)""")


def insert_leaderboard(rating_tuples):
    time_arr = [trpr[0] for trpr in rating_tuples]
    rank_arr = [trpr[1] for trpr in rating_tuples]
    pname_arr = [trpr[2] for trpr in rating_tuples]
    rating_arr = [trpr[3] for trpr in rating_tuples]
    ps_leaderboard_insert.load_rows(rating_tuples)
