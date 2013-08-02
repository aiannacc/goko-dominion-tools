#!/usr/bin/env python

import datetime
import pytz

import tornado.web
import tornado.template

from ..model import db_manager


class LeaderboardHandler(tornado.web.RequestHandler):

    def post(self):
        return NotImplemented

    def get(self):

        # Display full or limited leaderboard
        full = self.get_argument('full', 'False') == 'True'
        if full:
            ratings = db_manager.fetch_all_ratings(None, None, None)
        else:
            lastmonth = datetime.datetime.now() - datetime.timedelta(days=30)
            ratings = db_manager.fetch_all_ratings(20, lastmonth, 0)

        # Get requested sort key
        sortkey = self.get_argument('sortkey', 'level')

        # Sort players 
        if sortkey == 'level':
            key = lambda x: ratings[x]['mu'] - 3 * ratings[x]['sigma']
        elif sortkey == 'mu':
            key = lambda x: ratings[x]['mu']
        elif sortkey == 'sigma':
            key = lambda x: ratings[x]['sigma']
        elif sortkey == 'numgames':
            key = lambda x: ratings[x]['n']
        elif sortkey == 'pname':
            key = lambda x: x
        else:
            raise "Unknown sort key"
        pnames = reversed(sorted(ratings, key=key))

        # Generate each player's row
        prs = []
        rank = 1
        for p in pnames:
            r = ratings[p]
            r['pname'] = p
            r['rank'] = rank
            r['games'] = ratings[p]['n']
            r['level'] = int(ratings[p]['mu'] - 3 * ratings[p]['sigma'])
            r['updown'] = ''
            r['updown_n'] = ''
            r['mu'] = "%5.2f" % ratings[p]['mu']
            r['3sigma'] = "%4.2f" % (3*ratings[p]['sigma'])
            r['sigma'] = "%4.2f" % ratings[p]['sigma']
            prs.append(r)
            rank = rank + 1

        # When ratings were last updated
        last_log_time_u = db_manager.fetch_last_rated_log_time()
        last_log_time = pytz.timezone('US/Pacific').localize(last_log_time_u)
        last_log_time_str = last_log_time.strftime('%a, %b %d at %I:%M %p %Z')
        ago = (datetime.datetime.now() - last_log_time_u).total_seconds()
        ago_m = int(ago / 60)
        ago_s = int(ago % 60)

        # Build page from template
        loader = tornado.template.Loader(".")
        self.write(loader.load("web/leaderboard.html").generate(
            title='Unofficial Goko TrueSkill Leaderboard',
            game_count_all=None,
            game_count_yesterday=None,
            date_updated=last_log_time_str,
            ago_m=ago_m,
            ago_s=ago_s,
            player_ratings=prs,
            full=full,
            sortkey=sortkey
        ))
