import time

import tornado.web
import tornado.websocket


class BlastWSH(tornado.websocket.WebSocketHandler):

    def on_message(self, msg):
        try:
            start = time.time()
            n = int(msg)
            for i in range(n):
                self.write_message('Sending message #%s' % i)
            elapsed = time.time() - start
            self.write_message('Server clock time elapsed: %10.6f sec' % elapsed)
        except:
            self.write_message("couldn't parse '%s' as an integer" %msg)
