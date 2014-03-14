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

logging.basicConfig(level=logging.INFO)

LINK_REGEX = re.compile('href="(log\S*txt)"')
FILE_REGEX = re.compile("log\.(.*)\.(.*)\.txt")

# Download up to 200 logs simultaneously
sema = threading.BoundedSemaphore(value=200)

# Download a log and save it to file
def download_log(logfile, dayurl, log_dir):
    headers = {'Accept-Encoding': 'gzip, deflate'}
    url = dayurl + '/' + logfile
    logging.debug('Fetching %s' % url)
    r = requests.get(url, headers=headers)
    sema.release()
    gzip.open(log_dir + '/' + logfile, 'wt').write(r.text)


def download_new_logs(date):

    datestr = date.strftime('%Y%m%d')
    #dayurl = 'http://dominionlogs.goko.com/%s' % datestr
    dayurl = 'http://logs.prod.dominion.makingfun.com/%s' % datestr
    r = requests.get(dayurl)
    remote_logs = LINK_REGEX.findall(r.text)

    # Determine which logs haven't already been downloaded
    log_dir = '/mnt/raid/media/dominion/logs/%s' % datestr
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    local_logs = os.listdir(log_dir)
    not_downloaded = set(remote_logs) - set(local_logs)
    logging.info('Found %d new logs on Goko' % len(not_downloaded))

    # Download logs in threads.  Restrict max number of connections using
    # BoundedSemahore
    i = 0
    threads = []
    for lf in not_downloaded:
        i += 1
        sema.acquire()
        t = threading.Thread(target=download_log, 
                             kwargs={'logfile': lf, 'dayurl': dayurl,
                                     'log_dir': log_dir})
        threads.append(t)
        t.start()

    # Wait for downloading to finish
    for t in threads:
        t.join()

    logging.info('Finished downloading')

def parse_new_logs(date):

    # Determine which logs we have downloaded but not yet parsed
    log_dir = '/mnt/raid/media/dominion/logs/%s' % date.strftime('%Y%m%d')
    local_logs = os.listdir(log_dir)
    dblogs = db_manager.search_daily_log_filenames(date)
    not_parsed = set(local_logs) - set(dblogs)
    logging.info('Found %d downloaded logs to be parsed' % len(not_parsed))

    # Parse the unparsed logs
    games = []
    failed = {}
    for logfile in not_parsed:
        (loghash, logtime) = FILE_REGEX.match(logfile).group(1, 2)
        logtime = datetime.datetime.fromtimestamp(int(logtime) / 1000)

        fail = False
        logfile_full = log_dir + '/' + logfile
        try:
            logtext = gzip.open(logfile_full, 'rt', encoding='utf-8').read()
        except:
            try:
                logtext = open(logfile_full, 'rt', encoding='utf-8').read()
            except:
                logging.warn('Cannot read file: ' + logfile_full)
                failed[logfile] = sys.exc_info()
                fail = True
        if not fail:
            try:
                game = gokoparse.parse_goko_log(logtext)
                game.logfile = logfile
                game.time = logtime
                games.append(game)
                if len(games) % 100 == 0:
                    logging.info('Parsed %d' % len(games))
            except:
                failed[logfile] = sys.exc_info()

    logging.info('Finished parsing')
    logging.info('%d games parsed' % len(games))
    logging.info('%d games failed' % len(failed))

    # Insert parsed games into database, 100 at a time
    # TODO: Logs are read in file order, not chronological order.  This
    # is a (minor) violation of the TrueSkill algorithm: a game played at
    # 11:59 PM might be processed before one played at 12:00 AM on the
    # same day (almost 24 hours earlier).
    count = 0
    total_inserted = 0
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
          total_inserted += count
    except:
        logging.info(sys.exc_info())

    logging.info('inserted %d parsed games into DB' % total_inserted)

    # Notify of failed logs.  Record in database.
    for f in failed:
        logging.warn('Failed to parse: %s in %s' % (failed[f][0].__name__, f))
        for line in traceback.format_tb(failed[f][2]):
            logging.warn(line)
        #TODO: record failures
        db_manager.insert_parsefail(f)

    return total_inserted

if __name__ == '__main__':
    if len(sys.argv) == 3:
        start_dir = sys.argv[1]
        if sys.argv[2] == 'd':
            logging.info('Downloading and parsing logs starting on %s' + sys.argv[1])
            date = datetime.datetime.strptime(sys.argv[1], '%Y%m%d')
            while date < datetime.datetime.now():
                logging.info('Downloading and parsing logs for %s' + date.strftime('%-%m-%d'))
                download_new_logs(date)
                parse_new_logs(date)
        else:
            logging.error('Check usage.')
    elif len(sys.argv) == 2:
        start_dir = sys.argv[1]
        logging.info('Parsing ALL previous downloaded logs after %s.  This may take a while.' + sys.argv[1])
        for log_dir in sorted(os.listdir('/mnt/raid/media/dominion/logs')):
            if log_dir > start_dir:
                if re.match('\d{8}', log_dir):
                    log_day = datetime.datetime.strptime(log_dir, '%Y%m%d')
                    logging.info('Parsing logs from %s' % log_day.strftime('%Y-%m-%d'))
                    parse_new_logs(log_day)
    else:
        logging.warn('Now watching for new logs to be posted to the Goko log server.')
        logging.warn('Note: Games played before 12:00 AM today will not be handled.\n')

        next_day = datetime.datetime.now()
        while True:
            # This ensures that we don't miss the very last logs posted before
            # the date ticks over at midnight.  We're guaranteed to search for
            # "yesterday's" logs at least once "today."
            # NOTE we can still lose logs if the local system's time gets ahead
            # of Goko's server time.  Might be better to have a 10 minute
            # window (12:00-12:10AM) in which we search for both yesterday's
            # and today's logs.
            next_day = datetime.datetime.now()
            parsecount = 0
            try:
                download_new_logs(next_day)
                parsecount = parse_new_logs(next_day)
            except:
                # TODO: Do something about these errors
                logging.error(sys.exc_info()[1])
                logging.error(sys.exc_info()[2])
                pass
            print('Found %d new logs. Checking again in 5 seconds.' % parsecount)
            print()
            time.sleep(5)
