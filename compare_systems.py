import sys
import datetime
import logging
import trueskill
import time

import gdt.ratings.update as x
import gdt.ratings.rating_system as rs
from gdt.ratings.rating_system import isotropish_variant
from gdt.model.domgame import GameRanks
from gdt.ratings.history import RatingHistory
from gdt.ratings.history import RatingAnalysis

logging.basicConfig(level=logging.INFO)

isotropish = RatingAnalysis(rs.isotropish)
isotweak = RatingAnalysis(rs.iso_tweak1)
dougz = RatingAnalysis(rs.dougz)
dougz_nd = RatingAnalysis(rs.dougz_nodecay)
dougz_od = RatingAnalysis(rs.dougz_only_decay)
elo = RatingAnalysis(rs.default_elo)
default_ts = RatingAnalysis(rs.default_ts)

gokohb = RatingAnalysis(rs.gokohb)
goko = RatingAnalysis(rs.goko)
goko2b = RatingAnalysis(rs.goko2b)
goko4b = RatingAnalysis(rs.goko4b)
goko8b = RatingAnalysis(rs.goko8b)

isotropish_50b = RatingAnalysis(
    isotropish_variant('50% beta', beta_multiplier=0.50))
isotropish_150b = RatingAnalysis(
    isotropish_variant('150% beta', beta_multiplier=1.50))
isotropish_200b = RatingAnalysis(
    isotropish_variant('200% beta', beta_multiplier=2.00))
isobetavars = [isotropish_50b, isotropish, isotropish_150b, isotropish_200b]

(lf, t) = (None, None)
for i in range(2000):
    print(i, datetime.datetime.now())
    time.sleep(.5)
    print('Next')

    x.rate_games_since(t, lf, isobetavars,
                       #chunk_size=sys.maxsize, max_games=sys.maxsize,
                       chunk_size=100000, max_games=50000,
                       allow_guests=False, include_unknown_rs=False,
                       only_2p_games=True, min_turns=1)
    #x.record_ratings(isotropish, 'elo')
    #x.record_ratings(isotropish, 'isotropish_analysis')
    #x.record_ratings(isotweak, 'isotweak_analysis')
    (lf, t) = isotropish.get_latest_game()

    #x.rate_games_since(t, lf, [gokohb, goko, goko2b, goko4b, goko8b],
    #                   #chunk_size=sys.maxsize, max_games=sys.maxsize,
    #                   chunk_size=100000, max_games=50000,
    #                   allow_guests=True, include_unknown_rs=False,
    #                   only_2p_games=False, min_turns=0)

    #(lf, t) = goko.get_latest_game()
    #x.record_ratings(gokohb, 'gokohb')
    #x.record_ratings(goko, 'goko')
    #x.record_ratings(goko2b, 'goko2b')
    #x.record_ratings(goko4b, 'goko4b')
    #x.record_ratings(goko8b, 'goko8b')

    #x.record_ratings(dougz, 'dougz_analysis')
    #x.record_ratings(dougz_od, 'dougz_od_analysis')

    print('Last game time %s' % t)

    for ra in isobetavars:
        print(ra.print_analysis())
