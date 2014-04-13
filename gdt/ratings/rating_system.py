import math
import random
import trueskill


# TODO: Implement some unit tests

# An abstract 2-player rating system
# TODO: cache results for faster repeat lookups?
class RatingSystem():
    def __init__(self, name):
        self.name = name

    def predict_score(self, r_a, r_b):
        return NotImplemented

    def decay(self, r, elapsed_days):
        return r

    def rate2p(self, r_a, r_b, score):
        return NotImplemented

    def rate(self, ratings, ranks):
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

    def rate2p(self, r_a, r_b, score):
        return (r_a, r_b)

    def rate(self, ratings, ranks):
        return ratings

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

    def rate2p(self, r_a, r_b, score):
        e = self.predict_score(r_a, r_b)
        d = self.k * (float(score) - e)
        return (r_a + d, r_b - d)

    def rate(self, ratings, ranks):
        if len(ratings) == 2:
            (r_a, r_b) = ratings
            score_a = 0.5 + 0.5 * (ranks[1] - ranks[0])
            (r_a2, r_b2) = self.rate2p(r_a, r_b, score_a)
            return [r_a2, r_b2]
        else:
            raise '3+ player games not implemented for Elo'


class NoisyEloSystem(LogisticEloSystem):
    def __init__(self, name, scale=400, k=15, noise_factor=0.1):
        """ Common defaults are scale = 400, k = 15 """
        super(NoisyEloSystem, self).__init__(name, scale=scale, k=k)
        self.noise_factor = noise_factor

    def rate2p(self, r_a, r_b, score):
        (r_a2, r_b2) = super(NoisyEloSystem, self).rate2p(r_a, r_b, score)
        rand_a = 2*self.noise_factor*(random.random()-0.5) * (r_a2 - r_a)
        rand_b = 2*self.noise_factor*(random.random()-0.5) * (r_b2 - r_b)
        return (r_a2 + rand_a, r_b2 + rand_b)

    def rate(self, ratings, ranks):
        if len(ratings) == 2:
            (r_a, r_b) = ratings
            score_a = 0.5 + 0.5 * (ranks[1] - ranks[0])
            (r_a2, r_b2) = self.rate2p(r_a, r_b, score_a)
            return [r_a2, r_b2]
        else:
            return ratings


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

    def rate2p(self, r_a, r_b, score):
        if score == 1:
            return trueskill.rate_1vs1(r_a, r_b, env=self.env)
        elif score == 0:
            return reversed(self.rate2p(r_b, r_a, 1))
        elif score == 0.5:
            return trueskill.rate_1vs1(r_a, r_b, env=self.env, drawn=True)
        else:
            raise 'Illegal score value: %s' % (score)

    def rate(self, ratings, ranks):
        groups = [tuple([r]) for r in ratings]
        groups2 = self.env.rate(groups, ranks)
        out = []
        for g in groups2:
            out.append(g[0])
        return out


class NoisyTrueSkillSystem(TrueSkillSystem):
    def __init__(self, name, trueskill_env, daily_sigma_decay=0,
                 noise_factor=0):
        super(NoisyTrueSkillSystem, self).__init__(
            name, trueskill_env, daily_sigma_decay=daily_sigma_decay)
        self.noise_factor = noise_factor

    def rate2p(self, r_a, r_b, score):
        (r_a2, r_b2) = super(NoisyTrueSkillSystem, self).rate2p(r_a, r_b, score)
        rand_a = 2*self.noise_factor*(random.random()-0.5) * (r_a2.mu - r_a.mu)
        rand_b = 2*self.noise_factor*(random.random()-0.5) * (r_b2.mu - r_b.mu)
        r_a2 = trueskill.Rating(r_a2.mu + rand_a, r_a2.sigma)
        r_b2 = trueskill.Rating(r_b2.mu + rand_b, r_b2.sigma)
        return (r_a2, r_b2)

    def rate(self, ratings, ranks):
        ratings2 = super(NoisyTrueSkillSystem, self).rate(ratings, ranks)
        for i in range(len(ratings2)):
            r = ratings[i]
            r2 = ratings2[i]
            z = random.random()         # Uniform from [0,1)
            c = self.noise_factor
            rand = 2 * c * (z - 0.5) * (r2.mu - r.mu)
            ratings2[i] = trueskill.Rating(r2.mu + rand, r2.sigma)
        return ratings2


