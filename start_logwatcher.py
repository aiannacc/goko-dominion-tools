#!/usr/bin/python

import datetime
import os
import re
import logging
import gzip
import sys
import threading
import traceback
import time

import requests

from gdt.logparse import gokoparse
from gdt.model import db_manager
import gdt.ratings.gdt_trueskill as ts

logging.basicConfig(level=logging.WARNING)

LINK_REGEX = re.compile('href="(log\S*txt)"')
FILE_REGEX = re.compile("log\.(.*)\.(.*)\.txt")

# Download up to 20 logs simultaneously
semaphore = threading.BoundedSemaphore(value=20)

# Download a log and save it to file
def download_log(logfile, dayurl, log_dir):
    headers = {'Accept-Encoding': 'gzip, deflate'}
    url = dayurl + '/' + logfile
    with semaphore:
        logging.debug('Fetching %s' % url)
        r = requests.get(url, headers=headers)
    gzip.open(log_dir + '/' + logfile, 'wt').write(r.text)


def download_new_logs(date, threads):
    datestr = date.strftime('%Y%m%d')
    dayurl = 'http://dominionlogs.goko.com/%s' % datestr
    r = requests.get(dayurl)
    remote_logs = LINK_REGEX.findall(r.text)

    # Determine which logs haven't been downloaded
    log_dir = '/mnt/raid/media/dominion/logs/%s' % datestr
    if !os.path.isdir(log_dir):
        os.makedirs(log_dir)
    local_logs = os.listdir(log_dir)
    not_downloaded = set(remote_logs) - set(local_logs)
    logging.info('Found %d new logs on Goko' % len(not_downloaded))

    # Download logs in threads
    i = 0
    for lf in not_downloaded:
        i += 1
        t = threading.Thread(target=download_log, 
                             kwargs={'logfile': lf, 'dayurl': dayurl,
                                     'log_dir': log_dir})
        threads.append(t)
        t.start()
        logging.debug('Started thread #%d' % i)

    # Wait for downloading to finish
    for t in threads:
        t.join()

    logging.info('Finished downloading')

    # Determine which logs haven't been parsed into the database
    # Include logs that were previously downloaded but not parsed
    dblogs = db_manager.search_daily_log_filenames(date)
    not_parsed = set(remote_logs) - set(dblogs)
    logging.info('Found %d new logs to parse' % len(not_parsed))

    # Parse the unparsed logs (not threaded)
    games = []
    failed = {}
    for logfile in not_parsed:
        (loghash, logtime) = FILE_REGEX.match(logfile).group(1, 2)
        logtime = datetime.datetime.fromtimestamp(int(logtime) / 1000)

        logfile_full = log_dir + '/' + logfile
        logtext = gzip.open(logfile_full, 'rt', encoding='utf-8').read()
        try:
            game = gokoparse.parse_goko_log(logtext)
            game.logfile = logfile
            game.time = logtime
            games.append(game)
        except:
            failed[logfile] = sys.exc_info()

    logging.info('Finished parsing')
    logging.info('%d games parsed' % len(games))
    logging.info('%d games failed' % len(failed))

    # Insert parsed games into database
    try:
        db_manager.inserts(games)
        # Update ratings
        count = -1
        while count != 0:
          x = db_manager.get_last_rated_game()
          if x:
            (t, l) = x
          else:
            (t, l) = (None, None)
          count = ts.record_ratings(100, t, l, ts.isodominion_env)
    except:
        print(sys.exc_info())

    logging.info('inserted games into DB')

    # TODO: handle failed logs
    for f in failed:
        logging.warn('Failed to parse: %s in %s' % (failed[f][0].__name__, f))
        for line in traceback.format_tb(failed[f][2]):
            logging.warn(line)

    print('Finished log cycle')

if __name__ == '__main__':
    while True:
        try:
            threads = []
            today = datetime.datetime.now()
            download_new_logs(today, threads)
            time.sleep(1)
        except:
            logging.error(sys.exc_info()[1])
            logging.error(sys.exc_info()[2])
            pass
