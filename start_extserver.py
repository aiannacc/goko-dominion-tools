#!/usr/bin/python

import sys
import logging
import os

import tornado.web
import tornado.ioloop

import gdt
from gdt.automatch.communicator import AutomatchWSH


class SFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")

# Handle extension updating
class ExtensionApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/(.*)", SFH, {"path": "web/static/gokosalvager/"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )

if __name__ == '__main__':

    # INFO-level logging to file
    logging.basicConfig(level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename='/var/log/ext_server.log',
        filemode='a')

    # Run logsearch+ on the requested port
    https_port = int(sys.argv[1])
    logging.info('Starting extension server on port %d' % https_port)

    ssl_options={"certfile": os.path.join("/etc/ssl/certs/",
                                          "gokosalvager_com.full.crt"),
                                          #"gokosalvager_com.crt"),
                 "keyfile": os.path.join("/etc/ssl/private/", "key.pem")}

    ExtensionApplication().listen(
        https_port, "",
        ssl_options=ssl_options,
        no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()
