import math
import sys


# TODO: Implement some unit tests

class RatingHistory():
    def __init__(self, system):
        self.system = system      # e.g. isotropish, gokopro
        self.total_gamecount = 0

        # Player info
        self.rating = {}
        self.numgames = {}
        self.last_gametime = {}
        self.last_logfile = {}

        self.updated = set()

        self.games = []

    def clear_updated(self):
        self.updated = set()

    def get_latest_game(self):
        last_logfile = None
        last_time = None
        for pname in self.last_gametime:
            t = self.last_gametime[pname]
            lf = self.last_logfile[pname]
            if last_time is None or last_time < t:
                last_time = t
                last_logfile = lf
        return (last_logfile, last_time)

    def set_player(self, pname, rating, numgames, last_gametime, last_logfile):
        self.rating[pname] = rating
        self.numgames[pname] = numgames
        self.last_gametime[pname] = last_gametime
        self.last_logfile[pname] = last_logfile

    def get_pregame_ratings(self, game_ranks):
        # Fetch ratings without uncertainty decay
        ratings = {}
        for pname in game_ranks.pnames:
            # Initialize rating if necessary
            if pname not in self.rating:
                self.rating[pname] = self.system.new_player_rating()
                self.last_gametime[pname] = None
                self.last_logfile[pname] = None
                self.numgames[pname] = 0
            # Fetch current rating
            ratings[pname] = self.rating[pname]

        # Apply continuous uncertainty decay to ratings
        for pname in game_ranks.pnames:
            if self.last_gametime[pname] is not None:
                elapsed = game_ranks.time - self.last_gametime[pname]
                elapsed = elapsed.days + elapsed.seconds / (24 * 3600)
                ratings[pname] = self.system.decay(ratings[pname], elapsed)

        return ratings

    def add_game(self, game_ranks):
        ratings = self.get_pregame_ratings(game_ranks)

        rating_list = []
        rank_list = []
        for i in range(len(game_ranks.pnames)):
            rating_list.append(ratings[game_ranks.pnames[i]])
            rank_list.append(game_ranks.ranks[i])

        # Calculate new ratings
        ratings_list2 = self.system.rate(rating_list, game_ranks.ranks)

        for i in range(len(game_ranks.pnames)):
            pname = game_ranks.pnames[i]

            # Update ratings
            self.rating[game_ranks.pnames[i]] = ratings_list2[i]

            # Update other player info
            self.last_logfile[pname] = game_ranks.logfile
            self.last_gametime[pname] = game_ranks.time
            self.numgames[pname] += 1

            # Note that the rating has changed
            self.updated.add(pname)

        self.games.append(game_ranks)

    def print_ratings(self):
        for items in reversed(sorted(self.rating.items(), key=lambda x: x[1])):
            print('%-40s %5.2f +/- %5.2f' % (items[0], items[1].mu,
                                             (3 * items[1].sigma)))


class WinBin():
    def __init__(self, min_pct, max_pct):
        self.pct_range = [min_pct, max_pct]
        self.wins = 0
        self.losses = 0
        self.draws = 0

    def observed_winrate(self):
        total = self.wins + self.draws + self.losses
        if total > 0:
            return (self.wins + 0.5 * self.draws) / total
        else:
            return float('NaN')

    def predicted_winrate(self):
        return (self.pct_range[0] + self.pct_range[1]) / 2


class RatingAnalysis(RatingHistory):
    def __init__(self, system, skip_total=0, skip_player=0,
                 num_winrate_bins=100):
        """ For calculating measures of rating quality.  Should skip the first
            however many games total and/or per player before beginning to
            calculate summary statistics.
        """
        super(RatingAnalysis, self).__init__(system)

        # Minimum rated games per player before calculateing statistics
        self.skip_player = skip_player

        # Minimum total rated games before calculating statistics
        self.skip_total = skip_total

        # Accuracy binned by win rate prediction
        self.winbin = []
        for i in range(num_winrate_bins):
            minp = i * 1 / num_winrate_bins
            maxp = (i + 1) * 1 / num_winrate_bins
            self.winbin.append(WinBin(minp, maxp))

        # How many games have contributed to statistics
        self.total_gamecount_qualified = 0

        # Correct/incorrect predictions of decisive results in qualified games
        self.total_called = 0
        self.total_upsets = 0
        self.total_drawn = 0

        # Negative log likelihood for qualified games (base-10)
        self.total_deviance = 0

    def add_game(self, game_ranks):

        # Save pre-game ratings
        ratings = self.get_pregame_ratings(game_ranks)

        # Calculate post-game ratings
        super(RatingAnalysis, self).add_game(game_ranks)
        ratings2 = self.get_pregame_ratings(game_ranks)

        # Adjust prediction accuracy statistics.
        # Consider only 2-player games, and only after the minimum number of
        # games have been rated.
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

            # Wins and losses binned by win probability
            idx = int(pscore_a * len(self.winbin))
            wb = self.winbin[idx]
            if score_a == 0.5:
                wb.draws += 1
            elif score_a == 1:
                wb.wins += 1
            elif score_a == 0:
                wb.losses += 1
            else:
                raise ('Illegal value for score_a: %4.2f' % score_a)

            # Negative base-10 log likelihood (ala Glickman)
            # Bounded at 1% and 99% (ala Deloitte/FIDE competition)
            y = float(score_a)
            e = max(0.01, min(0.99, pscore_a))
            dev = -(y * math.log10(e) + (1 - y) * math.log10(1 - e))
            self.total_deviance += dev

            # Number of games to use for averages
            self.total_gamecount_qualified += 1

        # Track number of games processed
        for pname in game_ranks.pnames:
            self.numgames[pname] += 1
        self.total_gamecount += 1

    def print_winbins(self):
        for i in range(len(self.winbin)):
            wb = self.winbin[i]
            total = wb.wins + wb.draws + wb.losses
            print('%s,%s,%s' %
                  ('%6.4f' % wb.predicted_winrate(),
                   '%6.4f' % wb.observed_winrate() if total > 0 else '',
                   total if total > 0 else ''))

    def print_analysis(self):
        if self.total_gamecount_qualified == 0:
            return '%s - Empty' % (self.system.name)
        else:
            # TODO: Implement "swinginess" as mean reversion
            uprate = 100 * self.total_upsets / self.total_gamecount_qualified
            carate = 100 * self.total_called / self.total_gamecount_qualified
            dwrate = 100 * self.total_drawn / self.total_gamecount_qualified
            deviance = self.total_deviance\
                / self.total_gamecount_qualified
            accuracy = 100 * carate / (carate + uprate)
            return (("%s - Accuracy: %6.2f%%, Deviance: %6.4f") %
                    (self.system.name, accuracy, deviance))
