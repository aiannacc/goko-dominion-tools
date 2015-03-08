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

from gdt.ratings.history import RatingHistory
import gdt.ratings.rating_system3 as rs
import gdt.ratings.update as ru


# Constants
LOGLEVEL = logging.DEBUG
LINK_REGEX = re.compile('href="(log\S*txt)"')
FILE_REGEX = re.compile("log\.(.*)\.(.*)\.txt")
LOG_DIR = '/gokologs'                 # For linode server
#LOG_DIR = '/mnt/raid/media/dominion/logs'  # For home server

RATING_SYSTEM_NAME = 'isotropish_nobots'

# Logging
logger = logging.getLogger('logwatcher')
logger.setLevel(LOGLEVEL)
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)

# Parse with up to 6 threads
parsesema = threading.BoundedSemaphore(value=6)

s = requests.Session()
#sproxies = {'http': 'socks5://127.0.0.1:9050',
#            'https': 'socks5://127.0.0.1:9050'}
#help(s)
#print(s.__attrs__)

# Download a log and save it to file
def download_log(logfile, dayurl, log_dir):
    headers = {'Accept-Encoding': 'gzip, deflate'}
    url = dayurl + '/' + logfile
    logger.debug('Fetching %s' % url)
    try:
        #r = s.get(url, headers=headers, timeout=60, stream=False, proxies=sproxies)
        r = s.get(url, headers=headers, timeout=60, stream=False)
        r.encoding = 'utf-8'
        gzip.open(log_dir + '/' + logfile, 'wt').write(r.text)
        logger.debug('Wrote log from %s' % url)
        return True
    except requests.exceptions.ConnectionError:
        # These are MaxRetryErrors
        return False


def download_new_logs(date):

    datestr = date.strftime('%Y%m%d')
    #dayurl = 'http://dominionlogs.goko.com/%s' % datestr
    dayurl = 'http://logs.prod.dominion.makingfun.com/%s' % datestr
    #r = requests.get(dayurl, timeout=30, proxies=sproxies)
    r = requests.get(dayurl, timeout=30)
    #print(r.text)
    remote_logs = LINK_REGEX.findall(r.text)

    # Determine which logs haven't already been downloaded
    log_dir = '%s/%s' % (LOG_DIR, datestr)
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    local_logs = os.listdir(log_dir)
    not_downloaded = set(remote_logs) - set(local_logs)
    #n = 100
    logger.info('Found %d new logs on Goko.' % (len(not_downloaded)))
    #logger.info('Found %d new logs on Goko.  Downloading %d of them.' % (len(not_downloaded), n))

    # Download logs in a single thread.
    #i = 0
    for lf in not_downloaded:
        #if i < n:
        #    i += 1
        #else:
        #    break
        download_log(lf, dayurl, log_dir)

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
    log_dir = '%s/%s' % (LOG_DIR, date.strftime('%Y%m%d'))
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
        db_manager.insert_parsefail(time, f, failed[f][0].__name__)

    return total_inserted


def rate_new_games(rhistory,
                   allow_guests=True, allow_bots=False,
                   min_turns=0, only_2p=False):
    (l, t) = rhistory.get_latest_game()
    logger.debug('Last rated game: %s, %s' % (t, l))

    # TODO: Remove max games parameter?
    #max_games = 1000
    max_games = 100000
    ru.rate_games_since(t, l, [rhistory],
                        allow_guests=allow_guests, allow_bots=allow_bots,
                        min_turns=min_turns, only_2p_games=only_2p,
                        use_gameresult_cache=False, gokomode='pro',
                        chunk_size=max_games/3, max_games=max_games)

    logger.debug('Rated games through: %s, %s' % rhistory.get_latest_game())
    logger.debug('Last rated game: %s, %s' % (t, l))

def normal_usage():
    logger.info('Now watching for new logs to be posted to MF logserver.')
    logger.info('Games played before 12:00 AM today will not be handled.')

    rsys = rs.TrueSkillSystem(RATING_SYSTEM_NAME, mu=25, sigma=25,
                              beta=25, tau=0.25,
                              draw_probability=0.05, k=3) 

    rhist = ru.get_rating_history_stub(rsys, RATING_SYSTEM_NAME)
    next_day = datetime.datetime.now()
    last_time = datetime.datetime.now()
    while True:
        # This ensures that we don't miss the very last logs posted before
        # the date ticks over at midnight.  We're guaranteed to search for
        # "yesterday's" logs at least once "today."
        #
        # NOTE we can still lose logs if the local system's time is ahead
        # of Goko's server time.  It might be better to have a 10 minute
        # window (12:00-12:10AM) in which we search for both yesterday's
        # and today's logs.
        #
        next_day = datetime.datetime.now()
        parsecount = 0
        last_time = datetime.datetime.now()
        try:
            download_new_logs(next_day)
            parsecount = parse_new_logs(next_day)
        except:
            # TODO: Do something about these errors
            logger.error(sys.exc_info()[1])
            logger.error(sys.exc_info()[2])
            pass

        logger.info('Rating new games')
        rate_new_games(rhist, allow_guests=False, min_turns=2, only_2p=True)
        logger.info('Finished.  Recording new ratings')
        ru.record_ratings(rhist, RATING_SYSTEM_NAME)
        logger.info('Finished.')

        sec_delta = (datetime.datetime.now() - last_time).seconds
        logger.info('Found %d new logs. Checking again in %d seconds.'
                    % (parsecount, 30 - sec_delta))
        if sec_delta < 30:
            time.sleep(30 - sec_delta)

if __name__ == '__main__':
    if len(sys.argv) == 3:
        start_dir = sys.argv[1]
        if sys.argv[2] == 'd':
            logger.info('Downloading/parsing logs starting on %s.  Not rating.'
                        % sys.argv[1])
            date = datetime.datetime.strptime(sys.argv[1], '%Y%m%d')
            while date < datetime.datetime.now():
                logger.info('Downloading logs for %s'
                            % (date.strftime('%Y-%m-%d')))
                download_new_logs(date)
                parse_new_logs(date)
                date += datetime.timedelta(days=1)
            normal_usage()
        else:
            logger.error('Check usage.')

    elif len(sys.argv) == 2 and sys.argv[1] == 'regen':
        while True:
            rsys = rs.TrueSkillSystem('iso_regen', mu=25, sigma=25,
                                      beta=25, tau=0.25,
                                      draw_probability=0.05, k=3) 
            rhist = ru.get_rating_history_stub(rsys, 'iso_regen')
            rate_new_games(rhist, allow_guests=False, min_turns=2, only_2p=True)
            ru.record_ratings(rhist, 'iso_regen')

    elif len(sys.argv) == 2:
        start_dir = sys.argv[1]
        logger.info('Parsing ALL previous downloaded logs after %s. '
                    + 'This may take a while.' + sys.argv[1])
        for log_dir in sorted(os.listdir(LOG_DIR)):
            if log_dir > start_dir:
                if re.match('\d{8}', log_dir):
                    log_day = datetime.datetime.strptime(log_dir, '%Y%m%d')
                    logger.info('Parsing logs from %s'
                                % log_day.strftime('%Y-%m-%d'))
                    parse_new_logs(log_day)

    else:
        normal_usage()
