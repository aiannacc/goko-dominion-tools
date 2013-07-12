#!/usr/bin/env python

import hashlib, sys, os, re, time
import datetime
from dominiongame import GameResult,PlayerResult

# Connect to the "dominionlogs" database
import postgresql
db = postgresql.open(user='ai',host='localhost',database='goko')

ps_insert_card = db.prepare("""INSERT INTO card_url VALUES ($1,$2)""")
def insert_card_url(card,url):
    ps_insert_card(card,url)

ps_fetch_card = db.prepare("""SELECT url FROM card_url WHERE card=$1""")
def fetch_card_image_url(card):
    x = ps_fetch_card(card)
    return(x[0][0])

def fetch_winners_losers(startdate):
    qry = 'SELECT p1.pname,p1.rank,p2.pname,p2.rank from game g join presult p1 using(logfile) join presult p2 using(logfile) where g.pcount=2 and g.bot=0 and g.guest=0 and p1.pname != p2.pname and adventure=0 and (rating is null or rating="pro") and time > "%s" order by g.time' % startdate.strftime('%Y-%m-%d')
    db.execute(qry)
    return db.fetchall()

def count_logs(date):
    start = date.strftime("%Y-%m-%d 00:00:00")
    end   = date.strftime("%Y-%m-%d 23:59:59")
    qry = 'SELECT count(logfile) FROM game WHERE time BETWEEN "%s" AND "%s"' % (start,end)
    db.execute(qry)
    return db.fetchone()[0]

# Get a list of all recorded logs from a given day
ps_list = db.prepare('SELECT logfile FROM game WHERE time BETWEEN $1 AND $2')
def list_logs(date):
    out = []
    for r in ps_list.rows(date,date + datetime.timedelta(days=1)):
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

ps_search = db.prepare("""SELECT time,logfile,supply
                            FROM game g
                            JOIN presult pa USING(logfile)
                            JOIN presult pb USING(logfile)
                           WHERE g.pcount=2
                             AND pa.pname = $1
                             AND pb.pname != pa.pname
                             AND ($2::varchar is NULL or pb.pname=$2)
                             AND ($3::smallint is NULL or pa.rank=$3)
                             AND ($4::boolean is NULL or g.bot=$4)
                             AND ($5::boolean is NULL or g.guest=$5)
                             AND ($6::varchar is NULL or g.rating=$6)
                             AND ($7::smallint is NULL or g.pcount=$7)
                             AND ($8::boolean is NULL or g.colony=$8)
                             AND ($9::boolean is NULL or g.shelters=$9)
                         AND ($10::boolean is NULL or ($10 = (pa.quit or pb.quit)))
                         AND ($11::smallint is NULL or ($11 <= GREATEST(pa.turns,pb.turns)))
                         AND ($12::smallint is NULL or ($12 >= GREATEST(pa.turns,pb.turns)))
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
                       ORDER BY time desc
                             """)

def search(pname1,pname2,p1rank,minturns,maxturns,kingdom,bot,guest,rating,pcount,colony,shelters,quit,supply):
    print('Search',(pname1,pname2,p1rank,minturns,maxturns,kingdom,bot,guest,rating,pcount,colony,shelters,quit,supply))
    if pname2 and not pname1:
        pname1 = pname2
        pname2 = None

    s = []
    for i in range(10):
        if supply and i<len(supply):
            s.append('.*' + supply[i] + '.*')
        else:
            s.append(None)
    
    tls_list = ps_search(pname1,pname2,p1rank,bot,guest,rating,pcount,colony,shelters,quit,minturns,maxturns,s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9])
    return build_games2(tls_list)

ps_search1 = db.prepare("""SELECT logfile
                            FROM presult
                           WHERE pcount=2
                             AND pname = $1
                             AND ($2::smallint is NULL or rank=$2)
                             AND ($3::smallint is NULL or pcount=$3)""")

