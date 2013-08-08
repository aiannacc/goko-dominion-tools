# Base modules
import re
import datetime
import sys

# Project modules
from gdt.model import db_manager
from gdt.model.constants import *
from gdt.model.domgame import GameResult
from gdt.model.domgame import PlayerResult
from gdt.model.domgame import GainRet

# Regular expressions used to parse goko logs.  Precompiled for speed.
RE_RATING = re.compile('Rating system: (.*)')
RE_SUPPLY = re.compile('[sS]upply cards: (.*)')
RE_COMMA = re.compile(', ')
RE_STARTC = re.compile('(.*) - starting cards: (.*)')
RE_TURNX = re.compile('--* (.*): turn ([0-9]*) ([posessed] )?--*')
RE_GAINS = re.compile('(.*) \- gains (.*)')
RE_RETS = re.compile('(.*) \- returns (.*) to')
RE_VPS = re.compile('(.*) - total victory points: (-?\d*)')
RE_NTURNS = re.compile('(.*) - turns: (\d*)')
RE_QUIT = re.compile('(.*) - quit')
RE_RESIGN = re.compile('(.*) - resigned')
RE_PLACE = re.compile('([0-9]).. place: (.*)')
RE_GUEST = re.compile('/i^guest[._]?[0-9]*')
RE_GAMEOVER = re.compile('--* Game Over --*')

# TODO: fix this
# advopps = db_manager.get_advbot_names()
advopps = []


class WrongPlacesException(Exception):
    pass


class TurnCountException(Exception):
    pass


class ParseException(Exception):
    pass


def scores_to_ranks(scores):
    ranks = [0] * len(scores)
    for i in range(len(scores)):
        larger = set()
        for j in range(len(scores)):
            if scores[j] > scores[i]:
                larger.add(scores[j])
        ranks[i] = len(larger) + 1
    return(ranks)


