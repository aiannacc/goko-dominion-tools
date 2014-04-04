import math


class RatingHistory():
    def __init__(self, system, skip_total=0, skip_player=0):
        """ system should be an instance of RatingSystem """
        self.system = system
        self.skip_player = skip_player
        self.skip_total = skip_total

        self.rating = {}
        self.last_change = {}
        self.last_gametime = {}
        self.numgames = {}

        self.total_upsets = 0
        self.total_called = 0
        self.total_drawn = 0
        self.total_percent_swing = 0
        self.total_deviance = 0
        self.total_gamecount = 0
        self.total_gamecount_qualified = 0
        self.total_mr = 0

    def add_game(self, pname_a, pname_b, score_a, gametime=None):
        # Initialize ratings if necessary
        for pname in [pname_a, pname_b]:
            if pname not in self.rating:
                self.rating[pname] = self.system.new_player_rating()
                self.last_gametime[pname] = None
                self.numgames[pname] = 0
                self.last_change[pname] = 0

        # Fetch current ratings
        r_a = self.rating[pname_a]
        r_b = self.rating[pname_b]

        # Apply uncertainty decay to current ratings
        elapsed_a = elapsed_b = None
        if gametime is not None:
            if self.last_gametime[pname_a] is not None:
                elapsed_a = gametime - self.last_gametime[pname_a]
                elapsed_a = elapsed_a.days + elapsed_a.seconds / (24 * 3600)
                r_a = self.system.decay(r_a, elapsed_a)
            if self.last_gametime[pname_b] is not None:
                elapsed_b = gametime - self.last_gametime[pname_b]
                elapsed_b = elapsed_b.days + elapsed_b.seconds / (24 * 3600)
                r_b = self.system.decay(r_b, elapsed_b)
            self.last_gametime[pname_a] = gametime
            self.last_gametime[pname_b] = gametime

        # Calculate new ratings
        (r_a2, r_b2) = self.system.rate(r_a, r_b, score_a)

        # Track system's predication accuracy, using only games in which
        # both players have "established" ratings (minimum number of games)
        if self.total_gamecount >= self.skip_total\
                and self.numgames[pname_a] >= self.skip_player\
                and self.numgames[pname_b] >= self.skip_player:

            # Expected score
            pscore_a = self.system.predict_score(r_a, r_b)

            # Simple upset measure.  Player with higher win probability is
            # expected to win.  Draws are ignored.
            if score_a == 0.5:
                self.total_drawn += 1
            elif round(pscore_a) == score_a:
                self.total_called += 1
            else:
                self.total_upsets += 1

            # Negative base-10 log likelihood (ala Glickman)
            # Bounded at 1% and 99% (ala Deloitte/FIDE)
            y = float(score_a)
            e = max(0.01, min(0.99, pscore_a))
            dev = -(y * math.log10(e) + (1 - y) * math.log10(1 - e))
            self.total_deviance += dev

            # Crude measure of mean reversion
            r_a_change = self.system.as_scalar(r_a2) \
                - self.system.as_scalar(r_a)
            x = r_a_change
            y = self.last_change[pname_a]
            if (x > 0 and y > 0):
                self.total_mr += x * y / (x**2 + y**2)
            self.last_change[pname_a] = r_a_change

            r_b_change = self.system.as_scalar(r_b2) \
                - self.system.as_scalar(r_b)
            x = r_b_change
            y = self.last_change[pname_b]
            if (x > 0 and y > 0):
                self.total_mr += x * y / (x**2 + y**2)**(0.5)
            self.last_change[pname_b] = r_b_change

            # Number of games to use for averages
            self.total_gamecount_qualified += 1

        # Update ratings
        self.rating[pname_a] = r_a2
        self.rating[pname_b] = r_b2

        # Track number of games processed
        self.numgames[pname_a] += 1
        self.numgames[pname_b] += 1
        self.total_gamecount += 1

    def __str__(self):
        if self.total_gamecount_qualified == 0:
            return '%s - Empty' % (self.system.name)
        else:
            # TODO: Implement "swinginess" as mean reversion
            uprate = 100 * self.total_upsets / self.total_gamecount_qualified
            carate = 100 * self.total_called / self.total_gamecount_qualified
            dwrate = 100 * self.total_drawn / self.total_gamecount_qualified
            swingy = -100 * self.total_mr / self.total_gamecount_qualified
            deviance = 100 * self.total_deviance\
                / self.total_gamecount_qualified
            accuracy = 100 * carate / (carate + uprate)
            return (("%s - Accuracy: %6.2f%%, "
                    + "Swinginess: %6.2f%%, Deviance: %6.2f") %
                    (self.system.name, accuracy, swingy, deviance))
