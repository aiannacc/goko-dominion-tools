#!/usr/bin/python

import sys
import logging

import tornado.web
import tornado.ioloop
import tornado.httpserver

import gdt
from gdt.automatch.communicator import AutomatchWSH


# Request to http://<host>/automatch spawns new AutomatchWSH websocket handler
class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
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

    logging.basicConfig(level=logging.DEBUG)

    try:
        port = int(sys.argv[-1])
        print('Starting server on port %d' % port)
    except:
        print('Usage: python start_automatch_server.py <port>')
        sys.exit(1)

    # Start server and keep process running
    tornado.httpserver.HTTPServer(Application()).listen(port)
    tornado.ioloop.IOLoop.instance().start()
