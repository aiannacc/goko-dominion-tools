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

#logging.basicConfig(level=logging.WARN)

logger = logging.getLogger('logwatcher')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)



LINK_REGEX = re.compile('href="(log\S*txt)"')
FILE_REGEX = re.compile("log\.(.*)\.(.*)\.txt")

LOG_DIR = '/dominion/logs'

# Download up to 200 logs simultaneously
dlsema = threading.BoundedSemaphore(value=200)

# Parse with up to 6 threads
parsesema = threading.BoundedSemaphore(value=6)

# Download a log and save it to file
def download_log(logfile, dayurl, log_dir):
    headers = {'Accept-Encoding': 'gzip, deflate'}
    url = dayurl + '/' + logfile
    logger.debug('Fetching %s' % url)
    r = requests.get(url, headers=headers)
    r.encoding='utf-8'
    dlsema.release()
    gzip.open(log_dir + '/' + logfile, 'wt').write(r.text)


def download_new_logs(date):

    datestr = date.strftime('%Y%m%d')
    #dayurl = 'http://dominionlogs.goko.com/%s' % datestr
    dayurl = 'http://logs.prod.dominion.makingfun.com/%s' % datestr
    r = requests.get(dayurl)
    remote_logs = LINK_REGEX.findall(r.text)

    # Determine which logs haven't already been downloaded
    log_dir = '/dominion/logs/%s' % datestr
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    local_logs = os.listdir(log_dir)
    not_downloaded = set(remote_logs) - set(local_logs)
    logger.info('Found %d new logs on Goko' % len(not_downloaded))

    # Download logs in threads.  Restrict max number of connections using
    # BoundedSemahore
    i = 0
    threads = []
    for lf in not_downloaded:
        i += 1
        dlsema.acquire()
        t = threading.Thread(target=download_log, 
                             kwargs={'logfile': lf, 'dayurl': dayurl,
                                     'log_dir': log_dir})
        threads.append(t)
        t.start()

    # Wait for downloading to finish
    for t in threads:
        t.join()

    logger.info('Finished downloading')


def parse_log(logfile):
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
            logger.warn('Cannot read file: ' + logfile_full)
            failed[logfile] = sys.exc_info()
            failed_logtime[logfile] = logtime
            fail = True
    if not fail:
        try:
            game = gokoparse.parse_goko_log(logtext)
            game.logfile = logfile
            game.time = logtime
            games.append(game)
            if len(games) % 100 == 0:
                logger.info('Parsed %d' % len(games))
        except:
            failed[logfile] = sys.exc_info()
            failed_logtime[logfile] = logtime


def parse_new_logs(date):

    # Determine which logs we have downloaded but not yet parsed
    log_dir = '/dominion/logs/%s' % date.strftime('%Y%m%d')
    local_logs = os.listdir(log_dir)
    dblogs = db_manager.search_daily_log_filenames(date)
    not_parsed = set(local_logs) - set(dblogs)
    logger.info('Found %d downloaded logs to be parsed' % len(not_parsed))

    # Parse the unparsed logs
    games = []
    failed = {}
    failed_logtime = {}
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
                logger.warn('Cannot read file: ' + logfile_full)
                failed[logfile] = sys.exc_info()
                failed_logtime[logfile] = logtime
                fail = True
        if not fail:
            try:
                game = gokoparse.parse_goko_log(logtext)
                game.logfile = logfile
                game.time = logtime
                games.append(game)
                if len(games) % 100 == 0:
                    logger.info('Parsed %d' % len(games))
            except:
                failed[logfile] = sys.exc_info()
                failed_logtime[logfile] = logtime

    logger.info('Finished parsing')
    logger.info('%d games parsed' % len(games))
    logger.info('%d games failed' % len(failed))

    # Insert parsed games into database, 100 at a time
    count = 0
    total_inserted = 0
    try:
        db_manager.inserts(games)
        total_inserted += len(games)
    except:
        logger.info(sys.exc_info())

    logger.info('inserted %d parsed games into DB' % total_inserted)

    # Notify of failed logs.  Record in database.
    for f in failed:
        logger.warn('Failed to parse: %s in %s' % (failed[f][0].__name__, f))
        for line in traceback.format_tb(failed[f][2]):
            logger.warn(line)
        time = failed_logtime[f]
        db_manager.insert_parsefail(time, f, failed[logfile])

    return total_inserted

if __name__ == '__main__':
    if len(sys.argv) == 3:
        start_dir = sys.argv[1]
        if sys.argv[2] == 'd':
            logger.info('Downloading and parsing logs starting on %s' %
                        (sys.argv[1]))
            date = datetime.datetime.strptime(sys.argv[1], '%Y%m%d')
            while date < datetime.datetime.now():
                logger.info('Downloading logs for %s' %
                            (date.strftime('%Y-%m-%d')))
                download_new_logs(date)
                #parse_new_logs(date)
                date += datetime.timedelta(days=1)
        else:
            logger.error('Check usage.')

    elif len(sys.argv) == 2:
        start_dir = sys.argv[1]
        logger.info('Parsing ALL previous downloaded logs after %s.  This may take a while.' + sys.argv[1])
        for log_dir in sorted(os.listdir('/dominion/logs')):
            if log_dir > start_dir:
                if re.match('\d{8}', log_dir):
                    log_day = datetime.datetime.strptime(log_dir, '%Y%m%d')
                    logger.info('Parsing logs from %s' % log_day.strftime('%Y-%m-%d'))
                    parse_new_logs(log_day)

    else:
        logger.warn('Now watching for new logs to be posted to the Goko log server.')
        logger.warn('Note: Games played before 12:00 AM today will not be handled.\n')

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
                logger.error(sys.exc_info()[1])
                logger.error(sys.exc_info()[2])
                pass
            logger.info('Found %d new logs. Checking again in 5 seconds.' % parsecount)
            time.sleep(5)
