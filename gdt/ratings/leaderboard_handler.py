#!/usr/bin/env python

import datetime

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

        loader = tornado.template.Loader(".")
        self.write(loader.load("web/leaderboard.html").generate(
            title='Unofficial Goko TrueSkill Leaderboard',
            game_count_all=None,
            game_count_yesterday=None,
            date_generated=datetime.datetime.now(),
            player_ratings=prs
        ))