class BoundedTrueSkillSystem(TrueSkillSystem):

    def __init__(self, name, trueskill_env, daily_sigma_decay=0,
                 mu_lower_bound=0):
        super(BoundedTrueSkillSystem, self).__init__(
            name, trueskill_env, daily_sigma_decay=daily_sigma_decay)
        self.mu_lower_bound = mu_lower_bound

    def rate2p(self, r_a, r_b, score):
        (r_a2, r_b2)\
            = super(BoundedTrueSkillSystem, self).rate2p(r_a, r_b, score)
        if r_a2.mu < self.mu_lower_bound:
            r_a2 = trueskill.Rating(self.mu_lower_bound, r_a2.sigma)
        if r_b2.mu < self.mu_lower_bound:
            r_b2 = trueskill.Rating(self.mu_lower_bound, r_b2.sigma)
        return (r_a2, r_b2)

    def rate(self, ratings, ranks):
        ratings2 = super(BoundedTrueSkillSystem, self).rate(ratings, ranks)
        for i in range(len(ratings2)):
            if ratings2[i].mu < self.mu_lower_bound:
                ratings2[i] = trueskill.Rating(self.mu_lower_bound,
                                               ratings2[i].sigma)
        return ratings2


### Specific systems of note

# Goko Pro TrueSkill implementation
gokohb = BoundedTrueSkillSystem('Goko Pro - Half Beta', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=0.5*1375, tau=27.5,
    draw_probability=0.05, backend='scipy'),
    mu_lower_bound=0, daily_sigma_decay=0.01)

goko = BoundedTrueSkillSystem('Goko Pro', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=1375, tau=27.5,
    draw_probability=0.05, backend='scipy'),
    mu_lower_bound=0, daily_sigma_decay=0.01)

goko2b = BoundedTrueSkillSystem('Goko Pro - 2x Beta', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=2*1375, tau=27.5,
    draw_probability=0.05, backend='scipy'),
    mu_lower_bound=0, daily_sigma_decay=0.01)

goko4b = BoundedTrueSkillSystem('Goko Pro - 4x Beta', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=4*1375, tau=27.5,
    draw_probability=0.05, backend='scipy'),
    mu_lower_bound=0, daily_sigma_decay=0.01)

goko8b = BoundedTrueSkillSystem('Goko Pro - 8x Beta', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=8*1375, tau=27.5,
    draw_probability=0.05, backend='scipy'),
    mu_lower_bound=0, daily_sigma_decay=0.01)

# Best guess (Apr 2014) for parameters used by Isotropic
dougz = TrueSkillSystem('dougz with decay', trueskill.TrueSkill(
    mu=25, sigma=25/3, beta=25, tau=25/300,
    draw_probability=0.05, backend='scipy'),
    daily_sigma_decay=0.01)

# Best guess (Apr 2014) for parameters used by Isotropic, excluding decay
dougz_nodecay = TrueSkillSystem('dougz nodecay', trueskill.TrueSkill(
    mu=25, sigma=25/3, beta=25, tau=25/300,
    draw_probability=0.05, backend='scipy'))

# Holger/WW suggestion (Isotropic with no per-game uncertainty increas)
dougz_only_decay = TrueSkillSystem('dougz no-tau; decay', trueskill.TrueSkill(
    mu=25, sigma=25/3, beta=25, tau=0,
    draw_probability=0.05, backend='scipy'),
    daily_sigma_decay=0.01)

# Parameters currently in use for Isotropish
isotropish = TrueSkillSystem('Isotropish', trueskill.TrueSkill(
    mu=25, sigma=25, beta=25, tau=25/100,
    draw_probability=0.05, backend='scipy'))

# Standard Elo, using a logistic curve with shape parameter 400
default_elo = LogisticEloSystem('Logistic Elo')

# Experimental improved parametrs
iso_tweak1 = TrueSkillSystem('Isotweak1', trueskill.TrueSkill(
    mu=25, sigma=25/3, beta=25/2, tau=25/300,
    draw_probability=0.0175, backend='scipy'))

# Microsoft's default TrueSkill parameters
default_ts = TrueSkillSystem('Default TS',
                             trueskill.TrueSkill(backend='scipy'))

# Goko Pro using the empirically observed draw probability
goko_fixed_draw = TrueSkillSystem('Goko TS', trueskill.TrueSkill(
    mu=5500, sigma=2250, beta=1375, tau=27.5,
    draw_probability=0.0175, backend='scipy'))


def isotropish_variant(name, beta_multiplier=1, noise_factor=0):
    return NoisyTrueSkillSystem('Isotropish %s' % name, trueskill.TrueSkill(
        mu=25, sigma=25, beta=25*beta_multiplier, tau=25/100,
        draw_probability=0.05, backend='scipy'), noise_factor=noise_factor)


def elo_variant(name, noise_factor=0):
    return NoisyEloSystem('Elo %s' % name, noise_factor=noise_factor)


def goko_variant(name, beta_factor=1, tau_factor=1,
                 draw_prob=0.05, decay=0.01):
    return BoundedTrueSkillSystem('Goko %s' % name, trueskill.TrueSkill(
        mu=5500, sigma=2250,
        beta=beta_factor*1375,
        tau=tau_factor*27.5,
        draw_probability=draw_prob,
        backend='scipy'),
        mu_lower_bound=0,
        daily_sigma_decay=decay)
