#!/usr/bin/env python

import dbmgr
import sys
import pickle
from datetime import datetime
from skills.elo import EloCalculator
from skills import GameInfo
import math

score = ['w', 'd', 'l']
DEFAULT_MEAN = 1500
WINDOW = 10

startdate = datetime.strptime(sys.argv[1], '%Y%m%d')

#tuples = []

#exp = {}
#ups = {}
#for x in range(0,100):
#    exp[x*WINDOW] = 0
#    ups[x*WINDOW] = 0

#deviance_by_card = {}
#count_by_card = {}

#tkn = 0
#tn = 0

#base = {'Cellar', 'Chapel', 'Moat', 'Chancellor', 'Village', 'Woodcutter',
#'Workshop', 'Bureaucrat', 'Feast', 'Gardens', 'Militia', 'Moneylender',
#'Remodel', 'Smithy', 'Spy', 'Thief', 'Throne Room', 'Council Room',
#'Festival', 'Laboratory', 'Library', 'Market', 'Mine', 'Witch', 'Adventurer'}
#core = {'Copper', 'Silver', 'Gold', 'Platinum', 'Potion', 'Curse', 'Estate',
#'Duchy', 'Province', 'Colony', 'Ruins'}

#try:
#    with open('data.pickle', 'rb') as f:
#        noise_by_card = pickle.load(f)
#except:
#    pass
#
ec = EloCalculator()
pr = {}
for r in dbmgr.fetch_winners_losers(startdate, sys.argv[2] == '100'):
    (p1, rank1, p2, rank2, supply) = r

    supply = supply.split(', ')

    #if len(set(supply) & base) == 10:
    #    continue

    if not p2in pr:
        pr[p2] = DEFAULT_MEAN
    if not p1in pr:
        pr[p1] = DEFAULT_MEAN
    rate1 = pr[p1]
    rate2 = pr[p2]
    adiff = int(abs(rate1 - rate2) / WINDOW) * WINDOW

    if rank1 == 1and rank2 == 2:
        score = 1
        s1 = 0
        s2 = 2
        #if rate1>rate2:
        #    exp[adiff] += 1
        #else:
        #    ups[adiff] += 1
    elif rank1 == 1and rank2 == 1:
        score = .5
        s1 = 1
        s2 = 1
    else:
        assert rank1 == 2and rank2 == 1
        score = 0
        s1 = 2
        s2 = 0
        #if rate2>rate1:
        #    exp[adiff] += 1
        #else:
        #    ups[adiff] += 1

#    try:
#        kingdom_noise = 0
#        kingdom_noise2 = 1
#        kingdom_noise3 = 0
#        sn = 0
#        for card in supply:
#            if card in core:
#                continue
#            sn += 1
#            card_noise = noise_by_card[card]
#            kingdom_noise3+= card_noise
#            kingdom_noise2+= 1/ card_noise
#            kingdom_noise = max(kingdom_noise, card_noise)
#        kingdom_noise2 = 1/ (kingdom_noise2/ sn)
#        kingdom_noise3 = kingdom_noise3/ sn
#
#        tkn += 1/ kingdom_noise2
#        tn += 1
#
#        #print(supply)
#        #print(kingdom_noise)
#
#        #gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3,
#                       DEFAULT_MEAN /6*math.pow(kingdom_noise2/.2798, -1),
#                       DEFAULT_MEAN /300,.1,3)
#        #gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3,
#                       DEFAULT_MEAN /6*math.pow(kingdom_noise2/.48966,10),
#                       DEFAULT_MEAN /300,.1,3)
#        gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3, DEFAULT_MEAN /6,
#                       DEFAULT_MEAN /300,.1,3)
#    except:
#        gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3, DEFAULT_MEAN /6,
#                       DEFAULT_MEAN /300,.1,3)

    gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN / 3, DEFAULT_MEAN / 6,
                  DEFAULT_MEAN / 300, .1, 3)
    #wexp = ec.expected_score(gi, rate1, rate2)
    #if wexp>.99:
    #    wexp = .99
    #elif wexp <.01:
    #    wexp = .01
    #print(rate1, rate2, wexp)
    #dev = - (score*math.log10(wexp) + (1- score)*math.log10(1- wexp))
    #for card in supply:
        #if card in core:
        #    continue
        #if not card in deviance_by_card:
        #    deviance_by_card[card] = 0
        #if not card in count_by_card:
        ##    count_by_card[card] = 0
        #deviance_by_card[card] += dev
        #count_by_card[card] += 1

    new_rate1 = ec.new_rating(gi, rate1, rate2, s1).mean
    new_rate2 = ec.new_rating(gi, rate2, rate1, s2).mean

    #tuples.append((rate1, rate2, supply, score))

    #print("%d - > %d, %d - > %d (%s)" % (rate1, new_rate1, rate2,
    #                                     new_rate2, score[s1]))

    pr[p1] = new_rate1
    pr[p2] = new_rate2