# Parse a game log.  Create and return the resulting GameResult object
def parse_goko_log(logtext):

    # First just sort the log lines.  This doubles the regex matching we have
    # to do, but it keeps the code cleaner.
    supplyl, ratingl = (None, None)
    startcl, turnl, gainl, retl = ([], [], [], [])
    vpl, nturnl, quitl, placel = ([], [], [], [])
    resignl = []
    gains = []
    rets = []

    cur_turn = None
    cur_player = None

    first_quit_line = None
    game_over_line = None
    line_number = 0
    for line in logtext.split('\n'):
        line_number += 1

        m = RE_SUPPLY.match(line)
        if m:
            supplyl = m
            continue
        m = RE_RATING.match(line)
        if m:
            ratingl = m
            continue
        m = RE_STARTC.match(line)
        if m:
            startcl.append(m)
            continue
        m = RE_TURNX.match(line)
        if m:
            turnl.append(m)
            if not m.group(3):
                cur_player = m.group(1)
                cur_turn = int(m.group(2))
            continue
        m = RE_GAINS.match(line)
        if m:
            pname = m.group(1)
            cname = m.group(2)
            if cname in RUINSES:
                cpile = 'Ruins'
            elif cname in KNIGHTS:
                cpile = 'Knight'
            else:
                cpile = cname
            gains.append(GainRet(cname, cpile, cur_player, cur_turn))
            continue
        m = RE_RETS.match(line)
        if m:
            pname = m.group(1)
            cname = m.group(2)
            if cname in RUINSES:
                cpile = 'Ruins'
            elif cname in KNIGHTS:
                cpile = 'Knight'
            else:
                cpile = cname
            rets.append(GainRet(cname, cpile, cur_player, cur_turn))
            continue
        m = RE_VPS.match(line)
        if m:
            vpl.append(m)
            continue
        m = RE_NTURNS.match(line)
        if m:
            nturnl.append(m)
            continue
        m = RE_RESIGN.match(line)
        if m:
            resignl.append(m)
            continue
        m = RE_QUIT.match(line)
        if m:
            quitl.append(m)
            first_quit_line = (first_quit_line
                               if first_quit_line
                               else line_number)
            continue
        m = RE_GAMEOVER.match(line)
        if m:
            game_over_line = line_number
            continue
        m = RE_PLACE.match(line)
        if m:
            placel.append(m)
            continue

    # Game data to be parsed
    supply = []       # List of supply cards
    rating = None     # Rating system used, if available
    presults = {}       # player name --> player game info

    # Game metadata to be parsed
    shelters = False
    guest = False
    bot = False
    pCount = 0
    colony = False
    adventure = False

    ## PRE-GAME SETUP ###

    # Parse supply
    for cname in RE_COMMA.split(supplyl.group(1)):
        if cname in RUINSES:
            cname = 'Ruins'
        elif cname in KNIGHTS:
            cname = 'Knight'
        if cname == 'Colony':
            colony = True
        supply.append(cname)

    # Parse rating system (not available for pre-May logs)
    if ratingl:
        rating = ratingl.group(1)

    # Parse various info from each player's starting cards
    # NOTE: Names are ordered alphabetically, not by order of play
    for m in startcl:
        pname = m.group(1)
        scards = RE_COMMA.split(m.group(2))

        # Count number of players
        pCount += 1

        # Determine whether a guest is playing
        if RE_GUEST.match(pname):
            guest = True

        # Determine whether a bot is playing
        for bname in BOT_NAMES:
            if pname.startswith(bname):
                bot = True

        # Determine whether this is an adventure
        if pname in advopps:
            adventure = True

        # Determine shelters or estates
        if len(set(['Hovel', 'Overgrown Estate', 'Necropolis']) & set(scards)):
            shelters = 1

        # Don't parse games with duplicate bot names
        if pname in presults:
            raise ParseException('Duplicate name: %s' % (pname))
        else:
            presults[pname] = PlayerResult(pname)

    ## GAME TURNS ##
    #
    # Parse turn numbers to obtain player names, order, and turns taken
    iOrder = 0
    for m in turnl:
        pname = m.group(1)
        turn_num = int(m.group(2))
        presults[pname].turns = turn_num
        iOrder += 1
        presults[pname].order = iOrder

    ## POST GAME ##

    # Total VPs
    for m in vpl:
        pname = m.group(1)
        vps = int(m.group(2))
        presults[pname].vps = vps

    # Parse resignations
    someoneResigned = False
    for m in resignl:
        pname = m.group(1)
        presults[pname].resign = True
        someoneResigned = True

    # Parse quits
    someoneQuit = False
    for m in quitl:
        pname = m.group(1)
        presults[pname].quit = True
        someoneQuit = True

    # Number of turns taken
    for m in nturnl:
        pname = m.group(1)
        turns = int(m.group(2))
        p = presults[pname]
        if not turns == p.turns:
            # Note: Goko counts turns incorrectly sometimes, and i can't figure
            # out why. I'm ignoring their count and using my own.
            pass

            # My past notes/code on the same error:
            # Note: Goko counts turns incorrectly with outpost.  This may have
            # led to some incorrect game results.  I'm ignoring it.
            #if (someoneQuit or someoneResigned or ('Outpost' in supply)):
            #    p.turns = turns
            #else:
            #    #print(someoneQuit)
            #    #print(someoneResigned)
            #    raise TurnCountException()

    # Calculate players' places/ranks
    # Note: I'm counting on there having been fewer than 1000 turns and
    #       no more than 99 curses (or other negative VPs). :)
    pnames = []
    scores = []
    for pname in presults:
        p = presults[pname]
        score = p.vps*1000 - p.turns  # Account for vps and turns taken
        if presults[pname].quit or presults[pname].resign:
            score = -99999
        pnames.append(pname)
        scores.append(score)
    ranks = scores_to_ranks(scores)
    for i in range(len(pnames)):
        presults[pnames[i]].rank = ranks[i]

    # Search & verify places/ranks. There are many ways that Goko screws up
    # ranking at the end of the game. I'm trusting my own rankings over theirs
    # whenever I can roughly determine that the error is one that they make
    # consistently.
    for m in placel:
        pname = m.group(2)
        place = int(m.group(1))
        if (presults[pname].rank != place):
            if presults[pname].rank != place:
                if (len(placel) > pCount):
                    # Ignore a Goko bug where player ranks were listed twice
                    # (with different results)
                    print('Places listed twice.')
                elif (first_quit_line == game_over_line + 1):
                    # Ignore a Goko bug where the "quit" shows up after the
                    # game over log messages
                    print('Playerquit-gameend race condition.')
                elif someoneQuit and len(presults) >= 3:
                    # Ignore a Goko bug where a player quitting screws up the
                    # ordering of the other players
                    print('Quit screwed up opponent rankings')
                elif presults[pname].turns < 2:
                    # Ignore a Goko bug where games that never really start end
                    # up with the wrong places.
                    print('Wrong rankings in <2 turn game')
                else:
                    print(presults)
                    print(pname, place)
                    raise WrongPlacesException()

    return GameResult(supply, gains, rets, rating, shelters, guest, bot,
                      pCount, colony, presults, adventure)

# For testing
# Usage: ./gokoparse.py [logfile]
if __name__ == "__main__":
    #x = scores_to_ranks([1, 4, 3, 3])
    #print(x)
    logfile = sys.argv[-1]
    g = parse_goko_log(open(logfile).read())
    print(g)