ps_search2 = db.prepare("""SELECT time,logfile,supply
                            FROM game g
                           WHERE logfile = ANY($1)
                             AND ($2::boolean is NULL or g.bot=$2)
                             AND ($3::boolean is NULL or g.guest=$3)
                             AND ($4::varchar is NULL or g.rating=$4)
                             AND ($5::smallint is NULL or g.pcount=$5)
                             AND ($6::boolean is NULL or g.colony=$6)
                             AND ($7::boolean is NULL or g.shelters=$7)
                             AND ($8::varchar IS NULL OR g.supply ~* $8)
                             AND ($9::varchar IS NULL OR g.supply ~* $9)
                             AND ($10::varchar IS NULL OR g.supply ~* $10)
                             AND ($11::varchar IS NULL OR g.supply ~* $11)
                             AND ($12::varchar IS NULL OR g.supply ~* $12)
                             AND ($13::varchar IS NULL OR g.supply ~* $13)
                             AND ($14::varchar IS NULL OR g.supply ~* $14)
                             AND ($15::varchar IS NULL OR g.supply ~* $15)
                             AND ($16::varchar IS NULL OR g.supply ~* $16)
                             AND ($17::varchar IS NULL OR g.supply ~* $17)
                           ORDER BY time desc""")

ps_search3 = db.prepare("""SELECT time,logfile,supply
                            FROM game g
                            JOIN presult pa USING(logfile)
                            JOIN presult pb USING(logfile)
                           WHERE g.pcount=2
                             AND pa.pname = $1
                             AND pb.pname != pa.pname
                             AND ($2::varchar is NULL or pb.pname=$2)
                             AND ($3::smallint is NULL or pa.rank=$3)
                             AND ($4::boolean is NULL or g.bot=$4)
                             AND ($5::boolean is NULL or g.guest=$5)
                             AND ($6::varchar is NULL or g.rating=$6)
                             AND ($7::smallint is NULL or g.pcount=$7)
                             AND ($8::boolean is NULL or g.colony=$8)
                             AND ($9::boolean is NULL or g.shelters=$9)
                             AND ($10::boolean is NULL or ($10 = (pa.quit or pb.quit)))
                             AND ($11::smallint is NULL or ($11 <= GREATEST(pa.turns,pb.turns)))
                             AND ($12::smallint is NULL or ($12 >= GREATEST(pa.turns,pb.turns)))
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
                             AND logfile = ANY($23)
                           ORDER BY time desc""")

def search2(pname1,pname2,p1rank,minturns,maxturns,kingdom,bot,guest,rating,pcount,colony,shelters,quit,supply):
    assert pname1

    logfiles = [r[0] for r in ps_search1(pname1,p1rank,pcount)]
    if (pname2):
        logfiles2 = [r[0] for r in ps_search1(pname2,None,pcount)]
        logfiles  = list(set(logfiles) & set(logfiles2))

    s = []
    for i in range(10):
        if supply and i<len(supply):
            s.append('.*' + supply[i] + '.*')
        else:
            s.append(None)

    tls_list = ps_search3(pname1,pname2,p1rank,bot,guest,rating,pcount,colony,shelters,quit,minturns,maxturns,\
                          s[0],s[1],s[2],s[3],s[4],s[5],s[6],s[7],s[8],s[9],logfiles)
    return build_games2(tls_list)

def build_games(tls_list):
    start = time.time()
    games = []
    for tls in tls_list:
        games.append(build_game(tls))
    print('Build elapsed: %f' %  (time.time()-start))
    return(games)

ps_pfetch = db.prepare("""SELECT pname,vps,turns,rank,quit,turnorder,resign 
                            FROM presult WHERE logfile=$1""")
def build_game(tls):
    (time,logfile,supply) = tls
    presults = {}
    for pr in ps_pfetch(logfile):
        (pname,vps,turns,rank,quit,turnorder,resign) = pr
        p = PlayerResult(pname)
        p.vps = vps
        p.turns = turns
        p.rank = rank
        p.quit = quit
        p.order = turnorder
        p.resign = resign
        presults[pname] = p
    g = GameResult(supply.split(','),None,None,None,None,None,None,None,\
                   len(presults),presults,None)
    g.time = time
    g.logfile = logfile
    return(g)

ps_pfetch2 = db.prepare("""SELECT logfile,pname,vps,turns,rank,quit,turnorder,resign 
                            FROM presult JOIN game USING(logfile) WHERE logfile = ANY($1)""")
def build_games2(tls_list):
    start = time.time()
    logfiles = [tls[1] for tls in tls_list]
    print(len(logfiles))

    games = {}
    for (t,logfile,supply) in tls_list:
        g = GameResult(supply.split(','),None,None,None,None,None,None,None,\
                   None,{},None)
        g.time = t
        g.logfile = logfile
        games[logfile] = g

    for pr in ps_pfetch2(logfiles):
        (logfile,pname,vps,turns,rank,quit,turnorder,resign) = pr
        p = PlayerResult(pname)
        p.vps = vps
        p.turns = turns
        p.rank = rank
        p.quit = quit
        p.order = turnorder
        p.resign = resign
        games[logfile].presults[pname] = p

    gamesout = []
    for logfile in games:
        g = games[logfile]
        g.pCount = len(games[logfile].presults)
        gamesout.append(g)

    print('Build elapsed: %f' %  (time.time()-start))
    return(gamesout)

