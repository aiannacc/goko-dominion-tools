#!/usr/bin/python

import os
import subprocess
import re
import sys
import logging

import tornado.web
import tornado.template
import tornado.ioloop
import tornado.httpserver

import gdt
from gdt.ratings.leaderboard_handler import LeaderboardHandler
from gdt.logsearch.logsearch_handler import SearchHandler
from gdt.kingviz.kingviz_handler import KingdomHandler
from gdt.automatch.communicator import AutomatchWSH
from gdt.automatch.manager import AutomatchManager


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
        ]
        tornado.web.Application.__init__(
            self, handlers, 
            static_path='web/static', 
            ssl_options={
                "certfile": "cert.cer",
                "keyfile":  "key.key",
            }
        )

if __name__ == '__main__':
    port = int(sys.argv[-1])
    server = tornado.httpserver.HTTPServer(Application())

    logging.basicConfig(level=logging.INFO)

    #TODO: Kill Python server currently listening on <port>
    print('Starting server on port %d' % port)
    server.listen(port)
    tornado.ioloop.IOLoop.instance().start()
