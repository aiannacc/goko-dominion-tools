#!/usr/bin/python

import sys
import logging
import os

import tornado.web
import tornado.ioloop

import gdt
from gdt.ratings.leaderboard_handler import LeaderboardHandler
from gdt.logsearch.logsearch_handler import SearchHandler
from gdt.kingviz.kingviz_handler import KingdomHandler


class SFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")

# Handle requests for log search, kingdom visualizer, and leaderboard.
class LogApplication(tornado.web.Application):
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
            (r"/static/(.*)", SFH, {"path": "web/static"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )

if __name__ == '__main__':

    # INFO-level logging to file
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename='./log_server.log',
        filemode='a')

    # Run logsearch+ on the requested port
    http_port = int(sys.argv[1])
    logging.info('Starting log server on port %d' % http_port)

    LogApplication().listen(
        http_port, "",
        no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()
