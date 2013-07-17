# Dominion game constants.

CORE_CARDS = ['estate', 'duchy', 'province', 'colony',
              'copper', 'silver', 'gold', 'platinum',
              'potion', 'curse', 'ruins']

# NOTE: Spoils can't be handled unambigously
NON_SUPPLY = {'diadem': 'tournament', 'followers': 'tournament',
              'trusty steed': 'tournament', 'princess': 'tournament',
              'bag of gold': 'tournament', 'madman': 'hermit',
              'mercenary': 'urchin'}

VP_CARDS = ['estate', 'duchy', 'province', 'colony', 'gardens', 'silk road',
            'vineyard', 'fairgrounds', 'duke', 'feodum', 'great hall',
            'nobles', 'tunnel', 'island']

RUINSES = ['ruined library', 'ruined village', 'survivors', 'ruined mine',
           'ruined market']

KNIGHTS = ['dame anna', 'dame josephine', 'dame molly', 'dame natalie',
           'dame sylvia', 'sir bailey', 'sir destry', 'sir vander',
           'sir michael', 'sir martin']

SHELTERS = ['hovel', 'overgrown estate', 'necropolis']

TREASURE_COUNTS = {'copper': 46, 'silver': 40, 'gold': 30, 'platinum': 12}

BOT_NAMES = ['Banker Bot', 'Conqueror Bot', 'Defender Bot', 'Lord Bottington',
             'Serf Bot', 'Villager Bot', 'Warlord Bot', 'Village Idiot Bot']
bot_copies = []
for bot in BOT_NAMES:
    for nth in ['I', 'II', 'III', 'IV', 'V', 'VI']:
        bot_copies.append('%s %s' % (bot, nth))
BOT_NAMES += bot_copies

