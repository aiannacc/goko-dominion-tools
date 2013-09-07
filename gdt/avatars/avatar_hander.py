import re
import requests

import tornado.web
import tornado.template

from . import builder


class AvatarHandler(tornado.web.RequestHandler):

    def post(self):
        return NotImplemented

    def get(self):
        pid = self.get_argument('playerId')
        url = 'http://dom.retrobox.eu/avatars/%s.png' % pid
        headers = {'Accept-Encoding': 'gzip, deflate'}
        r = requests.get(url, headers=headers)
        print(r)
