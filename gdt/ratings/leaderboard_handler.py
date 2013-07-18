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
        ratings = db_manager.fetch_all_ratings()
        rank = lambda x: ratings[x]['mu'] - 3 * ratings[x]['sigma']
        pnames = sorted(ratings, key=rank)

        prs = []
        rank = len(pnames)
        for p in pnames:
            r = ratings[p]
            r['pname'] = p
            r['rank'] = rank
            r['games'] = 0
            r['level'] = int(r['mu'] - 3 * r['sigma'])
            r['updown'] = ''
            r['updown_n'] = ''
            r['mu'] = "%5.2f" % r['mu']
            r['sigma'] = "%4.2f" % r['sigma']
            prs.append(r)
            rank = rank - 1
        prs = reversed(prs)

        last_log_time = db_manager.fetch_last_rated_log_time()
        last_log_time = pytz.timezone('US/Pacific').localize(last_log_time)
        last_log_time_str = last_log_time.strftime('%a, %b %d at %I:%M %p %Z')

        loader = tornado.template.Loader(".")
        self.write(loader.load("web/leaderboard.html").generate(
            title='Unofficial Goko TrueSkill Leaderboard',
            game_count_all=None,
            game_count_yesterday=None,
            date_updated=last_log_time_str,
            player_ratings=prs
        ))
