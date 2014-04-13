import sys
import datetime
import gdt.ratings.rating_system
from gdt.ratings.update import rate_games_since
from gdt.model import db_manager
from gdt.ratings.history import RatingAnalysis
from gdt.model.domgame import GameRanks

from gdt.ratings.rating_system import dougz
from gdt.ratings.rating_system import dougz_only_decay
from gdt.ratings.rating_system import isotropish
from gdt.ratings.rating_system import goko
from gdt.ratings.rating_system import default_ts
from gdt.ratings.rating_system import default_elo

chunk_size = 100

def compare_systems(rhistories, allow_guests=True, allow_bots=True,
                    max_games=None, rating_system='pro', min_turns=0,
                    only_2p_games=True):
    global chunk_size
    rate_games_since(None, None, rhistories,
                     chunk_size=chunk_size, max_games=sys.maxsize,
                     allow_guests=allow_guests, include_unknown_rs=False,
                     allow_bots=allow_bots, rating_system=rating_system,
                     min_turns=min_turns, only_2p_games=only_2p_games)
    return(rhistories)


def write_comparison(systems, allow_guests, allow_bots, max_games,
                     rating_system, min_turns, only_2p_games,
                     print_ratings):
    rhistories = [RatingAnalysis(s, skip_player=0) for s in systems]
    print('%s-player, %s mode, %s guests, %s bots, %s, %s min turns'
          % ('2' if only_2p_games else 'Multi',
             rating_system,
             'Allow' if allow_guests else 'No',
             'Allow' if allow_bots else 'No',
             ('%d games' % max_games) if max_games else 'All games',
             min_turns if min_turns else 'No'))
    out = compare_systems(rhistories, allow_guests=allow_guests,
                          allow_bots=allow_bots, max_games=max_games,
                          rating_system=rating_system, min_turns=min_turns,
                          only_2p_games=only_2p_games)
    for rh in out:
        print(rh)
        if (print_ratings):
            for r in reversed(sorted(rh.rating.items(), key=lambda x: x[1])):
                print(r)


if __name__ == '__main__':
    systems = [dougz, dougz_only_decay, isotropish, goko, default_ts, default_elo]

    if len(sys.argv) == 3:
        max_games = int(sys.argv[2])
    else:
        max_games = None

    if len(sys.argv) == 1 or len(sys.argv) > 3:
        print('Arguments: [mode] [num_games]')
        print('Ex: python compare_system.py 2 4000')
        sys.exit(-1)

    if sys.argv[1] == '1':
        write_comparison(systems, True, True, max_games, 'pro', 0, True, False)

    elif sys.argv[1] == '2':
        # 1+ turns
        write_comparison(systems, True, True, max_games, 'pro', 1, True, False)

    elif sys.argv[1] == '3':
        # No guests, 1+ turns
        write_comparison(systems, False, True, max_games,
                         'pro', 1, True, False)

    elif sys.argv[1] == '4':
        # No guests, no bots, 1+ turns
        write_comparison(systems, False, False, max_games,
                         'pro', 1, True, False)

    elif sys.argv[1] == '5':
        # Use multiplayer games for rating.  Use only 2-p games for stats
        write_comparison(systems, True, True, max_games,
                         'pro', 0, False, False)