def build_games_many_queries(tlsp):
    games = []
    # Get PlayerResult info by logfile
    for (time,logfile,bot,guest,rating,pcount,colony,shelters,endcode,supply) in tlsp:
        g = GameResult(supply.split(','),None,rating,shelters,guest,bot,pcount,colony,{},None)
        g.time = time
        g.logfile = logfile

        qry = 'SELECT pname,vps,turns,rank,quit,turnorder,resign,logfile \
                 FROM presult \
                WHERE logfile="%s" \
                ORDER BY rank' % logfile
        db.execute(qry)
        for r in db.fetchall():
            (pname,vps,turns,rank,quit,turnorder,resign,logfile) = r
            p = PlayerResult(pname)
            p.vps = vps
            p.turns = turns
            p.rank = rank
            p.quit = quit
            p.order = turnorder
            p.resign = resign
            g.presults[pname] = p
        games.append(g)
    return(games)

# Write a dominion GameResult object to the database
# Note: all tables use the log's goko filename as primary/foreign key
ps_game_insert = db.prepare(
    "INSERT INTO game VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)")
ps_presult_insert = db.prepare(
    "INSERT INTO presult VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9)")
ps_gain_insert = db.prepare("INSERT INTO gain VALUES($1,$2,$3,$4,$5)")
ps_ret_insert = db.prepare("INSERT INTO ret VALUES($1,$2,$3,$4,$5)")
def inserts(games):
    (game_arr, presult_arr, gain_arr, ret_arr) = ([],[],[],[])
    for g in games:
        # TODO: Include supply, plist, adventures
        supply  = ','.join(g.supply)
        plist   = ','.join(list(g.presults.keys()))
        
        game_arr.append((g.time,g.logfile,supply,g.colony,g.shelters,
                   len(g.presults),plist,g.bot,g.guest,g.rating,
                   g.adventure,None))

        for pname in g.presults:
            p = g.presults[pname]
            presult_arr.append((pname,p.vps,p.turns,p.rank,p.quit,
                          p.order,p.resign,g.logfile,len(g.presults)))
    
        # Write gains/returns
        for gain in g.gains:
            gain_arr.append((g.logfile,gain.cname,gain.cpile,gain.pname,gain.turn))

        for ret in g.rets:
            ret_arr.append((g.logfile,ret.cname,ret.cpile,ret.pname,ret.turn))
    
    ps_game_insert.load_rows(game_arr)
    ps_presult_insert.load_rows(presult_arr) 
    ps_gain_insert.load_rows(gain_arr)
    ps_ret_insert.load_rows(ret_arr)

def insert(g):
    # TODO: Include supply, plist, adventures
    supply  = ','.join(g.supply)
    plist   = ','.join(list(g.presults.keys()))
    ps_game_insert(g.time,g.logfile,supply,g.colony,g.shelters,
                   len(g.presults),plist,g.bot,g.guest,g.rating,
                   g.adventure,None)

    # Write player results
    for pname in g.presults:
        p = g.presults[pname]
        ps_presult_insert(pname,p.vps,p.turns,p.rank,p.quit,
                          p.order,p.resign,g.logfile,len(g.presults))
    
    # Write gains/returns
    gains_arr = []
    for gain in g.gains:
        gains_arr.append((gain.cname,gain.cpile,gain.pname,gain.turn))
    ps_gain_insert.load_rows(gains_arr)

    rets_arr = []
    for ret in g.rets:
        rets_arr.append((ret.cname,ret.cpile,ret.pname,ret.turn))
    ps_ret_insert.load_rows(rets_arr)

RE_LOGNAME = re.compile(".*(log\.(.*)\.(.*)\.txt)")

# For testing from command line
if __name__ == "__main__":
    import gokoparse,sys
    logfile_full = sys.argv[1]
    m = RE_LOGNAME.match(logfile_full)
    logfile = m.group(1)
    loghash = m.group(2)
    logtime = datetime.datetime.fromtimestamp(int(m.group(3))/1000)

    print('Reading')
    logtext = open(logfile_full).read()

    print('Parsing')
    game = gokoparse.parse_goko_log(logtext)
    game.logfile = logfile
    game.time = logtime

    print('Inserting')
    insert(game)

