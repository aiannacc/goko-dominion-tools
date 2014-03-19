import threading
import time
import logging
import requests
import os
from PIL import Image
import tornado.ioloop

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
        self.avatar_table = None

        # Check for ratings changes every 3 seonds.  Notify clients.
        (self.iso_table, self.iso_latest) = db_manager.get_all_ratings_by_id()
        tornado.ioloop.PeriodicCallback(self.check_iso_levels, 3000).start()

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
            db_manager.store_blacklist(client.playerId, message['blacklist'],
                                       message['merge'])

        elif msgtype == 'QUERY_BLACKLIST':
            blist = db_manager.fetch_blacklist(client.playerId)
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
                logging.info('Recording new playerInfo: (%s, %s)' %
                      (message['playerId'], message['playerName']))
            if rating is None:
                isolevel = 0
            else:
                (mu, sigma, numgames) = rating
                isolevel = round(mu - 3 * sigma, 2)
            self.interface.respondToClient(client, msgtype, msgid,
                                           isolevel=isolevel)

        elif msgtype == 'QUERY_ISO_TABLE':
            self.interface.respondToClient(client, msgtype, msgid,
                                           isolevel=self.iso_table)

        elif msgtype == 'QUERY_AVATAR_TABLE':
            if self.avatar_table is None:
                self.avatar_table = db_manager.get_all_avatar_info()
            self.interface.respondToClient(client, msgtype, msgid,
                                           available=self.avatar_table)

        elif msgtype == 'QUERY_AVATAR':
            pid = message['playerId']
            if self.avatar_table is None:
                self.avatar_table = db_manager.get_all_avatar_info()
            if not pid in self.avatar_table:
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
                logging.debug('Avatar info found for %s %s - %s'
                              % (pid, msgid, self.avatar_table[pid]))
                self.interface.respondToClient(client, msgtype, msgid,
                                               playerid=pid,
                                               available=self.avatar_table[pid])
        else:
            logging.warn("""Received unknown message type %s from client %s
                         """ % (msgtype, client))
            self.interface.respondToClient(client, msgtype, msgid,
                                           response="Unknown message type")

    def check_iso_levels(self):
        (iso_new, self.iso_latest) = db_manager.get_new_ratings(self.iso_latest)
        for playerId in iso_new:
            self.iso_table[playerId] = iso_new[playerId]
        if iso_new != {}:
            print(iso_new)
            self.interface.sendToAllClients('UPDATE_ISO_LEVELS', new_levels=iso_new)
