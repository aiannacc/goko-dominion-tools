#!/usr/bin/python

import sys
import logging

import tornado.web
import tornado.ioloop
import tornado.httpserver

import gdt
from gdt.ratings.leaderboard_handler import LeaderboardHandler
from gdt.logsearch.logsearch_handler import SearchHandler
from gdt.kingviz.kingviz_handler import KingdomHandler


# Handle requests for log search, kingdom visualizer, and leaderboard.
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", SearchHandler),
            (r"/logsearch", SearchHandler),
            (r"/logsearch/", SearchHandler),
            (r"/kingdom", KingdomHandler),
            (r"/kingdom/", KingdomHandler),
            (r"/kingdomvisualize", KingdomHandler),
            (r"/kingdomvisualize/", KingdomHandler),
            (r"/leaderboard", LeaderboardHandler),
            (r"/leaderboard/", LeaderboardHandler),
        ]
        tornado.web.Application.__init__(
            self, handlers, static_path='web/static'
        )

if __name__ == '__main__':
    # Detailed logging while developing
    logging.basicConfig(level=logging.INFO)

    # Usage: python start_logserver.py <port>
    port = int(sys.argv[-1])
    print('Starting server on port %d' % port)

    # Start server and keep process open
    tornado.httpserver.HTTPServer(Application()).listen(port)
    tornado.ioloop.IOLoop.instance().start()
