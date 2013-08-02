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
from gdt.automatch.communicator import AutomatchWSH
from gdt.blast.blast import BlastWSH


class SFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")


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
            (r"/automatch", AutomatchWSH),
            (r"/wshblast", BlastWSH),
            (r"/static/(.*)", SFH, {"path": "web/static"})
        ]
        tornado.web.Application.__init__(
            self, handlers,
            #static_path='web/static',
            ssl_options={
                "certfile": "cert.cer",
                "keyfile":  "key.key",
            }
        )

if __name__ == '__main__':
    # Detailed logging while developing
    logging.basicConfig(level=logging.DEBUG)

    # Usage: python start_logserver.py <port>
    port = int(sys.argv[-1])
    print('Starting server on port %d' % port)

    # Start server and keep process open
    tornado.httpserver.HTTPServer(Application()).listen(port)
    tornado.ioloop.IOLoop.instance().start()
