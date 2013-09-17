#!/usr/bin/python

import sys
import logging
import os

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

# Handle extension updating
class ExtensionApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/gs/(.*)", SFH, {"path": "web/static/gokosalvager/"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )

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
            (r"/wshblast", BlastWSH),
            (r"/automatch", AutomatchWSH),
            (r"/static/(.*)", SFH, {"path": "web/static"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )

class AutomatchApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/automatch", AutomatchWSH),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )


if __name__ == '__main__':

    # INFO-level logging to file
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename='./servers.log',
        filemode='a')

    # WARNING-level logging to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.WARN)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # Run logsearch+ on the requested port
    http_port = int(sys.argv[1])
    logging.info('Starting log server on port %d' % http_port)
    https_port = int(sys.argv[2])
    logging.info('Starting extension server on port %d' % https_port)
    ws_port = int(sys.argv[3])
    logging.info('Starting automatch server on port %d' % ws_port)

    ssl_options={"certfile": os.path.join("/etc/ssl/certs/",
                                          "andrewiannaccone_com.full.crt"),
                 "keyfile": os.path.join("/etc/ssl/private/", "key.pem")}

    LogApplication().listen(
        http_port, "",
        no_keep_alive=True)
    ExtensionApplication().listen(
        https_port, "",
        ssl_options=ssl_options,
        no_keep_alive=True)
    AutomatchApplication().listen(
        ws_port, "",
        ssl_options=ssl_options,
        no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()
