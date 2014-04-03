#!/usr/bin/env python

import datetime
import pytz
import math

import tornado.web
import tornado.template

from ..model import db_manager


class LeaderboardQuery(tornado.web.RequestHandler):

    def post(self):
        return NotImplemented

    def get(self):
        print('Received leaderboard request')

        sortkey = self.get_argument('sortkey', 'level')
        full = bool(self.get_argument('full', 'False'))
        offset = int(self.get_argument('offset', 0))
        count = int(self.get_argument('count', 100))

        if full:
            ratings = db_manager.fetch_ratings(
                guest=False, offset=offset, count=count, sortkey=sortkey)
        else:
            lastmonth = datetime.datetime.now() - datetime.timedelta(days=30)
            ratings = db_manager.fetch_ratings(
                min_level=0, min_games=20, active_since=lastmonth,
                guest=False, offset=offset, count=count, sortkey=sortkey)

        for r in ratings:
            r['mu'] = round(r['mu'], 2)
            r['sigma3'] = round(3 * r['sigma'], 2)

        print('Fetched leaderboard')

        # Tornado requires lists to be wrapped in dicts
        self.write({'ratings': ratings})
        self.flush()
        self.finish()

