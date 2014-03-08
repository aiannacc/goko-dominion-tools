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
from gdt.model import db_manager
from gdt.ws.gsserver import MainWSH
from gdt.automatch.communicator import AutomatchWSH
from gdt.ratings.leaderboard_handler import LeaderboardHandler
from gdt.logsearch.logsearch_handler import SearchHandler
from gdt.kingviz.kingviz_handler import KingdomHandler


class ComprehensiveApplication(tornado.web.Application):
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
            (r"/gs/submit_avatar", AvatarUploadHandler),
            (r"/gs/websocket", MainWSH),
            (r"/gs/avatars/(.*)", AvatarSFH, {"path": "web/static/avatars"}),
            (r"/static/(.*)", DocumentSFH, {"path": "web/static"}),
            (r"/(.*)", DocumentSFH, {"path": "web/static/gokosalvager/"}),
        ]
        tornado.web.Application.__init__(
            self, handlers
        )


class AvatarSFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Pragma-directive", "no-cache")
        self.set_header("Cache-directive", "no-cache")
        self.set_header("Cache-control", "no-cache")
        self.set_header("Pragma", "no-cache")
        self.set_header("Expires", "0")
        self.set_header('Cache-Control',
                        'no-store, no-cache, must-revalidate, max-age=0')


class DocumentSFH(tornado.web.StaticFileHandler):
    def set_extra_headers(self, path):
        self.set_header("Access-Control-Allow-Origin", "*")


# TODO: move this somewhere more sensible
class AvatarUploadHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")

    def options(self):
        pass

    def post(self):
        playerid = self.get_argument('playerid')
        logging.info('Handling avatar upload for playerid %s' % playerid)

        file1 = self.request.files['avatar'][0]
        original_fname = file1['filename']

        # TODO: read the binary directly into a PIL.Image
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
        img = img.convert('RGB')
        img.save('web/static/avatars/' + playerid + '.jpg', "JPEG",
                 quality=95)

        try:
            os.remove(playerid)
        except OSError as e:
            print("Error deleting temporary avatar file: %s - %s."
                  % (e.filename, e.strerror))

        db_manager.save_avatar_info(playerid, True)
        self.finish(json.dumps('file uploaded successfully'))


if __name__ == '__main__':

    # Log to file
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M',
        filename='/var/log/comp_server.log',
        filemode='a')

    # Logg to console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

    ssl_options_ai = {
        "certfile": os.path.join("/etc/ssl/certs/", "andrewiannaccone_com.full.crt"),
        "keyfile": os.path.join("/etc/ssl/private/", "key.pem")
    }

    ssl_options_gs = {
        #"certfile": os.path.join("/etc/ssl/certs/", "gokosalvager_com.crt"),
        "certfile": os.path.join("/etc/ssl/certs/", "gokosalvager_com.full.crt"),
        "keyfile": os.path.join("/etc/ssl/private/", "key.pem")
    }

    app = ComprehensiveApplication()
    app.listen(80, "", no_keep_alive=True)

    # Old websocket URL/port for v2.4.3 and below (automatch only)
    app.listen(443, "", ssl_options=ssl_options_ai, no_keep_alive=True) 

    # New websocket URL/port for v2.5 and above (all WS communication)
    app.listen(8889, "", ssl_options=ssl_options_gs, no_keep_alive=True)

    # Support old extension-hosting port.  TODO: change to 443
    app.listen(8888, "", ssl_options=ssl_options_gs, no_keep_alive=True) 

    tornado.ioloop.IOLoop.instance().start()
