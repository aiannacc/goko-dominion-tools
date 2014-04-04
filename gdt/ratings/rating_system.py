import math
import random
import trueskill


# An abstract 2-player rating system
# TODO: cache results for faster repeat lookups?
class RatingSystem():
    def __init__(self, name):
        self.name = name

    def predict_score(self, r_a, r_b):
        return NotImplemented

    def decay(self, r, elapsed_days):
        return r

    def rate(self, r_a, r_b, score):
        """ New ratings from old ratings, game result, and days elapsed """
        return NotImplemented

    def as_scalar(self, r):
        return NotImplemented

    def new_player_rating(self):
        return NotImplemented


class NoiseSystem(RatingSystem):
    """ Predict game results randomly """

    def __init__(self, name, draw_probability):
        super(NoiseSystem, self).__init__(name)
        self.draw_bound_min = 0.5 - 0.5 * draw_probability
        self.draw_bound_max = 0.5 + 0.5 * draw_probability

    def new_player_rating(self):
        return 0

    def rate(self, r_a, r_b, score):
        return (0, 0)

    def as_scalar(self, r):
        return r

    def predict_score(self, r_a, r_b):
        s = random.random()
        if s > self.draw_bound_max:
            return 1
        elif s > self.draw_bound_min:
            return 0.5
        else:
            return 0


# TODO: Consider implementing variable k's, as used by FIDE and USCF
class LogisticEloSystem(RatingSystem):
    def __init__(self, name, scale=400, k=15):
        """ Common defaults are scale = 400, k = 15 """
        super(LogisticEloSystem, self).__init__(name)
        self.scale = scale
        self.k = k

    def new_player_rating(self):
        """ Common default is 1500 """
        return 1500

    def predict_score(self, r_a, r_b):
        """ Elo cannot distinguish win/tie probabilities; only total score """
        q_a = 10**(r_a / self.scale)
        q_b = 10**(r_b / self.scale)
        return q_a / (q_a + q_b)

    def as_scalar(self, r):
        return r

    def rate(self, r_a, r_b, score):
        e = self.predict_score(r_a, r_b)
        d = self.k * (float(score) - e)
        return (r_a + d, r_b - d)


class TrueSkillSystem(RatingSystem):
    """ Microsoft TrueSkill as implemented by the PyPi package "trueskill",
        available at trueskill.org
    """
    def __init__(self, name, trueskill_env, daily_sigma_decay=0):
        super(TrueSkillSystem, self).__init__(name)
        self.env = trueskill_env
        self.daily_sigma_decay = daily_sigma_decay
        self.draw_margin = trueskill.calc_draw_margin(
            self.env.draw_probability, 2, env=self.env)

    def new_player_rating(self):
        return trueskill.Rating(self.env.mu, self.env.sigma)

    def win_prob(self, r_a, r_b):
        deltaMu = r_a.mu - r_b.mu - self.draw_margin
        rsss = (r_a.sigma**2 + r_b.sigma**2 + 2 * self.env.beta**2)**(0.5)
        return self.env.cdf(deltaMu/rsss)

    def decay(self, r, elapsed_days=None):
        if elapsed_days is None:
            return r
        else:
            s = r.sigma * (1 + self.daily_sigma_decay)**elapsed_days
            return trueskill.Rating(r.mu, s)

    def as_scalar(self, r):
        return r.mu

    def predict_score(self, r_a, r_b):
        p_a = self.win_prob(r_a, r_b)
        p_b = self.win_prob(r_b, r_a)
        return (0.5) * (1 + p_a - p_b)

    def rate(self, r_a, r_b, score):
        if score == 1:
            return trueskill.rate_1vs1(r_a, r_b, env=self.env)
        elif score == 0:
            return reversed(self.rate(r_b, r_a, 1))
        elif score == 0.5:
            return trueskill.rate_1vs1(r_a, r_b, env=self.env, drawn=True)
        else:
            raise 'Illegal score value: %s' % (score)

# Specific systems of note
goko = TrueSkillSystem('Goko TS', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=1375, tau=27.5,
    draw_probability=0.05, backend='scipy'))

goko_fixed_draw = TrueSkillSystem('Goko TS', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=1375, tau=27.5,
    draw_probability=0.0175, backend='scipy'))

dougz = TrueSkillSystem('dougz TS', trueskill.TrueSkill(
    mu=25, sigma=25, beta=25, tau=25/100,
    draw_probability=0.05, backend='scipy'))

dougz_decayed = TrueSkillSystem('dougz decay TS', trueskill.TrueSkill(
    mu=25, sigma=25, beta=25, tau=25/100,
    draw_probability=0.05, backend='scipy'),
    daily_sigma_decay=0.01)

dougz_tweaked = TrueSkillSystem('dougz tweak TS', trueskill.TrueSkill(
    mu=25, sigma=25/3, beta=25, tau=25/300,
    draw_probability=0.0175, backend='scipy'))
