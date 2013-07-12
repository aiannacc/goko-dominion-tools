#!/usr/bin/env python

import tornado.ioloop
import tornado.web
import tornado.escape
from tornado import template

import datetime
import re
import sys
import os
import signal
import time

sys.path.append('../db')
sys.path.append('../kingdomimg/')
import gokoconstants
import build_kingdom_http
from dominiongame import GameResult
from dominiongame import PlayerResult
import dbmgr

gainable = dbmgr.get_gainable_cards(True)
bots = dbmgr.get_bot_names()
advbots = dbmgr.get_advbot_names()

print('Starting Handler')


class OfflineHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        print('Allowing all origins.')

    def get(self):
        print('OfflineHandler received get.')
        return self.post()

    def post(self):
        print('OfflineHandler received post.')
        loader = template.Loader(".")
        self.write(loader.load("offline.html")
                         .generate(title='Goko Log Search'))


class KingdomImgHandler(tornado.web.RequestHandler):

    def get(self):
        return self.post()

    def post(self):
        err = False
        logurl = self.get_argument('logurl', default='')
        if(logurl):
            try:
                m = re.match('.*/(201.*/log.*txt)', logurl)
                logurl = m.group(1)
                logurl = 'http://dominionlogs.goko.com/' + logurl
            except:
                err = True
                logurl = ''

        width = self.get_argument('width', default='100')
        try:
            wint = int(width)
        except:
            wint = 100

        if logurl:
            bbcode = build_kingdom_http.parse_and_build_bb(logurl, wint)
            htmlcode = tornado.escape.xhtml_unescape(
                build_kingdom_http.parse_and_build_html(logurl, wint))
        else:
            bbcode = None
            htmlcode = None

        loader = template.Loader(".")
        self.write(loader.load("../kingdomimg/build.html")
                         .generate(title='Kingdom Image Builder',
                                   logurl=logurl, width=width,
                                   bbcode=bbcode, htmlcode=htmlcode, err=err))


