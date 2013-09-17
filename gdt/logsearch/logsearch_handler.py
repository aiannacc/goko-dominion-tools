#!/usr/bin/env python

import datetime
import time
import re

import tornado.web
import tornado.template

from ..model import constants
from ..model import domgame
from ..model import db_manager


class SearchHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.supply_cards = [c.lower() for
                             c in db_manager.fetch_supply_cards()]
        self.search_params = {
            'p1name': '',
            'p2name': '',
            'casesensitive': 'off',
            'p1score': 'any',
            'bot': 'false',
            'guest': 'false',
            'shelters': 'any',
            'colony': 'any',
            'pcount': '2',
            'supply': '',
            'nonsupply': '',
            'minturns': '',
            'maxturns': '',
            'rating': 'pro+',
            'quit': 'false',
            'resign': '',
            'startdate': '08/05/2012',
            'enddate': datetime.datetime.now().strftime('%m/%d/%Y'),
            'limit': '20',
            'offset': '0',
            'submitted': 'false'}

    def post(self):
        return NotImplemented

    def get(self):

        # Parse arguments into search dict
        try:
            arg = {}
            arg_str = {}
            for p in self.search_params:
                arg_str[p] = self.get_argument(p,
                                               default=self.search_params[p])
                if arg_str[p] in ('any', ''):
                    arg[p] = None
                elif p in ['p1name', 'p2name', 'supply', 'nonsupply']:
                    arg[p] = arg_str[p]
                elif arg_str[p] in ('true', 'on'):
                    arg[p] = True
                elif arg_str[p] in ('false', 'off'):
                    arg[p] = False
                elif re.match('\d\d\d\d-\d\d-\d\d', arg_str[p]):
                    arg[p] = datetime.datetime.strptime(arg_str[p], '%Y-%m-%d')
                elif re.match('\d\d\/\d\d\/\d\d\d\d', arg_str[p]):
                    arg[p] = datetime.datetime.strptime(arg_str[p], '%m/%d/%Y')
                elif re.match('\d+', arg_str[p]):
                    arg[p] = int(arg_str[p])
                else:
                    arg[p] = arg_str[p]
        except:
            self.show_error('Error processing argument: %s="%s"' %
                            (p, arg_str[p]), arg_str)
            return

        #print(arg)
        #print(arg_str)

        # TODO: log the logsearch request

        # Make end date inclusive
        arg['enddate'] = arg['enddate'] + datetime.timedelta(days=1)

        # Parse the kingdom search field
        #print(arg_str['supply'])
        x = self.parse_supply(arg_str['supply'])
        if x:
            (sup, shel, col, err) = x
        else:
            self.show_error('Error parsing supply', arg_str)
            return

        if err:
            self.show_error(err, arg_str)
            return
        else:
            arg['supply'] = sup
            if shel:
                arg['shelters'] = True
                arg_str['shelters'] = 'true'
            if col:
                arg['colony'] = True
                arg_str['colony'] = 'true'

        # Parse the excluded kingdom field
        (nsup, nshel, ncol, err) = self.parse_supply(arg_str['nonsupply'])
        if err:
            self.show_error(err, arg_str)
            return
        else:
            arg['nonsupply'] = nsup
            if nshel:
                arg['shelters'] = False
                arg_str['shelters'] = 'false'
            if col:
                arg['colony'] = False
                arg_str['colony'] = 'false'

        # Don't try to return more than 1000 results at once
        if (arg['limit'] > 1000):
            arg_str['limit'] = 1000
            self.show_error("""Really? 1000 results at a time isn't
                            enough?""", arg_str)
            return

        # Don't do an overly-imprecise non-indexed search
        if (not arg['p1name'] and not arg['p2name'] and not arg['supply']):
            self.show_error("""Please enter a player name or a kingdom""",
                            arg_str)
            return

        # Don't do an overly-precise non-indexed search
        if (not arg['p1name'] and not arg['p2name']
                and len(arg['supply']) > 3):
            self.show_error("""No way am I gonna try that search. Please
                            enter a player name or a smaller kingdom""",
                            arg_str)
            return

        # Perform the search
        games = []
        start = time.time()
        if arg['submitted']:
            games = db_manager.search_game_results(arg)
            if len(games) == 0:
                self.show_error("No matching games found.", arg_str)
                return
            #print('Result Count: %d' % len(games))
        elapsed = time.time() - start

        # TODO: include overall record, total number of games

        #print('show_result')
        out = tornado.template.Loader('.').load("web/logsearch.html").generate(
            title='Goko Log Search',
            error_text=None,
            elapsed=elapsed,
            games=games,
            search_params=arg_str)
        self.write(out)
        self.finish()

    def parse_supply(self, supply_str):
        out = []
        shelters = False
        colony = False
        error = None

        # Parse supply
        for card in re.split(',', supply_str):
            lcard = card.lower().strip()

            # Goko spells Jack of all Trades strangely
            if lcard.startswith('jack'):
                out.append('JackOfallTrades')

            # Categorical cards: Knights, Ruins
            elif lcard in constants.KNIGHTS:
                out.append('Knights')
            elif lcard in constants.RUINSES:
                out.append('Ruins')

            # Shelters/Colonies have their own search parameters
            elif lcard in constants.SHELTERS:
                shelters = True
            elif lcard in ('colony', 'platinum'):
                colony = True

            # Transland non-supply cards to the cards they imply.
            # Ex: Madman --> Hermit
            # Skip Spoils, which could imply Marauder, Pillage, etc.
            elif lcard in constants.NON_SUPPLY:
                out.append(constants.NON_SUPPLY[card])
            elif lcard == 'spoils':
                error = "Spoils not implemented."
                return

            # Ignore base treasures and VPs
            elif lcard in constants.CORE_CARDS:
                pass

            # Ignore extra commas and blank entries
            elif not lcard:
                pass

            # Ordinary supply cards
            elif lcard in self.supply_cards:
                out.append(lcard)

            # Misspellings
            else:
                error = "Unrecognized card: %s" % card
                return

        return (out, shelters, colony, error)

    def show_error(self, err_text, arg_str):
        #print('show_error')
        out = tornado.template.Loader('.').load("web/logsearch.html").generate(
            title='Goko Log Search',
            search_params=arg_str,
            error_text=err_text,
            games=[])
        self.write(out)
        self.finish()

    def write_error(self, status_code, **kwargs):
        import traceback
        if self.settings.get("debug") and "exc_info" in kwargs:
            exc_info = kwargs["exc_info"]
            trace_info = ''.join(["%s<br/>" % line for line
                                  in traceback.format_exception(*exc_info)])
            request_info = ''.join(["<strong>%s</strong>: %s<br/>" %
                                    (k, self.request.__dict__[k]) for
                                    k in self.request.__dict__.keys()])
            error = exc_info[1]

            self.set_header('Content-Type', 'text/html')
            self.finish("""<html>
                             <title>%s</title>
                             <body>
                                <h2>Error</h2>
                                <p>%s</p>
                                <h2>Traceback</h2>
                                <p>%s</p>
                                <h2>Request Info</h2>
                                <p>%s</p>
                             </body>
                           </html>""" % (error, error,
                                         trace_info, request_info))
