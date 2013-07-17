#!/usr/bin/env python

# Base modules
from datetime import datetime
import postgresql.exceptions
import sys
import re
import os
import traceback
import gzip
import time

# Project modules
sys.path.append('../db')
from ..model.dominiongame import GameResult
from ..model import db_manager
import .gokoparse

RE_LOGNAME = re.compile(".*(log\.(.*)\.(.*)\.txt)")

# For command-line
# Usage: ./log2db.py <logdir>
# Note: about .06s/log: .03s for db, .015 for parsing, .015 for file access
if __name__ == "__main__":
    logdir = sys.argv[1]
    print(logdir)
    m = re.match('.*/?(201.....)/?$', logdir)
    day_str = m.group(1)
    print(day_str)
    date = datetime.strptime(day_str, '%Y%m%d')

    dblogs = set(dbmgr.list_logs(date))
    filelogs = set(os.listdir(logdir))
    newlogs = filelogs - dblogs
    print("%d old logs and %d new logs" % (len(dblogs), len(newlogs)))

    start_time = time.time()
    n = 0
    games = []
    for logfile in newlogs:
        logfile_full = sys.argv[1] + '/' + logfile
        try:
            m = RE_LOGNAME.match(logfile)
            logfile = m.group(1)
            loghash = m.group(2)
            logtime = datetime.fromtimestamp(int(m.group(3))/1000)

            try:
                logtext = open(logfile_full, encoding='utf-8').read()
            except UnicodeDecodeError:
                logtext = gzip.open(logfile_full, 'rt',
                                    encoding='utf-8').read()

            print('Now handling %s' % (logfile))
            game = gokoparse.parse_goko_log(logtext)
            game.logfile = logfile
            game.time = logtime

            games.append(game)
            if len(games) % 10 == 0:
                dbmgr.inserts(games)
                games = []
                elapsed_time = time.time() - start_time
                n += 10
                print(n, elapsed_time, elapsed_time/n)
        except gokoparse.WrongPlacesException:
            print("WrongPlacesException in %s.  Fuck you, Goko." % logfile)
        except gokoparse.TurnCountException:
            print("TurnCountException in %s.  Fuck you, Goko." % logfile)
        except postgresql.exceptions.UniqueError:
            print("UniqueError in %s" % logfile)
        except:
            print('Exception handling %s/%s' % (logdir, logfile))
            raise
    for g in games:
        g_arr = [g]
        try:
            dbmgr.inserts(g_arr)
        except postgresql.exceptions.UniqueError:
            print("UniqueError in %s" % logfile)
        except:
            print('Exception handling %s/%s' % (logdir, logfile))
            raise
