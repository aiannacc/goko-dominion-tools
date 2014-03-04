import threading
import time
import logging

from gdt.util.sync import synchronized

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

    def addClient(self, client):
        self.clients.add(client)

    def remClient(self, client):
        self.clients.remove(client)
        # TODO: clean up client's remaining dependencies

    def receiveFromClient(self, client, msgtype, msgobj):
        if msgtype == 'QUERY_CLIENTLIST':
            self.interface.sendToClient(client, 'CLIENTLIST', 
#                                        clientlist=client)
                                        # TODO: fix when done testing
                                        clientlist=self.clients)
