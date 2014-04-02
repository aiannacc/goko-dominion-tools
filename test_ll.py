import trueskill
import postgresql
import math
#import skills
#from skills import elo
import scipy.optimize
from trueskill import Rating

from gdt.model import db_manager
from gdt.ratings.result import Result

dougzmod_env = trueskill.TrueSkill(
    mu=25,
    sigma=25/3,
    beta=25,
    tau=25/100,
    draw_probability=0.0175,
    backend='scipy')

dougzmod_env2 = trueskill.TrueSkill(
    mu=25,
    sigma=25/3,
    beta=25,
    tau=25/100,
    draw_probability=0.0175,
    backend='scipy')

dougz_env = trueskill.TrueSkill(
    mu=25,
    sigma=25,
    beta=25,
    tau=25/100,
    draw_probability=0.05,
    backend='scipy')

isotropish_env = trueskill.TrueSkill(
    mu=25,
    sigma=25/3,
    beta=25/6,
    tau=25/300,
    draw_probability=0.0175,
    backend='scipy')

goko_env1 = trueskill.TrueSkill(
    mu=5500,
    sigma=2250,
    beta=1375,
    tau=27.5,
    draw_probability=0.05,
    backend='scipy')

goko_env2 = trueskill.TrueSkill(
    mu=5500,
    sigma=2250,
    beta=1375,
    tau=27.5,
    draw_probability=0.0175,
    backend='scipy')

def run_frequent_ll(skipcount):
    _con = postgresql.open(user='ai', host='localhost', database='goko')

    #env1 = isotropish_env
    #draw_margin1 = trueskill.calc_draw_margin(0.0175, 2, env1)

    env1 = dougzmod_env
    draw_margin1 = trueskill.calc_draw_margin(0.0175, 2, env1)

    #env2 = goko_env
    #draw_margin2 = trueskill.calc_draw_margin(0.05, 2, env2)

    env2 = dougz_env
    draw_margin2 = trueskill.calc_draw_margin(0.05, 2, env2)

    ps = _con.prepare("""SELECT time, logfile, p1name, p2name, p1score
                           FROM res2p2""")

    #ps = _con.prepare("""
    #  SELECT time, logfile, p1name, p2name, p1score
    #    FROM res2p_many
    #   WHERE NOT p1name IN ('Conqueror Bot', 'Lord Bottington', 'Banker Bot',
    #                  'Defender Bot', 'Villager Bot')
    #     AND NOT p2name IN ('Conqueror Bot', 'Lord Bottington', 'Banker Bot',
    #                  'Defender Bot', 'Villager Bot')""")

    r1 = {}
    r2 = {}
    last_time = {}
    n = {}
    total_ll1 = 0
    total_ll2 = 0
    total_count = 0
    i = 0

    for row in ps():
        (time, logfile, p1name, p2name, p1score) = row

        # Initialize or look up ratings if necessary
        for pname in (p1name, p2name):
            if not pname in r1:
                r1[pname] = env1.create_rating()
                r2[pname] = env2.create_rating()
                n[pname] = 0

        ## Decay 1% per day (apply continuously)
        ## Apply only to the first system
        #if p1name in last_time:
        #    td = (time-last_time[p1name])
        #    elapsed = td.days + td.seconds/(3600*24)
        #    r1[p1name] = Rating(r1[p1name].mu,
        #                        r1[p1name].sigma*(1.01**elapsed))
        #if p2name in last_time:
        #    td = (time-last_time[p2name])
        #    elapsed = td.days + td.seconds/(3600*24)
        #    r1[p2name] = Rating(r1[p2name].mu,
        #                        r1[p2name].sigma*(1.01**elapsed))

        # Update total log likelihood metric
        res1 = Result(r1[p1name], r1[p2name], env1, p1score, draw_margin1)
        res2 = Result(r2[p1name], r2[p2name], env2, p1score, draw_margin2)

        #if p1name == 'Serf Bot':
            #print('SB: %7.2f +/- %5.f' % (res1.r1.mu, res1.r1.sigma))

        i += 1
        if i > skipcount:
            total_ll1 += res1.calc_ll()
            total_ll2 += res2.calc_ll()
            total_count += 1

        # Update ratings
        old11 = r1[p1name]
        old12 = r1[p2name]
        old21 = r2[p1name]
        old22 = r2[p2name]
        (r1[p1name], r1[p2name]) = Result(r1[p1name], r1[p2name], 
                                          env1, p1score, draw_margin1).post_game_ratings()
        (r2[p1name], r2[p2name]) = Result(r2[p1name], r2[p2name], 
                                          env2, p1score, draw_margin2).post_game_ratings()
        n[p1name] = n[p1name] + 1
        n[p2name] = n[p2name] + 1
        #print("%3.1f %5.2f %5.2f %5.2f %5.2f" % (p1score, old11.mu,
        #                                         r1[p1name].mu, old12.mu,
        #                                         r1[p2name].mu))
        #print("%3.1f %5.2f %5.2f %5.2f %5.2f" % (p1score, old21.mu,
        #                                         r2[p1name].mu, old22.mu,
        #                                         r2[p2name].mu))
        #print(p1score, old11.sigma, r1[p1name].sigma, old12.sigma,
        #r1[p2name].sigma)

        if total_count > 0 and (total_count % 1000) == 0:
            print(total_count)

        if total_count > 0 and (total_count % 100) == 0:
            print('%6.4f %6.4f' % (total_ll1/total_count,
                                   total_ll2/total_count))
        
        last_time[p1name] = time
        last_time[p2name] = time


def misc_checks():
    rX = Rating(6801, 265)
    #rA = Rating(10000, 20) 
    rB = Rating(1176, 280)
    print(rX)
    print(rX.mu - 2 * rX.sigma)

    #dm = trueskill.calc_draw_margin(0.05, 2, goko_env1)
    #res1 = Result(rX, rA, goko_env1, 1, dm)
    #(rX, rA) = res1.post_game_ratings()
    #print(rX.mu - 2 * rX.sigma)

    dm = trueskill.calc_draw_margin(0.05, 2, goko_env1)
    res1 = Result(rX, rB, goko_env1, 1, dm)
    (rX, rB) = res1.post_game_ratings()
    print(rX)
    print(rX.mu - 2 * rX.sigma)


if __name__ == '__main__':
    #run_frequent_ll(0)
    misc_checks()
