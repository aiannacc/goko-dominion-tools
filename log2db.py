#!/usr/bin/env python

# Base modules
import postgresql.exceptions
import sys
import re
import os
import traceback
import gzip
import time
import datetime

# Project modules
import gdt
from gdt.model import db_manager
from gdt.logparse import gokoparse

RE_LOGNAME = re.compile(".*(log\.(.*)\.(.*)\.txt)")

# TODO: Kill this class entirely, along with update_logdb.sh

# For command-line
# Usage: ./log2db.py <logdir>
if __name__ == "__main__":
    logdir = sys.argv[1]
    print(logdir)
    m = re.match('.*/?(201.....)/?$', logdir)
    day_str = m.group(1)
    print(day_str)
    date = datetime.datetime.strptime(day_str, '%Y%m%d')

    # Figure out which logs are already in the database for this day
    dblogs = set(db_manager.search_daily_log_filenames(date))

    filelogs = set(os.listdir(logdir))
    newlogs = filelogs - dblogs
    print("%d old logs and %d new logs" % (len(dblogs), len(newlogs)))

    start_time = time.time()
    n = 0
    games = []
    print(len(newlogs))
    for logfile in newlogs:
        games = []
        logfile_full = sys.argv[1] + '/' + logfile
        try:
            m = RE_LOGNAME.match(logfile)
            logfile = m.group(1)
            loghash = m.group(2)
            logtime = datetime.datetime.fromtimestamp(int(m.group(3))/1000)

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
            if len(games) % 100 == 0:
                db_manager.inserts(games)
                games = []
        except gokoparse.WrongPlacesException:
            print("WrongPlacesException in %s.  Fuck you, Goko." % logfile)
            games = []
        except gokoparse.TurnCountException:
            print("TurnCountException in %s.  Fuck you, Goko." % logfile)
            games = []
        except postgresql.exceptions.UniqueError:
            print("UniqueError in %s" % logfile)
            games = []
        except:
            print('Exception handling %s/%s' % (logdir, logfile))
            games = []
            raise
    for g in games:
        g_arr = [g]
        games = []
        try:
            db_manager.inserts(g_arr)
        except postgresql.exceptions.UniqueError:
            print("(post) UniqueError in %s" % logfile)
        except:
            print('(post) Exception handling %s/%s' % (logdir, logfile))
            raise
