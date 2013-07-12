#!/usr/bin/env python

#CARD_SETS = {
#        BASE    = 'Base', 
#        ALCHEMY = 'Alchemy', 
#        SEASIDE = 'Seaside', 
#        DA_KK   = 'Dark Ages - Knights and Knaves'
#        }

class Player():
    def __init__(self):
        self.rating = None
        self.sets = ['Base']

class Match():
    def __init__(self):
        self.requests = []
        self.host = None
        self.guests = []

class RequestQueue():

    # Bidirectional dictionary between requests and clients
    clients = bidict.bidict()
    requests = ~clients

    # Last ping response time for each client
    timeout = 30
    pongs = {}

    def __init__(self):
        self.clients = set()

    def add_request(self,request):
        pass

    def cancel_request(self,request):
        pass

    def get_matches():
        return []

    def accept_match():
        pass

    def decline_match():
        pass

    def maintenance(self):
        # TODO: Notify matched players
        # TODO: Remove matched players from queue
        pass
