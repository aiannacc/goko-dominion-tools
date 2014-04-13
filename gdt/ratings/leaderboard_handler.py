#!/usr/bin/env python

import datetime
import pytz
import sys

import tornado.web
import tornado.template

from ..model import db_manager


class LeaderboardHandler(tornado.web.RequestHandler):

    def post(self):
        return NotImplemented

    def get(self):

        system_dbname = self.get_argument('system', 'isotropish')

        # Get requested sort key
        sortkey = self.get_argument('sortkey', 'level')

        # Display full or limited leaderboard
        full = self.get_argument('full', 'False') == 'True'

        offset = self.get_argument('offset', 0)
        count = self.get_argument('count', sys.maxsize)

        # Let WW ruin stuff
        if self.get_argument('ww', 'false') == 'true':
            full = True
            sortkey = 'mu'

        if full:
            ratings = db_manager.fetch_ratings2(
                system_dbname, guest=False, offset=offset,
                count=count, sortkey=sortkey)
        else:
            lastmonth = datetime.datetime.now() - datetime.timedelta(days=30)
            ratings = db_manager.fetch_ratings2(
                system_dbname, min_level=0, min_games=20, active_since=lastmonth,
                guest=False, offset=offset, count=count, sortkey=sortkey)

        # Generate each player's row
        prs = []
        rank = 1
        for r in ratings:
            r['rank'] = rank
            r['games'] = r['numgames']
            r['level'] = int(r['level'])
            r['updown'] = ''
            r['updown_n'] = ''
            r['mu'] = "%5.2f" % r['mu']
            r['3sigma'] = "%4.2f" % (3*r['sigma'])
            r['sigma'] = "%4.2f" % (r['sigma'])
            prs.append(r)
            rank = rank + 1

        # When ratings were last updated
        last_log_time_u = db_manager.get_last_rated_game2('isotropish')[0]
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
            ww=self.get_argument('ww', 'false'),
            full=full,
            sortkey=sortkey,
        ))
        self.finish()

    def write_error(self, status_code, **kwargs):
        import traceback
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br/>" % line for line
                                  in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br/>" %
                                    (k, self.request.__dict__[k]) for
                                    k in self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                             <title>%s</title>
                             <body>
                                <h2>Error</h2>
                                <p>%s</p>
                                <h2>Traceback</h2>
                                <p>%s</p>
                                <h2>Request Info</h2>
                                <p>%s</p>
                             </body>
                           </html>""" % (error, error,
                                         trace_info, request_info))
