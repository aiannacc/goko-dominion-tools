import threading
import time
import logging
import requests
import os
from PIL import Image

from gdt.util.sync import synchronized
from gdt.model import db_manager

# For synchronization. Can be acquired multiple times by the same thread, but a
# second thread has to wait.
lock = threading.RLock()


# Logic for the GokoSalvager server.  Uses the GSInterface for convenience.
#
# All methods are synchronized, but messages from players can still get lost or
# cross with messages from the server, or can get lost or arrive out of order.
# This class is responsible for all of the edge cases and race conditions.
# More specific classes (e.g. automatch Match objects) should be able to assume
# that they're living in a single-threaded world.
#
class GSManager():

    def __init__(self, gsinterface):
        self.interface = gsinterface
        self.clients = set()

    @synchronized(lock)
    def addClient(self, client):
        self.clients.add(client)

    @synchronized(lock)
    def remClient(self, client):
        self.clients.remove(client)
        # TODO: clean up client's remaining dependencies

    @synchronized(lock)
    def receiveFromClient(self, client, msgtype, msgid, message):
        if msgtype == 'QUERY_CLIENTLIST':
            self.interface.respondToClient(client, msgtype, msgid,
                                           clientlist=self.clients)

        elif msgtype == 'SUBMIT_BLACKLIST':
            print('submit_bl')
            print(message)
            db_manager.store_blacklist(client.playerId, message['blacklist'],
                                       message['merge'])

        elif msgtype == 'QUERY_BLACKLIST':
            blist = db_manager.fetch_blacklist(client.playerId)
            print(blist)
            self.interface.respondToClient(client, msgtype, msgid,
                                           blacklist=blist)

        elif msgtype == 'QUERY_BLACKLIST_COMMON':
            cbl = db_manager.fetch_blacklist_common(message['percentile'])
            self.interface.respondToClient(client, msgtype, msgid,
                                           common_blacklist=cbl)

        elif msgtype == 'QUERY_ISOLEVEL':
            rating = db_manager.get_rating_by_id(message['playerId'])
            if rating is None:
                db_manager.record_player_id(message['playerId'],
                                            message['playerName'])
                rating = db_manager.get_rating(message['playerName'])
            if rating is None:
                isolevel = 0
            else:
                (mu, sigma, numgames) = rating
                isolevel = round(mu - sigma, 2)
            self.interface.respondToClient(client, msgtype, msgid,
                                           isolevel=isolevel)

        #elif msgtype == 'QUERY_ISOLEVELS':
        #    print(message)
        #    self.interface.respondToClient(client, msgtype, msgid,
        #                                   isolevels=[19])

        elif msgtype == 'QUERY_AVATAR':
            pid = message['playerId']
            ainfo = db_manager.get_avatar_info(pid)
            if ainfo is None:
                logging.info('Avatar info not found.  Looking up on '
                             + 'retrobox -- playerId: %s' % pid)
                url = "http://dom.retrobox.eu/avatars/%s.png"
                url = url % message['playerId']
                r = requests.get(url, stream=True)
                available = r.status_code != 404
                if available:
                    logging.info('Writing avatar to file: %s' % pid)

                    # As uploaded
                    with open(pid, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                        f.flush()
                        f.close()

                    # As uploaded
                    img = Image.open(pid)
                    (w, h) = img.size
                    img = img.resize((100, 100), Image.ANTIALIAS)
                    img = img.convert('RGB')
                    img.save('web/static/avatars/' + pid + '.jpg', "JPEG",
                             quality=95)

                    # As uploaded
                    try:
                        os.remove(pid)
                    except OSError as e:
                        print("Error: %s - %s." % (e.filename, e.strerror))

                    db_manager.save_avatar_info(pid, True)
                else:
                    db_manager.save_avatar_info(pid, False)
                self.interface.respondToClient(client, msgtype, msgid,
                                               available=available)
            else:
                logging.debug('Avatar info found for %s %s - %s, %s'
                              % (pid, msgid, ainfo[0], ainfo[1]))
                self.interface.respondToClient(client, msgtype, msgid,
                                               playrid=pid, available=ainfo[1])
        else:
            logging.warn("""Received unknown message type %s from client %s
                         """ % (msgtype, client))
            self.interface.respondToClient(client, msgtype, msgid,
                                           response="Unknown message type")
