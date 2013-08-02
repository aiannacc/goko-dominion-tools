# Genrate TS ratings from scratch

import math
import gdt
import gdt.ratings.gdt_trueskill as ts
from scipy.stats.distributions import norm

def calc_ratings(env):
    (h,r) = ts.generate_ratings(10000000, None, None, False, env)

    #for n in sorted(r, key = lambda n: r[n].mu - 3 * r[n].sigma):
    #    print(n, r[n])

    return (h,r)


def calc_mbd(history, env):
    tbd = 0
    for h in history:
        p = h['old_rating']
        o = h['old_opp_rating']
        #m = p.mu - o.mu
        #s = pow(p.sigma * p.sigma + o.sigma * o.sigma, .5)
        #E = min(.99, max(.01, norm.cdf(m/s)))
        E = ts.pwin(p, o, env)
        E = min(.99, max(.01, E))
        Y = h['score']
        bd = 0 - (Y*math.log(E,10) + (1-Y)*math.log(1-E,10))
        tbd += bd
    return tbd/len(history)


def main():
    #h0 = gdt.model.db_manager.get_ts_rating_history(100)
    (h0, r0) = calc_ratings(ts.isodominion_env)
    (h1, r1) = calc_ratings(ts.dominion_env)
    mbd0 = calc_mbd(h0, ts.isodominion_env)
    mbd1 = calc_mbd(h1, ts.dominion_env)
    print(mbd0)
    print(mbd1)
    #return (h0, r0, mbd0, h1, r1, mbd1)

    return NotImplemented     


if __name__ == '__main__':
    main()
