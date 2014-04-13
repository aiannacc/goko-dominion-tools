import sys
import datetime
import logging
import trueskill
import time
import random

import gdt.ratings.update as x
import gdt.ratings.rating_system as rs
from gdt.ratings.rating_system import isotropish_variant
from gdt.model.domgame import GameRanks
from gdt.ratings.history import RatingHistory
from gdt.ratings.history import RatingAnalysis

from gdt.model import db_manager

LOGLEVEL = logging.DEBUG

logger = logging.getLogger('logwatcher')
logger.setLevel(LOGLEVEL)
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL)
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(ch)


isotropish = RatingAnalysis(rs.isotropish)
dougz = RatingAnalysis(rs.dougz)
goko = RatingAnalysis(rs.goko_variant(''))


def level(tsrating, k):
    return tsrating.mu - k * tsrating.sigma


def match_until_even(r_hi, r_lo, k, sys, lo_winrate, num_repeat=1):
    if num_repeat == 1:
        i = 0
        #print(level(r_hi, k), level(r_lo, k))
        while level(r_hi, k) > level(r_lo, k):
            score = (0 if lo_winrate > random.random() else 1)
            (r_hi, r_lo) = sys.rate2p(r_hi, r_lo, score)
            #print(level(r_hi, k), level(r_lo, k))
            i += 1
        return i
    else:
        total = 0
        for j in range(num_repeat):
            total += match_until_even(r_hi, r_lo, k, sys, lo_winrate, 1)
        return total / num_repeat

def print_matcheven(r_hi, r_lo, k, sys, lo_winrate, num_repeat=1):
    print('%s - %6.2f vs %6.2f: %d games' %
          (sys.name, level(r_hi, k), level(r_lo, k),
           match_until_even(r_hi, r_lo, 2, sys, lo_winrate, num_repeat)))


if __name__ == '__main__':
    goko = rs.goko
    isotropish = rs.isotropish

    goko1 = trueskill.Rating(7296.412290438991, 273.36108768114735)
    goko10 = trueskill.Rating(6981.488163335486, 267.4413376586472)
    goko50 = trueskill.Rating(6456.236285716229, 280.53213483835697)
    goko100 = trueskill.Rating(6243.602006182668, 285.9582322236868)

    isotropish1 = trueskill.Rating(61.9297, 3.3785)
    isotropish10 = trueskill.Rating(57.1281, 3.3337)
    isotropish50 = trueskill.Rating(51.6863, 3.3730)
    isotropish100 = trueskill.Rating(48.6080, 3.3198)

    print(goko.predict_score(goko100, goko10))
    print(goko.predict_score(isotropish100, isotropish10))

    #print_matcheven(goko1, goko50, 2, goko, 1)
    #print_matcheven(goko1, goko10, 2, goko, 1)
    #print_matcheven(goko1, goko100, 2, goko, 1)
    print_matcheven(goko10, goko50, 2, goko, 1)
    print_matcheven(goko10, goko100, 2, goko, 1)
    print_matcheven(goko50, goko100, 2, goko, 1)

    #print_matcheven(isotropish1, isotropish50, 3, isotropish, 1)
    #print_matcheven(isotropish1, isotropish10, 3, isotropish, 1)
    #print_matcheven(isotropish1, isotropish100, 3, isotropish, 1)
    print_matcheven(isotropish10, isotropish50, 3, isotropish, 1)
    print_matcheven(isotropish10, isotropish100, 3, isotropish, 1)
    print_matcheven(isotropish50, isotropish100, 3, isotropish, 1)


    # Input:
    # print('Goko - %d vs %d: %d games' %
    #       (goko1, goko50, match_until_even(goko1, goko50, 2, goko, 1, 1)))
    # print('Goko - %d vs %d: %d games' %
    #       (goko1, goko100, match_until_even(goko1, goko100, 2, goko, 1, 1)))
    # print('Isotropish - %d vs %d: %d games' %
    #       (isotropish1, isotropish50,
    #        match_until_even(isotropish1, isotropish50, 2, isotropish, 1, 1)))
    # print('Isotropish - %d vs %d: %d games' %
    #       (isotropish1, isotropish100,
    #        match_until_even(isotropish1, isotropish100, 2, isotropish, 1, 1)))
    
    # Output:
    # Goko - 7939 vs 7270: 10 games
    # Goko - 7939 vs 7021: 13 games
    # Isotropish - 61 vs 51: 18 games
    # Isotropish - 61 vs 48: 22 games
