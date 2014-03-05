#!/usr/bin/python

import sys
import logging
import os

import tornado.web
import tornado.ioloop
import tornado.httpserver

import gdt
from gdt.ws.gsserver import MainWSH


class SFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")

class GSApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/gs/wsConn", MainWSH),
            (r"/avatars/(.*)", SFH, {"path": "web/static/avatars"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )

if __name__ == '__main__':

    # Logging to file
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename='/var/log/gs_server.log',
        filemode='a')

    # Logging to the sys.stderr
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    # Run logsearch+ on the requested port
    ws_port = int(sys.argv[1])
    logging.info('Starting GokoSalvager server on port %d' % ws_port)

    ssl_options={"certfile": os.path.join("/etc/ssl/certs/",
                                          "andrewiannaccone_com.full.crt"),
                 "keyfile": os.path.join("/etc/ssl/private/", "key.pem")}

    GSApplication().listen(
        ws_port, "",
        ssl_options=ssl_options,
        no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()
