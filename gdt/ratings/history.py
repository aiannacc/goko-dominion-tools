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

        self.total_deviance = 0
        self.total_gamecount = 0
        self.total_gamecount_qualified = 0

    #def add_game(self, pname_a, pname_b, score_a, gametime=None):
    def add_game(self, game_ranks, gametime=None):
        # Initialize ratings if necessary
        for pname in game_ranks.pnames:
            if pname not in self.rating:
                self.rating[pname] = self.system.new_player_rating()
                self.last_gametime[pname] = None
                self.numgames[pname] = 0

        # Fetch current ratings
        ratings = {}
        for pname in game_ranks.pnames:
            ratings[pname] = self.rating[pname] 

        # Apply uncertainty decay to current ratings
        elapsed = {}
        if gametime is not None:
            for pname in game_ranks.pnames:
                if self.last_gametime[pname] is not None:
                    elapsed = gametime - self.last_gametime[pname]
                    elapsed = elapsed.days + elapsed.seconds / (24 * 3600)
                    ratings[pname] = self.system.decay(ratings[pname], elapsed)
                self.last_gametime[pname] = gametime

        # Calculate new ratings
        ratings_values2 = self.system.rate(ratings.values(), game_ranks.ranks)
        ratings2 = {}
        for i in range(len(game_ranks.pnames)):
            ratings2[game_ranks.pnames[i]] = ratings_values2[i]

        # Track system's predication accuracy, using only games in which
        # both players have "established" ratings (minimum number of games)
        if (self.total_gamecount >= self.skip_total
                and len(game_ranks.pnames) == 2
                and self.numgames[game_ranks.pnames[0]] >= self.skip_player
                and self.numgames[game_ranks.pnames[1]] >= self.skip_player):

            r_a = ratings[game_ranks.pnames[0]]
            r_b = ratings[game_ranks.pnames[1]]
            r_a2 = ratings2[game_ranks.pnames[0]]
            r_b2 = ratings2[game_ranks.pnames[1]]
            score_a = 0.5 + 0.5 * (game_ranks.ranks[1] - game_ranks.ranks[0])

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
            # Bounded at 1% and 99% (ala Deloitte/FIDE competition)
            y = float(score_a)
            e = max(0.01, min(0.99, pscore_a))
            dev = -(y * math.log10(e) + (1 - y) * math.log10(1 - e))
            self.total_deviance += dev

            # Number of games to use for averages
            self.total_gamecount_qualified += 1

        # Update ratings
        for pname in game_ranks.pnames:
            self.rating[pname] = ratings2[pname]

        # Track number of games processed
        for pname in game_ranks.pnames:
            self.numgames[pname] += 1
        self.total_gamecount += 1

    def __str__(self):
        if self.total_gamecount_qualified == 0:
            return '%s - Empty' % (self.system.name)
        else:
            # TODO: Implement "swinginess" as mean reversion
            uprate = 100 * self.total_upsets / self.total_gamecount_qualified
            carate = 100 * self.total_called / self.total_gamecount_qualified
            dwrate = 100 * self.total_drawn / self.total_gamecount_qualified
            deviance = 100 * self.total_deviance\
                / self.total_gamecount_qualified
            accuracy = 100 * carate / (carate + uprate)
            return (("%s - Accuracy: %6.2f%%, Deviance: %6.2f") %
                    (self.system.name, accuracy, deviance))
