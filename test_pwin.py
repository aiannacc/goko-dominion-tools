import random
import math

import trueskill

import gdt
import gdt.ratings.gdt_trueskill as ts
import gdt.model.db_manager as dbm

#dominion_env = trueskill.TrueSkill(draw_probability=0.0175, backend='scipy')
#isodominion_env = trueskill.TrueSkill(mu=25, sigma=25, beta=25, tau=25/100, draw_probability=0.05, backend='scipy')

#base_env = trueskill.TrueSkill(beta = 4.166, backend='scipy')
#isotropic_env = trueskill.TrueSkill(beta = 4.166, draw_probability=0.05, backend='scipy')
#aisotropic_env = trueskill.TrueSkill(beta = 4.166, draw_probability=0.0175, backend='scipy')
#
#for env in [base_env, isotropic_env, aisotropic_env]:
#    r1 = trueskill.Rating(0 + env.beta, 0.0001)
#    r2 = trueskill.Rating(0, 0.00001)
#    x = ts.pwin(r1,r2,env=env)
#    y = ts.pwin(r2,r1,env=env)
#    print(x,y,1-x-y)
#    z = trueskill.quality_1vs1(r1, r2, env=env)
#    print(z)
#
#print()

def ts_sim():
    p1mu = 25 + 25/6;
    p2mu = 25

    env = trueskill.TrueSkill(backend='scipy')
    r1 = trueskill.Rating()
    r2 = trueskill.Rating()

    def cycle(r1, r2):
        perf1 = random.gauss(p1mu, env.beta)
        perf2 = random.gauss(p2mu, env.beta)
        margin = env.ppf((env.draw_probability + 1) / 2.) * math.sqrt(2) * env.beta

        drawn = (math.fabs(perf1 - perf2) < margin)
        if perf1 > perf2:
            (r1, r2) = trueskill.rate_1vs1(r1, r2, drawn, env=env)
        else:
            (r2, r1) = trueskill.rate_1vs1(r2, r1, drawn, env=env)
        return (r1, r2)

    meanmu = 0
    meansig = 0
    meanpwin = 0
    lastmu = 0
    lastsig = 0
    lastpwin = 0
    n = 0
    while True:
        (r1, r2) = cycle(r1, r2)
        mudiff = r1.mu - r2.mu
        sigtot = math.sqrt(r1.sigma ** 2 + r2.sigma ** 2)
        pwin = ts.pwin(r1, r2, env=env)

        meanmu = (100 * meanmu - lastmu + mudiff) / 100
        meansig = (100 * meansig - lastsig + sigtot) / 100
        meanpwin = (100 * meanpwin - lastpwin + pwin) / 100
        lastmu = mudiff
        lastsig = sigtot
        lastpwin = pwin

        n += 1
        if n == 100:
            print(100 * meanpwin)
            n = 0

ts_sim()
