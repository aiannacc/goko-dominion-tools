#!/usr/bin/env python

# Automatch server for Goko Dominion
#
# Written for Python v3.3.2 and Tornado 3.1

import datetime
import sys
import os
import signal
import time
import json
import bidict
import random

import vimpdb; vimpdb.set_trace()

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.escape
import tornado.template


class Request():
    def __init__(self, rdict):
        self.pname = rdict['pname']
        self.rating = rdict['rating']
        self.rdiff = rdict['rdiff']
        self.num_players = rdict['num_players']
        self.sets_owned = rdict['sets_owned']
        self.sets_wanted = rdict['sets_wanted']

    def __tostr__(self):
        return self.__dict__.__tostr__()

    def __repr__(self):
        return self.__dict__.__repr__()


class Match():
    def __init__(self, reqs, host_pname):
        self.reqs = reqs
        self.host_pname = host_pname

    def __tostr__(self):
        return self.__dict__.__tostr__()

    def __repr__(self):
        return self.__dict__.__repr__()

    @staticmethod
    def generate_match(reqs):
        # Check if ratings are all acceptable
        for r1 in reqs:
            for r2 in reqs:
                if abs(r2.rating - r1.rating) > r1.rdiff:
                    return None
        # Check if the number of players is acceptable
        for r in reqs:
            if not len(reqs) in r.num_players:
                return None
        # TODO Check if there is a host that owns all necessary sets.
        #      Choose host.
        return Match(reqs, reqs[0].pname)


class MREncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Match):
            reqs_str = [r.__dict__ for r in obj.reqs]
            return {'host_pname': obj.host_pname, 'reqs': reqs_str}
        if isinstance(obj, Request):
            return obj.__dict__
        return json.JSONEncoder.default(self, obj)


class RequestQueue():
    def __init__(self):
        # Bidirectional dictionary between player names and requests,
        # clients, offers, accepts
        self.requests = {}
        self.clients = {}
        self.matches = {}
        self.acceptances = {}
        self.pongs = {}

        # Last ping response time for each client
        self.timeout = 30

    def __tostr__(self):
        return self.__dict__.__tostr__()

    def __repr__(self):
        return self.__dict__.__repr__()

    def remove(self, pname):
        print('Removing player: %s' % pname)
        if pname in self.requests:
            del self.requests[pname]
        if pname in self.pnames:
            del self.clients[pname]
        if pname in self.matches:
            del self.matches[pname]
        if pname in self.acceptances:
            del self.acceptances[pname]
        if pname in self.pongs:
            del self.pongs[pname]

    def update_timeout(self, client, time):
        print('Updating timeout: %s' % client)
        self.pongs[client] = time

    def add_request(self, client, request):
        print('Adding request: %s' % client)
        if type(request).__name__ == 'dict':
            request = Request(request)
        self.requests[client] = request

    def generate_matches(self):
        print('Generating matches')
        matches = {}
        #for req_i in self.requests.values():
        #    for req_j in self.requests.values():
        #        client_i = self.clients[req_i]
        #        client_j = self.clients[req_j]
        #        if (client_i in matches) or (client_j in matches):
        #            continue
        #        if req_i.matches_with(req_j):
        #            match = Match(req_i, req_j)
        #            matches[client_i] = match
        #            matches[client_j] = match

        print('---')
        for r in self.matches.keys():
            print(r)
        print('')
        for r in self.requests.values():
            print(r)
        print('')

        # Isotropic's algorithm
        for n in (6, 5, 4, 3, 2):

            # Let S be the set of players interested in an N-player game
            ok_num_players = lambda r: n in r.num_players
            reqs_n = list(filter(ok_num_players, self.requests.values()))

            # Ignore players who currently have pending match offers
            not_matched = lambda r: not r in self.matches.keys()
            reqs_n = list(filter(not_matches, reqs_n))

            #while |S| >= N:
            while len(reqs_n) >= n:
                #randomly choose a player X, remove from S.
                random.shuffle(reqs_n)
                req = reqs_n.pop()
                #try 5 times:
                for i in range(5):
                    #randomly choose N-1 other players from S
                    random.shuffle(reqs_n)
                    reqs = reqs_n[0: n-1]
                    reqs.append(req)
                    #see if {X + the N-1 other players}
                    m = Match.generate_match(reqs)
                    # if it is, remove players from S and propose game.
                    if (m):
                        for r in reqs:
                            matches[r] = m
                        if len(reqs_n) > n:
                            reqs_n = reqs_n[n:]
                        else:
                            reqs_n = []
                        break
        return matches

    def cancel_match_offer(self, match):
        print('Canceling match offer: %s' % match)
        pass

    def accept_match(self, req, match):
        print('Match accepted by %s:' % req)
        match.accepted_by.add[req]

    def decline_match(self, req, match):
        print('Match declined by %s:' % req)
        #TODO: implement this
        pass

    def cleanup_cycle(self):
        print('Running cycle')

        # Close any client that has timed out
        for client in self.pongs:
            elapsed = time.time() - self.pongs[client]
            if (elapsed > timeout):
                remove(client)

        # Generate and offer matches
        self.matches = self.generate_matches()
        for req in self.matches.keys():
            match = self.matches[req]
            client = self.clients[req]
            client.offer_match(match)


