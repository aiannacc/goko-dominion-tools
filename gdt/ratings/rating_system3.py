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

    # Generate a pseudo-random game result based on the given skill levels
    # Only wins and losses are generated.  No draws.
    def random_result(self, s1, s2):
        x = random.random()
        if x < self.predict_score(s1, s2):
            return 1
        else:
            return 0


class LogisticEloSystem(RatingSystem):
    def __init__(self, name, scale=400, k=15, new_rating=1500):
        super(LogisticEloSystem, self).__init__(name)
        self.scale = scale
        self.k = k
        self.new_rating = new_rating

    def new_player_rating(self):
        return self.new_rating

    def predict_score(self, r_a, r_b):
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
            # Silently return ratings unchanged if asked to rate muliplayer
            return ratings


class NoisyEloSystem(LogisticEloSystem):
    def __init__(self, name, noise_factor=0.1, **kwargs):
        super(NoisyEloSystem, self).__init__(name, **kwargs)
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
            # Silently return ratings unchanged if asked to rate muliplayer
            return ratings


class TrueSkillSystem(RatingSystem):
    """ Microsoft TrueSkill as implemented by the PyPi package "trueskill",
        available at trueskill.org.  Keyword arguments are passed on to the
        TrueSkill __init__.
    """
    def __init__(self, name, daily_sigma_decay=0, k=3,
                 established_sigma=None, **kwargs):
        super(TrueSkillSystem, self).__init__(name)
        self.env = trueskill.TrueSkill(**kwargs)
        self.daily_sigma_decay = daily_sigma_decay
        self.established_sigma = established_sigma
        self.k = k
        self.two_p_draw_margin = trueskill.calc_draw_margin(
            self.env.draw_probability, 2, env=self.env)

    def new_player_rating(self):
        return trueskill.Rating(self.env.mu, self.env.sigma)

    def win_prob(self, r_a, r_b):
        deltaMu = r_a.mu - r_b.mu - self.two_p_draw_margin
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
            return list(reversed(self.rate2p(r_b, r_a, 1)))
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

    def level(self, rating):
        return rating.mu - self.k * rating.sigma


class NoisyTrueSkillSystem(TrueSkillSystem):
    def __init__(self, name, noise_factor=0, **kwargs):
        super(NoisyTrueSkillSystem, self).__init__(name, **kwargs)
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
    def __init__(self, name, mu_lower_bound=0, **kwargs):
        super(BoundedTrueSkillSystem, self).__init__(name, **kwargs)
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
