#!/usr/bin/python

import sys
import logging
import os
import json
from PIL import Image

import tornado.web
import tornado.ioloop
import tornado.httpserver

import gdt
from gdt.ws.gsserver import MainWSH


class SFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Pragma-directive", "no-cache")
        self.set_header("Cache-directive", "no-cache")
        self.set_header("Cache-control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")
        self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')

class GSApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/gs/wsConn", MainWSH),
            (r"/submit_avatar", AvatarHandler),
            (r"/avatars/(.*)", SFH, {"path": "web/static/avatars"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )


class AvatarHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    def options(self):
        pass

    # TODO: move this somewhere more sensible
    def post(self):
        playerid = self.get_argument('playerid')
        logging.info('Handling avatar upload for playerid %s' % playerid)
        file1 = self.request.files['avatar'][0]
        original_fname = file1['filename']

        # Temporarily write file, since I don't know how to read binary in PIL
        output_file = open(playerid, 'wb')
        output_file.write(file1['body'])
        output_file.close()

        # Crop/Resize image to 100x100
        img = Image.open(playerid)
        (w, h) = img.size
        d = int(abs(w-h)/2)
        if w > h:
            box = (d, 0, w-d, h)
        else:
            box = (0, d, w, h-d)
        img = img.crop(box)
        img = img.resize((100, 100), Image.ANTIALIAS)
        img.save('web/static/avatars/' + playerid + '.jpg', "JPEG",
                 quality=95)

        try:
            os.remove(playerid)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

        self.finish(json.dumps('file uploaded successfully'))


if __name__ == '__main__':

    # Logging to file
    logging.basicConfig(
        level=logging.INFO,
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

    ssl_options = {
        "certfile": os.path.join("/etc/ssl/certs/",
                                 "andrewiannaccone_com.full.crt"),
        "keyfile": os.path.join("/etc/ssl/private/", "key.pem")
    }

    GSApplication().listen(
        ws_port, "",
        ssl_options=ssl_options,
        no_keep_alive=True)
    tornado.ioloop.IOLoop.instance().start()