# The server object. Receives match requests, keeps the connection open until
# a match is found, and then notifies matched players.
#
class AutomatchWSH(tornado.websocket.WebSocketHandler):
    def open(self):
        print('Connection opened.')

    def on_message(self, message_str):
        message = json.loads(message_str)
        if (message['msgtype'] == 'submit_request'):
            queue.add_request(self, message['request'])
        elif (message['msgtype'] == 'cancel_request'):
            queue.remove(self)
        elif (message['msgtype'] == 'accept_match'):
            queue.accept_match(self, message['match'])
        elif (message['msgtype'] == 'decline_match'):
            queue.accept_match(self, message['match'])
        elif (message['msgtype'] == 'ping'):
            queue.update_timeout(self, time.time())
        else:
            print('Unrecognized message type: %s' % message_str)

    def offer_match(self, match):
        print('Offering match')
        message = {'msgtype': 'offer_match',
                   'match': match,
                   'matchid': id(match)}
        self.write_message(MREncoder().encode(message))

    def notify_match_accepted(self, match, matchid):
        print('Notifying of match')
        message = {'msgtype': 'notify_match_accepted',
                   'match': match,
                   'matchid': matchid}
        self.write_message(MREncoder().encode(message))

    def notify_match_declined(self, match, matchid, decliner_pname):
        print('Notifying of match accepted')
        message = {'msgtype': 'notify_match_declined',
                   'decliner_pname': decliner_pname,
                   'match': match,
                   'matchid': matchid}
        self.write_message(MREncoder().encode(message))

    def cancel_offer(self, match, matchid, cancel_reason):
        print('Canceling match')
        message = {'msgtype': 'cancel_offer',
                   'match': match,
                   'matchid': matchid,
                   'cancel_reason': cancel_reason}
        self.write_message(MREncoder().encode(message))

    def on_close(self):
        print('Connection closed.')
        queue.remove(self)

# For running the Automatch server.
# Usage: ./automatch [port]
if __name__ == "__main__":

    # Run on requested port or on default
    try:
        port = int(sys.argv[-1])
    except:
        DEFAULT_PORT = 8080
        port = DEFAULT_PORT

    # Close the existing server process, if any.
    # TODO: Use pgrep or such, rather than the cached pid <?>
    # TODO: Make this OS independent <?>
    if os.path.exists('automatch.pid'):
        f = open('automatch.pid', 'r')
        pid = int(f.readline())
        try:
            print('Stopping old Automatch server.')
            os.kill(pid, signal.SIGTERM)
        except:
            # TODO: deal with potential errors here
            pass
        os.remove('automatch.pid')

    # Cache the new process id.
    f = open('automatch.pid', 'w')
    f.write("%d" % os.getpid())
    f.close()

    queue = RequestQueue()
    application = tornado.web.Application([
        (r'/ws', AutomatchWSH),
        ], debug=True)
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)

    print('Starting Automatch server on port %d.' % port)

    # Keep the server running indefinitely
    tornado.ioloop.PeriodicCallback(queue.cleanup_cycle, 3000).start()
    tornado.ioloop.IOLoop.instance().start()
