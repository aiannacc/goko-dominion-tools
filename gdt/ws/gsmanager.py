import threading
import time
import logging
import requests

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
        elif msgtype == 'QUERY_AVATAR':
            pid = message['playerid']
            ainfo = db_manager.get_avatar_info(pid)
            if ainfo is None:
                logging.info('Avatar info not found.  Looking up on '
                             + 'retrobox -- playerid: %s' % pid)
                url = "http://dom.retrobox.eu/avatars/%s.png"
                url = url % message['playerid']
                r = requests.get(url, stream=True)
                available = r.status_code != 404
                if available:
                    logging.info('Writing avatar to file: %s' % pid)
                    path = "/home/ai/code/goko-dominion-tools/web/static/" \
                           + "avatars/medium/%s.png" % pid
                    with open(path, 'wb') as f:
                        for chunk in r.iter_content(1024):
                            f.write(chunk)
                        f.flush()
                        f.close()
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
