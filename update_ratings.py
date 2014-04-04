import datetime
import gdt.ratings.rating_system
from gdt.ratings.update import rate_games_since
from gdt.model import db_manager


if __name__ == '__main__':
    systems = [
        gdt.ratings.rating_system.dougz,
        gdt.ratings.rating_system.dougz_decayed,
        gdt.ratings.rating_system.dougz_tweaked,
        gdt.ratings.rating_system.goko,
        gdt.ratings.rating_system.goko_fixed_draw,
        gdt.ratings.rating_system.LogisticEloSystem('Logistic Elo'),
        gdt.ratings.rating_system.NoiseSystem('Noise', .0175)
    ]
    #rate_games_since(db_manager.get_last_rated_game())
    rate_games_since(None, None, systems)
