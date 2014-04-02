import math
import trueskill
from trueskill import Rating

class Result():
    def __init__(self, r1, r2, env, score, draw_margin):
        self.r1 = r1
        self.r2 = r2
        self.env = env
        self.score = score
        self.draw_margin = draw_margin

    def predict_score(self):
        return self.pwin() + self.env.draw_probability/2

    def calc_ll(self):
        e = self.predict_score()
        e = max(.01, e)
        e = min(.99, e)
        y = self.score
        x = -(y * math.log10(e) + (1 - y) * math.log10(1 - e))
        return x

    def pwin(self):
        deltaMu = self.r1.mu - self.r2.mu - self.draw_margin
        rsss = (self.r1.sigma**2 + self.r2.sigma**2
                + 2 * self.env.beta**2)**(0.5)
        return self.env.cdf(deltaMu/rsss)

    def plose(self):
        deltaMu = self.r2.mu - self.r1.mu - self.draw_margin
        rsss = (self.r1.sigma**2 + self.r2.sigma**2
                + 2 * self.env.beta**2)**(0.5)
        return self.env.cdf(deltaMu/rsss)

    def post_game_ratings(self):
        if self.score == 1:
            (ra2, rb2) = trueskill.rate_1vs1(self.r1, self.r2, env=self.env)
        elif self.score == -1:
            (ra2, rb2) = reversed(trueskill.rate_1vs1(self.r2, self.r1,
                                                      env=self.env))
        else:
            (ra2, rb2) = trueskill.rate_1vs1(self.r1, self.r2, env=self.env, drawn=True)
        return (ra2, rb2)
