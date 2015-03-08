#!/usr/bin/env python

import datetime
import pytz
import math
import trueskill

import tornado.web
import tornado.template

from ..model import db_manager
import gdt.ratings.rating_system3 as rs

goko = rs.TrueSkillSystem('Goko', mu=5500, sigma=2250, beta=1375,
                          tau=27.5, draw_probability=0.05, k=2,
                          daily_sigma_decay=0.01)

isotropish = rs.TrueSkillSystem('Isotropish', mu=25, sigma=25, beta=25,
                                tau=0.25, draw_probability=0.05, k=3)

class GokoProRatingQuery(tornado.web.RequestHandler):
    def new_goko_rating(self, r_a, d_a, r_b, score_a):
        (r_a2, r_b2) = goko.rate2p(r_a, r_b, score_a)
        d_a2 = max(0, int(r_a2.mu - 2 * r_a2.sigma))
        if score_a == 1 and d_a > d_a2:
            delta = 0
        else:
            delta = d_a2 - d_a
        return {
            'mu': r_a2.mu,
            'sigma': r_a2.sigma,
            'displayed': d_a2,
            'delta': delta
        }

    def get(self):
        print('Received goko pro rating query')

        query_type = self.get_argument('query_type')

        if (query_type == 'rating_list'):
            ratings = db_manager.fetch_all_pro_ratings()
            self.write({'ratings': ratings})

        elif (query_type == 'player_rating'):
            player_id = self.get_argument('player_id')
            r = db_manager.fetch_pro_rating(player_id)
            (m, s, d) = r
            self.write({
                'mu': m,
                'sigma': s,
                'displayed': d
            })

        elif (query_type == 'probabilities'):
            player_id_A = self.get_argument('player_id_A')
            (m, s, d_a) = db_manager.fetch_pro_rating(player_id_A)
            r_a = trueskill.Rating(m, s)

            player_id_B = self.get_argument('player_id_B')
            (m, s, d_b) = db_manager.fetch_pro_rating(player_id_B)
            r_b = trueskill.Rating(m, s)

            pgwin = goko.win_prob(r_a, r_b)
            pgloss = goko.win_prob(r_b, r_a)
            pgdraw = 1 - pgwin - pgloss

            player_name_A = self.get_argument('player_name_A')
            r_a = db_manager.fetch_ts2_rating(player_name_A, 'isotropish_nobots')

            player_name_B = self.get_argument('player_name_B')
            r_b = db_manager.fetch_ts2_rating(player_name_B, 'isotropish_nobots')

            piwin = isotropish.win_prob(r_a, r_b)
            piloss = isotropish.win_prob(r_b, r_a)
            pidraw = 1 - piwin - piloss

            p = {
                'isotropish': {
                    'p1win': piwin,
                    'draw': pidraw,
                    'p1loss': piloss
                },
                'goko': {
                    'p1win': pgwin,
                    'draw': pgdraw,
                    'p1loss': pgloss 
                }
            };
            self.write({'probs': p})

        elif (query_type == 'record'):
            pnameA = self.get_argument('player_name_A')
            pnameB = self.get_argument('player_name_B')
            self.write(db_manager.get_heads_up_record(pnameA, pnameB))

        elif (query_type == 'assess'):
            player_id_A = self.get_argument('player_id_A')
            (m, s, d_a) = db_manager.fetch_pro_rating(player_id_A)
            r_a = trueskill.Rating(m, s)

            player_id_B = self.get_argument('player_id_B')
            (m, s, d_b) = db_manager.fetch_pro_rating(player_id_B)
            r_b = trueskill.Rating(m, s)

            self.write({
                'a_win': {
                    'r_a': self.new_goko_rating(r_a, d_a, r_b, 1),
                    'r_b': self.new_goko_rating(r_b, d_b, r_a, 0),
                },
                'a_draw': {
                    'r_a': self.new_goko_rating(r_a, d_a, r_b, 0.5),
                    'r_b': self.new_goko_rating(r_b, d_b, r_a, 0.5),
                },
                'a_loss': {
                    'r_a': self.new_goko_rating(r_a, d_a, r_b, 0),
                    'r_b': self.new_goko_rating(r_b, d_b, r_a, 1),
                }
            })
        self.flush()
        self.finish()
