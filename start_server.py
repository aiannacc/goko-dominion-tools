#!/usr/bin/python

import tornado.web
import tornado.template
import tornado.ioloop

import sys

import gdt
from gdt.ratings.leaderboard_handler import LeaderboardHandler
from gdt.logsearch.logsearch_handler import SearchHandler
from gdt.kingviz.kingviz_handler import KingdomHandler

application = tornado.web.Application([
    (r"/", SearchHandler),
    (r"/logsearch", SearchHandler),
    (r"/logsearch/", SearchHandler),
    (r"/kingdomvisualize", KingdomHandler),
    (r"/kingdomvisualize/", KingdomHandler),
    (r"/leaderboard", LeaderboardHandler),
    (r"/leaderboard/", LeaderboardHandler)
], static_path="web/static")

if __name__ == "__main__":
    port = int(sys.argv[-1])
    print('Starting server on port %d' % port)
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()