#wp = {}
#for x in range(1,100):
#    if (exp[x*WINDOW] + ups[x*WINDOW] == 0):
#        wp[x*WINDOW] = None
#    else:
#        wp[x*WINDOW] = (exp[x*WINDOW] / (exp[x*WINDOW] + ups[x*WINDOW]))

pranks = {}

sorted_pr = sorted(pr, key=pr.get)
n = 0
for key in sorted_pr:
    n = n + 1
    print("%s - %4.0f" % (key, pr[key]))

#sorted_wp = sorted(wp)
#for key in sorted_wp:
#    print("%s - %0.2f" % (key, wp[key]))
#
#sleep(1000)
#
#total_dev = 0
#total_count = 0
#noise_by_card = {}
#for card in deviance_by_card:
#    noise_by_card[card] = deviance_by_card[card] / count_by_card[card]
#    total_dev += deviance_by_card[card]
#    total_count += count_by_card[card]
#
#mean_dev = total_dev / total_count
#print(total_dev / total_count)
#
#sorted_noise = sorted(noise_by_card, key = noise_by_card.get)
#i = 0
#for key in sorted_noise:
#    #if key in base:
#    #    continue
#    i += 1
#    #print("%02d.%s - %0.3f, %0.3f" \
#           % (i, key, noise_by_card[key] / mean_dev, noise_by_card[key]))
#
##with open('data.pickle', 'wb') as f:
##    pickle.dump(noise_by_card, f, pickle.HIGHEST_PROTOCOL)
#
##print(tkn, tn)
##print(1/ (tkn / tn))
#
##print(tuples)
#
#allcards = deviance_by_card
#
#carddev = {}
#for s in deviance_by_card:
#    carddev[s] = 0
#
#def calc_mdev(tuples, cd):
#    tdev = 0
#    tn = 0
#    for t in tuples:
#        (rate1, rate2, supply, score) = t
#        kd = 0
#        kd2 = 0
#        kd3 = 0
#        kn = 0
#        for c in supply:
#            if c in core:
#                continue
#            kd += cd[c]
#            kd2 = max(kd, cd[c])
#            kd3+= math.exp(cd[c])
#            kn += 1
#        kd = kd / kn
#        kd3 = kd3/ kn
#        #print(kd)
#        #gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3,
#               DEFAULT_MEAN /6*math.exp(kd), DEFAULT_MEAN /300,.1,3)
#        #gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3,
#               DEFAULT_MEAN /6*math.exp(kd /10), DEFAULT_MEAN /300,.1,3)
#        gi = GameInfo(DEFAULT_MEAN, DEFAULT_MEAN /3,
#               DEFAULT_MEAN /6*kd3, DEFAULT_MEAN /300,.1,3)
#        #print(kd2)
#        wexp = ec.expected_score(gi, rate1, rate2)
#        wexp = min(.99, max(.01, wexp))
#        #print(rate1, rate2, wexp)
#        tdev += - (score*math.log10(wexp) + (1- score)*math.log10(1- wexp))
#        tn += 1
#    return tdev / tn
#
#def hashcopy(h):
#    new = {}
#    for x in h:
#        new[x] = h[x]
#    return new
#
#last_mdev = 100
#mdev = calc_mdev(tuples, carddev)
#
#print(mdev)
#
#adj = 5
#while adj>.1:
#    changed = False
#    print(carddev)
#    print(mdev)
#    print(adj)
#    for c in allcards:
#        mdev = calc_mdev(tuples, carddev)
#
#        carddev[c] += adj
#        new_mdev1 = calc_mdev(tuples, carddev)
#
#        carddev[c] -= adj
#        carddev[c] -= adj
#        new_mdev2 = calc_mdev(tuples, carddev)
#
#        if (new_mdev1< new_mdev2) and (new_mdev1< mdev):
#            mdev = new_mdev1
#            carddev[c] += adj
#            carddev[c] += adj
#            changed = True
#        elif (new_mdev2< new_mdev1) and (new_mdev2< mdev):
#            mdev = new_mdev2
#            changed = True
#        else:
#            assert (mdev < = new_mdev1) and (mdev < = new_mdev2)
#            carddev[c] += adj
#    if not changed:
#        adj = adj /2
#
#sorted_noise = sorted(carddev, key = carddev.get)
#i = 0
#for key in sorted_noise:
#    if key in base:
#        continue
#    i += 1
#    print("%02d.%s - %0.2f" % (i, key, carddev[key]))
#