class SearchHandler(tornado.web.RequestHandler):

    def get(self):
        return self.post()

    def post(self):
        try:
            errors = []
            games = []

            p1 = self.get_argument('p1', default='')
            p1won = self.get_argument('p1won', default='either')
            p2 = self.get_argument('p2', default='')
            kreq = self.get_argument('kreq', default='')

            startdatedef = datetime.datetime.now()\
                - datetime.timedelta(days=14)
            enddatedef = datetime.datetime.now()

            startdate = self.get_argument(
                'startdate', default=startdatedef.strftime('%Y-%m-%d'))
            enddate = self.get_argument(
                'enddate', default=enddatedef.strftime('%Y-%m-%d'))

            try:
                startdateq = datetime.datetime.strptime(startdate, '%Y-%m-%d')
            except:
                startdateq = startdatedef
                errors.append("""Invalid date format: %s.
                                  Format like 2012-01-15.""" % startdate)

            try:
                enddateq = datetime.datetime.strptime(enddate, '%Y-%m-%d')
            except:
                enddateq = enddatedef
                errors.append("""Invalid date format: %s.
                                  Format like 2012-01-15.""" % enddate)

            casesensitive = self.get_argument('casesensitive', default="no")
            bots = self.get_argument('bots', default='no')
            guests = self.get_argument('guests', default='no')
            colonies = self.get_argument('colonies', default='either')
            shelters = self.get_argument('shelters', default='either')
            pcount = self.get_argument('pcount', default='two')
            rating = self.get_argument('rating', default='pro+')
            minturns = self.get_argument('minturns', default='')
            maxturns = self.get_argument('maxturns', default='')
            quit = self.get_argument('quit', default='no')
            pagesize = self.get_argument('pagesize', default='20')

            ontfhash = {'on': True, 'no': False, None: None}
            yesnohash = {'yes': 1, 'no': 0, 'either': None}
            yntfhash = {'yes': True, 'no': False, 'either': None}

            submit = self.get_argument('submit', default='')
            if (submit == 'Clear'):
                p1 = ''
                p1won = 'either'
                p2 = ''
                kreq = ''
                casesensitive = "no"
                bots = 'no'
                guests = 'no'
                colonies = 'either'
                shelters = 'either'
                pcount = 'two'
                rating = 'pro+'
                minturns = ''
                maxturns = ''
                quit = 'no'
                pagesize = '20'
                startdatedef = datetime.datetime.now()\
                    - datetime.timedelta(days=14)
                enddatedef = datetime.datetime.now()
                startdate = startdatedef.strftime('%Y-%m-%d')
                enddate = enddatedef.strftime('%Y-%m-%d')

            try:
                pagesizeq = int(pagesize)
            except:
                pagesize = '20'
                pagesizeq = 20

            try:
                minturnsq = int(minturns)
            except:
                minturns = ''
                minturnsq = None

            try:
                maxturnsq = int(maxturns)
            except:
                maxturns = ''
                maxturnsq = None

            p1q = p1 if p1 else None
            p2q = p2 if p2 else None
            casesensitiveq = ontfhash[casesensitive]
            ratingq = None if (rating == 'any') else rating
            quitq = yesnohash[quit]
            botq = yesnohash[bots]
            guestq = yesnohash[guests]
            colq = yesnohash[colonies]
            shelq = yesnohash[shelters]
            pcountq = {'one': 1, 'two': 2, 'three': 3, 'four': 4,
                       'five': 5, 'six': 6, 'any': None}[pcount]

            p1rankq = None
            p1wonq = yntfhash[p1won]
            if (not p1wonq is None):
                p1rankq = (1 if p1wonq else 2)

            kreq_cards = []
            for card in re.split(',', kreq):
                if card:
                    if card.lower() in (nscard.lower() for nscard
                                        in gokoconstants.NON_SUPPLY):
                        card = gokoconstants.NON_SUPPLY[card]
                        kreq_cards.append(card)
                    elif card.lower() in (kcard.lower() for kcard in
                                          gokoconstants.KNIGHTS):
                        kreq_cards.append('Knights')
                    elif card.lower().startswith("jack"):
                        kreq_cards.append('JackOfAllTrades')
                    elif card.lower() in (rcard.lower() for rcard in
                                          gokoconstants.RUINSES):
                        kreq_cards.append('Ruins')
                    elif card.lower() in (scard.lower() for scard in
                                          gokoconstants.SHELTERS):
                        shelters = 'yes'
                        shelq = True
                    elif not card.lower().strip() in gainable:
                        errors.append("""Error: Unrecognized card: %s.
                                         Please verify spelling.""" % card)
                    else:
                        kreq_cards.append(re.escape(card.strip()))
            if len(kreq_cards) == 0:
                kreq_cards = None

            print("""p1=%s, p1won=%s, p2=%s, kreq=%s, casesensitive=%s,
                     bots=%s, guests=%s, colonies=%s, shelters=%s,
                     pcount=%s, rating=%s, minturns=%s, maxturns=%s,
                     quit=%s, enddate=%s, startdate=%s
                  """ % (p1, p1won, p2, kreq, casesensitive, bots, guests,
                  colonies, shelters, pcount, rating, minturns, maxturns,
                  quit, enddate, startdate))

            submit = self.get_argument('submit', default='')
            if submit == "Newer":
                pageno = int(self.get_argument('pageno', default=1)) - 1
            elif submit == "Older":
                pageno = int(self.get_argument('pageno', default=1)) + 1
            else:
                pageno = 1

            print("submit value: %s" % submit)
            if submit in ('Search', 'Newer', 'Older'):
                if not p1 and not p2 and not kreq_cards:
                    errors.append("Must enter a player or a kingdom.")
                if dbmgr.is_bot(p1) and not p2:
                    errors.append("Too many games for bot '%s'" % p1)
                elif dbmgr.is_bot(p2) and not p1:
                    errors.append("Too many games for bot '%s'" % p2)

                try:
                    f = open('requests', 'a')
                    f.write(repr(self.request)+'\n')
                    f.write(repr((p1q, p2q, p1rankq, minturnsq, maxturnsq,
                            kreq_cards, botq, guestq, ratingq, pcountq,
                            colq, shelq, quitq, kreq_cards))+'\n')
                    f.close()
                except:
                    print("Couldn't write to requests file")

                if (len(errors) == 0):
                    print((p1q, p2q, casesensitiveq, p1rankq,
                           minturnsq, maxturnsq, kreq_cards, botq, guestq,
                           ratingq, pcountq, colq, shelq, quitq, kreq_cards,
                           startdateq, enddateq))
                    games = dbmgr.search(p1q, p2q, casesensitiveq, p1rankq,
                                         minturnsq, maxturnsq, kreq_cards,
                                         botq, guestq, ratingq, pcountq,
                                         colq, shelq, quitq, kreq_cards,
                                         startdateq, enddateq)

            if len(games) == 0 and (len(errors) == 0) \
               and (submit in ("Search", "Newer", "Older")):
                errors.append("No matching games found.")

            # Calculate overall record
            player_record = {}
            for g in games:
                if len(g.presults) != 2:
                    continue
                winner_count = 0
                for pname in g.presults:
                    p = g.presults[pname]
                    if p.rank == 1:
                        winner_count += 1
                tie = winner_count == 2

                for pname in g.presults:
                    p = g.presults[pname]

                    if not (p.pname.lower() == p1.lower()
                       or p.pname.lower() == p2.lower()):
                        continue

                    if not p.pname in player_record:
                        player_record[p.pname] = {}
                        player_record[p.pname]['wins'] = 0
                        player_record[p.pname]['losses'] = 0
                        player_record[p.pname]['ties'] = 0
                    if p.rank == 1 and tie:
                        player_record[p.pname]['ties'] += 1
                    elif p.rank == 2:
                        player_record[p.pname]['losses'] += 1
                    else:
                        assert p.rank == 1
                        player_record[p.pname]['wins'] += 1

            total_num_games = len(games)
            if len(games) > pagesizeq:
                start = (pageno-1)*pagesizeq
                end = min(pageno*pagesizeq, len(games))
                games = games[start:end]

            print('Request complete.')

            loader = template.Loader(".")
            self.write(loader.load("search.html").generate(
                title='Goko Log Search',
                datetime=datetime,
                re=re,
                PlayerResult=PlayerResult,
                GameResult=GameResult,
                gokoconstants=gokoconstants,
                pagesize=pagesizeq,
                pageno=pageno,
                player_record=player_record,
                errors=errors,
                p1won=p1won,
                quit=quit,
                minturns=minturns,
                maxturns=maxturns,
                searchmade=(True if submit else False),
                total_num_games=total_num_games,
                bots=bots,
                guests=guests,
                rating=rating,
                pcount=pcount,
                colonies=colonies,
                shelters=shelters,
                casesensitive=casesensitive,
                games=games,
                p1=p1,
                p2=p2,
                startdate=startdate,
                enddate=enddate,
                kreq=kreq))

        except:
            raise
            #loader = template.Loader(".")
            #self.write(loader.load("maintenance.html")
            #                 .generate(title='Goko Log Search'))

application = tornado.web.Application([
    (r"/", SearchHandler),
    (r"/search", SearchHandler),
    (r"/kingdom", KingdomImgHandler),
    (r"/offline", OfflineHandler)
    ])

#application = tornado.web.Application([
#    (r"/", OfflineHandler),
#    ])

if __name__ == "__main__":
    if os.path.exists('request.pid') and sys.argv[1] == '80':
        f = open('request.pid', 'r')
        pid = int(f.readline())
        try:
            os.kill(pid, signal.SIGTERM)
        except:
            pass
        os.remove('request.pid')
        f = open('request.pid', 'w')
        f.write("%d" % os.getpid())
        f.close()
    application.listen(sys.argv[1])
    tornado.ioloop.IOLoop.instance().start()
